# NC文件插值处理

## 一、NC文件特点
1. 经纬度范围：24.5N-36.5N，117.5E-129.5，一度一个数据。
2. 经纬度的属性名为X,Y或lat,lon，一般会有long_name属性，为对应首字母大写的单词。
3. 时间单位要么是日，要么是月，月的话值为小数。
4. 真正的观测值只能有一个。
5. 除了经纬度两个维度外，只能再有时间或深度维度，其中时间维度是必要的。

## 二、生成文件的规律
1. 先创建与nc文件同名文件夹-->文件名组成：时间，深度，分辨率(多少x多少)，若没有深度，则空字符串。

## 三、ncinterp.py使用
```python
>>> import ncinterp as ni
>>> rootPath = r'/Users/littlesec/Downloads/'
>>> file = ni.NcFile('cldc.mean.nc',rootPath)
>>> file.processAFileData(5)
>>> # 如果是想直接将nc导出csv文件，则可以：
>>> file.processAFileData(60)
```
2. 若nc文件定义无missing_value，程序会提示输入。
3. 没有现成的封装能仅仅处理一组数据。也无法现成的封装设置缺失值（但可以修改代码，搜索代码：`data.setNaNValue(50)`，50即为缺失值）
4. 运行过程可能会弹出很多很多异常信息，可忽略（try-catch造成）
5. 或把符合条件的nc文件放到文件夹中，并修改代码中main函数的rootPath路径，直接运行py文件即可。