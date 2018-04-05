import numpy as np
import os
import csvwriteop

def diffu(u):
    for i in range(np.shape(u)[1]-1, 0, -1): # 考虑到右边界数据比左边界多，所以尽可能保留右部数据
        u[:,i] = u[:,i] - u[:,i-1] # i column - i-1 column
    return np.delete(u, 0, axis=1)

def diffv(v):
    for i in range(np.shape(v)[0]-1, 0, -1): # 下边界数据比上边界多，尽可能保留下边界数据
        v[i] = v[i] - v[i-1] # i row - i-1 row
    return np.delete(v, 0, axis=0)

def OkuboWeiss(diffU, diffV, diffX, diffY):
    '''
    Sn = U'x - V'y
    Ss = V'x + U'y
    w = V'x - U'y
    q = Sn^2 + Ss^2 - w^2
      = (U'x^2 + V'y^2 - 2U'xV'y) + (V'x^2 + U'y^2 +2V'xU'y) - (V'x^2 + U'y^2 - 2V'xU'y)
      = U'x^2 + V'y^2 - 2U'xV'y + V'x^2 + U'y^2 +2V'xU'y - V'x^2 - U'y^2 + 2V'xU'y
      = U'x^2 + V'y^2 - 2U'xV'y + 4V'xU'y
    '''
    Ux = diffU/diffX
    Vy = diffV/diffY
    Vx = diffV/diffX
    Uy = diffU/diffY
    q = Ux**2 + Vy**2 - 2*Ux*Vy + 4*Vx*Uy
    return q

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
    x = csvU[0,2:] # delete first column
    y = csvU[2:,0] # delete first row
    u = csvU[1:,1:].copy()
    v = csvV[1:,1:].copy()
    diffX = x[1] - x[0]
    diffY = y[1] - y[0]
    diffU = np.delete(diffu(u), 0, axis=0) # diffu() have deleted axis=1
    diffV = np.delete(diffv(v), 0, axis=1) # diffv() have deleted axis=0
    ow = OkuboWeiss(diffU, diffV, diffX, diffY)
    # write csv
    csvwriteop.writeCSVgrid(x, y, ow, dataInfo=None, absFileName=savePath)
    # convenience to test(plot)
    # return ow

def processAFolderOW(rootPath, uFolder, vFolder):
    '''
    attention:
        There is no code to check files' name in uFolder and vFolder are same.
        Please ensure that before call this function.
    owFolder: relative humidity1960-2017_grid_(13x13)_OW
    '''
    os.chdir(rootPath + '/' + uFolder)
    fileList = os.listdir()
    os.chdir('..')
    owFolder = uFolder + '_OW'
    if not os.path.exists(owFolder):
        os.mkdir(owFolder)
    owAbsPath = rootPath + '/' + owFolder
    for file in fileList:
        if file[-4:] == '.csv':
            uFile = './' + uFolder + '/' + file
            vFile = './' + vFolder + '/' + file
            savePath = owAbsPath + '/' + file
            culAndSaveOWparam(uFile, vFile, savePath)

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

    