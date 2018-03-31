import os
import numpy as np
import pandas as pd
from scipy.io import netcdf
from scipy import interpolate
import re
import datetime
import time

'''
备忘录：
2018-02-02
dataProcessor深度空列表操作最好有误提示！
2018-02-08
考虑一下从有深度切换到无深度是否需要清空与深度相关的code，因为部分func会通过dataInfo的键进行判断
2018-02-09
处理文件函数还是放回文件类比较合适
2018-02-11
调整写文件参数，加入指定文件名模块，方便调试
'''

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
		self.observedValue = self.getObservedValue() # will get missing_value, too
		self.dimension = len(self.f.dimensions) 
		# f.dimensions不要用于获取某个维度的大小，
		# nc文件在创建时很有可能在这里记录错误，例如sst1960-2017.nc这个文件的'T'维度大小是None
		# 要想获得数据的数量，还是以实际数据的列表长度为准
		self.dateStrList = self.getTimeValue()
		if(self.dimension == 4):
			self.depthDataList = self.getDepthValue()
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
		depthDataList = []
		for key in self.f.variables.keys():
			if key.lower() in ['depth', 'z']:
				depthDataList = self.f.variables[key].data
				self.depthUnits = str(self.f.variables[key].units, encoding = 'utf-8')
				break
		return depthDataList

	def getObservedValue(self):
		'''获取所有实际测量的值，默认属性名不用以下名字：['X', 'Y', 'Z', 'T', 'lat', 'lon', 'depth']'''
		observedValue = []
		for key in self.f.variables.keys():
			if(key in ['T', 'X', 'Y', 'Z', 'lat', 'lon', 'time', 'depth']):
				continue # 利用短路运算提高速度，保证for循环中有且仅有一次是遍历整个list
			else:
				var = self.f.variables[key]
				observedValue = var.data.astype(float)
				self.missingValue = np.float(var.missing_value)
				if('add_offset' in dir(var) and 'scale_factor' in dir(var)): # 源数据经过处理，例如sst2960-2017.nc
					# 不可以observedValue *= 1，因为这只是个指向文件数据而已，而数据是只读的。
					observedValue = var.data.astype(float) * var.scale_factor + var.add_offset
					self.missingValue *= var.scale_factor 
					self.missingValue += var.add_offset
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
		Have hard code.
		param:
			depthStr can be: "num(+)", "num1-num2"(num1 < num2) and "num-"
		'''
		if self.depthList is None:
			print("No depth in this file!")
			return
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

		# return list(range(index1, index2 + 1)) # for test
		self.depthSelectList = range(index1, index2 + 1)

	def selectByTimeAndDepth(self, time, depth):
		pass

class DataProcessor:
	def __init__(self, file):
		self.x = file.x # 源经度
		self.y = file.y # 源纬度
		self.observedValue = file.observedValue # 源数据值
		self.dimension = file.dimension
		dataInfo = {}
		dataInfo["RootPath"] = file.rootPath
		dataInfo["DirsName"] = file.fileName[:-3]
		self.dataInfo = dataInfo
		self.dateStringList = file.dateStrList
		if self.dimension == 4:
			self.depthList = file.depthDataList
		else:
			self.depthList = []
		self.NaNValue = file.missingValue
		self.xi = self.x # 提高密度后的经度序列
		self.yi = self.y
		self.interpFunc = None

	def setNaNValue(self, NaNReplaceValue = None):
		'''循环遍历设置缺失值，以方便全数据参与插值运算'''
		if NaNReplaceValue is None:
			NaNReplaceValue = self.NaNValue
		self.observedValue[np.isnan(self.observedValue)] = NaNReplaceValue
		self.observedValue[self.observedValue == self.NaNValue] = NaNReplaceValue

	def setResolution(self, minutes = 1):
		'''设置分辨率，minutes指多少分就有一个数据，返回新的经纬度序列'''
		numOfSectionsInOneDegree = 60 // minutes
		min_x = np.min(self.x)
		max_x = np.max(self.x)
		min_y = np.min(self.y)
		max_y = np.max(self.y)
		n_x = complex(0, (max_x - min_x) * numOfSectionsInOneDegree + 1)
		n_y = complex(0, (max_y - min_y) * numOfSectionsInOneDegree + 1)
		xi = np.ogrid[min_x:max_x:n_x]
		yi = np.ogrid[min_y:max_y:n_y]
		return xi, yi

	def __setInterpFunc(self, z):
		'''计算插值函数（二元三次样条插值）'''
		self.interpFunc = interpolate.interp2d(self.x, self.y, z, kind='cubic')

	def __interpAGroupData(self):
		return self.interpFunc(self.xi, self.yi)

	def __processAGroupData(self, timeIndex=0, depthIndex=0, minutes=1, nanValue=None, csvForm='grid'):
		'''这些nc文件的组织规律如下：
		z[time]([depth]if have)[x][y]
		'''
		if nanValue is not None:
			self.setNaNValue(nanValue)
		self.xi, self.yi = self.setResolution(minutes = minutes)
		if self.dimension == 4:
			z = self.observedValue[timeIndex][depthIndex]
		elif self.dimension == 3:
			z = self.observedValue[timeIndex]
		self.__setInterpFunc(z)
		self.interpValue = self.__interpAGroupData()

		if csvForm.lower() == 'tuple':
			writeInCSVWithTuple(self.xi, self.yi, self.interpValue, self.dataInfo)
		else:
			writeInCSVWithGrid(self.xi, self.yi, self.interpValue, self.dataInfo)

	def processAFileData(self, minutes=1, nanValue=None, csvForm='grid'):
		'''
		ds = DataSelector([''], [''])
		ds.timeSelectList = range(len(self.dateStringList))
		ds.depthSelectList = range(len(self.depthList))
		'''
		self.processARangeData(ds=None, minutes=minutes, nanValue=nanValue, csvForm=csvForm)

	def processARangeData(self, ds, minutes=1, nanValue=None, csvForm='grid'):
		if ds is None:
			ds = DataSelector(self.dateStringList, self.depthList)
		if self.dimension == 4:
			for i in ds.timeSelectList:
				self.dataInfo["Time"] = self.dateStringList[i]
				for j in ds.depthSelectList:
					self.dataInfo["Depth"] = self.depthList[j]
					self.__processAGroupData(timeIndex=i, depthIndex=j, minutes=minutes, nanValue=nanValue, csvForm=csvForm)
		elif self.dimension == 3:
			for i in ds.timeSelectList:
				self.dataInfo["Time"] = self.dateStringList[i]
				self.__processAGroupData(timeIndex=i, depthIndex=0, minutes=minutes, nanValue=nanValue, csvForm=csvForm)

def writeInCSVWithGrid(xi, yi, value, dataInfo):
	'''
	The situation of same time(and same depth) just has a csv file.
	Format of directory: nc file name + '_grid_' + resolution(how many lats x how many lons),
		e.g. 'relative humidity1960-2017_grid_(13x13)'
	Format of csv file name: timeStr(+ depth with units)
		e.g. '1960-01-16'
		e.g. '1960-01-16,200m' 
	The units of depth is 'm' by default
	'''
	# dataInfo: RootPath, DirsName, Time(str), Depth(num)
	os.chdir(dataInfo["RootPath"]) 
	dirsName = r"{0}_grid_({1}x{2})".format(dataInfo["DirsName"], value.shape[-2], value.shape[-1])
	if not os.path.exists(dirsName):
		os.makedirs(dirsName)
	os.chdir(r'%s' % dirsName)
	if "Depth" in dataInfo:
		fileName = r'{0}, {1:.2f}m.csv'.format(dataInfo['Time'], dataInfo['Depth'])
		pd.DataFrame(value, columns=xi, index=yi).to_csv(fileName, na_rep='NaN')
	else:
		fileName = r'{0}.csv'.format(dataInfo['Time'])
		pd.DataFrame(value, columns=xi, index=yi).to_csv(fileName, na_rep='NaN')
	
def writeInCSVWithTuple(xi, yi, value, dataInfo):
	'''
	The situation of same nc file and same resolution has the same one csv file.
	Format of directory: nc file name + '_tuple'
		e.g. 'relative humidity1960-2017_tuple'
	Format of csv file name: time(+ depth range) + resolution(how many lats x how many lons)
		e.g. '1960-01-16,5m-200m,(13x13).csv'
	'''
	os.chdir(dataInfo["RootPath"]) 
	dirsName = r"%s_tuple" % dataInfo["DirsName"]
	if not os.path.exists(dirsName):
		os.makedirs(dirsName)
	os.chdir(r'%s' % dirsName)
	
	if not "Depth" in dataInfo:
		fileName = r'{0},({1}x{2}).csv'.format(
				dataInfo["Time"], value.shape[-2], value.shape[-1])
		header = ['log', 'lat', '']
		x, y = np.meshgrid(xi, yi)
		point = np.rec.fromarrays([x, y])
		dt1 = pd.DataFrame(point.ravel())
		dt2 = pd.DataFrame(value.ravel())
		pd.concat([dt1, dt2], axis=1).to_csv(fileName, index=False, header=header, na_rep='NaN')
	else: # have depth
		fileNamePattern = '{0}.*\({1}x{2}\)\.csv'.format(
				dataInfo["Time"], value.shape[-2], value.shape[-1])
		fileNameRegex = re.compile(fileNamePattern)
		for fname in os.listdir(os.getcwd()):
			if fileNameRegex.match(fname):
				# read file
				# 读：csv = np.genfromtxt('some.csv',delimiter=",")[1:,:]
				csv = pd.read_csv(fname)
				csvdepth = [eval(h[:-1]) for h in csv.columns[2:]] # at least have one item, and ascending
				# insert or update
				for i in range(len(csvdepth)):
					if round(dataInfo["Depth"], 2) > csvdepth[i]:
						continue
					elif round(dataInfo["Depth"], 2) < csvdepth[i]:
						csv.insert(i+2, '{0:.2f}m'.format(dataInfo["Depth"]), value.ravel())
						break
					else:
						csv.update({'{0:.2f}m'.format(dataInfo["Depth"]): value.ravel()})
						break
				else: # maybe len is 1 or depth is max
				# for...else have some attentions https://www.cnblogs.com/dspace/p/6622799.html
					if round(dataInfo["Depth"], 2) > csvdepth[i]:
						csv.insert(i+1+2, '{0:.2f}m'.format(dataInfo["Depth"]), value.ravel())
					else:
						csv.insert(i+2, '{0:.2f}m'.format(dataInfo["Depth"]), value.ravel())
				# update filename
				fileName = r'{0},{1}m-{2}m,({3}x{4}).csv'.format(
					dataInfo["Time"], csv.columns[2], csv.columns[-1], value.shape[-2], value.shape[-1])
				# write back
				csv.to_csv(fileName, index=False, na_rep='NaN')
				os.remove(fname)
				break
		else: # new file
			header = ['log', 'lat', '{0:.2f}m'.format(dataInfo["Depth"])]
			fileName = r'{0},{1:.2f}m,({2}x{3}).csv'.format(
				dataInfo["Time"], dataInfo["Depth"], value.shape[-2], value.shape[-1])
			x, y = np.meshgrid(xi, yi)
			point = np.rec.fromarrays([x, y])
			dt1 = pd.DataFrame(point.ravel())
			dt2 = pd.DataFrame(value.ravel())
			pd.concat([dt1, dt2], axis=1).to_csv(fileName, index=False, header=header, na_rep='NaN')
	
if __name__ == '__main__':
	'''
	f1 = NcFile('relative humidity1960-2017.nc')
	f1.processAFileData()
	'''
	start = time.clock()
	rootPath = r'/Users/littlesec/Desktop/毕业设计/caoweidongdata/'
	os.chdir(rootPath)
	fileNamePattern = re.compile(r'.*.nc')
	fileList = os.listdir()
	for file in fileList:
		if fileNamePattern.match(file):
			pass

	elapsed = (time.clock()-start)
	print("run time: "+str(elapsed)+" s")