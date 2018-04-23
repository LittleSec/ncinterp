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
1. 对于有定义```__name__```的模块可以直接修改其中代码运行。注意确保数据文件在对应的路径。
2. plot1.m画单幅热力图，传入参数是单个csv文件。
3. plot2comparison.m画两类热力图对比，一左一右，一般用于对比插值前后效果；传入参数是两个csv文件（一般用于对比插值前后的效果）。
4. quiveruv.m画单幅向量场，传入参数是两个速度场csv文件。

## 五、需要用到的测试文件
1. 为了repo的干净度，已将nc文件存入[百度云盘](https://pan.baidu.com/s/1J6yRH381XUPwyD0lsybliQ)，可根据文件名下载。
2. 若发现链接失效或链接未更新，请联系给我发[邮件](kuaiqleqren@163.com)