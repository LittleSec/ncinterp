> 原始nc数据文件超过100M，无法上传到GitHub。已上传到[百度网盘](https://pan.baidu.com/s/1htsTZcK)链接:https://pan.baidu.com/s/1htsTZcK  密码:vhqq。
> 若链接失效请联系[邮箱](kuaiqleqren@163.com)

## 代码说明
1. 该小工具的作用是提取mask(掩码)，方便之后使用mask去判断哪些点需要插值（海洋点），哪些点不需要插值（非海洋点，包括陆地冰川湖泊等）。
2. 在该nc文件中，mask的值对应如下：需要注意的是读出来的值是byte类型（所以后面用B标注），注意类型转换。实际上规律是八位二进制，高四位全0，低四位有且仅有一位是1。

|flag_values|1B|2B|4B|8B|
|:-|:-:|:-:|:-:|:-:|
|flag_meanings|sea|land|lake|ice|
3. 生成csv文件里除了sea区域为1，其他均为0。
4. 代码不依赖于自己写其他py库（主分支上的），考虑到这些py文件会不停修改函数名等，甚至会拆解。

## 前期文件准备
1. 最初的原始文件依然是网盘上的文件。0.05度一个数据。
2. 但已经裁剪了很多信息，代码直接使用的文件是[```sst_mask_cutlatlon.nc```](./sst_mask.nc)。只留下剩下数据：
    + 经纬度范围：lat：12.025,33.025，lon：109.475,131.075
    + 只保留了mask属性
3. 以上工作使用一个命令行工具包完成。
    + 最初参考[StackOverflow](https://stackoverflow.com/questions/29135885/netcdf4-extract-for-subset-of-lat-lon)
    + 工具包为[nco](http://nco.sourceforge.net/nco.html#ncks-netCDF-Kitchen-Sink)
    + 命令：```ncks -v mask -d lat,12.025,33.025 -d lon,109.475,131.075 20140101-UKMO-L4HRfnd-GLOB-v01-fv02-OSTIA.nc sst_mask.nc```
    + 命令抽象：```ncks -v [需要提取的属性名，空格分隔] -d lat,[开始纬度],[结束纬度] -d lon,[开始经度],[结束经度] [源nc文件] [目标nc文件]```
4. 不懂为什么还保留了time属性。。。。
4. 所截取的经纬度其实和需要的经纬度不太吻合，相差0.25度。这个后期再决定如何处理。
