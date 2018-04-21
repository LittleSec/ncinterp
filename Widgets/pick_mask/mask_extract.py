import os
from scipy.io import netcdf
import numpy as np
import pandas as pd

'''
Todo
1. be a function
2. complete setResolution function()
'''

# 以下是可能需要修改的变量
# ncFileName = 'sst_mask_cutlatlon.nc'
tupleCSVName = 'mask_tuple.csv'
gridCSVName = 'mask_grid.csv'

# 以下代码获取nc文件名而已，可以上面直接使用硬编码
currentdir = os.path.dirname(__file__)
fileList = os.listdir(currentdir)
for file in fileList:
    if file[-3:] == '.nc':
        ncFileName = file
        break

# 正式处理代码
os.chdir(currentdir)
f = netcdf.netcdf_file(ncFileName, 'r')
lon = f.variables['lon'].data # 251
lat = f.variables['lat'].data # 331
mask = f.variables['mask'].data[0] # (331, 251)# 不懂为啥还保留了time属性
header = ['lon', 'lat', 'mask']
newMask = np.where(mask == 1, mask, 0)
x, y = np.meshgrid(lon, lat)
point = np.rec.fromarrays([x, y])
dt1 = pd.DataFrame(point.ravel())
dt2 = pd.DataFrame(newMask.ravel())
pd.concat([dt1, dt2], axis=1).to_csv(tupleCSVName, index=False, header=header)
print(pd.DataFrame(newMask, columns=lon, index=lat)).to_csv(gridCSVName) #有bug，已提交issue
f.close()

def setResolution(degrees):
    '''
    param:
        degrees: how many degresss have a data. (>0.05)(better mod 0.05 == 0)
    return:
        two list: what indexs should be deleted
        0: lon
        1: lat
    '''
    if degrees <= 0.05:
        return
    else:
        pass