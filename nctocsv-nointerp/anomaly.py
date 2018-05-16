# 计算异常模块
# 参考OkuboWeiss-correction-branch分支下的anomaly.py
# 逐月多日平均值
# 整份代码使用grid形式的csv

import os
import numpy as np
import pandas as pd
import time

ROOTPATH = '/Users/openmac/Downloads/'

def calMean(year, month, srcPath, tarPath):
    '''
    计算一个月的平均值
    params:
        year: int or str
        month: int or str
    attention:
        请确保年月合法和存在对应的文件，确保网格统一
    output:
        tarPath/yyyy-mm.csv
    '''
    
    ym = '{:>4}-{:0>2}'.format(year, month)
    fileList = []
    for file in os.listdir(srcPath):
        if file[:7] == ym and file[-4:] == '.csv':
            fileList.append('/'.join([srcPath, file]))
    sum = 0
    for file in fileList:
        csv = np.genfromtxt(file, delimiter=',')
        lon = csv[0,1:]
        lat = csv[1:,0]
        value = csv[1:,1:]
        sum += value
    thisMonthMean = sum / len(fileList)
    pd.DataFrame(thisMonthMean, columns=lon, index=lat).to_csv('/'.join([tarPath, ym+'.csv']), na_rep='NaN')
    
def calAnomaly(srcFile, srcPath, tarPath, meanPath):
    '''
    params:
        源文件、源路径、目标存储路径、平均值存放路径
    output:
        tarPath/srcFile
    attention:
        确保网格一致，确保文件存在
    '''
    csv = np.genfromtxt('/'.join([srcPath, srcFile]), delimiter=',')
    lon = csv[0,1:]
    lat = csv[1:,0]
    meancsv = np.genfromtxt('/'.join([meanPath, srcFile[:7]+'.csv']), delimiter=',')
    attr = csv[1:, 1:]
    mean = meancsv[1:, 1:]
    anomaly = attr - mean
    pd.DataFrame(anomaly, columns=lon, index=lat).to_csv('/'.join([tarPath, srcFile]), na_rep='NaN')

YEARS_MONTHS_DICT = {
    "2014": [7, 8, 9, 10, 11, 12],
    "2015": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "2016": [5, 6, 7, 8, 9, 10, 11, 12],
    "2017": [1, 2, 3, 4, 5, 6, 7, 8, 9]
}


def dealAfolderAnomaly(srcFolder, meanFolder, tarPath):
    pass

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    srcPath = 'surf_el_grid'
    meanPath = 'ssh_mean_monthly_grid'

    # 计算平均值
    # if not os.path.exists(meanPath):
    #     os.makedirs(meanPath)
    # for year, months in YEARS_MONTHS_DICT.items():
    #     for month in months:
    #         calMean(year, month, srcPath, meanPath)
    #     print("run time: "+str(time.clock()-start)+" s")
    
    # 计算异常值
    anomalyPath = 'sla_grid'
    if not os.path.exists(anomalyPath):
        os.makedirs(anomalyPath)
    for file in os.listdir(srcPath):
        if file[-4:] == '.csv':
            calAnomaly(file, srcPath, anomalyPath, meanPath)
    print("run time: "+str(time.clock()-start)+" s")