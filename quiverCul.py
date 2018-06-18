import numpy as np
import pandas as pd
import os
import time

RESOLUTION = 1 # 2/25*6 * 2 --> 1 # 该数值应该通过实验修改
ROOTPATH = '/Users/openmac/Downloads/LittleSec/new nc data/速度矢量场数据/'
DEPTHLIST = ['0.0m', '8.0m', '15.0m', '30.0m', '50.0m']
ATTRLIST = ['water_u', 'water_v']

def culEndPoint(absfileName):
    '''
    param:
        absfileName: tuple csv文件的绝对地址
        绘制quiver图的箭头，svg绘制线箭头需要确定起终点，该函数就是根据uv算出理论上终点的经纬度
    attention:
        c的float保证6位有效
        为了提高前段计算效率, 最后存储时最多保留6位有效
    '''
    df = pd.read_csv(absfileName)
    maxuv = np.round(np.max(np.abs(df[['water_u', 'water_v']].values)), 6)
    scaleFactor = RESOLUTION/maxuv
    df['lon1'] = df['lon'] + df['water_u'] * scaleFactor
    df['lat1'] = df['lat'] + df['water_v'] * scaleFactor
    df['scalar'] = np.sqrt(df['water_u'].round(6)**2 + df['water_v'].round(6)**2)
    df.round(6).to_csv(absfileName, index=False, na_rep='NaN')

def sparseResolution(srcFile, srcPath, tarPath, reso=6):
    '''
    func:
        将目标文件的密度稀疏，
    param:
        srcFile: 源文件名()
        srcPath: 基于工作目录的源文件路径
        tarPath: 基于工作目录的保存路径，默认文件名同名
        reso: 源文件数据隔reso个间隔保留一个数据
    attention:
        请确保csv是grid形式，代码不作合法性判断。
        请确保路径和文件名都存在，代码不作检查。
    refer to:
        ../Widgets/pick_mask/mask_extract.py
    '''
    csv = np.genfromtxt('/'.join([srcPath, srcFile]), delimiter=',')
    lon = csv[0,1:]
    lat = csv[1:,0]
    value = csv[1:, 1:]
    lonDeleteList = [i for i in range(0, len(lon)) if i % reso != 0]
    latDeleteList = [i for i in range(0, len(lat)) if i % reso != 0]
    lon = np.delete(lon, lonDeleteList, axis=0)
    lat = np.delete(lat, latDeleteList, axis=0)
    value = np.delete(value, lonDeleteList, axis=1)
    value = np.delete(value, latDeleteList, axis=0)
    pd.DataFrame(value, columns=lon, index=lat).to_csv('/'.join([tarPath, srcFile]), na_rep='NaN')


if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    # 稀疏化密度
    # for attr in ATTRLIST:
    #     for depth in DEPTHLIST:
    #         srcPath = '/'.join([attr+'_grid', depth])
    #         tarPath = '/'.join(['s_'+attr+'_grid', depth])
    #         os.makedirs(tarPath)
    #         for file in os.listdir(srcPath):
    #             sparseResolution(file, srcPath, tarPath)
    #     print("run time: "+str(time.clock()-start)+" s")

    # 计算quiver终点
    for depth in DEPTHLIST:
        if os.path.isdir(depth):
            for file in os.listdir(depth):
                if file[-4:] == '.csv':
                    culEndPoint('/'.join([depth, file]))
        print("run time: "+str(time.clock()-start)+" s")
        start = time.clock()