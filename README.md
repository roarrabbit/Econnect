# 更新终止

由于个人问题，除非bug发生了或者是新的想法冒出来了，项目就暂时搁置于此了。Econnect已经更新到了1.3的版本了，在目前来说算也是能用的版本了，最后这里感谢下学校NIC。

# 下载

具体文件可在[releases](https://github.com/MLLR-L/Econnect/releases)中下载或gitee中[下载](https://gitee.com/bittrabbit/Emotion)


# 特色

Econnect由python制作而成，.exe文件为打包好的脚本，无需安装具体环境

* 范围选择
* 信息录入
  * 由于太菜。。所以采用csv文件录入，具体格式请看标题或下面，第一行切记请勿更改！
  * IP地址, 用户名, 密码, enable密码
* 备份
  * 自带tftp服务器，无需另外开启
  * 自动备份到一个`tftp_box`的文件夹内，下一层为`YYYYMMDDhh`，具体备份文件为`交换机名+ip第四位.text`
  * 开启tftp服务前会检测本地是否有程序占用69端口，若占用则会kill对应进程
  * 备份命令：copy flash:config.text tftp://**IP**//**路径**.text
* 巡检
  * 在1.2版本中有导出excel的想法
  * 巡检命令如下：
    * show int status
    * show memory
    * show cpu
* 支持
  * 我只测试了如下设备
    * 锐捷
      * S2628
      * S2652
      * S3760
      * S5750
    * 华为
      * S5700
  * 目前其中一台锐捷的S3760不能进入特权模式

# 版本

*  Econnect 1.1

  * 如上所示
  * Econnect 1.1 iso+text文件备份
* Econnect 1.2

  * Econnect.py 新增内容
  * 巡检完毕会自动导出excel报告
    * 速度加快
    * 文件都塞box里
*  Econnect 1.3 bate
   * Econnect_直出进度条版.py
     * 上面基础上添加了进度条

# 使用流程

1. 如果是第一次使用请确保当前路径没有一个叫`switch_info.csv`的文件，脚本会自动创建一个新的文件请按照格式填写即可，一行一台设备
2. 请输入要执行的数字  1.巡检 2.备份 3.退出：
   * 进入请根据需求在此界面输入[1 / 2 / 3]，其他数字无效
3. 具体
   1. 巡检
      1. 请选择需要执行的交换机[格式：1、1-5]：
         * 按照所提示的设备对应输入单个数字即可
         * 单个模式：[number]；例如：5
         * 批量模式：[number]-[number]；例如：5-10
   2. 备份
      1. 请选择需要执行的交换机[格式：1、1-5]：
         * 按照所提示的设备对应输入单个数字即可
         * 单个模式：[number]；例如：5
         * 批量模式：[number]-[number]；例如：5-10
   3. 退出


# 常见问题

* 如果遇到tftp开启失败

  1. 如遇防火墙请允许通过，因为tftp服务器需要监听69端口

  2. 请右键管理员运行（这个问题大多数出现在win8）
* 若端口关闭失败请参考

  * https://jingyan.baidu.com/article/fb48e8be97ddc92e622e14f3.html
* 关于netmiko模块ssh交换机遇到more的问题：

  * https://blog.csdn.net/weixin_34217711/article/details/91615805
* 关于tftp集成的参考

  * https://stackoverflow.com/questions/57109992/how-to-stop-tftp-server-using-tftpy-on-python
* 打包exe使用的命令：

   * pyinstaller  -F -i ./network.ico  Econnect.py
* 备份失败没有文件？
   * 打开控制面板：`控制面板\系统和安全\Windows Defender 防火墙\允许的应用`允许`Econnect`的专用或公用通过

-------
# Telnet 版本
telnet版本已不再更新，已具备基本连接巡检备份功能
