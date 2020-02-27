import xlsxwriter
from time import strftime, localtime
from subprocess import Popen

title = ['管理IP', '品牌、型号', 'CPU使用(5s内)', '内存使用', '网络状态', '情况摘要']
data = [['172.16.1.53', '锐捷 RG-S3760E-48', 3, 75, 0],
        ['172.16.1.11', '锐捷 RG-S3760E-48', 4, 53, 0],
        ['172.16.1.85', '锐捷 RG-S3760E-48', 60, 66, 1],
        ['172.16.1.58', '锐捷 RG-S3760E-48', 5, 68, 0],
        ['172.16.1.55', '锐捷 RG-S3760E-48', 5, 69, 1],
        ['172.16.1.56', '锐捷 RG-S3760E-48', 31, 57, 0],
        ['172.16.1.54', '锐捷 RG-S3760E-48', 18, 51, 0]]
# 阈值，超出下值则写入摘要
Threshold_cpu = 20
Threshold_memory = 60


def turn_xlsx(data_list, Threshold_cpu, Threshold_memory):
    '''

    :param data_list: 选择的一个列表范围，格式[[],[],[],[],]
    包含：管理IP,品牌、型号,CPU使用(5s内),内存使用,网络状态生成摘要
    摘要：cpu>60 = cpu超出阀值, 内存>60 = 内存超出阀值, 连接状态=1 =连接状态异常
    :return:一个excel文件
    '''
    # 处理列表
    for i in range(len(data_list)):
        # 初始化一个摘要字符串
        total = ''
        # CPU，超出阈值则写入
        if data_list[i][2] >= Threshold_cpu:
            total += 'cpu超出阀值 '
        # 内存，超出阈值则写入
        if data_list[i][3] >= Threshold_memory:
            total += '内存超出阀值 '
        # 网络连接状态，如果等于1则说明连接失败，写入
        if data_list[i][4] == 1:
            total += '连接状态异常'
        if total:
            data_list[i].append(total)
        else:
            data_list[i].append('正常')
    # 添加一个标准值
    data_list.append(['固定参考值', '最大值', 100, 100])
    data_list.append(['固定参考值', '最小值', 0, 0])
    # 初始化一个表的名字，以时间为年月日为前缀
    xlsx_name = '%s-巡检表.xlsx' % strftime('%Y%m%d', localtime())
    # 新建一个xlsx文件
    workbook = xlsxwriter.Workbook(xlsx_name)
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
    worksheet_inspection.conditional_format('C2:D%s' % (len(data_list) + 1), {
        'type': 'data_bar',
        'bar_color': '#92d050',
        'bar_solid': True,
        'format': format_border
    })
    # set_column(位置, 宽度)
    worksheet_inspection.set_column('A:A', 12)
    worksheet_inspection.set_column('B:B', 18)
    worksheet_inspection.set_column('F:F', 35)
    workbook.close()
    Popen(['start', xlsx_name], shell=True)


turn_xlsx(data, Threshold_cpu, Threshold_memory)
