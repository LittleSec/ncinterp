import numpy as np
import pandas as pd
import os
import time

RESOLUTION = 0.4 # 2/25*6 --> 0.4
ROOTPATH = '/Users/openmac/Downloads/new nc data/速度矢量场数据/'
DEPTHLIST = ['0.0m', '8.0m', '15.0m', '30.0m', '50.0m']

def culEndPoint(absfileName):
    '''
    param:
        absfileName: tuple csv文件的绝对地址
        绘制quiver图的箭头，svg绘制线箭头需要确定起终点，该函数就是根据uv算出理论上终点的经纬度
    '''
    df = pd.read_csv(absfileName)
    maxuv = np.max(np.abs(df[['water_u', 'water_v']].values))
    scaleFactor = RESOLUTION/maxuv
    df['lon1'] = df['lon'] + df['water_u'] * scaleFactor
    df['lat1'] = df['lat'] + df['water_v'] * scaleFactor
    df.to_csv(absfileName, index=False, na_rep='NaN')

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    for depth in DEPTHLIST:
        if os.path.isdir(depth):
            for file in os.listdir(depth):
                if file[-4:] == '.csv':
                    culEndPoint('/'.join([depth, file]))
    print("run time: "+str(time.clock()-start)+" s")