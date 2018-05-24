# 计算异常模块
# 参考OkuboWeiss-correction-branch分支下的anomaly.py，本代码的缺点在于需要遍历目录12次。当然两份代码适用的文件目录不一样
# 多年逐月平均值
# 整份代码使用grid形式的csv

import os
import numpy as np
import pandas as pd
import time

ROOTPATH = '/Users/openmac/Downloads/LittleSec/OceanVisualizationD3/oceandata'

def calMean(month, srcPath, tarPath):
    '''
    计算距平
    params:
        month: int or str
    attention:
        请确保年月合法和存在对应的文件，确保网格统一。
        确保文件名为: yyyy-mm-dd.csv
    output:
        tarPath/mm.csv
    '''
    
    mm = '{:0>2}'.format(month)
    cnt = 0
    sum = 0
    for file in os.listdir(srcPath):
        if file[5:7] == mm and file[-4:] == '.csv':
            csv = np.genfromtxt('/'.join([srcPath, file]), delimiter=',')
            lon = csv[0,1:]
            lat = csv[1:,0]
            value = np.round(csv[1:,1:], 6)
            sum += value
            cnt += 1
    thisMonthMean = sum / cnt
    pd.DataFrame(thisMonthMean, columns=lon, index=lat).to_csv('/'.join([tarPath, mm+'.csv']), na_rep='NaN')
    
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
    meancsv = np.genfromtxt('/'.join([meanPath, srcFile[5:7]+'.csv']), delimiter=',')
    attr = np.round(csv[1:, 1:], 6)
    mean = meancsv[1:, 1:]
    anomaly = attr - mean
    pd.DataFrame(anomaly, columns=lon, index=lat).to_csv('/'.join([tarPath, srcFile]), na_rep='NaN')

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    srcPath = 'surf_el_grid'
    meanPath = 'ssh_mean_monthly_grid'

    # 计算平均值
    if not os.path.exists(meanPath):
        os.makedirs(meanPath)
    for month in range(1,13):
        calMean(month, srcPath, meanPath)
        print("run time: "+str(time.clock()-start)+" s")
        start = time.clock()
    
    # 计算异常值
    anomalyPath = 'sla_grid'
    if not os.path.exists(anomalyPath):
        os.makedirs(anomalyPath)
    for file in os.listdir(srcPath):
        if file[-4:] == '.csv':
            calAnomaly(file, srcPath, anomalyPath, meanPath)
    print("run time: "+str(time.clock()-start)+" s")