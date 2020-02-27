# -*- coding: UTF-8 -*-
import threading
from time import sleep, ctime


class myThread (threading.Thread):
   def __init__(self, threadID, name, s, e):
       threading.Thread.__init__(self)
       self.threadID = threadID
       self.name = name
       self.s = s
       self.e = e

   def run(self):
       print("Starting " + self.name+ctime())
      # 获得锁，成功获得锁定后返回True
      # 可选的timeout参数不填时将一直阻塞直到获得锁定
      # 否则超时后将返回False
       threadLock.acquire()
       #线程需要执行的方法
       printImg(self.s, self.e)
       # 释放锁
       threadLock.release()


listImg = []  # 创建需要读取的列表，可以自行创建自己的列表
for i in range(179):
   listImg.append(i)

# 按照分配的区间，读取列表内容，需要其他功能在这个方法里设置


def printImg(s, e):
   for i in range(s, e):
       print(i)


totalThread = 3  # 需要创建的线程数，可以控制线程的数量

lenList = len(listImg)  # 列表的总长度
gap = lenList / totalThread  # 列表分配到每个线程的执行数

threadLock = threading.Lock()  # 锁
threads = []  # 创建线程列表

# 创建新线程和添加线程到列表
for i in range(totalThread):
   thread = 'thread%s' % i
   if i == 0:
       thread = myThread(0, "Thread-%s" % i, 0, gap)
   elif totalThread == i+1:
       thread = myThread(i, "Thread-%s" % i, i*gap, lenList)
   else:
       thread = myThread(i, "Thread-%s" % i, i*gap, (i+1)*gap)
   threads.append(thread)  # 添加线程到列表

# 循环开启线程
for i in range(totalThread):
   threads[i].start()

# 等待所有线程完成
for t in threads:
   t.join()
print("Exiting Main Thread")
