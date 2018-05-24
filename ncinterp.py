import os
import numpy as np
import pandas as pd
from scipy.io import netcdf
from scipy import interpolate
import re
import datetime
import time
import csvjsonwriteop

'''
备忘录：
2018-02-02
dataProcessor深度空列表操作最好有误提示！
2018-02-08
考虑一下从有深度切换到无深度是否需要清空与深度相关的code，因为部分func会通过dataInfo的键进行判断
'''

def indexOfList(dataList, value):
	'''
	The main idea is bin_search.
	If find successfully, than return the index.
	If find unsuccessfully，than return the index whose value is closer to value.
		This is Different from list.index() function(will throw a ValueError)
	By the way, dataList is an ascending sequence by default and haven't same value.
	'''
	low = 0
	high = len(dataList) - 1
	if value <= dataList[0]:
		return 0
	elif value >= dataList[-1]:
		return len(dataList)-1
	while low <= high:
		mid = (low + high) // 2
		if dataList[mid] == value:
			return mid
		elif dataList[mid] > value:
			high = mid - 1
		else:
			low = mid + 1
	if dataList[low] - value >= value - dataList[high]: # now the dataList[low] > dataList[high] 
		return high
	else:
		return low

class NcFile:
	def __init__(self, fileName, rootPath):
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
		'''
		self.x, self.y = self.getLongiAndLati()
		self.resolution = self.x[1] - self.x[0]
		self.observedValue = self.getObservedValue() # will get missing_value, too
		self.dimension = len(self.f.dimensions) 
		# f.dimensions不要用于获取某个维度的大小，
		# nc文件在创建时很有可能在这里记录错误，例如sst1960-2017.nc这个文件的'T'维度大小是None
		# 要想获得数据的数量，还是以实际数据的列表长度为准
		self.dateStrList = self.getTimeValue()
		if(self.dimension == 4):
			self.depthDataList = self.getDepthValue()

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
		So, this function will change number to a date string('yyyy-mm-dd') by combining with the units.
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
				decimalPart = round(dateNumberList[i] - intPart, 1) # try 1.9-1 = 0.899...
				day = startDay + int(decimalPart * 30)
				month = startMonth
				year = startYear
				if(day > 30 or day < 0): # 待考虑，统一每个月只有30天
					month = month + 1 if day > 30 else month - 1
					day %= 30
				month += intPart
				if(month > 12 or month < 0):
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
		'''
		return a depth list, value in list is a float(without units)
		'''
		depthDataList = []
		for key in self.f.variables.keys():
			if key.lower() in ['depth', 'z']:
				depthDataList = self.f.variables[key].data
				self.depthUnits = str(self.f.variables[key].units, encoding = 'utf-8')
				break
		return depthDataList

	def getObservedValue(self):
		'''
		获取所有实际测量的值，默认属性名不用以下名字：['X', 'Y', 'Z', 'T', 'lat', 'lon', 'depth']
		return ndarray of observedvalue, ndim == 3 or 4(depend on whether have depth)
		关于missing_value(_FillValue)
			nc文件中虽然显示NaN，但是missing_value(_FillValue)却不是NaNf，这是文件所定义的机制。
			如果使用追加(a)模式修改这个属性的字段值为NaNf(np.nan)，那么显示的就不再是NaN了，而且定义的数据类型的最小值（一绘图就知道区别了）。
			无论如何，读出来都不会是NaN。
			综上nc文件实际上是没有定义NaN类型的（虽然会显示说缺失值是NaNf），官方社区有相关的回答。
			因此需要在这里修改这些值为NaN方便后期使用。
		'''
		observedValue = []
		for key in self.f.variables.keys():
			if(key in ['T', 'X', 'Y', 'Z', 'lat', 'lon', 'time', 'depth']):
				continue # 利用短路运算提高速度，保证for循环中有且仅有一次是遍历整个list
			else:
				var = self.f.variables[key]
				observedValue = var.data.astype(float)
				missingValue = np.float(var.missing_value)
				if not np.isnan(missingValue):
					observedValue[observedValue == missingValue] = np.nan
				if('add_offset' in dir(var) and 'scale_factor' in dir(var)): # 源数据经过处理，例如sst2960-2017.nc
					# 不可以observedValue *= 1，因为这只是个指向文件数据而已，而数据是只读的。
					observedValue = var.data.astype(float) * var.scale_factor + var.add_offset
				break
		return observedValue

class DataSelector:
	def __init__(self, dateStringList, depthList=None):
		self.dateStringList = dateStringList # ['1960-02-16', '1960-03-16', '1960-04-16', '1961-05-16', '1970-06-16', '2001-07-16', '2008-06-16']
		self.startDate = dateStringList[0]# '1960-02-16' #
		self.endDate = dateStringList[-1]# '2008-06-16'
		self.depthList = depthList # [1, 2.3, 3.45, 4.567, 5.65, 6.3, 7]
		self.timeSelectList = range(len(dateStringList))
		if depthList is None:
			self.depthSelectList = range(0)
		else:
			self.depthSelectList = range(len(depthList))

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

		# return list(range(index1, index2 + 1)) # for test
		self.timeSelectList = range(index1, index2 + 1)

	def selectByDepth(self, depthStr):
		'''
		Have hard code.
		param:
			depthStr can be: "num(+)", "num1-num2"(num1 < num2) and "num-"
		'''
		if self.depthList is None:
			print("No depth in this file!")
			return
		strSplitList = depthStr.split('-')
		numPattern = r'-?(([1-9]\d*\.\d*|0?\.\d*[1-9]\d*|0?\.0+|0)|([1-9]\d*))'
		numRegex = re.compile(numPattern)

		if len(strSplitList) == 1:
			if numRegex.match(depthStr):
				index1 = index2 = indexOfList(self.depthList, eval(depthStr))
			else:
				index1 = index2 = 0
		elif len(strSplitList) == 2:
			if numRegex.match(strSplitList[0]):
				index1 = indexOfList(self.depthList, eval(strSplitList[0]))
			else:
				index1 = 0

			if numRegex.match(strSplitList[1]):
				index2 = indexOfList(self.depthList, eval(strSplitList[1]))
			else:
				index2 = len(self.depthList) - 1

		if index1 > index2:
			index1, index2 = index2, index1

		# return list(range(index1, index2 + 1)) # for test
		self.depthSelectList = range(index1, index2 + 1)

	def selectByTimeAndDepth(self, time, depth):
		pass

def ncToCSVgrid(ncfile, dataselector=None):
	x = ncfile.x # 源经度
	y = ncfile.y # 源纬度
	observedValue = ncfile.observedValue # 源数据值
	# dimension = ncfile.dimension
	dataInfo = {}
	dataInfo["RootPath"] = ncfile.rootPath
	dataInfo["DirsName"] = ncfile.fileName[:-3]
	dataInfo["Resolution"] = str(ncfile.resolution).replace('.', 'p')
	dateStringList = ncfile.dateStrList
	if ncfile.dimension == 4:
		depthList = ncfile.depthDataList
	else:
		depthList = []
	if dataselector is None:
		dataselector = DataSelector(dateStringList, depthList)
	if ncfile.dimension == 4:
		for i in dataselector.timeSelectList:
			dataInfo["Time"] = dateStringList[i]
			for j in dataselector.depthSelectList:
				dataInfo["Depth"] = depthList[j]
				csvjsonwriteop.writeCSVgrid(x, y, observedValue[i][j], dataInfo)
	elif ncfile.dimension == 3:
		for i in dataselector.timeSelectList:
			dataInfo["Time"] = dateStringList[i]
			csvjsonwriteop.writeCSVgrid(x, y, observedValue[i], dataInfo)

if __name__ == '__main__':
	start = time.clock()
	rootPath = '/Users/littlesec/Desktop/毕业论文实现/new nc data'
	'''
	file = NcFile('ssh.nc', rootPath)
	file.getFileInfo()
	# print(file.dateStrList)
	ds = DataSelector(file.dateStrList)
	ds.selectByTime('2000-') # param can be 'yyyy' or 'yyyymm' or 't-t'(t can be yyyy or yyyymm or ignore one) 
	ncToCSVgrid(file, ds)
	'''
	elapsed = (time.clock()-start)
	print("run time: "+str(elapsed)+" s")
