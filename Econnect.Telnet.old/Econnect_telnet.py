#! python3
# 交换机巡检.py - 检查交换机状态并导出excel文档以便于查看
# 参考https://www.jianshu.com/p/0db784257447

import telnetlib
from time import sleep
from sys import exit
from re import findall, search, sub
from os import unlink, startfile, popen
popen('mode con cols=110 lines=20')
sleep(0.7)
print('by MLLR')
popen('title=交换机巡检+备份2.5')
# ----------文件的操作--------------
def switch_list():
    global Switch_info, Switch_del_num, next_while,ip

    # 定义一个保存的函数
    def save_logging(Switch_info):
        if len(Switch_info) > 0:
            # 写入py文件
            file_txt = open('Switch_logging.py', 'w')
            file_txt.write('Switch_logging =' + str(Switch_info).replace('], ','], \n'))
            file_txt.close()

    # 尝试打开交换机信息表
    def open_Switch_logging():
        try:
            from Switch_logging import Switch_logging as logging_list
            if len(logging_list) == 0:
                return 1
            else:
                return logging_list
        except:
            print('您还没有数据，请输入1以添加交换机信息\n')
            return 1

    open_Switch_logging()
    # 循环开始序号执行数据的交互
    while True:
        next_while = input('[ 0:执行巡检命令 | 1:执行备份命令 | 2:添加交换机数据 |  3:删除交换机数据 | 4:查看交换机已有数据 | 5.退出]\n：')
        # 执行巡检
        if next_while == '0':
            if open_Switch_logging() == 1:
                continue
            break
            # 执行备份
        if next_while == '1':
            if open_Switch_logging() == 1:
                continue
            print('请打开tftp软件')
            ip = input('输入ip或回车自动使用本地ip做tftp服务器：')
            if len(ip) < 7:
                try:
                    from get_ip import get_host_ip
                    ip = get_host_ip()
                except:
                    print('没有找到获取本地ip脚本')
                    pass
            print()
            break
        # 添加
        elif next_while == '2':
            # 尝试导入命令集并重命名
            try:
                from Switch_logging import Switch_logging as Switch_info
            except ModuleNotFoundError:
                Switch_info = []
                pass
            Switch_info.append([
                input('请输入交换机IP：'),
                input('请输入telnet用户名：'),
                input('请输入telnet密码：'),
                input('请输入enable密码：')])
            save_logging(Switch_info)
        elif next_while == '3':
            if open_Switch_logging() == 1:
                print('您还没有数据，请输入1以添加交换机信息\n')
                continue
            else:
                Switch_logging = open_Switch_logging()
            # 循环打出要删除的内容
            a = open_Switch_logging()
            for i in range(len(Switch_logging)):
                print(i + 1, ' ', Switch_logging[i])
            # 尝试删除
            try:
                Switch_del_num = int(input('请输入要删除的序号')) - 1
                del Switch_logging[Switch_del_num]
                print('删除成功！')
                print('序号 交换机IP  telnet用户名  telnet密码  enable密码')
                for i in range(len(Switch_logging)):
                    print(i + 1, ' ', Switch_logging[i])
                if len(Switch_logging) == 0:
                    try:
                        unlink('Switch_logging.py')
                    except:
                        pass
                    continue
                save_logging(Switch_logging)
            except Exception as e:
                print('输入有误！请重试\n', e)
                continue
        # 查询
        elif next_while == '4':
            if open_Switch_logging() == 1:
                print('您还没有数据，请输入1以添加交换机信息\n')
                continue
            else:
                Switch_logging = open_Switch_logging()
            # 循环打出要查询的内容
            print('序号 交换机IP  telnet用户名  telnet密码  enable密码')
            for i in range(len(Switch_logging)):
                print(i + 1, ' ', Switch_logging[i])
        # 退出
        elif next_while == '5':
            print('已断开...')
            exit(0)
        # 输入其他就回到一开始
        else:
            print('输入错误，请重新输入！\n')
            continue
        print()


# ----------交换机的操作--------------
# Telnet to Switch， 格式为交换机ip，telnet用户名，密码
def Telnet_to_Switch(tel_ip, username, password):
    # 尝试telnet登陆交换机
    try:
        tn = telnetlib.Telnet(tel_ip, port=23, timeout=60)
        print('正在连接...', end='')
        # 使用try以免登录失败
        # 等待交换机出现Username:，60s为超时时间
        tn.read_until(b'Username:', timeout=60)
        # 输入用户名
        tn.write(username.encode('ascii') + b'\n')
        # 等待交换机出现Password:，60s为超时时间
        tn.read_until(b'Password:', timeout=10)
        # 输入密码
        tn.write(password.encode('ascii') + b'\n')
    except Exception as e:
        print('连接超时或密码错误！请重试!\n', e)
        exit(1)
    else:
        print('连接成功！')
        return tn


# Enter enable to next
def Enter_enable(tn, en_password):
    # print('正在进入特权模式')
    err = '% Access denied'
    tn.write(b'\n')
    while True:
        # Enter enable to next
        tn.write(b'enable\n')
        # 等待交换机出现Password:，10s为超时时间
        tn.read_until(b'Password:', timeout=10)
        tn.write(en_password.encode('ascii') + b'\n')
        msg = (tn.read_very_eager()).decode('gbk')
        if err in msg:
            continue
        break
    # print('已进入特权模式')


# 进行show操作
def get_show(tn, Enter_cmd):
    # 定义空内容接受信息
    confComplete = ''
    sleep(0.5)
    # 执行要查询的show命令，要编码为ascii然后在后面添加回车
    tn.write(Enter_cmd.encode('ascii') + b'\n')
    sleep(0.5)
    # 获取交换机输出的内容，由于测试中有台交换机编码X0aa，用gbk编码保险点
    msg = (tn.read_very_eager()).decode('gbk')
    confComplete = confComplete + msg
    # 如果有--More--更多内容则进行额外处理
    moreReg = 'More'
    moreFlag = search(moreReg, msg)
    # 循环将内容放入，如果匹配到more则为True，否则反之
    while (moreFlag):
        print('.', end='')
        # 传输空格
        tn.write(' '.encode('ascii'))
        # 阻塞2s以让交换机打出更多信息
        sleep(2)
        # 获取内容
        msg = (tn.read_very_eager()).decode('ascii')
        # 将more替换为空格
        confComplete = sub(moreReg, ' ', confComplete)
        confComplete = confComplete + msg
        moreFlag = search(moreReg, msg)
        sleep(0.2)
    # print('执行%s完成！' % Enter_cmd)
    # 导出confComplete以便处理
    return confComplete

# -----------------备份与巡检
def Swith_copy(tn):   
    dong = get_show(tn, 'write')
    dong = dong[dong.find('\n')+1:dong.find('#')]
    
    copy_name = 'copy flash:config.text tftp://%s/%s.text' % (ip, dong)
    copy_enter = get_show(tn, copy_name)
    try:
        copy_enter.split('\n')
    except:
        pass
    finally:
        print(copy_enter)
    # 发送exit以关闭telnet！
    tn.write(b'exit')
    print('备份文件名为：%s.text\n正在断开连接...'% dong)

# 巡检内容
sh_all_int_brief = 'show ip interface brief'  # 查看简要端口信息
sh_cpu = 'show cpu'  # 查看cpu信息
sh_mem = '  show memory'  # 查看内存信息
txt = []
def Swith_show(tn,i):
    global  txt
    txt_list=[]
    a1=get_show(tn, sh_all_int_brief)
    a2=get_show(tn, sh_cpu)
    get_show(tn, 'z')
    sleep(1)
    a3=get_show(tn, sh_mem)
    txt_list.append(a1)
    txt_list.append(a2)
    txt_list.append(a3)
    txt.append(txt_list)
    # 发送exit以关闭telnet！
    tn.write(b'exit')
    sleep(0.2)
    # 获取交换机名字
    try:
        Switch_name = search('(\w.+)#', txt[i][0]).group()
        Switch_name = Switch_name.replace('#', '：')
        print(Switch_name)
    except:
        print('未知')
    # 获取简要端口信息
    print('端口简要信息：')
    Switch_vlan = txt[i][0].split('\r\n')
    for n in Switch_vlan[2:-1]:
        print(n)
    # 写入CPU使用率
    try:
        cpu_re = findall('(\d.*?%)', txt[i][1])
        Switch_cpu = 'CPU使用率： 五秒内使用：%s， 一分钟内使用：%s， 五分钟内使用%s' % (cpu_re[0], cpu_re[1], cpu_re[2])
    except Exception as e:
        print(e)
        print(txt[i][1])
    print(Switch_cpu)
    print()
    # 写入内存使用率
    memory_re = findall('(\d.*?%)', txt[i][2])
    memory_num = memory_re[0]
    Switch_memory = '内存使用率为：%s' % memory_num
    print(Switch_memory)
    print()
    #休息一下~~
    sleep(1)

def main():
    # 查询是否需要添加新信息
    switch_list()
    # 循环读取py文件导出账号集合
    from Switch_logging import Switch_logging as Switch_list
    # 循环打出要查询的内容
    # 为了安全起见将密码不显示，只在修改时显示
    print('序号 交换机IP  telnet用户名  ')
    for i in range(len(Switch_list)):
        print(i + 1, ' ', Switch_list[i][:2])
    print()
    print('单个执行请输入一个数字，例如3，批量执行请输入序号*-序号*，例如1-5')
    list_num = input('请输入要执行的序列：')
    if '-' in list_num:
        print('批量执行模式')
        list_num = list_num.split('-')
        list_num[0] = int(list_num[0]) - 1
        list_num[1] = int(list_num[1])
        Switch_list = Switch_list[list_num[0]:list_num[1]]
    else:
        print('单个指定执行')
        Switch_list = Switch_list[int(list_num) - 1:int(list_num)]

    for i in range(len(Switch_list)):
        tel_ip = Switch_list[i][0]
        username = Switch_list[i][1]
        password = Switch_list[i][2]
        en_password = Switch_list[i][3]
        print(tel_ip, username,end='')
        # 执行telnet到交换机，指定ip,用户名,密码并将获取到的tn赋予给tn
        tn = Telnet_to_Switch(tel_ip, username, password)
        # 传输enable密码
        Enter_enable(tn, en_password)
        if int(next_while) == 0:
            Swith_show(tn,i)
        elif int(next_while) == 1:
            Swith_copy(tn)

# 运行主函数
if __name__ == '__main__':
    while True:
        main()

