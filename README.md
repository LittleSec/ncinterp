# NC文件插值处理

## 一、环境
1. matlab 2016a
2. python 3.4.3(配合matlab版本即可)
3. 用到的第三方库:
    + numpy
    + scipy
    + pandas
    + matlab
4. 前三个库可使用pip安装，自行安装或进入该git目录下输入命令可一次性安装：```pip3 -r install requestment.txt```
5. matlab引擎的安装：下载并安装matlab 2016a后参考官网运行setpy.py[安装用于 Python 的 MATLAB 引擎 API](https://ww2.mathworks.cn/help/matlab/matlab_external/install-the-matlab-engine-for-python.html)
6. 安装完成后把```interpACSV.m```放入matlab的工作目录下。
>注意：实际上，python和matlab的版本不一定要上述说明的版本，唯一的硬性要求是安装matlab引擎版本所支持的python版本即可。如果使用matlab 2017b或以上，则可以使用python 3.6.x。

## 二、NC文件特点
1. 经纬度范围：东黄海区域。要求网格间隔必须一致（这是调用的matlab插值函数所限制的）。
2. 经纬度的属性名为X,Y或lat,lon或latitude,longitude（字母大小写都可以）。
3. 时间单位要么是日，要么是月，月的话值为小数。
4. 真正的观测值只能有一个。
5. 除了经纬度两个维度外，只能再有时间或深度维度，其中时间维度是必要的。

## 三、生成文件的规律
>具体说明参看csvjsonwriteop库
1. 文件夹：与nc文件同名文件夹 + csv的形式（grid或tuple）/ JSON (+ 特殊的值名如ow)
2. 文件名组成：时间，深度。

## 四、使用
1. 测试文件不建议直接点击运行，肯定会出错。应当打开后根据需要修改文件名（必要时修改路径），复制相应的代码在IDLE或matlab的命令窗口来执行。
1. 插值和导出文件的操作参考testSample.py
    + 必须先导出csv文件然后再插值
    + 运行速度很慢，耐性等待。建议使用dataselector选择数据再导出，以减少处理的文件数量
2. plotSample.m是matlab文件，用于快速查看插值前后的效果。

## 五、分支说明
1. OkuboWeiss参数计算有差别只是数据集不同而已，并非方法错误。
2. 父分支是直接通过速度数据集uv算出，而该分支是通过ssh推导出地转流速uv再算出。
3. 但该分支中新增的anomaly模块中求平均(mean)和异常(anomaly)适用于之后的分析，可以考虑部分合并。
4. 已发现在ncinterp模块中的interpAFolder()存在bug，具体参考该模块的todo，**注意该bug在其他分支中也存在**。