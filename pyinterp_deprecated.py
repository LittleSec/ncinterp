import numpy as np
from scipy import interpolate
import pandas as pd
import os
import time
import ncinterp as ni
import csvjsonwriteop as fop

'''
todo:
写函数还是太怪了，另外有硬编码
'''

class DataProcessor:
	def __init__(self, file):
		self.x = file.x  # 源经度
		self.y = file.y  # 源纬度
		x, y = np.meshgrid(self.x, self.y)
		self.sourcePoints = np.rec.fromarrays([x, y]).ravel()
		self.observedValue = file.observedValue  # 源数据值
		self.dimension = file.dimension
		dataInfo = {}
		dataInfo["RootPath"] = file.rootPath
		dataInfo["DirsName"] = file.fileName[:-3]
		dataInfo["Resolution"] = str(file.resolution).replace('.', 'p')
		self.dataInfo = dataInfo
		self.dateStringList = file.dateStrList
		if self.dimension == 4:
			self.depthList = file.depthDataList
		else:
			self.depthList = []

	def filterNaN(self, sourceValues, sourcePoints=None):
		self.noNaNPoints = []
		self.noNaNValues = []
		if sourcePoints is None:
			sourcePoints = self.sourcePoints
		for i in range(len(sourceValues)):
			if not np.isnan(sourceValues[i]):  # 在这里对整个sourceValues判NaN不起作用，不知道为啥
				self.noNaNPoints.append(list(sourcePoints[i]))
				self.noNaNValues.append(sourceValues[i])

	def getInterpPointsAndDF(self, degree=0.1):
		'''
		params:
		    degree: how many degresss have a data.
				must one of [0.05, 0.1, 0.2, 0.25] (source is 0.5)
		func:
			通过读取文件去获得需要插值的点（排除陆地点）
			构造对应的二维表（DataFrame），用NaN填充。（该工作是为了以grid形式存储插值数据，ow参数的计算依赖于grid形式）
		'''
		if degree not in [0.05, 0.1, 0.2, 0.25]:
			degree = 0.1

		currentdir = os.path.dirname(__file__)
		fileName = '{0}/Widgets/pick_mask/mask_tuple_{1}.csv'.format(currentdir, str(degree).replace('.', 'p'))
		csv = np.genfromtxt(fileName, delimiter=',')
		self.interpPoints = csv[csv[:, 2] == 1][:, :2] # 先筛选mask为1的，后切片形成坐标点

		fileName = '{0}/Widgets/pick_mask/mask_grid_{1}.csv'.format(currentdir, str(degree).replace('.', 'p'))
		self.interpDF = pd.read_csv(fileName, index_col=0).replace(to_replace=[0, 1], value=np.nan) # 全部置为NaN

	def writeCSV(self, dataInfo):
		# grid: maybe can reuse code
		os.chdir(dataInfo["RootPath"])
		dirsName = "{0}_grid_{1}".format(dataInfo["DirsName"], dataInfo['Resolution'])
		if not os.path.exists(dirsName):
			os.makedirs(dirsName)
		os.chdir(dirsName)
		if "Depth" in dataInfo:
			fileName = r'{0},{1:.2f}m.csv'.format(dataInfo['Time'], dataInfo['Depth'])
		else:
			fileName = r'{0}.csv'.format(dataInfo['Time'])
		for i in range(len(self.interpPoints)):
			point = self.interpPoints[i]
			self.interpDF[str(point[0])][point[1]]= self.interpValues[i] # c['118.675'][37.225]
		self.interpDF.to_csv(fileName)

		# tuple:
		fop.writeCSVtuple(self.interpPoints, self.interpValues, dataInfo=dataInfo)
		# head= ['lon', 'lat', 'value']
		# dt1= pd.DataFrame(self.interpPoints)
    	# dt2= pd.DataFrame(self.interpValues)
		# pd.concat([dt1, dt2], axis=1).to_csv(fileName, index=False, header=header)

	def __processAGroupData(self, timeIndex=0, depthIndex=0, degree=0.1):
		'''这些nc文件的组织规律如下：
		z[time]([depth]if have)[x][y]
		'''
		if self.dimension == 4:
			z= self.observedValue[timeIndex][depthIndex]
		elif self.dimension == 3:
			z= self.observedValue[timeIndex]

		self.filterNaN(sourceValues=z.ravel())
		self.getInterpPointsAndDF(degree=degree)
		# interpData
		self.interpValues= interpolate.griddata(self.noNaNPoints, self.noNaNValues, self.interpPoints, method='cubic')

	def processAFileData(self, degree=0.1):
		'''
		ds = DataSelector([''], [''])
		ds.timeSelectList = range(len(self.dateStringList))
		ds.depthSelectList = range(len(self.depthList))
		'''
		self.processARangeData(ds=None, degree=degree)

	def processARangeData(self, ds, degree=0.1):
		if ds is None:
			ds = ni.DataSelector(self.dateStringList, self.depthList)
		self.dataInfo['Resolution'] = str(degree).replace('.', 'p')
		if self.dimension == 4:
			for i in ds.timeSelectList:
				self.dataInfo["Time"]= self.dateStringList[i]
				for j in ds.depthSelectList:
					self.dataInfo["Depth"]= self.depthList[j]
					self.__processAGroupData(timeIndex=i, depthIndex=j, degree=degree)
					self.writeCSV(self.dataInfo)
		elif self.dimension == 3:
			for i in ds.timeSelectList:
				self.dataInfo["Time"]= self.dateStringList[i]
				self.__processAGroupData(timeIndex=i, depthIndex=0, degree=degree)
				self.writeCSV(self.dataInfo)

if __name__ == '__main__':
	'''
	about running time:
	ssh数据没有深度，时间从2000-2008年9年乘12个月，分辨率0.5-->0.1，耗时：342.44729099999995 s
	salt数据集，有深度不筛选，时间也是9年乘12个月，分辨率0.5-->0.1，耗时：
	'''
	start = time.clock()
	rootPath = r'/Users/littlesec/Desktop/毕业论文实现/new nc data'
	file = ni.NcFile('salinity.nc', rootPath)
	file.getFileInfo()
	# print(file.dateStrList)
	ds = ni.DataSelector(file.dateStrList, file.depthDataList)
	ds.selectByTime('2000-') # param can be 'yyyy' or 'yyyymm' or 't-t'(t can be yyyy or yyyymm or ignore one)
	ni.ncToCSVgrid(file, ds)
	dp = DataProcessor(file)
	dp.processARangeData(ds)
	file.f.close()
	elapsed = (time.clock()-start)
	print("run time: "+str(elapsed)+" s")