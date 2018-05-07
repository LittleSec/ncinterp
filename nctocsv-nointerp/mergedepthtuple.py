import pandas as pd
import numpy as np
import os
import time

ROOTPATH = '/Users/openmac/Downloads/LittleSec/'

DEPTHLIST = ['0.0m', '8.0m', '15.0m', '30.0m', '50.0m']

ATTRLIST = ['salinity', 'water_temp', 'water_u', 'water_v']

def mergedepth(attr):
    if not os.path.exists(attr):
        os.makedirs(attr)
    folderList = []
    for depth in DEPTHLIST:
        folderList.append(attr + ',' + depth + '_tuple')
    fileList = os.listdir(folderList[0])
    for file in fileList:
        if file[-4:] == '.csv':
            flat = False
            for folder in folderList:
                df1 = pd.read_csv('/'.join([folder, file]))
                if flat:
                    df2 = pd.merge(df2, df1, how='inner', on=['lon', 'lat'])
                else:
                    df2 = df1.copy()
                    flat = True
            df2.to_csv('/'.join([attr, file]), index=False, na_rep='NaN')

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    for attr in ATTRLIST:
        mergedepth(attr)
        print("run time: "+str(time.clock()-start)+" s")
        start = time.clock()