import numpy as np
from scipy import interpolate
import pandas as pd
# import os
# os.chdir(r'/Users/littlesec/Desktop/')
csv = np.genfromtxt('minisome.csv',delimiter=',')
xi = csv[0,1:]
yi = csv[1:,0]
x, y = np.meshgrid(xi,yi)
point = np.rec.fromarrays([x,y])
value = csv[1:,1:]
point = point.ravel()
value = value.ravel()
pointWithValue = np.array([point[i] for i in range(point.size) if not np.isnan(value[i])])
zj = np.array([v for v in value if not np.isnan(v)])
xj = np.array([pointWithValue[i][0] for i in range(pointWithValue.size)])
yj = np.array([pointWithValue[i][1] for i in range(pointWithValue.size)])
xnew = np.linspace(np.min(xi), np.max(xi), xi.size*5-4) # xi.size*n-(n-1)
ynew = np.linspace(np.min(yi), np.max(yi), yi.size*5-4)
f = interpolate.interp2d(xj, yj, zj, kind='cubic', fill_value=np.nan)
pd.DataFrame(f(xnew, ynew),index=ynew).to_csv('somenew.csv',header=xnew)