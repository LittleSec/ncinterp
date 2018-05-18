# 没有查重功能切勿重复跑
# 处理一个文件需要的时间很长，不建议一次性跑完5个深度。跑一个深度也很久了。

import pandas as pd
import os
import numpy as np
import time

ROOTPATH = '/Users/openmac/Downloads/LittleSec/OceanVisualizationD3/oceandata'
DEPTHLIST = ['0.0m', '8.0m', '15.0m', '30.0m', '50.0m']

def floatToStr(num):
    return str(num).replace('.', 'p')

def ddToll(fileName, depth, srcPath):
    '''
    1date1depth csv to lonlat csv
    fileName is date, too
    depth is str with units
    '''
    df = pd.read_csv('/'.join([srcPath, fileName])).round(6)
    df['date'] = fileName[:-4]
    df['depth'] = depth
    dicts = df.to_dict('record')
    for record in dicts:
        tarPath = floatToStr(record['lon'])
        tarFile = '/'.join([tarPath, floatToStr(record['lat'])+'.csv'])
        del record['lon']
        del record['lat']
        df1 = pd.DataFrame(data=record, index=['new'])
        if os.path.isfile(tarFile):
            df2 = pd.read_csv(tarFile)
            pd.concat([df2, df1], axis=0, ignore_index=True).to_csv(tarFile, index=False)
        elif not os.path.exists(tarPath):
            os.makedirs(tarPath)
            df1.to_csv(tarFile, index=False)
        else:
            df1.to_csv(tarFile, index=False)

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    depth = DEPTHLIST[0]
    for file in os.listdir(depth):
        if file[-4:] == '.csv':
            ddToll(file, depth, depth)
        print("now the file is " + file + " run time: "+str(time.clock()-start)+" s")
        start = time.clock()