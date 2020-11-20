from netmiko import ConnectHandler
from re import search, findall
from time import sleep
ip='*****'
user='*****'
pwd='*****'
secret = '*****'
def Econ_inspection(ip,user,secret,pwd):
    print('开始连接'+ip)
    device={
        'device_type':'cisco_ios',
        'ip':ip,
        'username':user,
        'secret':secret,
        'password':pwd,
    }
    print(device)
    input()
    Econ_list=[]
    net_connect = ConnectHandler(**device)
    sshconfirm = net_connect.find_prompt()[:-1]
    Econ_list.append(sshconfirm)
    print('连接成功！' + sshconfirm,'\n开始巡检...')
    net_connect.enable()
    output = net_connect.send_command('show int sta',expect_string=r'--More--',delay_factor=2)
    # 去掉more
    output_del = output[:output.rfind('--More--')]
    # 如果遇到more，就多输入几个空格
    # normalize=False 不取消命令后空格
    while '--More--' in output:
        sleep(0.1)
        output = net_connect.send_command_timing(' ',strip_prompt=False,strip_command=False,normalize=False)
        # 将空格获取的内容添加到
        output_del += output
    # 去掉末尾的#
    output_del = output_del[:output_del.rfind('\n%s#'%(sshconfirm))]
    Econ_list.append(output_del)
    # 执行show memory
    output = net_connect.send_command('show memory')
    # 正则匹配需要的百分比
    output = search(r'(\d.*)%', output).group()
    Econ_list.append(output)
    output = net_connect.send_command('show cpu',expect_string=r'--More--',delay_factor=2)
    # 将显示cpu的内容缩小范围，到NO截至之前的则是想要的内容
    output = output[:output.find('NO')]
    output = findall(r'(\d.*%)',output)
    Econ_list.append(output)
    net_connect.disconnect()
    return Econ_list


alist=Econ_inspection(ip,user,secret,pwd)
for i in alist:
    print(i)
