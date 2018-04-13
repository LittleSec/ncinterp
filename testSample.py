import ncinterp as ni
import okuboweiss as ow
rootPath = r'/Users/littlesec/Desktop/毕业论文实现/SODA v2p2p4 new'
file = ni.NcFile('1000m_zonal_velocity1960-2008.nc', rootPath)
file.getFileInfo()
ds = ni.DataSelector(file.dateStrList, file.depthDataList)
ds.selectByDepth('-400') # param can be '5-100' or '-100' or '100-' or '100'
ds.selectByTime('2000-') # param can be 'yyyy' or 'yyyymm' or 't-t'(t can be yyyy or yyyymm or ignore one) 
ni.ncToCSVgrid(file, ds)
path = rootPath + '/' + '1000m_zonal_velocity1960-2008_grid_(33x25)'
ni.interpAFolder(path, 1)
file = ni.NcFile('1000m_meridional_velocity1960-2008.nc', rootPath)
file.getFileInfo()
ni.ncToCSVgrid(file, ds)
path = rootPath + '/' + '1000m_meridional_velocity1960-2008_grid_(33x25)'
ni.interpAFolder(path, 1)
uFolder = '1000m_zonal_velocity1960-2008_grid_(33x25)'
vFolder = '1000m_meridional_velocity1960-2008_grid_(33x25)'
ow.processAFolderOW(rootPath,uFolder,vFolder)