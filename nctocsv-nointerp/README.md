# nctocsv-nointerp模块

>由于时间问题没有进行模块化重用，故写一个README.md说明临时用法

## 使用顺序：nctocsv --> gridtotuple --> mergetuple
### ```nctocsv.py```
4. 使用:
    + 修改ROOTPATH，把需要处理的nc文件放到该目录下即可，生成的文件会在该目录下。
    + 注意会处理全部nc文件
    + 有多进程的代码，可以选择尝试，效果不明显，时间打印也有问题。
1. 代码用于将nc文件导出grid形式的csv
2. nc文件的若干说明：
    + 时间单位是hours since yyyy-mm-dd 00:00
    + 要么没深度要么只有一个深度
    + 时空维度顺序为：[time][depth]
    + 除了经纬度时空外允许有多个属性
    + 只选择导出12点的数据（12点的判断是基于since的时间必须是00:00）
2. 生成csv文件组织形式```./attr_tuple/(depth/)yyyy-mm-dd.csv```

### ```gridtotuple```
1. 使用:
    + 修改ROOTPATH，grid文件所在目录
    + ATTRLIST_ALL，需要转化csv形式的属性，注意，确保ROOTPATH有这些属性的grid文件夹，名为：attr_grid
    + DEPTHLIST，需要转化的属性的深度，注意，属性要么没有深度，要么有同样的深度，默认surf_el属性没有深度，其他都有。会对surf_el特殊对待
2. 代码用于将grid形式的csv转化成tuple形式

### ```mergetuple```
1. 使用：
    + 修改ROOTPATH，tuple文件所在目录
    + ATTRLIST_ALL，需要合并的属性。
    + ATTRLIST，有深度的属性
    + DEPTHLIST，深度。
    + 注意确保csv名字和数量都要一致。
2. 代码将同一深度同一时刻的多个属性合并到一个csv(tuple)，没有深度属性的surf_el默认全深度。
2. 文件组织形式```./0.0m/yyyy-mm-dd.csv```
3. 注意日期序列的获取，当前代码是通过文件夹里的文件获取。另外可以通过已有函数获取。