"""
Decode air_lichen_query codenames to scientific names using a plant list,
but only add/populate the scientific name for rows where the air file's
'Name' column is blank or NaN.

Rule for codenames:
- Codename = first 3 letters of genus + first 3 letters of species + first 3 letters of subspecies (if present).
- Ties are broken by appending the first differing letter(s) in the species epithet between colliding names.

"""
#!/usr/bin/env python3
import pandas as pd
import re
import unicodedata

# -------------------- I/O helpers -------------------- #

def robust_read(path: str) -> pd.DataFrame:
    """
    Try to read a CSV file; if that fails, retry with python engine and then with tab separator.
    """
    for kwargs in (
        {},
        {"engine": "python", "on_bad_lines": "skip"},
        {"sep": "\t", "engine": "python", "on_bad_lines": "skip"},
    ):
        try:
            return pd.read_csv(path, **kwargs)
        except Exception:
            continue
    # If everything failed, let the last error propagate
    return pd.read_csv(path)


# -------------------- Name / code helpers -------------------- #

def normalize_token(s: str) -> str:
    """Normalize Latin name token: strip accents, lowercase, keep only a–z."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    return re.sub(r"[^a-z]", "", s)


def parse_scientific_name(name_with_author: str):
    """
    Parse 'Genus species [subsp. ...] Author' into (genus, species, subspecies),
    normalized for coding.
    """
    if not isinstance(name_with_author, str):
        return "", "", ""

    tokens = name_with_author.strip().split()
    if not tokens:
        return "", "", ""

    genus = normalize_token(tokens[0])
    species = ""
    subspecies = ""

    i = 1
    while i < len(tokens):
        raw = tokens[i]
        t = raw.lower().strip(".")

        if t in {"sp", "sp.", "cf", "cf.", "aff", "aff.", "nr", "nr."}:
            i += 2
            continue

        # Clean alphabetical token after genus is the species
        if not species and re.fullmatch(r"[A-Za-z-]+", raw):
            species = normalize_token(raw)
            i += 1
            continue

        # Subspecies / variety, e.g. 'subsp. foo', 'var. bar'
        if t in {"subsp", "ssp", "var", "forma", "f"} and i + 1 < len(tokens):
            subspecies = normalize_token(tokens[i + 1])
            i += 2
            continue

        i += 1

    return genus, species, subspecies


def base_code(genus: str, species: str, subspecies: str = "") -> str:
    """
    Base code: first 3 letters of genus + species (+ subspecies if present).
    """
    return (genus[:3] + species[:3] + subspecies[:3]).lower()


def resolve_ties(group: pd.DataFrame) -> pd.DataFrame:
    """
    For a single base_code group, ensure each row gets a unique 'codename'.
    Start from the shared base_code and append additional letters from
    the species epithet until unique; if still colliding, add numeric suffixes.
    """
    base = group.name  # base_code value for this group

    # Trivial case: only one row
    if len(group) == 1:
        out = group.copy()
        out["codename"] = base
        return out

    species_list = group["species_full"].tolist()
    max_len = max(len(s) for s in species_list)

    # start every codename with the same base
    codenames = [base] * len(group)

    # append differing letters from species epithet until unique
    for idx in range(3, max_len):
        chars = [s[idx] if idx < len(s) else "" for s in species_list]

        # bucket by current code to find collisions
        buckets = {}
        for i, code in enumerate(codenames):
            buckets.setdefault(code, []).append(i)

        any_collision = False
        for code, idxs in buckets.items():
            if len(idxs) > 1:
                any_collision = True
                for i in idxs:
                    extra = chars[i]
                    if extra:
                        codenames[i] += extra

        if not any_collision:
            break

    # last fallback
    seen = {}
    for i, code in enumerate(codenames):
        if code in seen:
            seen[code] += 1
            codenames[i] = f"{code}{seen[code]}"
        else:
            seen[code] = 1

    out = group.copy()
    out["codename"] = codenames
    return out


# -------------------- Main pipeline -------------------- #

def main():
    air_path = "../air_lichen_query.csv"
    plant_path = "../plantlist.csv"
    air_code_col = "Code for scientific name and authority in lookup table"
    plant_sci_col = "Scientific Name with Author"
    name_col = "Name"
    out_joined = "air_lichen_scinames.csv"

    # Read data
    air_df = robust_read(air_path)
    plant_df = robust_read(plant_path)

    # Parse names from plant list
    names = plant_df[plant_sci_col].astype(str).fillna("")
    parsed_series = names.apply(parse_scientific_name)
    plant_parsed = pd.DataFrame(parsed_series.tolist(), columns=["genus", "species", "subspecies"])

    # Reconstruct a clean scientific name
    plant_parsed["sci_name"] = (
        plant_parsed["genus"].str.capitalize()
        + " "
        + plant_parsed["species"]
        + plant_parsed.apply(
            lambda r: f" subsp. {r['subspecies']}" if r["subspecies"] else "",
            axis=1,
        )
    )

    # Base codes and tie resolution
    plant_parsed["base_code"] = plant_parsed.apply(
        lambda r: base_code(r["genus"], r["species"], r["subspecies"]),
        axis=1,
    )
    plant_parsed["species_full"] = plant_parsed["species"]

    gb = plant_parsed.groupby("base_code", group_keys=False)
    try:
        resolved = gb.apply(resolve_ties, include_groups=False).reset_index(drop=True)
    except TypeError:
        resolved = gb.apply(resolve_ties).reset_index(drop=True)

    mapping_df = resolved[["codename", "sci_name"]].drop_duplicates()

    # Merge mapping into air table
    merged = air_df.merge(mapping_df, left_on=air_code_col, right_on="codename", how="left")

    # Only fill Name where it's blank or NaN
    if name_col not in merged.columns:
        raise ValueError(f"Name column '{name_col}' not found in air file.")

    is_blank = merged[name_col].isna() | (merged[name_col].astype(str).str.strip() == "")
    merged.loc[is_blank, name_col] = merged.loc[is_blank, "sci_name"]

    merged.to_csv(out_joined, index=False)


if __name__ == "__main__":
    main()
