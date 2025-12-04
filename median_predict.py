import numpy as np
import pandas as pd

unpickled_df = pd.read_pickle('element_analysis.pkl')
airPolName = [col for col in unpickled_df if 'air pollution' in col.lower()][0]
airPoll = unpickled_df[airPolName]

vals = airPoll.unique()
counts = []
for i in vals:
    curr = (airPoll == i).sum()
    counts.append(curr)

ind = counts.index(max(counts))
print(f'Value: {vals[ind]}')
print(f'accuracy: {counts[ind] / sum(counts)}')