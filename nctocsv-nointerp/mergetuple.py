import pandas as pd
import numpy as np
import os
import time
from datetime import datetime

ROOTPATH = '/Users/openmac/Downloads/LittleSec/OceanVisualizationD3/oceandata'
DEPTHLIST = ['0.0m', '8.0m', '15.0m', '30.0m', '50.0m']
ATTRLIST = ['salinity', 'water_temp', 'water_u', 'water_v']
ATTRLIST_ALL = ['salinity', 'water_temp', 'water_u', 'water_v', 'surf_el']

# 弃用：已经不适合最新的文件命名规则。
def mergedepth(attr):
    '''!弃用：已经不适合最新的文件命名规则。
    param:
        attr: (str)需要合并深度的属性
    attention:
        Be ensure in the work place before call this function
    output:
        a tuple csv. 一个csv里记录同一时刻同一属性的五个深度。
    '''
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
            # df2.columns = ['lon', 'lat'] + DEPTHLIST
            df2.to_csv('/'.join([attr, file]), index=False, na_rep='NaN')

def mergeAttr(date, depth):
    '''
    param:
        date: (str)需要合并属性的时间（日期）
        depth: (str)需要合并属性的深度(with units)
    attention:
        Be ensure in the work place before call this function.
        Be ensure the date and depth are existed.
        ssh属于所有深度
    output:
        a tuple csv. 一个csv里记录同一时刻同一深度的五个属性。
        （输出）命名规则：./0.0m/yyyy-mm-dd.csv
        （输入）命名规则：./attr_tuple/(depth/)yyyy-mm-dd.csv
    '''
    if not os.path.exists(depth):
        os.makedirs(depth)
    fileList = ['/'.join([attr+'_tuple', depth, date+'.csv']) for attr in ATTRLIST] # 没有ssh
    fileList.append('/'.join(['surf_el_tuple', date+'.csv']))
    flat = False
    for file in fileList:
        df1 = pd.read_csv(file)
        if flat:
            df2 = pd.merge(df2, df1, how='inner', on=['lon', 'lat'])
        else:
            df2 = df1.copy()
            flat = True
    # df2.columns = ['lon', 'lat'] + ATTRLIST_ALL
    df2.to_csv('/'.join([depth, date+'.csv']), index=False, na_rep='NaN')


# 小小的脚本
def del1Script(rootPath=ROOTPATH):
    '''
    遍历目录下所有的文件和文件夹，把00点的csv文件删除，把12点的csv文件改名去掉时间仅保留日期
    '''
    for root, dirs, files in os.walk(rootPath):
        for file in files:
            if file[-6:] == '00.csv':
                os.remove('/'.join([root, file]))
            elif file[-6:] == '12.csv':
                os.rename('/'.join([root, file]), '/'.join([root, file[:-7]+'.csv']))

def datelist(beginDate, endDate):
    '''
    beginDate, endDate是形如'20160601'的字符串或datetime格式
    日期序列生成函数，返回一列表，每个元素是字符串，格式为'yyyy-mm-dd'
    '''
    date_l = [datetime.strftime(x, '%Y-%m-%d') for x in list(pd.date_range(start=beginDate, end=endDate))]
    return date_l

def finddiff(path):
    dateset = set(datelist('20140701', '20160430'))
    fileset = set([file[:-4] for file in os.listdir(path)])
    diff = list(dateset.difference(fileset))
    print(diff)


def attrMergeInTuple(srcFile, srcPath, tarPath):
    dt1 = pd.read_csv('/'.join([srcPath, srcFile]))
    # dt1['sla'] = dt1['sla'] * 100
    dt2 = pd.read_csv('/'.join([tarPath, srcFile]))
    dt2 = pd.merge(dt2, dt1, how='inner', on=['lon', 'lat'])
    dt2.round(6).to_csv('/'.join([tarPath, srcFile]), index=False, na_rep='NaN')

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    # fileList = os.listdir('surf_el_tuple')
    # for depth in DEPTHLIST:
    #     for file in fileList:
    #         if file[-4:] == '.csv':
    #             mergeAttr(file[:-4], depth)
    #     print("run time: "+str(time.clock()-start)+" s")
    #     start = time.clock()

    srcPath = 'ow_tuple'
    for depth in DEPTHLIST:
        for file in os.listdir('/'.join([srcPath, depth])):
            attrMergeInTuple(file, '/'.join([srcPath, depth]), depth)
        print("run time: "+str(time.clock()-start)+" s")
        start = time.clock()
