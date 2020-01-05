#! python3
# Econnect.py - 交换机巡检(ssh)&备份
# 关于netmiko模块ssh交换机遇到more的问题：https://blog.csdn.net/weixin_34217711/article/details/91615805
# 关于tftp的参考：https://stackoverflow.com/questions/57109992/how-to-stop-tftp-server-using-tftpy-on-python
# 打包exe使用的命令 - pyinstaller  -F -i ./network.ico  Econnect.py
print('by MLLR')
from netmiko import ConnectHandler
from re import search, findall, S
from time import sleep
from sys import exit
from os import system, popen, makedirs
from os.path import exists
from subprocess import Popen
from csv import reader
from tftpy import TftpServer
import threading

popen('title=Econnect - by MLLR')


def info_to_list():
    """
    将本地的switch_info.csv打开并从list转换为dict
    :return: 交换机的信息 列表[[IP, user, pwd, en_pwd]]
    """

    # 尝试打开文件，如果打不开则创建文件
    try:
        with open('switch_info.csv') as f:
            reader_csv = reader(f)
            switch_list = list(reader_csv)
    except FileNotFoundError:
        print('switch_info.csv文件缺失，正在创建.....', end='')
        sleep(0.5)
        with open('switch_info.csv', 'w') as f:
            f.writelines('IP地址,用户名,密码,enable密码,第一行请勿更改！')
        print('创建成功！请添加完信息后重新打开\n')
        # 打开文件
        print('正在尝试打开')
        Popen(['start', 'switch_info.csv'], shell=True)
        system('pause')
        exit(1)
    # 如果得到的列表数目小于1那就说明列表内没信息
    if len(switch_list) > 1:
        return switch_list
    else:
        print('你貌似还没输入信息，请添加信息后重新打开,例如：')
        print('\nIP地址   用户名 密码 enable密码\n10.1.1.1 test test test\n10.1.1.2 test test test\n')
        # 打开文件
        Popen(['start', 'switch_info.csv'], shell=True)
        system('pause')
        exit(1)


def choice_list(switch_list):
    """
    选择要执行的设备单个/批量
    :param switch_list: csv转换的列表
    :return: 选择好的交换机信息 - 列表
    """
    print('序号 IP地址        用户名     密码')
    # 从1开始逐行打印
    for i in range(1, len(switch_list)):
        print(i, '   %s %s %s' % (
        switch_list[i][0], switch_list[i][1], switch_list[i][2][:4] + '*' * len(switch_list[i][2][4:])))
    # 用于循环数字，w用于循环
    loop_choice_num = 1
    while loop_choice_num:
        try:
            # 使用''.split('-')分割成列表
            Switch_list_choice_num = input('\n请选择需要执行的交换机[格式：1、1-5]：').split('-')
            if int(Switch_list_choice_num[0]) == 0:
                print('不在范围内！请重新输入')
            elif len(Switch_list_choice_num) == 1:
                if int(Switch_list_choice_num[0]) >= len(switch_list):
                    print('超过指定范围')
                    raise NameError
                # 否则如果是单个执行，则len()的值为1，假设input->2处理后->['2']
                switch_list = switch_list[int(Switch_list_choice_num[0]):int(Switch_list_choice_num[0]) + 1]
                # 值为0，while False，下一轮不执行
                loop_choice_num = 0
            elif len(Switch_list_choice_num) == 2:
                if int(Switch_list_choice_num[1]) >= len(switch_list):
                    print('超过指定范围')
                    raise NameError
                # 否则如果是批量执行，则len()的值为2，假设input->2-4处理后->['2','4']
                switch_list = switch_list[int(Switch_list_choice_num[0]):int(Switch_list_choice_num[1]) + 1]
                # 值为0，while False，下一轮不执行
                loop_choice_num = 0
            else:
                print('输入有误！请重新输入')
        except:
            print('输入有误！请重新输入正确的格式：1 或 1-5')
    return switch_list


def start_tftp_process(tftp_ip_addr, tftp_folder, tftp_log_level):
    global tftpsrv, TFTP_srv_thread
    tftpsrv = PYTFTPServer(tftp_ip_addr, tftp_folder, tftp_log_level)
    TFTP_srv_thread = threading.Thread(name="TFTP Server thread", target=tftpsrv.start_tftp_server)
    TFTP_srv_thread.start()


def stop_tftp_process():
    tftpsrv.stop_tftp_server()
    TFTP_srv_thread.join()


def get_host_ip():
    """
    获取出口的包得到出口的ip地址
    :return: ip地址
    """
    # 局部导入socket，在外面导入会与其他模块冲突
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('114.114.114.114', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
        # 删掉你怕了怕了QAQ
        del socket
    return ip


class PYTFTPServer(object):
    def __init__(self, tftp_ip_addr, tftp_folder, tftp_log_level):
        self.tftp_ip_addr = tftp_ip_addr
        self.tftp_folder = tftp_folder
        self.tftp_server = TftpServer(self.tftp_folder)
        self.tftp_log_level = tftp_log_level

    def start_tftp_server(self):
        try:
            self.tftp_server.listen(self.tftp_ip_addr, 69)
        except KeyboardInterrupt:
            pass

    def stop_tftp_server(self):
        self.tftp_server.stop()  # Do not take any new transfers, but complete the existing ones.
        # self.server.stop(True)            # Drop all connections and stop the server. Can be used if needed.


def Econ_connect(ip, user, pwd, secret):
    print('开始连接%s...' % ip)
    device = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': user,
        'secret': secret,
        'password': pwd,
    }
    # net_connect = ConnectHandler(**device) # 使用这个方法报错了就莫得了..
    try:
        # 防止意外退出
        net_connect = ConnectHandler(**device)
        # 输出得到的交换机名并去掉末尾的>
        sshconfirm = net_connect.find_prompt()[:-1]
        print(sshconfirm, '连接成功！尝试进入特权模式中...')
        # 进入特权模式
        net_connect.enable()
        print('成功！', end='')
        return net_connect, sshconfirm
    except:
        print('连接失败(,,• ₃ •,,)...请检查网络配置！')
        return 0, 0


def Econ_inspection(net_connect, sshconfirm):
    """
    巡检-------------------->
    :param net_connect：连接交换机的会话
    :param sshconfirm：交换机的名字
    :return: 一个关于巡检内容的列表 - [交换机名, show int status, sh memory, [5sec, 1min, 5min]]
    """
    print('开始巡检...')
    print('查看接口状态(show int status)：')
    output = net_connect.send_command('show int status', expect_string=r'--More--', delay_factor=2)
    # 去掉more
    print(output[:output.rfind('--More--')], end='')
    # 如果遇到more，就多输入几个空格
    # normalize=False 不取消命令后空格
    while '--More--' in output:
        sleep(0.1)
        output = net_connect.send_command_timing(' ', strip_prompt=False, strip_command=False, normalize=False)
        # 尝试找'--More--'并输出它之前的内容，再找最后主机名并输出他之前的内容，如果找不到则为-1，不改变其内容本身
        print(output[:output.rfind('--More--') - 1][:output.rfind('\n%s#' % sshconfirm)])
    # 执行show memory
    output = net_connect.send_command('show memory')
    # 正则匹配需要的百分比
    output = search(r'(\d.*)%', output).group()
    print('查看内存(show memory)：', output)
    output = net_connect.send_command('show cpu', expect_string=r'--More--')
    # 输入一个e以结束more
    net_connect.send_command_timing('e', strip_prompt=False, strip_command=False, normalize=False)
    # 将显示cpu的内容缩小范围，到NO截至之前的则是想要的内容
    output = output[:output.find('NO')]
    output = findall(r'(\d.*%)', output)
    print('查看CPU(show cpu)： 五秒内使用：%s， 一分钟内使用：%s， 五分钟内使用%s' % (output[0], output[1], output[2]))
    print('断开连接中...', end='')
    net_connect.disconnect()
    print('已断开\n')


def tftp_server():
    # 尝试关闭69进程
    try_shutdown_69 = popen('netstat -aon|findstr "69"').read()
    if try_shutdown_69:
        search_69 = findall(r'UDP .*?:69.*?(\d+)', try_shutdown_69, S)
        if len(search_69):
            print(popen('taskkill /f /pid %s' % search_69[0]).read())
    # 存放路劲
    folor = './tftp_box'
    # 获取ip
    tftp_ip = get_host_ip()
    # 开始调用TFTP监听69端口
    try:
        print('请允许防火墙通过，否则将不能使用备份功能')
        start_tftp_process(get_host_ip(), folor, 1)
    except:
        print('错误！69端口被占用，自动关闭失败如需解决请参考：\nhttps://jingyan.baidu.com/article/fb48e8be97ddc92e622e14f3.html')
        system('pause')
        exit(1)
    print('正在监听%s:69\n' % tftp_ip)
    return tftp_ip


def Econ_backup(net_connect, sshconfirm, tftp_ip):
    """
    备份-------------------->
    :param net_connect：连接交换机的会话
    :param sshconfirm：交换机的名字
    :return: NONE
    """
    net_connect.send_command('write')
    copy_name = 'copy flash:config.text tftp://%s/%s.text' % (tftp_ip, sshconfirm)
    print(sshconfirm, '开始备份...')
    try:
        output = net_connect.send_command(copy_name, delay_factor=3)
        print(output)
    except:
        print('备份失败(′▽`〃) 请检查相关设置')
    print('断开连接中...', end='')
    net_connect.disconnect()
    print('已断开\n')


def main():
    Switch_list = info_to_list()
    main_loop_num = 1
    while main_loop_num:
        try:
            run_num = int(input('\n请输入要执行的数字  1.巡检 2.备份 3.退出：'))
        except:
            print('输入有误！请重新输入\n')
            continue
        if run_num == 1:
            # 选择要执行的范围
            Switch_list_choice = choice_list(Switch_list)
            for i in Switch_list_choice:
                # 去掉其中的空格以免账号密码错误
                for n in range(len(i)):
                    i[n] = i[n].replace(' ', '')
                net_connect, sshconfirm = Econ_connect(i[0], i[1], i[2], i[3])
                if net_connect == 0:
                    print('\n由于连接%s失败，正在跳转到下一台设备中..\n' % i[0])
                    sleep(0.3)
                    continue
                Econ_inspection(net_connect, sshconfirm)
        elif run_num == 2:
            # 选择要执行的范围
            Switch_list_choice = choice_list(Switch_list)
            # 判断文件是否存在，不存在则创建
            if not exists('tftp_box'):
                print('tftp_box文件夹创建中...')
                makedirs('tftp_box')
            # 调用tftp服务
            tftp_ip = tftp_server()
            for i in Switch_list_choice:
                # 去掉其中的空格以免账号密码错误
                for n in range(len(i)):
                    i[n] = i[n].replace(' ', '')
                net_connect, sshconfirm = Econ_connect(i[0], i[1], i[2], i[3])
                if net_connect == 0:
                    print('\n由于连接%s失败，正在跳转到下一台设备中..\n' % i[1])
                    sleep(0.3)
                    continue
                Econ_backup(net_connect, sshconfirm, tftp_ip)
            print('正在关闭tftp服务器....')
            try:
                stop_tftp_process()
            except:
                print('关闭失败！为了避免不必要的错误正在关闭中...')
                sleep(1.5)
                exit(1)
            print('关闭成功！')
        elif run_num == 3:
            main_loop_num = 0
    print('退出中..')


if __name__ == '__main__':
    main()
