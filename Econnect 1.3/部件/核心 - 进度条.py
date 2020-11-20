import time
import sys


def progress_test():
    bar_length = 20
    for percent in range(0, 100):
        hashes = '>' * int(percent / 100.0 * bar_length)
        spaces = '-' * (bar_length - len(hashes))
        sys.stdout.write("\rPercent: [%s] %d%%" % (hashes + spaces, percent))
        sys.stdout.flush()
        time.sleep(0.1)


#progress_test()
a=list(range(30))
def progress_test2(li):
    bar_length = 40
    tol=len(li)
    for percent in range(0, tol):
        hashes = '>' * int(percent / (tol-1) * bar_length)
        spaces = '-' * (bar_length - len(hashes))
        sys.stdout.write("\r完成度: [%s] %s|%s" % (hashes + spaces, percent+1,tol))
        sys.stdout.flush()
        time.sleep(0.2)


progress_test2(a)
