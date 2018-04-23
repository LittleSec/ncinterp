import os
from scipy.io import netcdf
import numpy as np
import pandas as pd

def setResolution(degree, lon, lat, mask):
    '''
    param:
        degree: how many degresss have a data.
            must one of [0.1, 0.2, 0.25, 0.5]
            else return parameters directly
        lon: source
        lat: source
        mask: source
    return:
        lon: target
        lat: target
        mask: target
    '''
    if degree in [0.1, 0.2, 0.25, 0.5]:
        d = degree // 0.05
        lonDeleteList = []
        latDeleteList = []
        for i in range(0, len(lon)):
            if i % d != 0:
                lonDeleteList.append(i)
        for i in range(0, len(lat)):
            if i % d != 0:
                latDeleteList.append(i)
        lon = np.delete(lon, lonDeleteList, axis=0)
        lat = np.delete(lat, latDeleteList, axis=0)
        mask = np.delete(mask, lonDeleteList, axis=1)
        mask = np.delete(mask, latDeleteList, axis=0)
    return lon, lat, mask

def mask(ncFileName, degree):
    # 正式处理代码
    f = netcdf.netcdf_file(ncFileName, 'r')
    lon = f.variables['lon'].data # 251
    lat = f.variables['lat'].data # 331
    mask = f.variables['mask'].data[0] # (331, 251)# 不懂为啥还保留了time属性
    header = ['lon', 'lat', 'mask']
    newMask = np.where(mask == 1, mask, 0)
    lon, lat, newMask = setResolution(degree, lon, lat, newMask)
    x, y = np.meshgrid(lon, lat)
    point = np.rec.fromarrays([x, y])
    dt1 = pd.DataFrame(point.ravel())
    dt2 = pd.DataFrame(newMask.ravel())
    pd.concat([dt1, dt2], axis=1).to_csv('mask_tuple_{0}.csv'.format(str(degree).replace('.', 'p')), index=False, header=header)

    # column和index对于数字类型的传参或默认强制转换成float64。
    # 该文件中的lon和lat都是float32类型的。
    # 当float32转换成float64是容易出现精度问题的，因此需要先转换成字符串。
    # 已提交的issue: https://github.com/pandas-dev/pandas/issues/20778
    pd.DataFrame(newMask, columns=[str(a) for a in lon], index=[str(a) for a in lat]).to_csv('mask_grid_{0}.csv'.format(str(degree).replace('.', 'p')))
    f.close()

if __name__ == '__main__':
    # ncFileName = 'sst_mask_cutlatlon.nc'
    degree = 0.05 # must one of [0.05, 0.1, 0.2, 0.25, 0.5]
    # 以下代码获取nc文件名而已，可以上面直接使用硬编码
    currentdir = os.path.dirname(__file__)
    fileList = os.listdir(currentdir)
    for file in fileList:
        if file[-3:] == '.nc':
            ncFileName = file
            break
    os.chdir(currentdir)
    mask(ncFileName, degree)
