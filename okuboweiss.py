import numpy as np
import os
import csvjsonwriteop

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
def culAndSaveOWparam(uFile, vFile, savePath):
    '''
    params:
        uFile: grid csv file name(abs path), eastward_sea_water_velocity, ZONAL VELOCITY
        vFile: grid csv file name(abs path), northward_sea_water_velocity, MERIDIONAL VELOCITY
    func:
        Calculate the OkuboWeiss paramter and save in a grid csv.
        After calculating, the shape of grid will be smaller: n*n-->(n-1)*(n-1).
        By default, cut the first row and first column(except lon and lat).
    attention:
        There is no code to check whether the file is grid format and to check the x or y in two file are same.
        Please ensure these two points before call this function.
    '''
    csvU = np.genfromtxt(uFile, delimiter=',')
    csvV = np.genfromtxt(vFile, delimiter=',')
    x = csvU[0,1:]
    y = csvU[1:,0]
    u = csvU[1:,1:]
    v = csvV[1:,1:]
    diffX = (x[1] - x[0]) * 111e3 * np.cos(np.radians(y))
    diffX = diffX.reshape((diffX.shape[0], 1)) # 转换成列向量
    diffY = (y[1] - y[0]) * 111e3
    ow = OkuboWeiss(u, v, diffX, diffY)
    # write csv
    csvjsonwriteop.writeCSVgrid(x[1:], y[1:], ow, dataInfo=None, absFileName=savePath)
    # convenience to test(plot)
    # return ow

def processAFolderOW(rootPath, uFolder, vFolder):
    '''
    attention:
        There is no code to check files' name in uFolder and vFolder are same.
        Please ensure that before call this function.
    owFolder: OkuboWeiss_(13x13)
    '''
    os.chdir(rootPath + '/' + uFolder)
    fileList = os.listdir()
    os.chdir('..')
    owFolder = 'OkuboWeiss_' + uFolder.split('_')[-1] # -1 is '(13x13)'
    if not os.path.exists(owFolder):
        os.mkdir(owFolder)
    owAbsPath = rootPath + '/' + owFolder
    for file in fileList:
        if file[-4:] == '.csv':
            uFile = './' + uFolder + '/' + file
            vFile = './' + vFolder + '/' + file
            savePath = owAbsPath + '/' + file
            culAndSaveOWparam(uFile, vFile, savePath)

if __name__ == '__main__':
    rootPath = '/Users/littlesec/Desktop/毕业论文实现/SODA v2p2p4 new'
    uFolder = '200m_zonal_velocity1960-2008_grid_(193x145)'
    vFolder = '200m_meridional_velocity1960-2008_grid_(193x145)'
    processAFolderOW(rootPath, uFolder, vFolder)

'''
[
    [{
        "coord" : [lon, lat],
        "value" : value
    },
    {
        "coord" : [lon, lat],
        "value" : value
    },
    .
    .
    .
    {
        "coord" : [lon, lat],
        "value" : value
    }]
]
'''

    