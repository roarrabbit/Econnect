from netmiko import ConnectHandler
from re import search, findall
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
    net_connect = ConnectHandler(**device)
    sshconfirm = net_connect.find_prompt()[:-1]
    print('连接成功！' + sshconfirm,'\n开始巡检...')
    net_connect.enable()
    output = net_connect.send_command('show int sta',expect_string=r'--More--',delay_factor=2)
    print(output)
    while '--More--' in output:
        # 如果遇到more，就多输入几个空格
        # normalize=False 不取消命令后空格
        output = net_connect.send_command_timing(' ',strip_prompt=False,strip_command=False,normalize=False)
        print(output)


Econ_inspection(ip,user,secret,pwd)