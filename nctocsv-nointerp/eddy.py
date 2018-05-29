import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt

ROOTPATH = '/Users/openmac/Downloads/LittleSec/OceanVisualizationD3/oceandata'

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
    srcSSH = sshcsv[1:, 1:]
    tarSSH = np.where(np.isnan(srcSSH), 0, BLACKGROUND)
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
    for i in range(radius, len(sshlat)-radius):
        for j in range(radius, len(sshlon)-radius):
            if np.isnan(srcSSH[i][j]):
                continue
            if np.nanmax(srcSSH[i-radius:i+radius+1, j-radius:j+radius+1]) == srcSSH[i][j]:
                # 当前点和矩阵最值对比是否同，是则对比ow
                queryExpr = 'lon=={0} and lat=={1}'.format(sshlon[j], sshlat[i])
                df1 = pd.read_csv('/'.join([owpath, fileName])).round(6)
                qdf = df1.query(queryExpr)
                if qdf.index.empty: # 该点没有ow
                    continue
                # print(queryExpr)
                if qdf['ow'].values[0] < 0: # 认为是涡核
                    # tarSSH[i-scale:i+scale+1, j-scale:j+scale+1] = WARMEDDYSCALE
                    tarSSH = sshthreshold(i, j, scale, sshlon, sshlat, srcSSH, tarSSH)
                    tarSSH[i][j] = WARMEDDYCENTER
    plt.imshow(tarSSH, origin='lower', cmap='Spectral')    
    plt.colorbar()
    plt.show()

# 先默认中心为最大值
def sshthreshold(centerI, centerJ, scale, lonList, latList, srcSSH, tarSSH):
    '''
    centerI,J是涡旋的中心在经纬序列中的索引
    lonList和latList是对应的经纬序列
    scale是为了指示开始扫描的内边界，为的是减少迭代次数
    共扫描八个方向，顺序为：
    6 2 7
    1   3
    5 4 8
    '''
    maxThreshold = -10 # srcSSH不可能为负值
    curI1 = curI2 = centerI # 方便遍历阈值范围内的点
    curJ1 = curJ2 = centerJ
    j = centerJ # scale内的点必定不符合条件
    while j > 0: # 左1
        if np.isnan(srcSSH[centerI][j-1]):
            break
        if srcSSH[centerI][j] < srcSSH[centerI][j-1] and srcSSH[centerI][j] < srcSSH[centerI][j+1]:
        # if maxThreshold < srcSSH[centerI][j]:
            # maxThreshold = srcSSH[centerI][j]
            # curI = centerI
            curJ1 = j
            break
        j -= 1

    i = centerI
    while i > 0: # 上2
        if np.isnan(srcSSH[i-1][centerJ]):
            break
        if srcSSH[i][centerJ] < srcSSH[i-1][centerJ] and srcSSH[i][centerJ] < srcSSH[i+1][centerJ]:
        # if maxThreshold < srcSSH[i][centerJ]:
            # maxThreshold = srcSSH[i][centerJ]
            curI1 = i
            # curJ = centerJ
            break
        i -= 1

    j = centerJ
    while j < len(lonList)-1: # 右3
        if np.isnan(srcSSH[centerI][j+1]):
            break
        if srcSSH[centerI][j] < srcSSH[centerI][j-1] and srcSSH[centerI][j] < srcSSH[centerI][j+1]:
        # if maxThreshold < srcSSH[centerI][j]:
            # maxThreshold = srcSSH[centerI][j]
            # curI = centerI
            curJ2 = j
            break
        j += 1

    i = centerI
    while i < len(latList)-1: # 下4
        if np.isnan(srcSSH[i+1][centerJ]):
            break
        if srcSSH[i][centerJ] < srcSSH[i-1][centerJ] and srcSSH[i][centerJ] < srcSSH[i+1][centerJ]:
        # if maxThreshold < srcSSH[i][centerJ]:
            # maxThreshold = srcSSH[i][centerJ]
            curI2 = i
            # curJ = centerJ
            break
        i += 1
    
    # i = centerI
    # j = centerJ
    # while i < len(latList)-1 and j > 0: # 左下5
    #     if np.isnan(srcSSH[i+1][j-1]):
    #         break
    #     if srcSSH[i][j] < srcSSH[i+1][j-1] and srcSSH[i][j] < srcSSH[i-1][j+1]:
    #         if maxThreshold < srcSSH[i][j]:
    #             maxThreshold = srcSSH[i][j]
    #             curI = i
    #             curJ = j
    #         break
    #     i += 1
    #     j -= 1

    # i = centerI
    # j = centerJ
    # while i > 0 and j > 0: # 左上6
    #     if np.isnan(srcSSH[i-1][j-1]):
    #         break
    #     if srcSSH[i][j] < srcSSH[i-1][j-1] and srcSSH[i][j] < srcSSH[i+1][j+1]:
    #         if maxThreshold < srcSSH[i][j]:
    #             maxThreshold = srcSSH[i][j]
    #             curI = i
    #             curJ = j
    #         break
    #     i -= 1
    #     j -= 1

    # i = centerI
    # j = centerJ
    # while j < len(lonList)-1 and i > 0: # 右上7
    #     if np.isnan(srcSSH[i-1][j+1]):
    #         break
    #     if srcSSH[i][j] < srcSSH[i-1][j+1] and srcSSH[i][j] < srcSSH[i+1][j-1]:
    #         if maxThreshold < srcSSH[i][j]:
    #             maxThreshold = srcSSH[i][j]
    #             curI = i
    #             curJ = j
    #         break
    #     i -= 1
    #     j += 1
    
    # i = centerI
    # j = centerJ
    # while j < len(lonList)-1 and i < len(latList)-1: # 右下8
    #     if np.isnan(srcSSH[i+1][j+1]):
    #         break
    #     if srcSSH[i][j] < srcSSH[i+1][j+1] and srcSSH[i][j] < srcSSH[i-1][j-1]:
    #         if maxThreshold < srcSSH[i][j]:
    #             maxThreshold = srcSSH[i][j]
    #             curI = i
    #             curJ = j
    #         break
    #     i += 1
    #     j += 1

    maxThreshold = np.max([srcSSH[centerI][curJ1], srcSSH[centerI][curJ2], srcSSH[curI1][centerJ], srcSSH[curI2][centerJ]])
    # scaleI = np.abs(curI-centerI)
    # scaleJ = np.abs(curJ-centerJ)
    # print(scaleI, scaleJ)
    for i in range(curI1, curI2+1):
        for j in range(curJ1, curJ2+1):
            # 这种方法有待商榷，1是因为是否真的能保证value都小于最大值？因为范围已经变了。2是理想中的圈的外面和范围之间的值也可能落入这个区间
            if maxThreshold <= srcSSH[i][j] < srcSSH[centerI][centerJ]:
                tarSSH[i][j] = WARMEDDYSCALE
    # plt.imshow(tarSSH, origin='lower', cmap='Spectral')    
    # plt.colorbar()
    # plt.show()
    return tarSSH

    # pdList = []
    # x = lonList[centerJ-scaleJ:centerJ+scaleJ]
    # y = latList[centerI-scaleI:centerI+scaleI]
    # value = srcSSH[centerI-scaleI:centerI+scaleI, centerJ-scaleJ:centerJ+scaleJ]
    # valueFlag = np.where(maxThreshold <= value, 1, 0) # 这种方法有待商榷，1是因为是否真的能保证value都小于最大值？因为范围已经变了。2是理想中的圈的外面和范围之间的值也可能落入这个区间
    # xi,yi = np.meshgrid(x,y)
    # points = np.rec.fromarrays([xi, yi]).ravel()
    # values = valueFlag.ravel()
    # for i in range(len(values)):
    #     if values[i]:
    #         pdList.append({'lon': points[i][0], 'lat': points[i][1], 'eddy': WARMEDDYSCALE})
    #     else:
    #         pdList.append({'lon': points[i][0], 'lat': points[i][1], 'eddy': BLACKGROUND})
    # pd.DataFrame(pdList)
            
if __name__ == '__main__':
    os.chdir(ROOTPATH)
    fileName = '2017-01-01.csv'
    sshpath = 'surf_el_grid'
    owpath = '0.0m'
    scale = 7
    eddy(fileName, sshpath, owpath, scale)