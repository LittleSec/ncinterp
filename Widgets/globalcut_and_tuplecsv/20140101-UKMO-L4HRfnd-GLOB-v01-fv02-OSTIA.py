import os
from scipy.io import netcdf
import numpy as np
import pandas as pd

# 以下是可能需要修改的变量
fileName = '20140101-UKMO-L4HRfnd-GLOB-v01-fv02-OSTIA.nc'  # 读取的文件名
nanValue = -500  # 缺失值的替代值
lonIndex1, lonIndex2 = 5990, 6200  # 经度索引
latIndex1, latIndex2 = 1100, 1310  # 纬度索引
keyList = ['analysed_sst', 'analysis_error', 'sea_ice_fraction']  # 观测值名称
csvName = '20140101-UKMO-L4HRfnd-v01-fv02-OSTIA_tuple.csv'  # 导出的文件名

# 正式处理代码
# os.chdir(r'/Users/littlesec/Desktop/')
f = netcdf.netcdf_file(fileName, 'r')
lon = f.variables['lon'].data[lonIndex1:lonIndex2]
lat = f.variables['lat'].data[latIndex1:latIndex2]
mask = f.variables['mask'].data[:, latIndex1:latIndex2, lonIndex1:lonIndex2]
header = ['lon', 'lat', 'mask']
x, y = np.meshgrid(lon, lat)
point = np.rec.fromarrays([x, y])
dt1 = pd.DataFrame(point.ravel())
dt2 = pd.DataFrame(mask.ravel())
csv = pd.concat([dt1, dt2], axis=1)
i = 3
for key in keyList:
    var = f.variables[key]
    observedValue = var.data[:, latIndex1:latIndex2,
                             lonIndex1:lonIndex2].copy()
    observedValue = np.where(observedValue == var._FillValue, nanValue, observedValue.astype(
        float) * var.scale_factor + var.add_offset)
    header.append(key)
    csv.insert(i, key, observedValue.ravel())
    i += 1
csv.to_csv(csvName, index=False, header=header)

'''
analysed_sst = f.variables['analysed_sst'].data[:,latIndex1:latIndex2,lonIndex1:lonIndex2]
analysis_error = f.variables['analysis_error'].data[:,latIndex1:latIndex2,lonIndex1:lonIndex2]
sea_ice_fraction = f.variables['sea_ice_fraction'].data[:,1100:latIndex2,lonIndex1:lonIndex2]
'''
