import ncinterp as ni
import os
import numpy as np
import csvjsonwriteop

def classifyFile(sourcePathAbs):
    os.chdir(sourcePathAbs)
    fileList = os.listdir()
    monthFileClassifyDict = {} # 共12个键值对
    # key为两位数的月份表示，value是对应csv文件的绝对路径
    for i in range(1, 13):
        monthFileClassifyDict["{:0>2}".format(i)] = []
    for file in fileList:
        if file[-4:] == '.csv':
            month = file[5:7]
            monthFileClassifyDict[month].append(sourcePathAbs + '/' + file)
    return monthFileClassifyDict

def calMean(monthFileClassifyDict):
    monthMeanDict = {} # 除了存储12个月的平均值外，还要存经纬度
    for month, fileList in monthFileClassifyDict.items():
        sum = 0
        for file in fileList:
            csv = np.genfromtxt(file, delimiter=',')
            if not 'x' in monthMeanDict:
                monthMeanDict['x'] = csv[0,1:]
            if not 'y' in monthMeanDict:
                monthMeanDict['y'] = csv[1:,0]
            ssh = csv[1:,1:]
            sum += ssh
        thisMonthMeanSSH = sum / len(fileList)
        monthMeanDict[month] = thisMonthMeanSSH
    return monthMeanDict

def writeMeanInCSV(rootPath, sourceFolder, meanDict):
    '''
    不适用于稠密网格数据，否则内存不够用而终止程序
    sourceFolder: like 'sea_surface_height1960-2008_grid_(33x25)'
    '''
    os.chdir(rootPath)
    targetFolder = 'MEAN_' + sourceFolder
    if not os.path.exists(targetFolder):
        os.makedirs(targetFolder)
    os.chdir(targetFolder)
    for month, mean in meanDict.items():
        if month in ['x', 'y']:
            continue
        absFileName = '{0}/{1}/{2}.csv'.format(rootPath, targetFolder, month)
        csvjsonwriteop.writeCSVgrid(meanDict['x'], meanDict['y'], mean, absFileName=absFileName)

def calAnomalyAndWriteInCSV(rootPath, sourceFolder, meanDict=None):
    os.chdir(rootPath)
    meanFolder = 'MEAN_' + sourceFolder
    anomalyFolder = 'ANOMALY_' + sourceFolder
    if not os.path.exists(anomalyFolder):
        os.makedirs(anomalyFolder)
    if meanDict is None:
        meanDict = {}
        os.chdir(meanFolder)
        fileList = os.listdir()
        for file in fileList:
            if file[-4:] == '.csv':
                csv = np.genfromtxt(file, delimiter=',')
                if not 'x' in meanDict:
                    meanDict['x'] = csv[0,1:]
                if not 'y' in meanDict:
                    meanDict['y'] = csv[1:,0]
                meanDict[file[:2]] = csv[1:,1:]
        os.chdir('..')
    
    os.chdir(sourceFolder)
    fileList = os.listdir()
    for file in fileList:
        if file[-4:] == '.csv':
            month = file[5:7]
            csv = np.genfromtxt(file, delimiter=',')
            value = csv[1:,1:]
            anomaly = value - meanDict[month]
            absFileName = '/'.join([rootPath, anomalyFolder, file])
            csvjsonwriteop.writeCSVgrid(meanDict['x'], meanDict['y'], anomaly, absFileName=absFileName)

if __name__ == '__main__':
    rootPath = r'/Users/littlesec/Desktop/毕业论文实现/SODA v2p2p4 new'
    sourceFolder = 'sea_surface_height1960-2008_grid_(193x145)'
    path = rootPath + '/' + sourceFolder
    fileDict = classifyFile(path)
    meanDict = calMean(fileDict)
    writeMeanInCSV(rootPath, sourceFolder, meanDict)
    calAnomalyAndWriteInCSV(rootPath, sourceFolder, meanDict=meanDict)