#! python3
# Econnect.py - 交换机巡检(ssh)&备份
# 关于netmiko模块ssh交换机遇到more的问题：https://blog.csdn.net/weixin_34217711/article/details/91615805
# 关于tftp的参考：https://stackoverflow.com/questions/57109992/how-to-stop-tftp-server-using-tftpy-on-python
# 打包exe使用的命令 - pyinstaller  -F -i ./network.ico  Econnect.py
from sys import exit, stdout
print('by MLLR')
from netmiko import ConnectHandler
from re import findall, S
from time import sleep, strftime, localtime,time
from os import system, popen, makedirs
from os.path import exists
from subprocess import Popen
from csv import reader
from tftpy import TftpServer
import threading
import xlsxwriter

# TODO: |-try- 备份多线程
popen('title=Econnect - by MLLR')
title = ['管理IP', '主机名', 'CPU - 5s', 'CPU - 1m', 'CPU - 5m', '内存使用', '情况摘要']
# 阈值，超出下值则写入摘要
Threshold_cpu = 30
Threshold_memory = 70
# 进度条长度
bar_length = 45


def info_to_list():
    """
    将本地的switch_info.csv打开并从list转换为list
    :return: 交换机的信息 列表[[IP, user, pwd, en_pwd]]
    """

    # 尝试打开文件，如果打不开则创建文件
    # 判断文件是否存在，不存在则创建
    if not exists('Econnect_box'):
        print('Econnect_box文件夹创建中...')
        makedirs('Econnect_box')
    try:
        with open('Econnect_box\\switch_info.csv') as f:
            reader_csv = reader(f)
            switch_list = list(reader_csv)
    except FileNotFoundError:
        print('switch_info.csv文件缺失，正在创建.....', end='')
        sleep(0.5)
        with open('Econnect_box\\switch_info.csv', 'w') as f:
            f.writelines('IP地址,用户名,密码,enable密码,第一行请勿更改！')
        print('创建成功！请添加完信息后重新打开\n')
        # 打开文件
        print('正在尝试打开')
        popen('cd Econnect_box && start switch_info.csv')
        system('pause')
        exit(1)
    # 如果得到的列表数目小于1那就说明列表内没信息
    if len(switch_list) > 1:
        return switch_list
    else:
        print('你貌似还没输入信息，请添加信息后重新打开,例如：')
        print('\nIP地址   用户名 密码 enable密码\n10.1.1.1 test test test\n10.1.1.2 test test test\n')
        # 打开文件
        popen('cd Econnect_box && start switch_info.csv')
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
        # 输出序号、ip地址、用户名（加密）、密码（加密），其中*号+1以混淆
        print(i, '   %s %s %s' % (
            switch_list[i][0], switch_list[i][1][:3] + '*' * (len(switch_list[i][1][3:]) + 1),
            switch_list[i][2][:3] + '*' * (len(switch_list[i][2][3:]) + 1)))
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
    device = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': user,
        'secret': secret,
        'password': pwd,
    }
    # net_connect = ConnectHandler(**device) # 使用这个方法报错了就莫得了..
    try:
        # 防止意外退出，这是连接交换机的进程
        net_connect = ConnectHandler(**device)
    except:
        print('连接失败(,,• ₃ •,,)...请检查网络配置！')
        return 0, 0
    try:
        # 获取到的名字，输出得到的交换机名并去掉末尾的>
        sshconfirm = net_connect.find_prompt()[:-1]
        # 有<说明为华为交换机
        if len(secret) != 0:
            # 进入特权模式
            net_connect.enable()
        return net_connect, sshconfirm
    except:
        net_connect.disconnect()
        return 0, sshconfirm


def turn_xlsx(data_list, Threshold_cpu, Threshold_memory):
    """
    :param data_list: 选择的一个列表范围，格式[[],[],[],[],]
    :param Threshold_memory: 内存阈值
    :param Threshold_cpu: cpu阈值
    包含：管理IP,主机名,CPU - 5s,CPU - 1m,CPU - 5m,内存使用,网络状态生成摘要
    摘要：cpu>Threshold_cpu = cpu偏高, 内存>Threshold_memory = 内存偏高
    :return:一个excel文件
    """
    # 预处理数据
    # 排序,使用主机名的前几位进行升序排序
    sorted(data_list, key=(lambda x: x[1][0:3]))
    # 对cpu、内存进行总结摘要
    for i in range(len(data_list)):
        # 初始化一个摘要字符串
        total = ''
        if data_list[i][1] == '1connect_faild':
            data_list[i][1] = '连接失败'
            data_list[i][2] = '连接失败'
            data_list[i][3] = '连接失败'
            data_list[i][4] = '连接失败'
            data_list[i][5] = '连接失败'
            data_list[i].append('连接失败,请检查网络配置！')
        elif data_list[i][2] == -1:
            data_list[i][2] = '数据已丢失'
            data_list[i][3] = '数据已丢失'
            data_list[i][4] = '数据已丢失'
            data_list[i][5] = '数据已丢失'
            # 由于80那台设备进入特权模式失败所以在此备注
            data_list[i].append('进入特权模式失败')
        else:
            # CPU，超出阈值则写入
            if data_list[i][2] >= Threshold_cpu:
                total += 'cpu超出偏高 '
            elif data_list[i][3] >= Threshold_cpu:
                total += 'cpu超出偏高 '
            elif data_list[i][4] >= Threshold_cpu:
                total += 'cpu超出偏高 '
            # 内存，超出阈值则写入
            if data_list[i][5] >= Threshold_memory:
                total += '内存偏高 '
            # 如果总结摘要存在则直接添加excel列表，否则替换字段为正常
            if total:
                data_list[i].append(total)
            else:
                data_list[i].append('正常')
            if '<' in data_list[i][1]:
                data_list[i][1] = data_list[i][1][1:]
    # 添加一个标准值
    data_list.append(['固定参考值', '最大值', 100, 100, 100, 100])
    data_list.append(['固定参考值', '最小值', 0, 0, 0, 0])
    time_folor = strftime('%Y%m%d%H', localtime())
    # 存放路劲
    folor = './Econnect_box/' + time_folor
    # 判断文件是否存在，不存在则创建
    if not exists(folor):
        makedirs(folor)
    # 初始化一个表的名字，以时间为年月日为前缀
    xlsx_name = '%s-巡检表.xlsx' % strftime('%Y%m%d', localtime())
    # 新建一个xlsx文件
    workbook = xlsxwriter.Workbook('%s\\%s' %(folor, xlsx_name))
    # 添加工作簿,名为巡检表
    worksheet_inspection = workbook.add_worksheet('巡检表')
    # 初始化样式
    format = workbook.add_format({'bg_color': '#0070c0', 'font_color': '#ffffff', 'border': 1})
    format_border = workbook.add_format({'border': 1})
    # 循环写入工作表的标题
    for row, row_data in enumerate(title):
        worksheet_inspection.write(0, row, row_data, format)
    # 循环写入对应的巡检数据
    for i in range(len(data_list)):
        # enumerate()用于将列表转换为可迭代的对象
        # list(enumerate([9,8,7])) -> [(0, 9), (1, 8), (2, 7)]
        # list(enumerate(['你', '好', '吗'])) -> [(0, '你'), (1, '好'), (2, '吗')]
        # 在for中则row为前面的序号，row_data为后面的值↓
        for row, row_data in enumerate(data_list[i]):
            worksheet_inspection.write(i + 1, row, row_data)
    # 对数据字段进行样式格式添加
    worksheet_inspection.conditional_format('C2:F%s' % (len(data_list) + 1), {
        'type': 'data_bar',
        'bar_color': '#92d050',
        'bar_solid': True,
        'format': format_border
    })
    # set_column(位置, 宽度)
    worksheet_inspection.set_column('A:A', 12)
    worksheet_inspection.set_column('B:B', 18)
    worksheet_inspection.set_column('G:G', 35)
    try:
        # 保存并推出
        workbook.close()
        # 打开excel文件
        popen('cd Econnect_box && cd %s && start %s'%(time_folor,xlsx_name))
    except:
        print('%s文件被占用，请关闭后重试！' % xlsx_name)


def Econ_inspection(net_connect, sshconfirm):
    """
    巡检-------------------->
    :param net_connect：连接交换机的会话
    :param sshconfirm: 从交换机截取的名字（'>'之前的）
    :return: 一个关于巡检内容的列表 - [sshconfirm, sh memory, 5sec, 1min, 5min]
    """
    cisco_memory = 'show memory'
    cisco_cpu = 'show cpu'
    huawei_memory = 'dis memory'
    huawei_cpu = 'dis cpu'
    if '<' not in sshconfirm:
        send_memory = cisco_memory
        send_cpu = cisco_cpu
    else:
        send_memory = huawei_memory
        send_cpu = huawei_cpu
    # 执行show memory
    output_memory = net_connect.send_command(send_memory)
    # 正则匹配需要的百分比
    output_memory = findall(r'(\d.*)%', output_memory)[0]
    output_cpu = net_connect.send_command(send_cpu, expect_string='',delay_factor=2)
    # 输入一个e以结束more
    net_connect.send_command_timing('e', strip_prompt=False, strip_command=False, normalize=False)
    # 将显示cpu的内容缩小范围，到NO截至之前的则是想要的内容,由于华为所以弃用
    if '<' not in sshconfirm:
        # 思科
        output_cpu = output_cpu[:output_cpu.find('NO')]
        output_cpu = findall(r'.*? (\d.*)%', output_cpu)
    else:
        # 华为
        output_cpu = output_cpu[output_cpu.find('CPU utilization'):]
        output_cpu = findall(r': (\d.*?)%', output_cpu)
    net_connect.disconnect()
    return [sshconfirm, float(output_cpu[0]), float(output_cpu[1]), float(output_cpu[2]), float(output_memory)]


def tftp_server():
    # 尝试关闭69进程
    try_shutdown_69 = popen('netstat -aon|findstr "69"').read()
    if try_shutdown_69:
        search_69 = findall(r'UDP .*?:69.*?(\d+)', try_shutdown_69, S)
        if len(search_69):
            print(popen('taskkill /f /pid %s' % search_69[0]).read())
    time_folor = strftime('%Y%m%d%H', localtime())
    # 存放路劲
    folor = './Econnect_box/' + time_folor
    # 判断文件是否存在，不存在则创建
    if not exists(folor):
        makedirs(folor)
    # 获取ip
    tftp_ip = get_host_ip()
    # 开始调用TFTP监听69端口
    try:
        start_tftp_process(get_host_ip(), folor, 1)
    except Exception as e:
        print(e)
        print('错误！69端口被占用，自动关闭失败如需解决请参考：\nhttps://jingyan.baidu.com/article/fb48e8be97ddc92e622e14f3.html')
        system('pause')
        exit(1)
    print('正在监听%s:69\n' % tftp_ip)
    return tftp_ip, time_folor


def Econ_backup(net_connect, sshconfirm, tftp_ip):
    """
    备份-------------------->
    :param net_connect：连接交换机的会话
    :param sshconfirm：交换机的名字
    :param tftp_ip：tftp服务器ip地址
    :return: NONE
    """
    if '<' not in sshconfirm:
        # 提前保存一遍再备份
        net_connect.send_command('write')
        copy_name = 'copy flash:config.text tftp://%s/%s.text' % (tftp_ip, sshconfirm)
    else:
        # 提前保存一遍再备份
        net_connect.send_command('save', expect_string='[Y/N]',delay_factor=2)
        sleep(0.5)
        net_connect.send_command('y', expect_string='', delay_factor=3)
        sleep(1)
        # 去掉'<'
        sshconfirm = sshconfirm[1:]
        copy_name = 'tftp %s put vrpcfg.zip %s.zip' % (tftp_ip,sshconfirm)
    try:
        net_connect.send_command(copy_name, delay_factor=3)
    except:
        print('备份失败(′▽`〃) 请检查相关设置')
    net_connect.disconnect()


def main_inspection(Switch_list_choice):
    # 初始化一个列表
    Econ_inspection_box = []
    print('巡检中，请稍后...')
    for i in range(len(Switch_list_choice)):
        bar_ok = '>' * \
            int(i / len(Switch_list_choice) * bar_length)
        bar_not = '-' * (bar_length - len(bar_ok))
        stdout.write("\r巡检完成度: [%s] %s|%s" %
                     (bar_ok + bar_not, i, len(Switch_list_choice)))
        stdout.flush()
        # 去掉其中的空格以免账号密码错误
        for n in range(len(Switch_list_choice[i])):
            Switch_list_choice[i][n] = Switch_list_choice[i][n].replace(
                ' ', '')
        net_connect, sshconfirm = Econ_connect(
            Switch_list_choice[i][0], Switch_list_choice[i][1], Switch_list_choice[i][2], Switch_list_choice[i][3])
        # 这里Econ_connect返回如果两个变量有内容则跳过，如果是0则跳转下一台
        if net_connect == 0:
            # 添加数据已丢失到列表中
            if sshconfirm == 0:
                # 如果sshconfirm=0则说明连接失败
                Econ_inspection_box.append(
                    [Switch_list_choice[i][0], '1connect_faild', -1, -1, -1, -1])
                continue
            else:
                # 如果sshconfirm=0则说明连接成功但是无法进入特权模式
                Econ_inspection_box.append(
                    [Switch_list_choice[i][0], sshconfirm, -1, -1, -1, -1])
                continue
        # 执行巡检动作
        Econ_inspection_info = Econ_inspection(net_connect, sshconfirm)
        # 将巡检得到的内容添加到列表中
        Econ_inspection_box.append(Econ_inspection_info)
        # 由于没有使用次数统计所以用总数-1代替
        Econ_inspection_box[len(
            Econ_inspection_box) - 1].insert(0, Switch_list_choice[i][0])
    turn_xlsx(Econ_inspection_box, Threshold_cpu, Threshold_memory)


def main_backup(Switch_list_choice):
    print('开始备份！')
    # 失败次数
    error_time = 0
    # 调用tftp服务
    tftp_ip, time_folor = tftp_server()
    for i in range(len(Switch_list_choice)):
        bar_ok = '>' * \
            int(i / len(Switch_list_choice) * bar_length)
        bar_not = '-' * (bar_length - len(bar_ok))
        stdout.write("\r备份完成度: [%s] %s|%s" %
                     (bar_ok + bar_not, i, len(Switch_list_choice)))
        stdout.flush()
        # 去掉其中的空格以免账号密码错误
        for n in range(len(Switch_list_choice[i])):
            Switch_list_choice[i][n] = Switch_list_choice[i][n].replace(
                ' ', '')
        net_connect, sshconfirm = Econ_connect(
            Switch_list_choice[i][0], Switch_list_choice[i][1], Switch_list_choice[i][2], Switch_list_choice[i][3])
        if net_connect == 0:
            error_time += 1
            continue
        Econ_backup(net_connect, sshconfirm, tftp_ip)
    # 调用命令行打开Econnect_box的文件夹
    system('start Econnect_box\\' + time_folor)
    print('正在关闭tftp服务器....')
    try:
        stop_tftp_process()
    except:
        print('关闭失败！为了避免不必要的错误正在关闭中...')
        sleep(1.5)
        exit(1)
    print('关闭成功！本次失败备份%s个' % error_time)

def main():
    # 读取数据
    Switch_list = info_to_list()
    # 设置循环字段
    main_loop_num = 1
    # 开始进入循环
    while main_loop_num:
        # 防乱输入
        try:
            run_num = int(input('\n请输入要执行的数字  1.巡检备份 2.退出：'))
        except:
            print('输入有误！请重新输入\n')
            continue
        if run_num == 1:
            start_time = time()
            # 选择要执行的范围
            Switch_list_choice = choice_list(Switch_list)
            b_sing = threading.Thread(
                target=main_inspection, args=(Switch_list_choice,))
            b_sing.start()
            main_backup(Switch_list_choice,)
            b_sing.join()
            end_time = time()
            print('总时长为：',end_time-start_time)
        elif run_num == 2:
            main_loop_num = 0
    print('退出中..')

            


if __name__ == '__main__':
    main()
