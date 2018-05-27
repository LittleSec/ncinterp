import numpy as np
import os
import pandas

def eddy(date, sshpath, owpath, scale):
    '''
    需要注意ssh grid和ow grdi的经纬度序列是不一样的，ow的要少一点。
    sshpath是grid的csv路径
    scale确保是个奇数！直径
    '''
    # 读取ssh和ow
    if scale % 2 != 0: #确保scale是奇数
        scale =  int(scale) + 1 # 不能简写成+=
    sshcsv = np.genfromtxt('/'.join([sshpath, date]), delimiter=',')
    sshlon = sshcsv[0, 1:]
    sshlat = sshcsv[1:, 0]
    ssh = sshcsv[1:, 1:]

    # 对ssh进行遍历
    radius = scale // 2
    '''
    ssh[-2:2] --> array([], shape=(0, ?), dtype=?)
    ssh[-2:] --> array([[?], [?]], shape=(2, ?), dtype=?)
    ssh[:len+2] --> array([], shape=(0, ?), dtype=?)
    想说明的是实际上可以不用规定从[radius][radius]这个点开始遍历，numpy的索引是循环的，在数值计算上不会存在越界这个说法。
    但是要考虑到一点是[len-1][len-1]如果按照下面的逻辑则该点会被判断为最大和最小值。
    所以在此依然空出四边的边界，这样也减少迭代次数。
    '''
    for i in range(radius, len(sshlon)-radius):
        for j in range(radius, len(sshlat)-radius):
            if np.isnan(ssh[i][j]):
                continue
            if np.nanmax(ssh[i-radius:i+radius, j-radius:j+radius]) == ssh[i][j]:
                pass
                # 当前点和矩阵最值对比是否同，是则对比ow