# base on the paper:
# Matsuoka D, Araki F, Inoue Y, et al.
# A new approach to ocean eddy detection, tracking, and event visualization–application to the northwest pacific ocean[J]. 
# Procedia Computer Science, 2016, 80: 1601-1611.

import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import time

ROOTPATH = '/Users/littlesec/Desktop/毕业论文实现/OceanVisualizationD3/oceandata'

LAND = 0
WARMEDDYCENTER = 1
COLDEDDYCENTER = 2
WARMEDDYSCALE = 3
COLDEDDYSCALE = 4
BLACKGROUND = 5

def eddy(fileName, sshpath, owpath, scale):
    '''
    需要注意ssh grid和ow grdi的经纬度序列是不一样的，ow的要少一点。
    sshpath是grid的csv路径
    scale确保是个奇数！直径
    '''
    # 读取ssh和ow
    if scale % 2 == 0: #确保scale是奇数
        scale =  int(scale) + 1 # 不能简写成+=
    sshcsv = np.genfromtxt('/'.join([sshpath, fileName]), delimiter=',')
    sshlon = sshcsv[0, 1:]
    sshlat = sshcsv[1:, 0]
    srcSSH = np.round(sshcsv[1:, 1:], 6)
    tarSSH = np.where(np.isnan(srcSSH), 0, BLACKGROUND)
    boundaryList = []
    owThreshold = 0.2 # 0.2 * std
    # 对srcSSH进行遍历
    radius = scale // 2
    '''
    srcSSH[-2:2] --> array([], shape=(0, ?), dtype=?)
    srcSSH[-2:] --> array([[?], [?]], shape=(2, ?), dtype=?)
    srcSSH[:len+2] --> array([], shape=(0, ?), dtype=?)
    想说明的是实际上可以不用规定从[radius][radius]这个点开始遍历，numpy的索引是循环的，在数值计算上不会存在越界这个说法。
    但是要考虑到一点是[len-1][len-1]如果按照下面的逻辑则该点会被判断为最大和最小值。
    所以在此依然空出四边的边界，这样也减少迭代次数。
    '''
    df1 = pd.read_csv('/'.join([owpath, fileName])).round(6)
    for i in range(radius, len(sshlat)-radius):
        for j in range(radius, len(sshlon)-radius):
            if np.isnan(srcSSH[i][j]):
                continue
            if np.nanmax(srcSSH[i-radius:i+radius+1, j-radius:j+radius+1]) == srcSSH[i][j]:
                # # 当前点和矩阵最值对比是否同，是则对比ow
                # queryExpr = 'lon=={0} and lat=={1}'.format(sshlon[j], sshlat[i])
                # qdf = df1.query(queryExpr)
                # if qdf.index.empty: # 该点没有ow
                #     continue
                # # print(queryExpr)
                # if qdf['ow'].values[0] < -owThreshold * np.nanstd(df1['ow']): # 认为是涡核
                if isEddyCenter(fileName, sshlon[j], sshlat[i], radius-1):
                    tarSSH[i-radius:i+radius+1, j-radius:j+radius+1] = WARMEDDYSCALE
                    tarSSH = sshthreshold(i, j, radius, sshlon, sshlat, srcSSH, tarSSH, 'warm')
                    tarSSH[i][j] = WARMEDDYCENTER

                    # threshold = sshthreshold(i, j, radius, sshlon, sshlat, srcSSH, tarSSH, 'warm')
                    # boundaryList.append(eddyBoundary(i, j, sshlon, sshlat, threshold, srcSSH, 'warm'))
            elif np.nanmin(srcSSH[i-radius:i+radius+1, j-radius:j+radius+1]) == srcSSH[i][j]:
                # # 当前点和矩阵最值对比是否同，是则对比ow
                # queryExpr = 'lon=={0} and lat=={1}'.format(sshlon[j], sshlat[i])
                # qdf = df1.query(queryExpr)
                # if qdf.index.empty: # 该点没有ow
                #     continue
                # # print(queryExpr)
                # if qdf['ow'].values[0] < -owThreshold * np.nanstd(df1['ow']) : # 认为是涡核
                if isEddyCenter(fileName, sshlon[j], sshlat[i], radius-1):
                    tarSSH[i-radius:i+radius+1, j-radius:j+radius+1] = COLDEDDYSCALE
                    tarSSH = sshthreshold(i, j, radius, sshlon, sshlat, srcSSH, tarSSH, 'cold')
                    tarSSH[i][j] = COLDEDDYCENTER

                    # threshold = sshthreshold(i, j, radius, sshlon, sshlat, srcSSH, tarSSH, 'cold')
                    # boundaryList.append(eddyBoundary(i, j, sshlon, sshlat, threshold, srcSSH, 'cold'))
    # print(boundaryList)
    plt.imshow(tarSSH, origin='lower', cmap='Spectral')
    plt.colorbar()
    plt.show()

def cmpGreater(a, b):
    return a > b

def cmpLess(a, b):
    return a < b

def sshthreshold(centerI, centerJ, radius, lonList, latList, srcSSH, tarSSH, eddyType):
    '''
    centerI,J是涡旋的中心在经纬序列中的索引
    lonList和latList是对应的经纬序列
    radius是为了指示开始扫描的内边界，为的是减少迭代次数
    srcSSH是原始ssh数据
    tarSSH是标记型的数据，具体数字见全局变量
    eddyType是str，要么warm要么cold，用于设置指示当前寻找的阈值的涡旋性质，代码中根据该值配置一定的参数用于代码重用
    共扫描八个方向，顺序为：
    6 2 7
    1   3
    5 4 8
    '''
    thresholdKVlist = [] # {'iscale': , 'jscale': , 'threshold':, 'pos':} # pos用于记录从哪个方向出来，用于调试
    j = centerJ-radius
    if eddyType == 'warm':
        cmp = cmpGreater
        scaleTag = WARMEDDYSCALE
    else:
        cmp = cmpLess
        scaleTag = COLDEDDYSCALE
    while j > 0: # 左1
        if np.isnan(srcSSH[centerI][j-1]):
            break
        if cmp(srcSSH[centerI][j-1], srcSSH[centerI][j]):
            break
        j -= 1
    thresholdKVlist.append({'iscale': centerJ-j, 'jscale': centerJ-j, 'threshold':srcSSH[centerI][j], 'pos':1})

    i = centerI-radius
    while i > 0: # 上2
        if np.isnan(srcSSH[i-1][centerJ]):
            break
        if cmp(srcSSH[i-1][centerJ], srcSSH[i][centerJ]):
            break
        i -= 1
    thresholdKVlist.append({'iscale': centerI-i, 'jscale': centerI-i, 'threshold':srcSSH[i][centerJ], 'pos':2})

    j = centerJ+radius
    while j < len(lonList)-1: # 右3
        if np.isnan(srcSSH[centerI][j+1]):
            break
        if cmp(srcSSH[centerI][j+1], srcSSH[centerI][j]):
            break
        j += 1
    thresholdKVlist.append({'iscale': j-centerJ, 'jscale': j-centerJ, 'threshold':srcSSH[centerI][j], 'pos':3})

    i = centerI+radius
    while i < len(latList)-1: # 下4
        if np.isnan(srcSSH[i+1][centerJ]):
            break
        if cmp(srcSSH[i+1][centerJ], srcSSH[i][centerJ]):
            break
        i += 1
    thresholdKVlist.append({'iscale': i-centerI, 'jscale': i-centerI, 'threshold':srcSSH[i][centerJ], 'pos':4})

    i = centerI+radius
    j = centerJ-radius
    while i < len(latList)-1 and j > 0: # 左下5
        if np.isnan(srcSSH[i+1][j-1]):
            break
        if cmp(srcSSH[i+1][j-1], srcSSH[i][j]):
            break
        i += 1
        j -= 1
    thresholdKVlist.append({'iscale': i-centerI, 'jscale': centerJ-j, 'threshold':srcSSH[i][j], 'pos':5})

    i = centerI-radius
    j = centerJ-radius
    while i > 0 and j > 0: # 左上6
        if np.isnan(srcSSH[i-1][j-1]):
            break
        if cmp(srcSSH[i-1][j-1], srcSSH[i][j]):
            break
        i -= 1
        j -= 1
    thresholdKVlist.append({'iscale': centerI-i, 'jscale': centerJ-j, 'threshold':srcSSH[i][j], 'pos':6})

    i = centerI-radius
    j = centerJ+radius
    while j < len(lonList)-1 and i > 0: # 右上7
        if np.isnan(srcSSH[i-1][j+1]):
            break
        if cmp(srcSSH[i-1][j+1], srcSSH[i][j]):
            break
        i -= 1
        j += 1
    thresholdKVlist.append({'iscale': centerI-i, 'jscale': j-centerJ, 'threshold':srcSSH[i][j], 'pos':7})

    i = centerI+radius
    j = centerJ+radius
    while j < len(lonList)-1 and i < len(latList)-1: # 右下8
        if np.isnan(srcSSH[i+1][j+1]):
            break
        if cmp(srcSSH[i+1][j+1], srcSSH[i][j]):
            break
        i += 1
        j += 1
    thresholdKVlist.append({'iscale': i-centerI, 'jscale': j-centerJ, 'threshold':srcSSH[i][j], 'pos':8})

    if eddyType == 'warm':
        maxThresholdKV = max(thresholdKVlist, key=lambda kv: kv['threshold'] if not np.isnan(kv['threshold']) else np.NINF) ################ 可能有理解偏差
    else:
        maxThresholdKV = min(thresholdKVlist, key=lambda kv: kv['threshold'] if not np.isnan(kv['threshold']) else np.PINF) ################ 可能有理解偏差        

    # return maxThresholdKV['threshold']
    # print('center', centerI, centerJ ,',max:', maxThresholdKV)
    for i in range(centerI-maxThresholdKV['iscale'], centerI+maxThresholdKV['iscale']+1):
        for j in range(centerJ-maxThresholdKV['jscale'], centerJ+maxThresholdKV['jscale']+1):
            if i < 0 or i >= len(latList) or j < 0 or j >= len(lonList): # 方向1-4中的scale是通过一个方向得来的，不能保证反方向其实已经越界
                continue # 不能用break，break会跳出所有嵌套的循环
            # 这种方法有待商榷，1是因为是否真的能保证value都小于最大值？因为范围已经变了。2是理想中的圈的外面和范围之间的值也可能落入这个区间
            if (cmp(srcSSH[i][j], maxThresholdKV['threshold']) or maxThresholdKV['threshold'] == srcSSH[i][j]) and cmp(srcSSH[centerI][centerJ], srcSSH[i][j]):
                tarSSH[i][j] = scaleTag
    # plt.imshow(tarSSH, origin='lower', cmap='Spectral')
    # plt.colorbar()
    # plt.show()
    return tarSSH

def eddyBoundary(centerI, centerJ, lonList, latList, threshold, srcSSH, eddyType):
    '''
    在上下左右方向上判断阈值后记录的范围ij实际上是不对的，如果当前遍历方向是i，那么j的方向是根据i计算而来，然而并非四个方向的变化速度是一致的，以下图为例：
        3
        2(+)
        3
        3.5
        4
        4.5
        5
        5.5
    *   6   5   4   3(+)   3.5   4.5
        *
    假设此时通过右方向得出是3为阈值，而3的i方向方位是3，此时j方向也默认是3，
    然而从图示可以看出，j方向的范围应该是6，也就是说j方向的范围缩小了。
    若是范围扩大了, 上述例子中返回6，那么i方向将会有更多的点进入范围内。
    干脆记录八个方向上阈值的点，然后做连线。
    json格式如下：
    [
        {
            "points": [[], [], [], [], [], [], ...], # 各个点，前段使用线段生成器就能轻松绘制线条，还可以设置张力更加平滑
            "center": [],
            "type": "warm"
        },
        {
            "points": [],
            "center": [],
            "type": "cold"
        },
        ...
    ]
    而返回值是一个元素，所以调用者要做好添加工作
    6 2 7
    1   3
    5 4 8
    '''
    pointsList = []

    if eddyType == 'warm':
        cmp = cmpLess
    else:
        cmp = cmpGreater

    j = centerJ
    while j > 0: # 左1
        if np.isnan(srcSSH[centerI][j-1]):
            break
        if cmp(srcSSH[centerI][j-1], threshold) or srcSSH[centerI][j-1] == threshold:
            break
        j -= 1
    pointsList.append([lonList[j], latList[centerI]])

    i = centerI
    j = centerJ
    while i > 0 and j > 0: # 左上6
        if np.isnan(srcSSH[i-1][j-1]):
            break
        if cmp(srcSSH[i-1][j-1], threshold) or srcSSH[i-1][j-1] == threshold:
            break
        i -= 1
        j -= 1
    pointsList.append([lonList[j], latList[i]])

    i = centerI
    while i > 0: # 上2
        if np.isnan(srcSSH[i-1][centerJ]):
            break
        if cmp(srcSSH[i-1][centerJ], threshold) or srcSSH[i-1][centerJ] == threshold:
            break
        i -= 1
    pointsList.append([lonList[centerJ], latList[i]])

    i = centerI
    j = centerJ
    while j < len(lonList)-1 and i > 0: # 右上7
        if np.isnan(srcSSH[i-1][j+1]):
            break
        if cmp(srcSSH[i-1][j+1], threshold) or srcSSH[i-1][j+1] == threshold:
            break
        i -= 1
        j += 1
    pointsList.append([lonList[j], latList[i]])

    j = centerJ
    while j < len(lonList)-1: # 右3
        if np.isnan(srcSSH[centerI][j+1]):
            break
        if cmp(srcSSH[centerI][j+1], threshold) or srcSSH[centerI][j+1] == threshold: 
            break
        j += 1
    pointsList.append([lonList[j], latList[centerI]])

    i = centerI
    j = centerJ
    while j < len(lonList)-1 and i < len(latList)-1: # 右下8
        if np.isnan(srcSSH[i+1][j+1]):
            break
        if cmp(srcSSH[i+1][j+1], threshold) or srcSSH[i+1][j+1] == threshold:
            break
        i += 1
        j += 1
    pointsList.append([lonList[j], latList[i]])

    i = centerI
    while i < len(latList)-1: # 下4
        if np.isnan(srcSSH[i+1][centerJ]):
            break
        if cmp(srcSSH[i+1][centerJ], threshold) or srcSSH[i+1][centerJ] == threshold:
            break
        i += 1
    pointsList.append([lonList[centerJ], latList[i]])

    i = centerI
    j = centerJ
    while i < len(latList)-1 and j > 0: # 左下5
        if np.isnan(srcSSH[i+1][j-1]):
            break
        if cmp(srcSSH[i+1][j-1], threshold) or srcSSH[i+1][j-1] == threshold:
            break
        i += 1
        j -= 1
    pointsList.append([lonList[j], latList[i]])

    return {"points": pointsList, "center": [lonList[centerJ], latList[centerJ]], "type": eddyType}

# 移至接口时，最好直接传ow和ow的lat和lon，防止过多的读写操作
# 目前用时约1min
def isEddyCenter(fileName, lon, lat, radius, velocityPath='0.0m', owPath='ow_grid/0.0m'):
    '''
    condition of eddy center:
        ssh: local max or min (judge before call this function)
        velocity: < 0.2 (this value is to be discussed, to be exact, is equal to 0)
        ow: local min and < 0.2*std
    params:
        fileName: yyyy-mm-dd.csc
        velocityPath: (tuple) ./depth(0.0m) [file with all attrs]
        owPath: (grid) ./depth(0.0m)
        lon, lat: practical lon and lat, not the index
        radius: ssh's radius - 1 (sub 1 before call this function)
    '''
    owThreshold = 0.2 # 0.2 * std
    # read velocity
    df1 = pd.read_csv('/'.join([velocityPath, fileName])).round(6)
    queryExpr = 'lon=={0} and lat=={1}'.format(lon, lat)
    qdf = df1.query(queryExpr)
    if qdf.index.empty: # 该点没有velocity
        velocity = 0 # to be discussed
    else:
        velocity = np.sqrt(qdf['water_u'].values[0]**2 + qdf['water_v'].values[0]**2)

    if velocity < 0.2:
        # judge ow
        owcsv = np.genfromtxt('/'.join([owPath, fileName]), delimiter=',')
        owlon = owcsv[0, 1:]
        owlat = owcsv[1:, 0]
        ow = owcsv[1:, 1:]
        centerI = np.where(owlat==lat)[0][0]
        centerJ = np.where(owlon==lon)[0][0]
        # print(centerI, centerJ)
        if centerI.size == 0 or centerJ.size == 0: # 该点不在ow的计算范围内
            return False
        if np.isnan(ow[centerI][centerJ]): # 该点ow为NaN
            return False
        if ow[centerI][centerJ] > -owThreshold * np.nanstd(ow):
            return False
        if np.nanmin(ow[centerI-radius:centerI+radius+1, centerJ-radius:centerJ+radius+1]) == ow[centerI][centerJ]:
            return True
        else:
            return False
    else:
        return False


if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    fileName = '2014-07-01.csv'
    sshpath = 'surf_el_grid'
    owpath = '0.0m'
    scale = 7
    eddy(fileName, sshpath, owpath, scale)
    print("run time: "+str(time.clock()-start)+" s")
    start = time.clock()