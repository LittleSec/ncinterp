import numpy as np
import os
import pandas as pd
import time

ROOTPATH = '/Users/openmac/Downloads/'
RESOLUTION = 0.08 # 2/25 instead of (y[1] - y[0]) or (x[1] - x[0])
DEPTHLIST = ['0.0m', '8.0m', '15.0m', '30.0m', '50.0m']

def diffu(u):
    for i in range(np.shape(u)[1]-1, 0, -1): # 考虑到右边界数据比左边界多，所以尽可能保留右部数据
        u[:,i] = u[:,i] - u[:,i-1] # i column - i-1 column
    return np.delete(u, 0, axis=1) # 少一列

def diffv(v):
    for i in range(np.shape(v)[0]-1, 0, -1): # 下边界数据比上边界多，尽可能保留下边界数据
        v[i] = v[i] - v[i-1] # i row - i-1 row
    return np.delete(v, 0, axis=0) # 少一行

def OkuboWeiss(U, V, diffX, diffY):
    '''
    params:
        U: 2-D 0x0
        V: 2-D 0x0
        diffX: 1-D = lon * 111e3 * cos(y), 列向量, unit: m
        diffY: a num = lat * 111e3, unit: m
    Sn = U'x - V'y
    Ss = V'x + U'y
    w = V'x - U'y
    q = Sn^2 + Ss^2 - w^2
      = (U'x^2 + V'y^2 - 2U'xV'y) + (V'x^2 + U'y^2 +2V'xU'y) - (V'x^2 + U'y^2 - 2V'xU'y)
      = U'x^2 + V'y^2 - 2U'xV'y + V'x^2 + U'y^2 +2V'xU'y - V'x^2 - U'y^2 + 2V'xU'y
      = U'x^2 + V'y^2 - 2U'xV'y + 4V'xU'y
    '''
    Ux = diffu(U)/diffX # 0x-1  /  0x0  少一列
    Vy = diffv(V)/diffY # -1x0  /  num  少一行
    Vx = diffu(V)/diffX # 0x-1  /  0x0  少一列
    Uy = diffv(U)/diffY # -1x0  /  num  少一行

    q = Ux[1:]**2 + Vy[:,1:]**2 - 2*Ux[1:]*Vy[:,1:] + 4*Vx[1:]*Uy[:,1:]
    return q

'''
纬度的每个度大约相当于111km，
经度的每个度的距离从0km到111km不等。它的距离随纬度的不同而变化，等于111km乘纬度的余弦
x: longitude经度 * cos(y) * 111e3 --> m
y: latitude纬度 * 111e3 --> m
'''
def culAndSaveOWparam(file, srcUpath, srcVpath, tarPath):
    '''
    params:
        file: grid csv file name(u,v are the same)
        srcUpath: where u.csv in
        srcUpath: where v.csv in
        tarPath: save path
    func:
        Calculate the OkuboWeiss paramter and save in a grid csv.
        After calculating, the shape of grid will be smaller: n*n-->(n-1)*(n-1).
        By default, cut the first row and first column(except lon and lat).
    attention:
        There is no code to check whether the file is grid format and to check the x or y in two file are same.
        Please ensure these two points before call this function.
    '''
    csvU = np.genfromtxt('/'.join([srcUpath, file]), delimiter=',')
    csvV = np.genfromtxt('/'.join([srcVpath, file]), delimiter=',')
    x = csvU[0,1:]
    y = csvU[1:,0]
    u = np.round(csvU[1:,1:], 6) # 有效位只有6位，是float型(c语言的float)
    v = np.round(csvV[1:,1:], 6)
    diffX = RESOLUTION * 111e3 * np.cos(np.radians(y))
    diffX = diffX.reshape((diffX.shape[0], 1)) # 转换成列向量, np.transport()转置函数对一维数组不起作用
    diffY = RESOLUTION * 111e3
    ow = OkuboWeiss(u, v, diffX, diffY) * 1e11
    # write csv
    pd.DataFrame(ow, columns=x[1:], index=y[1:]).to_csv('/'.join([tarPath, file]), na_rep='NaN')
    
    # convenience to test(plot)
    # return ow

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    uFolder = 'water_u_grid'
    vFolder = 'water_v_grid' # 默认csv文件名数量和名字都一致
    owFolder = 'ow_grid'

    for depth in DEPTHLIST:
        nowOWpath = '/'.join([owFolder, depth])
        if not os.path.exists(nowOWpath):
            os.makedirs(nowOWpath)
        for file in os.listdir('/'.join([uFolder, depth])):
            if file[-4:] == '.csv':
                culAndSaveOWparam(file, '/'.join([uFolder, depth]), '/'.join([vFolder, depth]), nowOWpath)
        print("run time: "+str(time.clock()-start)+" s")

    