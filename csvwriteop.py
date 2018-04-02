import os
import numpy as np
import pandas as pd
import re
import datetime

'''
Todo:
2018-04-02:
function: csvToJSON()
'''

def writeCSVgrid(xi, yi, value, dataInfo):
	'''
	The situation of same time(and same depth) just has a csv file.
	Format of directory: nc file name + '_grid_' + resolution(how many lats x how many lons),
		e.g. 'relative humidity1960-2017_grid_(13x13)'
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
	'''
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

def writeCSVtuple(xi, yi, value, dataInfo):
    os.chdir(dataInfo["RootPath"]) 
	dirsName = r"%s_tuple" % dataInfo["DirsName"]
	if not os.path.exists(dirsName):
		os.makedirs(dirsName)
	os.chdir(r'%s' % dirsName)

    if not "Depth" in dataInfo:
        writeCSVtupleNoDepth(xi, yi, value, dataInfo)
    else:
        writeCSVtupleWithDepth(xi, yi, value, dataInfo)

def writeCSVtupleNoDepth(xi, yi, value, dataInfo):
	'''
	The situation of same nc file, same resolution and same year has the same one csv file.
	Format of directory: nc file name + '_tuple'
		e.g. 'relative humidity1960-2017_tuple'
	Format of csv file name: year + resolution(how many lats x how many lons)
		e.g. '1960,(13x13).csv'
    Attention:
        Always be called by writeCSVtuple().
        If call it alone, please make sure the workpath is right.
	'''
    fileName = r'{0},({1}x{2}).csv'.format(
            dataInfo["Time"][:4], value.shape[-2], value.shape[-1])
    for fname in os.listdir(os.getcwd()):
        if fname == fileName:
            # read file
            csv = pd.read_csv(fname)
            csvdate = [datetime.datetime.strptime(d, "%Y/%m/%d") for d in csv.columns[2:]] # at least have one item, and ascending
            # insert or update
            for i in range(len(csvdate)): # ascending
                if datetime.datetime.strptime(dataInfo["Time"], "%Y-%m-%d") > csvdate[i]:
                    continue
                elif datetime.datetime.strptime(dataInfo["Time"], "%Y-%m-%d") < csvdate[i]:
                    csv.insert(i+2, dataInfo["Time"].replace('-', '/'), value.ravel())
                    break
                else: # ==
                    csv.update({dataInfo["Time"].replace('-','/'): value.ravel()})
                    break
            else: # maybe len is 1 or depth is max
                if datetime.datetime.strptime(dataInfo["Time"], "%Y-%m-%d") > csvdate[i]:
                    csv.insert(i+1+2, dataInfo["Time"], value.ravel())
                else:
                    csv.insert(i+2, dataInfo["Time"], value.ravel())
            # write back
            csv.to_csv(fileName, index=False, na_rep='NaN')
            break
    else: # new file
        header = ['log', 'lat', dataInfo["Depth"].replace('-', '/')]
        x, y = np.meshgrid(xi, yi)
        point = np.rec.fromarrays([x, y])
        dt1 = pd.DataFrame(point.ravel())
        dt2 = pd.DataFrame(value.ravel())
        pd.concat([dt1, dt2], axis=1).to_csv(fileName, index=False, header=header, na_rep='NaN')

def writeCSVtupleWithDepth(xi, yi, value, dataInfo):
	'''
	The situation of same nc file and same resolution has the same one csv file.
	Format of directory: nc file name + '_tuple'
		e.g. 'relative humidity1960-2017_tuple'
	Format of csv file name: time(+ depth range) + resolution(how many lats x how many lons)
		e.g. '1960-01-16,5m-200m,(13x13).csv'
    Attention:
        Always be called by writeCSVtuple().
        If call it alone, please make sure the workpath is right.
	'''
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
            for i in range(len(csvdepth)): # ascending
                if round(dataInfo["Depth"], 2) > csvdepth[i]:
                    continue
                elif round(dataInfo["Depth"], 2) < csvdepth[i]:
                    csv.insert(i+2, '{0:.2f}m'.format(dataInfo["Depth"]), value.ravel())
                    break
                else: # ==
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
            if fileName != fname:
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
	
def gridToTupleCSV(gridCSVfileName, savePath):
    '''
    There is no code to check whether the input csv file is grid format, so, caller should ensure it.
    params:
        girdCSVfileName just has 2 situation: timeStr(, depth with units).
        savePath should consistant with RootPath/DirsPath.
        See more: param in writeCSVgrid() function.
    The output file name refer to writeCSVtupleNoDepth/writeCSVtupleWithDepth() function.
    '''
    fileInfo = gridCSVfileName.split(',')
    dataInfo = {}
    dataInfo["RootPath"] = '/'.join(savePath.split('/')[:-1]) + '/'
    dataInfo["DirsName"] = savePath.split('/')[-1] # source data file name(without ext)
    dataInfo["Time"] = fileInfo[0]
    if len(fileInfo) == 2:
        dataInfo["Depth"] = eval(fileInfo[1][:-1]) # last char is unit 'm'
    csv = np.genfromtxt(gridCSVfileName, delimiter=',')
    xi = csv[0,1:]
    yi = csv[1:,0]
    value = csv[1:, 1:]
    writeCSVtuple(xi, yi, value, dataInfo)

def csvToJSON(csvFile, savePath):
    pass