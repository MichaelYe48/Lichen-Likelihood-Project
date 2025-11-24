import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt


def loadData(file_name):
    '''
    Loads csv containing element analysis data

    Input:
        file_name - path and name for csv containing data
    Output:
        element_df - pandas DataFrame containing loaded data
    '''
    #force element cols to be floats
    with open(file_name, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        element_headers = [h for h in next(csv_reader) if 'dw' in h]
    typeDict = dict.fromkeys(element_headers, np.float64)
    
    element_df = pd.read_csv(file_name, engine='python', on_bad_lines='skip',
                             dtype=typeDict, na_values=['n.d.','nd','n.d'],keep_default_na=True)
    return element_df



def filterByElement(name, element_df, min=None, max=None, verbose=False):
    '''
    Filters DataFrame based on a single column

    Input:
        name - string to search for within column headers. Does not need to be entire name
        element_df - pandas DataFrame containing loaded data
    Output:
        filtered_df - pandas dataframe containing filtered data
    '''
    #Get desired column, filter for NaNs
    header = [col_name for col_name in element_df.columns if name.lower() in col_name.lower()]
    assert len(header)==1, f"Expected 1 column to be fetched for name {name}. Got: {len(header)}"
    col = header[0]

    #Filter out NaN and min/max, if passed in
    filtered_df = element_df.dropna(subset=[col])
    if min!=None:
        filtered_df = filtered_df[filtered_df[col] >= min]
    if max!=None:
        filtered_df = filtered_df[filtered_df[col] <= max]

    #Look at data
    if verbose:
        print(filtered_df[col].describe())
        hist = df[col].hist(bins=1000)
        plt.show()

    return filtered_df




if __name__ == "__main__":
    path = 'air_lichen_query.csv'
    df = loadData(path)
    #Copper, Chromium, Nickel, Iron
    df_filtered = df.copy()
    print(f'Original df size: {len(df_filtered)}')
    cols = ['copper','chromium','nickel','iron','year']
    for i in cols:
        filterByElement(i,df_filtered,verbose=True)