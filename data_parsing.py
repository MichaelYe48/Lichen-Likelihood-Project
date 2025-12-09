import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
from collections import defaultdict


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

    return df, intervals.tolist()

def binYearNode(colName, df):
    newColName = colName + '_binned'
    bins = ["before 1995", "1995-2005", "2005-present"]
    intervals = [0,1995,2005,np.inf]
    df[newColName] = pd.cut(df[colName], intervals, labels=bins)
    return df, intervals

def binAirPollutionNode(colName, df):
    newColName = colName + '_binned'
    bins = ['unaffected','affected']
    intervals = [-np.inf, -.11, np.inf]
    #intervals = [-10, -.11, .02, .21, .35, .49, np.inf]
    #bins = ['best', 'good', 'fair', 'degraded', 'poor', 'worst']
    df[newColName] = pd.cut(df[colName], intervals, labels=bins)
    return df, intervals

    #return binElementNode(colName, df) #percentile binning

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
    bins = [list(v) for k,v in inv_map.items()]
    return df, bins

def binSpeciesNode(colName,df):
    df.dropna(subset=[colName], inplace=True)
    newColName = colName + '_binned'
    bins = {
        'alesar' :'Species 1',
        'flacap' : 'Species 2',
        'hypina' : 'Species 3',
        'letvul' : 'Species 4',
        'plagla' : 'Species 5'
    }
    df[newColName] = df[colName].map(bins).fillna('Other')
    return df, list(bins.keys())+['Other']
    


#Load
path = 'element_analysis.csv'
df = loadData(path)

#Elements
element_list = [
    'nitrogen',
    'sulfur',
    'phosphorous',
    'lead',
    'copper',
    'chromium'
    #'air pollution score'
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
    df_mod, newCol = filterByNode(n,df_mod,verbose=False)
    if n in element_list:
        elementNames.append(newCol)

for n in notNum_list:
    df_mod, newCol = filterByNode(n,df_mod,isNum=False,verbose=False)


#Bin elements
nodeNameBinMap = defaultdict(list)
for n in elementNames:
    df_mod, intervals = binElementNode(n,df_mod)
    nodeNameBinMap[n] = intervals
# Bin other nodes
df_mod, inF = binYearNode(num_list[0],df_mod)
df_mod, inP = binAirPollutionNode(num_list[1],df_mod)
df_mod, inR = binRegionNode(notNum_list[0],df_mod)
df_mod, inS = binSpeciesNode(notNum_list[1],df_mod)
for name,bin in zip(num_list+notNum_list,[inF,inP,inR,inS]):
    nodeNameBinMap[name] = bin
for node,bin in nodeNameBinMap.items():
    print(f"{node}: {bin}")

#Final DF:
bin_names = [b for b in list(df_mod.columns) if "_binned" in b]
final_df = df_mod[bin_names]
print(f'Cleaned dataset shape: {final_df.shape}')
final_df.to_pickle('element_analysis.pkl')

#To load pickle file:
#unpickled_df = pd.read_pickle('element_analysis.pkl') 