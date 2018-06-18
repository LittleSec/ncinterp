## 一、说明
1. 本仓库为2018 OUC本科毕业设计[多元海洋时空数据的可视化](https://github.com/LittleSec/OceanVisualizationD3)对应的数据处理代码。
2. 源数据文件为NetCDF格式，个数比较多，后期上传到百度盘后再分享。
3. 生成的csv文件较多，后期也以百度盘的形式分享（只分享实际用到的）。
3. 该仓库主要作用是nc-->csv（去NaN），OkuboWeiss参数的计算以及涡旋识别。

## 二、使用顺序：nctocsv --> gridtotuple --> mergetuple

### 环境：
1. Python 3.6.x (3.4.x以上)
2. 用到的Python第三方库在```./requirements.txt```，进入仓库目录后执行命令：```pip3 install -r requirements.txt```，或一个一个安装。目前来说直接安装最新版本也行，可以无需指定版本。

### ```nctocsv.py```
1. 使用:
    + 修改ROOTPATH，把需要处理的nc文件放到该目录下即可，生成的文件会在该目录下。
    + 注意会处理全部nc文件
    + ~~有多进程的代码，可以选择尝试，效果不明显，时间打印也有问题。~~
2. 代码用于将nc文件导出grid形式的csv
3. nc文件的若干说明：
    + 时间单位是hours since yyyy-mm-dd 00:00
    + 要么没深度要么只有一个深度
    + 时空维度顺序为：[time][depth]
    + 除了经纬度时空外允许有多个属性
    + 只选择导出12点的数据
4. 生成csv文件组织形式```./attr_grid/(depth/)yyyy-mm-dd.csv```

### ```gridtotuple.py```
1. 使用:
    + 修改ROOTPATH，grid文件所在目录
    + ATTRLIST_ALL，需要转化csv形式的属性，注意，确保ROOTPATH有这些属性的grid文件夹，名为：attr_grid
    + DEPTHLIST，需要转化的属性的深度，注意，属性要么没有深度，要么有同样的深度，默认surf_el属性没有深度，其他都有。会对surf_el特殊对待
2. 代码用于将grid形式的csv转化成tuple形式

### ```mergetuple.py```
1. 使用：
    + 修改ROOTPATH，tuple文件所在目录
    + ATTRLIST_ALL，需要合并的属性。
    + ATTRLIST，有深度的属性
    + DEPTHLIST，深度。
    + 注意确保csv名字和数量都要一致。
2. 代码将同一深度同一时刻的多个属性合并到一个csv(tuple)，没有深度属性的surf_el默认全深度。
2. 文件组织形式```./0.0m/yyyy-mm-dd.csv```
3. 注意日期序列的获取，当前代码是通过文件夹里的文件获取。另外可以通过已有函数获取。
4. 仅仅合并uv的话要注意除了修改两个ATTRLIST外还需要注释mergeAttr()里的合并surf_el的filelist.append()语句

### ```quiverCul.py```
1. 使用SVG绘制箭头的原理是在<line>加入一个<marker>id，而<line>的属性是起终点的坐标，因此根据速度绘制箭头需要知道终点的坐标，改代码的作用就是如此。
2. 为了效果，需要稀疏化后的速度场(u, v)，在此为0.48°

### ```okuboweiss.py```
1. 根据速度场计算Okubo Weiss参数

## 联系
1. 直接在issue提问。
2. email: 517862788@qq.com
3. 若需要开发，请切换到nctocsv-nointerp-branch分支的nctocsv-nointerp目录。

> 注：本repo有插值的代码，但最后的论文所使用的数据源不需要插值了，因此这部分在这里没有显示。
> 该分支来源于nctocsv-nointerp-branch的nctocsv-nointerp目录。nctocsv-nointerp-branch的其他```*.py```来自master分支。