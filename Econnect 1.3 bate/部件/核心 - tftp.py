# tftp请参考下行地址
# 关于tftp的参考：https://stackoverflow.com/questions/57109992/how-to-stop-tftp-server-using-tftpy-on-pythonfrom tftpy import TftpServer
from os import popen, makedirs
from os.path import exists
from re import findall, S
import threading
from tftpy import TftpServer

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


def start_tftp_process(tftp_ip_addr, tftp_folder, tftp_log_level):
    global tftpsrv, TFTP_srv_thread
    tftpsrv = PYTFTPServer(tftp_ip_addr, tftp_folder, tftp_log_level)
    TFTP_srv_thread = threading.Thread(name="TFTP Server thread", target=tftpsrv.start_tftp_server)
    TFTP_srv_thread.start()


def stop_tftp_process():
    tftpsrv.stop_tftp_server()
    TFTP_srv_thread.join()


# 文件不存在则创建
if not exists('tftp_box'):
    print('tftp_box文件夹创建中...')
    makedirs('tftp_box')
# 尝试关闭69进程
try_shutdown_69 = popen('netstat -aon|findstr "69"').read()
if try_shutdown_69:
    search_69 = findall(r'UDP .*?:69.*?(\d+)', try_shutdown_69, S)
    if len(search_69):
        print(popen('taskkill /f /pid %s' % search_69[0]).read())
# 获取ip
tftp_ip = get_host_ip()
# 开始调用TFTP监听69端口
folor = './tftp_box'
print('开始监听中...')
start_tftp_process(tftp_ip,folor,1)
input('回车结束监听')
print('正在关闭中...')
stop_tftp_process()