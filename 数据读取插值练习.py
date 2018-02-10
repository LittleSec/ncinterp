import os
from scipy.io import netcdf

#nc文件的读取
os.chdir(r'/Users/littlesec/Desktop/ncinterp') #进入工作目录
f = netcdf.netcdf_file(r'potden_monthly1994.nc','r') #使用scipy自带nc文件读写方法
print(f.dimensions) #Out: OrderedDict([('Z', 24), ('T', 12), ('Y', 13), ('X', 13)])
print(f.variables.keys()) #Out: odict_keys(['Z', 'T', 'Y', 'X', 'O2'])
'''
variables类型是collections.OrderedDict有序字典
#f的属性和nc文件是一致的，包括variable下的属性也和nc文件中的结构一致，可用Panoply查看
'''
O2 = f.variables['O2'] 
print(O2.shape) #Out: (12, 24, 13, 13) #维度
X = f.variables['X'] #经度
Y = f.variables['Y'] #纬度
x = X.data #正确访问数据的方法
y = Y.data
z = O2.data[0][0] #选取第一个时间（1960-01-16）和第一个深度（0m）的数据作为练习
print(z.shape) #Out: (13, 13)

#插值与绘图
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate #插值模块
import matplotlib.pylab as pl

interp = interpolate.interp2d(x, y, z, kind='cubic')
xi = np.ogrid[117.5:129.5:101j] #[start:end:step]，其中若step为复数，则虚部数字n表示分割成n个数，包括终点值
yi = np.ogrid[24.5:36.5:101j] #等同yi = np.linspace(24.5, 36.5, 101)
zi = interp(xi, yi)
print(zi.shape) #Out: (100, 100)

pl.subplot(121) #pyplot中也有subplot，但这个是pylab的，二者是不一样的
#121并非一百二十一的意思，是三个单独的数字，表示将figure分割成1*2的形式，因此取值范围是[1,9]
#而最后一个数字指示当前是第几个图，因此取值范围是[1, 1*2]
im1 = pl.imshow(z, extent=[117.5,129.5,24.5,36.5], origin="lower") #这里是对原始值z进行描图
#可以指定参数interpolation，默认none，具体使用请用help命令查看
#extent是xy轴的范围：[left, right, bottom, top]，仅仅是标数字，例如交换left和right两值，图像形状无变化
#origin是关于原点位置的参数，通俗来说就是x轴方向固定，lower的y轴正方向上即原点在下面，upper的y轴正方向下即原点在上面。
plt.set_cmap('RdYlBu') #设置颜色
pl.colorbar(im1) #颜色示例条

pl.subplot(122)
im2 = pl.imshow(zi, extent=[117.5,129.5,24.5,36.5], origin="lower") #对插值后的zi进行描图
plt.set_cmap('RdYlBu')
pl.colorbar(im2)

pl.show()

#history，ipython特有的命令，用于查看命令历史