import os
import numpy as np
import pandas as pd
from scipy.io import netcdf
from scipy import interpolate 
import datetime
import re
import time

class NcFile:
	def __init__(self, fileName, rootPath = r'/Users/littlesec/Desktop/毕业设计/caoweidongdata/'):
		self.rootPath = rootPath
		self.fileName = fileName
		self.f = self.__openAnNcFile()

	def __openAnNcFile(self):
		'''
		This function is called by __init__(), can't called by other.
		And will return a object<scipy.io.netcdf.netcdf_file>.
		If fail to open, then return None.
		'''
		try:
			os.chdir(self.rootPath) #进入工作目录
			return netcdf.netcdf_file(self.fileName, 'r') #使用scipy自带nc文件读写方法
		except FileNotFoundError as err:
			print(err, '\nPlease check your directory and file are both existed!')
			return None

	def getFileInfo(self):
		'''
		The information is included:
				longitude and latitude(type: numpy.ndarray, dimension: 1)
				observed value(type: numpy.ndarray)
				observed value's demension: 3 or 4 
				missingValue(must float, if the file doesn't define, it will prompt user to input)
		'''	
		self.x, self.y = self.getLongiAndLati()
		self.getObservedValue() # will get missing_value, too
		self.dimension = len(self.f.dimensions) 
		# f.dimensions不要用于获取某个维度的大小，
		# nc文件在创建时很有可能在这里记录错误，例如sst1960-2017.nc这个文件的'T'维度大小是None
		# 要想获得数据的数量，还是以实际数据的列表长度为准
		self.timeListself.getTimeValue()
		if(self.dimension == 4):
			self.getDepthValue()
		if np.isnan(self.missingValue):
			print("There is no missing_value in this file: " + self.fileName)
			print("The observed value: **max: {0}**, **min: {1}**".format(np.nanmax(self.observedValue), np.nanmin(self.observedValue)))
			self.missingValue = float(eval(input("Please input a num to replace the missing_value: ")))

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
		# 直接用正则表达式匹配X,Y,lat,lon,latitude,longitude
		for key in self.f.variables.keys():
			if(len(x) != 0 and len(y) != 0):
				break
			if key.lower() in ['lon', 'x', 'longitude']:
				x = self.f.variables[key].data
				#self.x = [x for x in self.f.variables[key].data if 117.5 <= x <= 129.5]
			elif key.lower() in ['lat', 'y', 'latitude']:
				y = self.f.variables[key].data
		return x, y

	def getTimeValue(self):
		'''
		This function will read the time(actually it's the date) list in nc file, and return it.
		In nc file, the item in time list is just a number started from 1 or 0.5, and it's not esay for us to read them intuitively.
		So, this function will change number to a date string(yyyy-mm-dd) by combining with the units.
		Attention, by default, every month just has 30 days.
		'''
		dateNumberList = []
		dateUnits = ''
		for key in self.f.variables.keys():
			if key.lower() in ['time', 't']:
				dateNumberList = self.f.variables[key].data
				dateUnits = str(self.f.variables[key].units, encoding = 'utf-8')
				break

		dateStringList = [] # 该序列每个元素都是时间直观的字符串
		startDate = dateUnits.split('since')[-1].strip() # 最后的子串是开始日期
		if(dateUnits.split()[0] == 'months'): # 单位是月，但相加的值可能是小数，因此要分年月日处理
			startDateSubList = startDate.split('-')
			startYear = int(startDateSubList[0])
			startMonth = int(startDateSubList[1])
			startDay = int(startDateSubList[2])
			for i in range(len(dateNumberList)):
				intPart = int(dateNumberList[i])
				decimalPart = round(dateNumberList[i] - intPart, 1) # just try 1.9-1
				day = startDay + int(decimalPart * 30)
				month = startMonth
				year = startYear
				if(day > 30): # 待考虑，统一每个月只有30天
					day %= 30
					month += 1
				month += intPart
				if(month > 12):
					year += (month // 12)
					month %= 12 # Can't invert the order, because this word will change month value
					if(month == 0): # think about e.g. 23.5, month=1+23=24, but 24/12=2...0, in fact year just +1 and month should be 12
						month = 12
						year -= 1
				date = '{:>4}-{:0>2}-{:0>2}'.format(year, month, day)
				dateStringList.append(date)
		elif(dateUnits.split()[0] == 'days'):
			startDate = startDate[:-10] # 舍去后面的时间00:00:0.0
			d = datetime.datetime.strptime(startDate, '%Y-%m-%d')
			for i in range(len(dateNumberList)):
				delta = datetime.timedelta(days=int(dateNumberList[i]))
				date = d + delta
				dateStringList.append(str(date.strftime('%Y-%m-%d')))
		return dateStringList


	def getDepthValue(self):
		for key in self.f.variables.keys():
			if key.lower() in ['depth', 'z']:
				self.depthDataList = self.f.variables[key].data
				self.depthUnits = str(self.f.variables[key].units, encoding = 'utf-8')
				break
		
	def getObservedValue(self):
		'''获取所有实际测量的值，默认属性名不用以下名字：['X', 'Y', 'Z', 'T', 'lat', 'lon', 'depth']'''
		for key in self.f.variables.keys():
			if(key in ['T', 'X', 'Y', 'Z', 'lat', 'lon', 'time', 'depth']):
				continue # 利用短路运算提高速度，保证for循环中有且仅有一次是遍历整个list
			else:
				var = self.f.variables[key]
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
		if(self.dimension == 4):
			data = DataProcessor(self.x, self.y, self.observedValue[timeIndex][depthIndex], dataInfo)
		else:
			data = DataProcessor(self.x, self.y, self.observedValue[timeIndex], dataInfo)
		data.setNaNValue(50)
		data.setResolution(minutes = minutes)
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
		if(self.dimension == 4):
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

class DataSelector:
	def __init__(self, dateStringList, depthList):
		self.startDate = dateStringList[0]# '1960-02-16' # 
		self.endDate = dateStringList[len(dateStringList)-1]# '2008-06-17' # 
		self.dateStringList = dateStringList # ['1960-02-16', '1960-03-16', '1960-04-16', '1961-05-16', '1970-06-16', '2001-07-16', '2008-06-16']
		self.depthList = depthList # [1, 2.3, 3.45, 4.567, 5.65, 6.3, 7]

	def __indexOfTime(self, timeStr):
		'''
		This function will return a index or timeStr in dateStringList.
		The format of value in dateStringList(like startDate, endDate) is yyyy-mm-dd, but the format of timeStr is yyyymm.
		By the way, this is a private function, the caller will ensure the format of timeStr is legal.
		If timeStr earlier than self.startDate, then return 0(the first index).
		Similarly, if timeStr later than self.endDate, then return the last index(length-1)
		By default, the dateStringList is an ascending and continuous-months sequence, and have't same date.
		'''
		startYear = int(self.startDate.split('-')[0])
		startMonth = int(self.startDate.split('-')[1])
		endYear = int(self.endDate.split('-')[0])
		endMonth = int(self.endDate.split('-')[1])
		year = int(timeStr[:4])
		month = int(timeStr[-2:])
		if(year < startYear):
			return 0 # 1960-01
		elif(year == startYear):
			if(month < startMonth):
				return 0
			else:
				return month - startMonth
		elif(year > endYear or (year == endYear and month > endMonth)):
			return len(self.dateStringList) - 1 # 2008-12
		else:
			return (year - startYear) * 12 + (month - 1)

	def selectByTime(self, timeStr):
		'''
		param: 
			timeStr can be："yyyy", "yyyymm" or "str1-str2"(str1 and str2 must be yyyymm or yyyy).
			As you think, yyyy alone means yyyy01-yyyy12 and in str1 means yyyy01, in str2 means yyyy12.
		Function:
			This function will retuan a list of time index.
			If param is ''
			If the format of timeStr is illegal, than return 0
		'''
		ymPattern = r'([12]\d{3})(0[1-9]|1[0-2])$' # yyyymm
		ymRegex = re.compile(ymPattern)

		yPattern = r'[12]\d{3}$' # yyyy
		yRegex = re.compile(yPattern)

		strSplitList = timeStr.split('-')
		if len(strSplitList) == 1: # no '-'
			if ymRegex.match(timeStr):
				index1 = index2 = self.__indexOfTime(timeStr)
			elif yRegex.match(timeStr): # Can't invert the order, because yyyymm is match yyyy, too.
				index1 = self.__indexOfTime(timeStr + '01')
				index2 = self.__indexOfTime(timeStr + '12') # Can't just +12, because +12 may index out of range
			else:
				index1 = index2 = 0
		elif len(strSplitList) == 2: # can be 'str1-str2', 'str1-', '-str2'
			if ymRegex.match(strSplitList[0]):
				index1 = self.__indexOfTime(strSplitList[0])
			elif yRegex.match(strSplitList[0]):
				index1 = self.__indexOfTime(strSplitList[0] + '01')
			else:
				index1 = 0

			if ymRegex.match(strSplitList[1]):
				index2 = self.__indexOfTime(strSplitList[1])
			elif yRegex.match(strSplitList[1]):
				index2 = self.__indexOfTime(strSplitList[1] + '12')
			else: # included the case like '201010-'
				index2 = self.__indexOfTime(self.endDate.replace('-','')[:-2])
		else:
			index1 = index2 = 0

		if index1 > index2:
			index1, index2 = index2, index1

		return list(range(index1, index2 + 1))

	def __indexOfDepth(self, num, depthList=None):
		'''
		The main idea is bin_search.
		If find successfully, than return the index.
		If find unsuccessfully，than return the index whose value is closer to num.
		By the way, depthList is an ascending sequence by default and haven't same value.
		'''
		depthList = self.depthList
		low = 0
		high = len(depthList) - 1
		if num <= depthList[0]:
			return 0
		elif num >= depthList[len(depthList)-1]:
			return len(depthList)-1
		while low <= high:
			mid = (low + high) // 2
			if depthList[mid] == num:
				return mid
			elif depthList[mid] > num:
				high = mid - 1
			else:
				low = mid + 1
		if depthList[low] - num >= num - depthList[high]: # now the depthList[low] > depthList[high] 
			return high
		else:
			return low

	def selectByDepth(self, depthStr):
		'''
		param:
			depthStr can be: "num(+)", "num1-num2"(num1 < num2) and "num-"
		'''
		strSplitList = depthStr.split('-')
		numPattern = '-?(([1-9]\d*\.\d*|0?\.\d*[1-9]\d*|0?\.0+|0)|([1-9]\d*))'
		numRegex = re.compile(numPattern)

		if len(strSplitList) == 1:
			if numRegex.match(depthStr):
				index1 = index2 = self.__indexOfDepth(eval(depthStr))
			else:
				index1 = index2 = 0
		elif len(strSplitList) == 2:
			if numRegex.match(strSplitList[0]):
				index1 = self.__indexOfDepth(eval(strSplitList[0]))
			else:
				index1 = 0

			if numRegex.match(strSplitList[1]):
				index2 = self.__indexOfDepth(eval(strSplitList[1]))
			else:
				index2 = self.__indexOfDepth(99999) # hard code: max num

		if index1 > index2:
			index1, index2 = index2, index1

		return list(range(index1, index2 + 1))

	def selectByTimeAndDepth(self, time, depth):
		pass

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

	def setResolution(self, min_x = 117.5, max_x = 129.5, min_y = 24.5, max_y = 36.5, minutes = 5):
		'''设置分辨率，minutes指多少分就有一个数据'''
		numOfSectionsInOneDegree = 60 // minutes
		# max_x = np.max(self.x)#
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
	rootPath = r'/Users/littlesec/Desktop/毕业设计/caoweidongdata/'
	os.chdir(rootPath) #进入工作目录
	fileNamePattern = re.compile(r'.*.nc') # 第一个点不能省略
	fileList = os.listdir()
	for file in fileList:
		if not fileNamePattern.match(file) is None:
			f1 = NcFile(file, rootPath)
			f1.processAFileData(5)

	elapsed = (time.clock()-start)
	print("run time: "+str(elapsed)+" s")