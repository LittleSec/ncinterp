import os
import numpy as np
import pandas as pd
from scipy.io import netcdf
from scipy import interpolate 
import datetime
import re
import time

class NcFile:
	def __init__(self, fileName, rootPath):
		self.rootPath = rootPath
		self.fileName = fileName
		self.openAnNcFile()

	def getFileInfo(self):
		# 获取文件信息
		self.getLongiAndLati()
		self.getObservedValue()
		self.dimensions = self.f.dimensions # dimensions不要用于获取某个维度的大小，
											# nc文件在创建时很有可能在这里记录错误，例如sst2960-2017.nc这个文件的'T'维度大小是None
											# 要想获得数据的数量，还是以实际数据的列表长度为准
		self.getTimeValue()
		if(len(self.dimensions) == 4):
			self.getDepthValue()
		if np.isnan(self.missingValue):
			print("There is no missing_value in this file: " + self.fileName)
			self.missingValue = float(eval(input("Please input a num to replace the missing_value: ")))
		'''
		# 下面获取数据的组数，注意有依赖关系即必须先获得观测值。
		num = 1
		for i in range(len(self.observedValue.shape)-2): # 默认后两个属性对应的值是经纬度
			num *= self.observedValue.shape[i]		
		self.numOfGroups = num # 数据的组数
		'''

	def openAnNcFile(self, fileName = None):
		os.chdir(self.rootPath) #进入工作目录
		if fileName is None:
			fileName = self.fileName
		self.f = netcdf.netcdf_file(fileName, 'r') #使用scipy自带nc文件读写方法

	def getLongiAndLati(self):
		'''获取经纬度，因为并非所有文件的经纬度索引key都是X和Y，因此需要通过long_name遍历搜索
		同时有一个文件的所有属性都没有long_name，因此通过两种方法进行获取'''
		self.x = []
		self.y = []
		for key in self.f.variables.keys():
			try: # 有些属性没有long_name，会引发异常
				if(self.f.variables[key].long_name == b"Longitude"):
					#self.x = [x for x in self.f.variables[key].data if 117.5 <= x <= 129.5]
					self.x = self.f.variables[key].data
				elif(self.f.variables[key].long_name == b"Latitude"):
					self.y = self.f.variables[key].data
			except Exception as e:
				print(key, "the error message is ", e)
		if(len(self.x) == 0):
			self.x = self.f.variables['X'].data
		if(len(self.y) == 0):
			self.y = self.f.variables['Y'].data

	def getTimeValue(self):
		'''获取时间序列'''
		dateNumberList = []
		dateUnits = ''
		for keys in self.f.variables.keys():
			try: # 有些属性没有long_name，会引发异常
				if(self.f.variables[keys].long_name == b"Time"):
					dateNumberList = self.f.variables[keys].data # 仅仅是一堆数字，不能直观反映绝对时间
					dateUnits = str(self.f.variables[keys].units, encoding = 'utf-8') # 单位
					break
			except Exception as e:
				print("the error message is ", e)
		if(dateUnits == ''):
			dateNumberList = self.f.variables['T'].data
			dateUnits = str(self.f.variables['T'].units, encoding = 'utf-8')

		self.timeList = [] # 该序列每个元素都是时间直观的字符串
		startDate = dateUnits.split('since')[-1] # 最后的子串是开始日期
		if(dateUnits.split()[0] == 'months'): # 单位是月，但相加的值可能是小数，因此要分年月日处理
			startDate = startDate.strip()
			startDateSubList = startDate.split('-')
			startYear = int(startDateSubList[0])
			startMonth = int(startDateSubList[1])
			startDay = int(startDateSubList[2])
			for i in range(len(dateNumberList)):
				intPart = int(dateNumberList[i])
				decimalPart = dateNumberList[i] - intPart
				day = startDay + int(decimalPart * 30)
				month = startMonth
				year = startYear
				if(day > 30): # 待考虑，统一每个月只有30天
					day %= 30
					month += 1
				month += intPart
				if(month > 12):
					month %= 12
					year += (month // 12)
				date = '{:>4}-{:0>2}-{:0>2}'.format(year, month, day)
				self.timeList.append(date)
		elif(dateUnits.split()[0] == 'days'):
			startDate = startDate.strip()[:-10] # 最后两位是小数点
			d = datetime.datetime.strptime(startDate, '%Y-%m-%d')
			for i in range(len(dateNumberList)):
				delta = datetime.timedelta(days=int(dateNumberList[i]))
				date = d + delta
				self.timeList.append(str(date.strftime('%Y-%m-%d')))

	def getDepthValue(self):
		self.depthDataList = self.f.variables['Z'].data
		self.depthUnits = str(self.f.variables['Z'].units, encoding = 'utf-8')

	def getObservedValue(self):
		'''获取所有实际测量的值，默认属性名不用以下名字：['X', 'Y', 'Z', 'T', 'lat', 'lon']'''
		for keys in self.f.variables.keys():
			if(keys in ['T', 'X', 'Y', 'Z', 'lat', 'lon', 'time']):
				continue # 利用短路运算提高速度，保证for循环中有且仅有一次是遍历整个list
			else:
				var = self.f.variables[keys]
				self.observedValue = var.data.astype(float)
				self.missingValue = np.float(var.missing_value)
				if('add_offset' in dir(var) and 'scale_factor' in dir(var)): # 源数据经过处理，例如sst2960-2017.nc
					# 不可以self.observedValue *= 1，因为这只是个指向文件数据而已，而数据是只读的。
					self.observedValue = var.data.astype(float) * var.scale_factor + var.add_offset
					self.missingValue *= var.scale_factor 
					self.missingValue += var.add_offset
				break

	def processAGroupData(self, dataInfo, timeIndex = 0, depthIndex = 0, minutes = 5):
		'''这些nc文件的组织规律如下：
		若是除了经纬度之外，还有时间和深度两个变量，则经纬度的索引分别是X,Y，而深度的索引是Z，时间的索引是T
		若是除了经纬度之外，只有时间这个变量，则经纬度的索引分别是lon,lat，时间的索引是time
		观测值的维度由外到内分别是：时间、深度（如果有的话）、经纬度'''
		if(len(self.dimensions) == 4):
			data = DataProcessor(self.x, self.y, self.observedValue[timeIndex][depthIndex], dataInfo)
		else:
			data = DataProcessor(self.x, self.y, self.observedValue[timeIndex], dataInfo)
		data.setNaNValue(50)
		data.setResolution(minutes)
		data.setInterpFunc()
		data.interpAGroupData()
		data.writeInCSV()

	def processAFileData(self, minutes = 5):
		'''处理整个nc文件的数据，分三元和四元情况，默认只有这两种情况'''
		self.getFileInfo()
		dataInfo = {}
		dataInfo['RootPath'] = self.rootPath
		dataInfo['DirsName'] = self.fileName[:-3]
		dataInfo['MissingValue'] = self.missingValue
		if(len(self.dimensions) == 4):
			for i in range(len(self.timeList)):
				dataInfo['Time'] = self.timeList[i]
				for j in range(len(self.depthDataList)):
					dataInfo['Depth'] =  str(self.depthDataList[j]) + str(self.depthUnits)
					self.processAGroupData(dataInfo, i, j, minutes)
		else:
			dataInfo['Depth'] = '' # 为了调用者代码重用
			for i in range(len(self.timeList)):
				dataInfo['Time'] = self.timeList[i]
				self.processAGroupData(dataInfo, i, 0, minutes)


class DataProcessor:
	def __init__(self, x, y, z, dataInfo):
		self.dataInfo = dataInfo# 记录该组数据对应时间和深度等信息
		self.x = x # 源经度
		self.y = y # 源纬度
		self.z = z # 源数据值
		self.NaNValue = dataInfo['MissingValue'] # 缺失值的替代值
		self.xi = self.x # 提高密度后的经度序列
		self.yi = self.y
		self.interpFunc = None
		self.zi = self.z # 提高密度插值后数据值

	def setNaNValue(self, NaNReplaceValue = None):
		'''循环遍历设置缺失值，以方便全数据参与插值运算'''
		
		'''输入缺失值的工作还是交付给上层做吧。
		if np.isnan(NaNReplaceValue):
			NaNReplaceValue = eval(input("Please input a value to replace the NaN: "))
		'''
		if NaNReplaceValue is None:
			NaNReplaceValue = self.NaNValue
		for i in range(self.z.shape[0]):
			for j in range(self.z.shape[1]):
				if np.isnan(self.z[i][j]) or self.z[i][j] == self.NaNValue:
					self.z[i][j] = NaNReplaceValue	

	def setResolution(self, minutes = 5):
		'''设置分辨率，minutes指多少分就有一个数据'''
		numOfSectionsInOneDegree = 60 // minutes
		max_x = 129.5#np.max(self.x)#
		min_x = 117.5#np.min(self.x)#
		max_y = 36.5#np.max(self.y)#
		min_y = 24.5#np.min(self.y)#
		n_x = complex(0, (max_x - min_x) * numOfSectionsInOneDegree + 1)
		n_y = complex(0, (max_y - min_y) * numOfSectionsInOneDegree + 1)
		self.xi = np.ogrid[min_x:max_x:n_x]
		self.yi = np.ogrid[min_y:max_y:n_y]

	def setInterpFunc(self):
		'''计算插值函数（二元三次样条插值）'''
		self.interpFunc = interpolate.interp2d(self.x, self.y, self.z, kind='cubic')

	def interpAGroupData(self):
		self.zi = self.interpFunc(self.xi, self.yi)

	def writeInCSV(self, dataInfo = None):
		if dataInfo is None:
			dataInfo = self.dataInfo
		os.chdir(dataInfo["RootPath"]) 
		if not os.path.exists(dataInfo["DirsName"]):
			os.makedirs(dataInfo["DirsName"])
		os.chdir(r'%s' % dataInfo["DirsName"])
		fileName = r'{0}, {1}, ({2}x{3}).csv'.format(dataInfo['Time'], dataInfo['Depth'], self.zi.shape[0], self.zi.shape[1])
		pd.DataFrame(self.zi, columns=self.xi, index=self.yi).to_csv(fileName)

if __name__ == '__main__':
	'''
	f1 = NcFile('relative humidity1960-2017.nc')
	f1.processAFileData()
	'''
	start = time.clock()
	rootPath = r'/Users/littlesec/Desktop/ncinterp/'
	os.chdir(rootPath) #进入工作目录
	fileNamePattern = re.compile(r'.*.nc') # 第一个点不能省略
	fileList = os.listdir()
	for file in fileList:
		if not fileNamePattern.match(file) is None:
		# if file in ['relative humidity1960-2017.nc', 'sea level pressure1960-2017.nc', 'sst1960-2017.nc', 'uwind1960-2017.nc', 'vwind1960-2017.nc']:
			f1 = NcFile(file, rootPath)
			f1.processAFileData(5)

	elapsed = (time.clock()-start)
	print("run time: "+str(elapsed)+" s")
		