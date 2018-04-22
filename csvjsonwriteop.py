import os
import numpy as np
import pandas as pd
import re
import datetime
import json

def writeCSVgrid(xi, yi, value, dataInfo=None, absFileName=None):
	'''
	The situation of same time(and same depth) just has a csv file.
	Format of directory: nc file name + '_grid_' + resolution(how many degree has a data),
		e.g. 'relative humidity1960-2017_grid_0.25'
	Format of csv file name: timeStr(+ depth with units)
		e.g. '1960-01-16'
		e.g. '1960-01-16,200m' 
	The units of depth is 'm' by default
    param:
        xi: a 1*n vector, longitude
        yi: a 1*m vector, latitude
        value: a m*n matrix
        dataInfo: a dict like 
        {
            RootPath: (str),abs path
            DirsName: (str),source data file name,
            Time: (str),format is 'yyyy-mm-dd',
            (if have)Depth: float
        }
		absFileName(not suggest): abs path/fileName
	attention:
		dataInfo and absFileName can't both None.
		If choose dataInfo is None, please ensure the abs path is exist.
	'''
	if not dataInfo is None:
		os.chdir(dataInfo["RootPath"]) 
		dirsName = r"{0}_grid_{1}".format(dataInfo["DirsName"], xi[1]-xi[0])
		if not os.path.exists(dirsName):
			os.makedirs(dirsName)
		os.chdir(r'%s' % dirsName)
		if "Depth" in dataInfo:
			fileName = r'{0},{1:.2f}m.csv'.format(dataInfo['Time'], dataInfo['Depth'])
		else:
			fileName = r'{0}.csv'.format(dataInfo['Time'])
	else:
		if absFileName is None:
			fileName = './error.csv'
		else:
			fileName = absFileName
	pd.DataFrame(value, columns=xi, index=yi).to_csv(fileName, na_rep='NaN')

def writeCSVtuple(points, values, dataInfo):
	'''
	params:
		points.shape = (N, 2) # before call this func, remember ravel()
		values.shape = (N) # can have NaN, this func will filter it.
		One-to-one correspondence between points and values
	The output file name refer to writeCSVgrid() function.
	'''
	os.chdir(dataInfo["RootPath"])
	dirsName = r"{0}_tuple_{1}".format(dataInfo["DirsName"], 0.1)
	if not os.path.exists(dirsName):
		os.makedirs(dirsName)
	os.chdir(r'%s' % dirsName)

	if "Depth" in dataInfo:
		fileName = r'{0},{1:.2f}m.csv'.format(dataInfo['Time'], dataInfo['Depth'])
	else:
		fileName = r'{0}.csv'.format(dataInfo['Time'])

	header = ['lon', 'lat', 'value']
	point1 = []
	value1 = []
	for i in range(len(values)):
		if not np.isnan(values[i]): # 在这里对整个values判NaN不起作用，不知道为啥
			point1.append(points[i])
			value1.append(values[i])
	dt1= pd.DataFrame(point1)
	dt2= pd.DataFrame(value1)
	pd.concat([dt1, dt2], axis=1).to_csv(fileName, index=False, header=header, na_rep='NaN')

def gridToTupleCSV(gridCSVfileName, savePath):
	'''
	There is no code to check whether the input csv file is grid format, so, caller should ensure it.
	params:
		girdCSVfileName just has 2 situation: timeStr(, depth with units).
			In other word, there is no path in this param, just a file name, caller should enter the workplace before call this functon.
		savePath should consistant with 'RootPath/DirsPath'.
			The caller should ensure the savePath is existed.
		See more: param in writeCSVgrid() function.
	'''
	fileInfo = gridCSVfileName.split(',')
	dataInfo = {}
	dataInfo["RootPath"] = '/'.join(savePath.split('/')[:-1]) + '/'
	dataInfo["DirsName"] = savePath.split('/')[-1] # source data file name(without ext)
	dataInfo["Time"] = fileInfo[0]
	if len(fileInfo) == 2:
		dataInfo["Depth"] = eval(fileInfo[1][:-5]) # last char is unit 'm.csv'
	csv = np.genfromtxt(gridCSVfileName, delimiter=',')
	x, y = np.meshgrid(csv[0,1:], csv[1:,0])
	points = np.rec.fromarrays([x, y]).ravel()
	values = csv[1:, 1:].ravel()
	writeCSVtuple(points, values, dataInfo)

def writeJSON(xi, yi, value, dataInfo=None, absFileName=None):
	'''
	params:
		refer to function writeCSVgrid()
	'''
	if not dataInfo is None:
		os.chdir(dataInfo["RootPath"])
		dirsName = r"{0}_json_({1}x{2})".format(dataInfo["DirsName"], value.shape[-2], value.shape[-1])
		if not os.path.exists(dirsName):
			os.makedirs(dirsName)
		os.chdir(r'%s' % dirsName)
		if "Depth" in dataInfo:
			fileName = r'{0}, {1:.2f}m.json'.format(dataInfo['Time'], dataInfo['Depth'])
		else:
			fileName = r'{0}.json'.format(dataInfo['Time'])
	else:
		if absFileName is None:
			fileName = './error.json'
		else:
			fileName = absFileName

	x, y = np.meshgrid(xi, yi)
	coords = np.rec.fromarrays([x, y]).ravel()
	elevations = value.ravel()
	jlist = []
	for i in range(len(elevations)):
		if np.isnan(elevations[i]):
			continue
		jlist.append({"coord": list(coords[i]), "elevation": elevations[i]})
	with open(fileName, 'w', encoding='utf-8') as f:
		f.write(json.dumps(jlist, indent=4))

def gridCsvToJSON(gridCSVfileName, savePath):
	'''
	params:
		refer to functon gridCSVfileName()
	'''
	fileInfo = gridCSVfileName.split(',')
	dataInfo = {}
	dataInfo["RootPath"] = '/'.join(savePath.split('/')[:-1]) + '/'
	dataInfo["DirsName"] = savePath.split('/')[-1] # source data file name(without ext)
	dataInfo["Time"] = fileInfo[0]
	if len(fileInfo) == 2:
		dataInfo["Depth"] = eval(fileInfo[1][:-5]) # last char is unit 'm.csv'
	csv = np.genfromtxt(gridCSVfileName, delimiter=',')
	xi = csv[0,1:]
	yi = csv[1:,0]
	value = csv[1:, 1:]
	writeJSON(xi, yi, value, dataInfo)