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
    #read
    with open(file_name, 'r', newline='') as file:
        csv_reader = csv.reader(file)
        target_headers = [h for h in next(csv_reader) if 'dw' in h or 'year' in h.lower() or 'pollution' in h.lower()]

    df = pd.read_csv(file_name, engine='python', on_bad_lines='skip',
                     na_values=['n.d.','nd','n.d'],keep_default_na=True)

    return df



def filterByNode(name, df, min=None, max=None, isNum = True, verbose=False):
    '''
    Filters DataFrame based on a single column to remove NaN

    Input:
        name - string to search for within column headers. Does not need to be entire name
        df - pandas DataFrame containing loaded data
    Output:
        filtered_df - pandas dataframe containing filtered data
    '''
    #Get desired column, filter for NaNs
    header = [col_name for col_name in df.columns if name.lower() in col_name.lower()]
    assert len(header)>0, f"Expected 1 column to be fetched for name {name}. Got: {len(header)}"
    col = header[0]

    #Filter
    filtered_df = df.copy()
    if isNum:
        filtered_df[col] = pd.to_numeric(df[col], errors='coerce')
        #Min / max
        if min!=None:
            filtered_df = filtered_df[filtered_df[col] >= min]
        if max!=None:
            filtered_df = filtered_df[filtered_df[col] <= max]

    filtered_df.dropna(subset=col, inplace=True)

    #Look at data
    if verbose:
        print(filtered_df[col].describe())
        #hist = df[col].hist(bins=1000)
        plt.show()

    return filtered_df, col



def binElementNode(colName, df):
    '''
    Creates new column in df to store binned values for given element.
    -based on value percentiles
    '''
    newColName = colName + '_binned'
    bins = ['low', 'medium', 'high']
    df[newColName] = pd.qcut(df[colName], q=3, labels=bins, retbins=True)

    return df, newColName


def binSpecialNode(colName, df, bins, values):
    '''
    Creates new column in df to store binned values for given node.
    -based on values passed in
    '''
    newColName = colName + '_binned'
    df[newColName] = pd.qcut(df[colName], q=3, labels=bins, retbins=True)


#Load
path = 'air_lichen_query.csv'
df = loadData(path)

#Elements
element_list = [
    'nitrogen',
    'sulfur',
    'phosphorous',
    'lead',
    'copper',
    'chromium'
    #'potassium', 'manganese'
]

#Other nodes
num_list = [
    'Year of tissue collection',
    'Air pollution score'
]
notNum_list = [
    'region',
    'Code for scientific name'
]

#Filter
df_mod = df.copy()
colNames = []
for n in element_list+num_list:
    df_mod, newCol = filterByNode(n,df_mod,verbose=True)
    colNames.append(newCol)

for n in notNum_list:
    df_mod, newCol = filterByNode(n,df_mod,isNum=False,verbose=True)
    colNames.append(newCol)

#Bin
bin_names = []
for n in element_list+num_list:
    df_mod, binCol = binElementNode(n,df_mod,verbose=True)
    bin_names.append(newCol)


print(df_mod.shape)

#Final DF:
final_df = df_mod[bin_names]