from netCDF4 import Dataset
import numpy as np
import pandas as pd
import os
import datetime
import time

ROOTPATH = '/Users/littlesec/Desktop/毕业论文实现/'

class NcFile:
    rootPath = ROOTPATH
    fileName = ''
    x = []
    y = []
    dateTimeList = []
    depth = '0m'
    resolution = 2 / 25
    observedValue = {}  # 可能有多个属性

    def __init__(self, fileName, rootPath=ROOTPATH):
        self.rootPath = rootPath
        self.fileName = fileName
        self.f = self.__openAnNcFile()

    def __openAnNcFile(self):
        '''
        This function is called by __init__(), can't called by other.
        And will return <class 'netCDF4._netCDF4.Dataset'>.
        If fail to open, then return None.
        '''
        try:
            os.chdir(self.rootPath)  #进入工作目录
            return Dataset(self.fileName)
        except FileNotFoundError as err:
            print(err, '\nPlease check your directory and file are both existed!')
            return None

    def getFileInfo(self):
        '''
        The information is included:
            longitude and latitude(type: numpy.ndarray)
            observed value(type: numpy.ndarray)
        '''
        self.x, self.y = self.getLongiAndLati()
        self.dateTimeList = self.getTimeValue()
        self.depth = self.getDepthValue()
        self.getObservedValue()

    def getLongiAndLati(self):
        '''
        This function will return two numpy.ndarrays,
        one is longitude(x), another is latitude(y).
        By the way, there is no code to handle date reading error.
        In other words, it's successfully get date by default.
        '''
        if self.f is None:
            print("Error: There is no file opening.")
            return
        x = []
        y = []
        for key in self.f.variables.keys():
            if (len(x) != 0 and len(y) != 0):
                break
            if key.lower() in ['lon', 'x', 'longitude']:
                x = self.f.variables[key][:]
            elif key.lower() in ['lat', 'y', 'latitude']:
                y = self.f.variables[key][:]
        return np.round(x, 2), np.round(y, 2)  # 保留两位小数

    def getTimeValue(self):
        '''
        This function will read the time(actually it's the datetime) list in nc file, and return it.
        In nc file, the item in time list is just a number started from units, and it's not esay for us to read them intuitively.
        So, this function will change number to a datetime string('yyyy-mm-dd hh:mm:ss') by combining with the units.
        Attention, by default, the unit is hour.
        '''
        dateTimeNumList = []
        dateTimeUnits = ''
        for key in self.f.variables.keys():
            if key.lower() in ['time', 't']:
                dateTimeNumList = self.f.variables[key][:]
                dateTimeUnits = self.f.variables[key].units
                break

        dateTimeStrList = []  # 该序列每个元素都是时间直观的字符串
        startDateTimeStr = ' '.join(dateTimeUnits.split()[-2:])  # -1是时间,-2是日期,'2000-01-01 00:00:00'
        stdt = datetime.datetime.strptime(startDateTimeStr, '%Y-%m-%d %H:%M:%S')
        if dateTimeUnits.split()[0] == 'hours':
            for dtn in dateTimeNumList:
                dt = stdt + datetime.timedelta(hours=dtn)  # type is datetime
                dateTimeStrList.append(dt.strftime('%Y-%m-%d'))

        return dateTimeStrList

    def getDepthValue(self):
        '''
        return a depth(with unit) str, round(1)
        by default, just a depth!!!
        '''
        depthList = None
        for key in self.f.variables.keys():
            if key.lower() in ['depth', 'z']:
                depthList = self.f.variables[key][:]
                depthUnits = self.f.variables[key].units
                break
        if depthList is None: # ssh 没有深度
            return
        return str(round(depthList[0], 1)) + depthUnits

    def getObservedValue(self):
        '''
        获取所有实际测量的值，默认属性名不用以下名字：['X', 'Y', 'Z', 'T', 'lat', 'lon', 'depth']
        关于missing_value(_FillValue)
            nc文件中虽然显示NaN，但是missing_value(_FillValue)却不是NaNf，这是文件所定义的机制。
            如果使用追加(a)模式修改这个属性的字段值为NaNf(np.nan)，那么显示的就不再是NaN了，而且定义的数据类型的最小值（一绘图就知道区别了）。
            无论如何，读出来都不会是NaN。
            综上nc文件实际上是没有定义NaN类型的（虽然会显示说缺失值是NaNf），官方社区有相关的回答。
            因此需要在这里修改这些值为NaN方便后期使用。
        '''
        observedValue = []
        for key in self.f.variables.keys():
            if (key in ['lat', 'lon', 'time', 'depth', 'T', 'X', 'Y', 'Z']):
                continue  # 利用短路运算提高速度，保证for循环中有且仅有一次是遍历整个list
            else:
                var = self.f.variables[key]
                observedValue = var[:]
                # observedValue = var.data.astype(float)
                # missingValue = np.float(var.missing_value)
                # if not np.isnan(missingValue):
                #     observedValue[observedValue == missingValue] = np.nan
                # if ('add_offset' in dir(var) and 'scale_factor' in dir(var)):  # 源数据经过处理，例如sst2960-2017.nc
                #     observedValue = var.data.astype(float) * var.scale_factor + var.add_offset
                self.observedValue[key] = observedValue

    def toCSVgrid(self):
        '''
        output:
            命名规则：./attr_tuple/(depth/)yyyy-mm-dd.csv
        '''
        if self.x == [] or self.y == [] or self.dateTimeList == [] or self.observedValue == {}:
            self.getFileInfo()
        for attr, value in self.observedValue.items():
            os.chdir(self.rootPath)
            folder = attr + '_grid'
            if not self.depth is None:
                folder = '/'.join([folder, self.depth])
            if not os.path.exists(folder):
                os.makedirs(folder)
            os.chdir(folder)
            for i in range(len(self.dateTimeList)):
                fileName = self.dateTimeList[i] + '.csv'
                if self.depth is None:
                    pd.DataFrame(value[i], columns=self.x, index=self.y).to_csv(
                        fileName, na_rep='NaN')
                else:
                    # value.shape: (552, 1, 263, 271)
                    pd.DataFrame(value[i][0], columns=self.x, index=self.y).to_csv(
                        fileName, na_rep='NaN')


if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    fileList = os.listdir()
    for file in fileList:
        if file[-3:] == '.nc':
            nc = NcFile(file)
            nc.toCSVgrid()
            print("run time: "+str(time.clock()-start)+" s")
            start = time.clock()