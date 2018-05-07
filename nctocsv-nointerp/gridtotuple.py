import pandas as pd
import numpy as np
import os
import time

ROOTPATH = '/Users/openmac/Downloads/LittleSec/'


def grid2Tuple(sourceFile, targetPath, depth=None):
    '''
    param:
        sourceFile: a grid csv file name, like: '2016-05-25 12.csv'
        targetPath: a abs sava path, like: ROOTPATH + '/temp,5.0m/' (should end with '/').
        (option)depth is a str with units(if sourceFile with depth)
    attention:
        By default, the work place is the path where the sourceFile in.
        And, make sure the targetPath is existed.
    '''
    csv = np.genfromtxt(sourceFile, delimiter=',')
    x, y = np.meshgrid(csv[0, 1:], csv[1:, 0])
    points = np.rec.fromarrays([x, y]).ravel()
    values = csv[1:, 1:].ravel()
    header = ['lon', 'lat', depth if depth is not None else 'value']
    # 去NaN
    point1 = []
    value1 = []
    for i in range(len(values)):
        if not np.isnan(values[i]):  # 在这里对整个values判NaN不起作用，不知道为啥
            point1.append(list(points[i]))
            value1.append(values[i])
    dt1 = pd.DataFrame(point1)
    dt2 = pd.DataFrame(value1)
    pd.concat([dt1, dt2], axis=1).to_csv(targetPath + sourceFile, index=False, header=header)


def dealAFolderG2T(sourceFolder):
    '''
    There is no code to check whether file in the folder is legal, and please ensure that.
    By default, the work place is the path where the sourceFolder in.
    '''
    if not os.path.isdir(sourceFolder):
        print("please ensure the param is a dir")
        return
    elif sourceFolder[-4:] != 'grid':
        print("if you ensure files in sourceFolder is grid, please rename the sourceFolder end with '_grid'!")
        return
    
    # else:
    targetPath = ROOTPATH + sourceFolder[:-4] + 'tuple/'
    if not os.path.exists(targetPath):
        os.makedirs(targetPath)
    if len(sourceFolder.split(',')) != 1: # 说明有深度
        depth_grid = sourceFolder.split(',')[1]
        depth = depth_grid.split('_')[0]
    else:
        depth = None
    os.chdir(sourceFolder)
    fileList = os.listdir()
    for file in fileList:
        if file[-4:] == '.csv':
            grid2Tuple(file, targetPath, depth)
    os.chdir('..')

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    dirList = os.listdir()
    for dirt in dirList:
        if os.path.isdir(dirt) and dirt[-4:] == 'grid':
            dealAFolderG2T(dirt)
            print("run time: "+str(time.clock()-start)+" s")
            start = time.clock()
