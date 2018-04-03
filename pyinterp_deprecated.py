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
			csvwriteop.writeCSVtuple(self.xi, self.yi, self.interpValue, self.dataInfo)
		else:
			csvwriteop.writeCSVgrid(self.xi, self.yi, self.interpValue, self.dataInfo)

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