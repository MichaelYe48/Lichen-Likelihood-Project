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
    df[newColName], intervals = pd.qcut(df[colName], q=3, labels=bins, retbins=True)

    return df, newColName, intervals

def binYearNode(colName, df):
    newColName = colName + '_binned'
    bins = ["before 1995", "1995-2005", "2005-present"]
    intervals = [0,1995,2005,np.inf]
    df[newColName] = pd.cut(df[colName], intervals, labels=bins)
    return df

def binAirPollutionNode(colName, df):
    newColName = colName + '_binned'
    bins = ['best', 'good', 'fair', 'degraded', 'poor', 'worst']
    intervals = [-10, -.11, .02, .21, .35, .49, np.inf]
    df[newColName] = pd.cut(df[colName], intervals, labels=bins)
    return df

def binRegionNode(colName, df):
    df.dropna(subset=[colName], inplace=True)
    newColName = colName + '_binned'
    bins = {
        '1-4' : [1,2,3,4,14],
        '5'   : [5],
        '6'   : [6],
        '7'   : [7],
        '8-9' : [8,9,89],
        '10'  : [10] 
    }
    inv_map = { v : k for (k,l) in bins.items() for v in l}
    df[newColName] = df[colName].map(inv_map)
    return df

def binSpeciesNode(colName,df):
    #TODO: Not implemented yet, but will be similar to region binning
    return df
    


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
    'Region',
    'Code for scientific name and authority in lookup table'
]

#Filter
df_mod = df.copy()
elementNames = []
for n in element_list+num_list:
    df_mod, newCol = filterByNode(n,df_mod,verbose=True)
    elementNames.append(newCol)

for n in notNum_list:
    df_mod, newCol = filterByNode(n,df_mod,isNum=False,verbose=True)

bin_names = []
#Bin elements
elementIntervals = []
for n in elementNames+num_list:
    df_mod, binCol, intervals = binElementNode(n,df_mod)
    bin_names.append(newCol)
    elementIntervals.append(intervals)
# Bin other nodes
df_mod = binYearNode(num_list[0],df_mod)
df_mod = binAirPollutionNode(num_list[1],df_mod)
df_mod = binRegionNode(notNum_list[0],df_mod)
df_mod = binSpeciesNode(notNum_list[1],df_mod)

print(df_mod.shape)

#Final DF:
final_df = df_mod[bin_names]
final_df.to_pickle('element_analysis.pkl')

#To load pickle file:
#unpickled_df = pd.read_pickle('element_analysis.pkl') 