from netCDF4 import Dataset
import numpy as np
import pandas as pd
import os
import datetime
import time
from multiprocessing import Pool

ROOTPATH = '/Users/littlesec/Downloads/nc1/'

DIFF1 = [
    '2014-07-08', '2014-07-27', '2014-08-02', '2014-08-05', '2014-09-07',
    '2014-09-20', '2014-10-06', '2014-10-27', '2014-12-09', '2014-12-13',
    '2014-12-21', '2015-01-05', '2015-01-07', '2015-01-21', '2015-01-26',
    '2015-01-28', '2015-02-09', '2015-02-23', '2015-02-25', '2015-03-06',
    '2015-03-18', '2015-03-21', '2015-03-28', '2015-03-30', '2015-04-03',
    '2015-04-06', '2015-04-08', '2015-04-10', '2015-04-11', '2015-04-12',
    '2015-04-13', '2015-04-15', '2015-04-19', '2015-04-22', '2015-04-23',
    '2015-04-25', '2015-04-27', '2015-05-07', '2015-05-17', '2015-05-31',
    '2015-06-04', '2015-06-08', '2015-07-08', '2015-07-21', '2015-08-06',
    '2015-08-27', '2015-10-09', '2015-10-13', '2015-10-21', '2015-11-05',
    '2015-11-07', '2015-11-21', '2015-11-26', '2015-11-28', '2015-12-10',
    '2015-12-24', '2015-12-26', '2016-01-04', '2016-01-16', '2016-01-22',
    '2016-01-27', '2016-01-31', '2016-02-03', '2016-02-05', '2016-02-07',
    '2016-02-08', '2016-02-09', '2016-02-11', '2016-02-15', '2016-02-18',
    '2016-02-19', '2016-02-22', '2016-02-25', '2016-03-06', '2016-03-07',
    '2016-03-13', '2016-03-27', '2016-03-31', '2016-04-14'
]

DIFF2 = [
    '2015-05-17', '2015-05-31', '2015-06-08', '2016-01-22', '2016-02-19',
    '2016-02-25', '2016-03-06', '2016-03-07', '2016-04-14'
]

DIFF3 = [
    '2015-06-18', '2015-09-11', '2015-10-01', '2015-10-31', '2015-12-05',
    '2015-12-15'
]

DIFF4 = [
    '2015-05-17', '2015-05-31', '2015-06-08', '2016-01-22', '2016-02-25',
    '2016-03-06', '2016-03-07', '2016-04-14'
]

DIFF5 = ['2016-03-07'] # surf_el这一天没有12,15点的数据


class NcFile:
    rootPath = ROOTPATH
    fileName = ''
    x = []
    y = []
    dateTimeList = []
    depth = None
    resolution = 2 / 25
    dateFlagList = []
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
            print(err,
                  '\nPlease check your directory and file are both existed!')
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
        startDateTimeStr = ' '.join(
            dateTimeUnits.split()[-2:])  # -1是时间,-2是日期,'2000-01-01 00:00:00'
        stdt = datetime.datetime.strptime(startDateTimeStr,
                                          '%Y-%m-%d %H:%M:%S')
        if dateTimeUnits.split()[0] == 'hours':
            for dtn in dateTimeNumList:
                dt = stdt + datetime.timedelta(hours=dtn)  # type is datetime
                ymd = dt.strftime('%Y-%m-%d')
                dateTimeStrList.append(ymd)
                # DIFF存放没有12点数据的日期，则取15点或9点的
                # if ymd in DIFF5 and dtn % 24 == 15:
                #     self.dateFlagList.append(True)
                #     print(ymd)
                # else:
                #     self.dateFlagList.append(False)
                # 只提取某天12点的数据
                if dtn % 24 == 12:
                    self.dateFlagList.append(True)
                else:
                    self.dateFlagList.append(False)

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
        if depthList is None:  # ssh 没有深度
            return None
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
                if self.dateFlagList[i] == False:
                    continue
                fileName = self.dateTimeList[i] + '.csv'
                if self.depth is None:
                    pd.DataFrame(
                        value[i], columns=self.x, index=self.y).to_csv(
                            fileName, na_rep='NaN')
                else:
                    # value.shape: (552, 1, 263, 271)
                    pd.DataFrame(
                        value[i][0], columns=self.x, index=self.y).to_csv(
                            fileName, na_rep='NaN')

if __name__ == '__main__':
    start = time.clock()
    os.chdir(ROOTPATH)
    # nc = NcFile('150501-160430_surf_el.nc')
    # nc.toCSVgrid()
    # print("run time: "+str(time.clock()-start)+" s")

    fileList = os.listdir()
    for file in fileList:
        if file[-3:] == '.nc':
            print("now: " + file)
            nc = NcFile(file)
            nc.toCSVgrid()
            nc.f.close()
            del nc
            print("run time: " + str(time.clock() - start) + " s")
            start = time.clock()
