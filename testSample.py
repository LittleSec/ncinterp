import ncinterp as ni
rootPath = r'./'
file = ni.NcFile(r'1000m_meridional_velocity1960-2008.nc',rootPath)
file.getFileInfo()
ds = ni.DataSelector(file.dateStrList, file.depthDataList)
ds.selectByDepth('5-50') # param can be '5-100' or '-100' or '100-' or '100'
ds.selectByTime('1960') # param can be 'yyyy' or 'yyyymm' or 't-t'(t can be yyyy or yyyymm or ignore one) 
dp = ni.DataProcessor(file)
# dp.processAFileData()
dp.processARangeData(ds, minutes=1, nanValue=2, csvForm='grid') # csvForm can also be 'tuple'