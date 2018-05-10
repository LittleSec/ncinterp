import pandas as pd
import numpy as np
import os
import time

ROOTPATH = '/Users/openmac/Downloads/new nc data/'
ATTRLIST_ALL = ['salinity', 'water_temp', 'water_u', 'water_v', 'surf_el']
DEPTHLIST = ['0.0m', '8.0m', '15.0m', '30.0m', '50.0m']

def grid2Tuple(file, sourcePath, targetPath, attr):
    '''
    param:
        file: a grid csv file name, like: '2016-05-25.csv'
        sourcePath: like './temp_grid/5.0m'
        targetPath: like './temp_tuple/5.0m'.
    attention:
        Make sure the all the paths and files are existed.
    '''
    # if not os.path.exists(targetPath):
    #     os.makedirs(targetPath)
    csv = np.genfromtxt('/'.join([sourcePath, file]), delimiter=',')
    x, y = np.meshgrid(csv[0, 1:], csv[1:, 0])
    points = np.rec.fromarrays([x, y]).ravel()
    values = csv[1:, 1:].ravel()
    header = ['lon', 'lat', attr]
    # 去NaN
    point1 = []
    value1 = []
    for i in range(len(values)):
        if not np.isnan(values[i]):  # 在这里对整个values判NaN不起作用，不知道为啥
            point1.append(list(points[i]))
            value1.append(values[i])
    dt1 = pd.DataFrame(point1)
    dt2 = pd.DataFrame(value1)
    pd.concat([dt1, dt2], axis=1).to_csv('/'.join([targetPath, file]), index=False, header=header)


def dealAattrG2T(attr):
    '''
    attr: like 'water_u'
    将一个属性的grid全部转成tuple
    Please make sure files and attr are legal.
    '''
    # if not os.path.isdir(sourceFolder):
    #     print("please ensure the param is a dir")
    #     return
    # elif sourceFolder[-5:] != '_grid':
    #     print("if you ensure files in sourceFolder is grid, please rename the sourceFolder end with '_grid'!")
    #     return

    if attr != 'surf_el':
        srcPathList = ['/'.join([attr+'_grid', depth]) for depth in DEPTHLIST]
    else:
        srcPathList = ['surf_el_grid']

    for srcPath in srcPathList:
        tarPath = srcPath.replace('_grid', '_tuple')
        if not os.path.exists(tarPath):
            os.makedirs(tarPath)
        for file in os.listdir(srcPath):
            if file[-4:] == '.csv':
                grid2Tuple(file, srcPath, tarPath, attr)

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)

    for attr in ATTRLIST_ALL:
        dealAattrG2T(attr)
        print("run time: "+str(time.clock()-start)+" s")
        start = time.clock()