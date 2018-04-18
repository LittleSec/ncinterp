import numpy as np
import os
import csvjsonwriteop

g = 9.8 # 重力加速度，单位m/s^2
w = 7.292e-5 # 自转角速度，单位rad/s

def fCal(w, lat):
    '''
    f = 2 * w * sin(Phi)
    f: 科氏参数，地转参数
    w: 地球自转角速度, rad/s
    Phi: 地理纬度latitude, 角度-->弧度
    '''
    return 2 * w * np.sin(np.radians(lat))

def diffu(u):
    for i in range(np.shape(u)[1]-1, 0, -1): # 考虑到右边界数据比左边界多，所以尽可能保留右部数据
        u[:,i] = u[:,i] - u[:,i-1] # i column - i-1 column
    return np.delete(u, 0, axis=1) # 比u少了一列

def diffv(v):
    for i in range(np.shape(v)[0]-1, 0, -1): # 下边界数据比上边界多，尽可能保留下边界数据
        v[i] = v[i] - v[i-1] # i row - i-1 row
    return np.delete(v, 0, axis=0) # 比v少了一行

'''
纬度的每个度大约相当于111km，
经度的每个度的距离从0km到111km不等。它的距离随纬度的不同而变化，等于111km乘纬度的余弦
x: longitude经度 * cos(y) * 111e3 --> m
y: latitude纬度 * 111e3 --> m
'''

def uCal(g, w, sla, y):
    diffSLA = diffv(sla) # 少了一行
    diffy = (y[1] - y[0]) * 111e3 # 单位：m
    f = fCal(w, y)
    f = np.delete(f, 0, axis=0)
    f = f.reshape((f.shape[0], 1)) # np.transport()转置函数对一维数组不起作用
    return (-g / f * diffSLA / diffy) # 比sla少了一行（第一行）

def vCal(g, w, sla, x, y):
    diffSLA = diffu(sla) # 少了一列
    diffx = (x[1] - x[0]) * 111e3 * np.cos(np.radians(y))
    diffx = diffx.reshape((diffx.shape[0], 1))
    f = fCal(w, y)
    f = f.reshape((f.shape[0], 1))
    return (g / f * diffSLA /diffx) # 比sla少了一列（第一列）

def OkuboWeiss(U, V, diffX, diffY):
    '''
    params:
        U: 2-D -1x0
        V: 2-D 0x-1
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
    
    Ux = diffu(U)/diffX[1:] # -1x-1  /  -1x0
    Vy = diffv(V)/diffY # -1x-1  /  num
    Vx = diffu(V)/diffX # 0x-2  /  0x0
    Uy = diffv(U)/diffY # -2x0  /  num

    q = Ux[1:,1:]**2 + Vy[1:,1:]**2 - 2*Ux[1:,1:]*Vy[1:,1:] + 4*Vx[2:]*Uy[:,2:]
    return q

def culAndSaveOWparam(slaFile, savePath):
    '''
    params:
        slaFile: a csv(grid) file name(without path)
    func:
        Calculate the OkuboWeiss paramter and save in a grid csv.
        After calculating, the shape of grid will be smaller: n*n-->(n-1)*(n-1).
        By default, cut the first row and first column(except lon and lat).
    attention:
        There is no code to check whether the file is grid format and to check whether python is in the right path.
        Please ensure these two points before call this function.
    '''
    slaCSV = np.genfromtxt(slaFile, delimiter=',')
    x = slaCSV[0,1:]
    y = slaCSV[1:,0]
    sla = slaCSV[1:,1:]
    u = uCal(g, w, sla, y) # 少一行
    v = vCal(g, w, sla, x, y) # 少一列
    diffX = (x[1] - x[0]) * 111e3 * np.cos(np.radians(y))
    diffX = diffX.reshape((diffX.shape[0], 1)) # 是一个ndarray，列向量
    diffY = (y[1] - y[0]) * 111e3 # 是个数

    ow = OkuboWeiss(u, v, diffX, diffY)
    # write csv
    absFileName = savePath + '/' + slaFile
    csvjsonwriteop.writeCSVgrid(x[2:], y[2:], ow, dataInfo=None, absFileName=absFileName)
    # convenience to test(plot)
    # return ow

def processAFolderOW(rootPath, salFolder):
    '''
    attention:
        There is no code to check files' name in uFolder and vFolder are same.
        Please ensure that before call this function.
    salFolder: ANOMALY_sea_surface_height1960-2008_grid_(33x25)
    saveFolder: OkuboWeiss_(13x13)
    '''
    os.chdir(rootPath)
    owFolder = 'OkuboWeiss_' + salFolder.split('_')[-1] # -1 is '(13x13)'
    if not os.path.exists(owFolder):
        os.makedirs(owFolder)
    savePath = rootPath + '/' + owFolder
    os.chdir(salFolder)
    fileList = os.listdir()
    for file in fileList:
        if file[-4:] == '.csv':
            culAndSaveOWparam(file, savePath)

if __name__ == '__main__':
    rootPath = '/Users/littlesec/Desktop/毕业论文实现/SODA v2p2p4 new'
    salFolder = 'ANOMALY_sea_surface_height1960-2008_grid_(33x25)'
    processAFolderOW(rootPath, salFolder)