#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Author  :   long.hou
@Email   :   long2.hou@luxshare-ict.com
@Ide     :   vscode & conda
@File    :   runThread.py
@Time    :   2023/06/06 19:32:00
'''
import subprocess
import time, json, re
from threading import Timer

from PyQt5.QtCore import QThread, pyqtSignal
from Tool.functions import choose_function, write_csv, get_config, update_mes
from Tool.Common import *
from Tool import test_plan


def RunShellWithTimeout(cmd, timeout=3):
    def process_timeout(process):
        process.kill()

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timer = Timer(timeout, process_timeout, [p])  # 设置定时器计算超时时间，超时杀死此线程
    try:  # 尝试运行，出错不停止
        timer.start()
        stdout, stderr = p.communicate()  # 读取终端返回的内容，stdout为返回正常内容。stderr为出错内容
        return_code = p.returncode  # 获取终端返回值，正常返回值为0，异常为其它
        stdout = stdout.decode(errors='ignore')
        stderr = stderr.decode(errors='ignore')
        return return_code, stdout, stderr
    finally:
        timer.cancel()


class InitThread(QThread):
    result_signal = pyqtSignal(bool, str)

    def __init__(self, parent, slot):
        super(InitThread, self).__init__(parent=parent)
        self.slot = slot

    def run(self):
        cmd = f'/usr/local/bin/enable_kis DUT0{self.slot} on'
        for i in range(2):
            return_code, stdout, stderr = RunShellWithTimeout(cmd, 70)
            print('return_code', return_code)
            print('**************stdout')
            print(stdout)
            print('**************stdout')
            print('**************stderr')
            print(stderr)
            print('**************stderr')
            if return_code == 0:
                f = re.search(f'cu.kis-\d*-ch-0', stderr)
                if f:
                    kis_port = f.group()
                    with open(f'/Users/gdlocal/Documents/readyDataVirGroup{self.slot-1}', 'w') as f:
                        f.write('/dev/'+kis_port)
                    self.result_signal.emit(True,
                                            f'Init Kis_Port success\nSerial Port Name: DUT0{self.slot}\nKis Port name: {kis_port}')
                    return
        self.result_signal.emit(False, f'Init Kis_Port failed\nSerial Port Name: DUT0{self.slot}\n')


class RunThread(QThread):
    test_value_signal = pyqtSignal(int, bool, str)
    test_result_signal = pyqtSignal(str)

    def __init__(self, parent, slot):
        super().__init__(parent)
        local_data.log = None
        self.slot = slot
        self.log_name = None
        self.mes_enable = False

    def set_args(self, log_file_name, mes_enable=False):
        self.log_name = log_file_name
        # set_log(local_data.log)
        self.mes_enable = mes_enable
        # print(local_data.log)

    def run(self):
        if not os.path.exists('/vault/log'):
            os.mkdir('/vault/log')
        log_path = '/vault/log/{}'.format(time.strftime("%Y-%m-%d"))
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        log = Log(f'{log_path}/{self.log_name}.log', 'Slot{}'.format(self.slot)).get_log()
        local_data.log = log
        local_data.index = 1
        local_data.sn = None
        local_data.slot = self.slot - 1
        # print('ssssssssss',local_data.slot)
        self.test_result_signal.emit('TEST')
        log.info('START TEST, PARSE PARAMETERS SUCCESSFULLY!')
        log.info('Load Test Plan Successfully! Test Plan as below:')
        for item in test_plan:
            log.info(str(item))
        self.main()
        if local_data.sn:
            os.rename(f'{log_path}/{self.log_name}.log',
                      f'{log_path}/{local_data.sn}-{time.strftime("%H-%M-%S")}-{self.log_name}.log')
        else:
            os.rename(f'{log_path}/{self.log_name}.log', f'{log_path}/{time.strftime("%H-%M-%S")}-{self.log_name}.log')

    def main(self):
        config = get_config()
        if config is None:
            local_data.log.error('Load Config Error!')
            self.test_result_signal.emit('FAIL')
            return
        result_dict = {'StartTime': time.strftime("%Y-%m-%d %H:%M:%S"), 'Site': "ITJX",
                       "Product": "B698", 'UnitNumber': 'None',
                       "SerialNumber": "None", 'SlotNumber': 1, 'WorkStationNumber': 1,
                       'Station ID': config['STATION_ID'],
                       'Version': config['GHLS_VERSION'],
                       'Test Pass/Fail Status': "PASS"}
        fail_list = {}
        IsSkip = False
        # 测试部分
        for i, item in enumerate(test_plan):
            try:
                if item['Mode'] == 'Special':
                    if IsSkip:
                        # self.test_value_signal.emit(i, False, "--FAIL--")
                        # time.sleep(0.1)
                        break
                    result, value = choose_function(item['TestItem'], *item['Input'])
                    self.test_value_signal.emit(i, result, value)
                    result_dict[item['TestItem']] = value
                    if not result:
                        IsSkip = True
                        result_dict['Test Pass/Fail Status'] = 'FAIL'
                        fail_list[item['TestItem']] = 'Upper:NA,Lower:NA,Value:{}'.format(value)
                elif item['Mode'] == 'Init':
                    result, value = choose_function(item['TestItem'], *item['Input'])
                    self.test_value_signal.emit(i, result, value)
                    result_dict[item['TestItem']] = value
                    if not result:
                        fail_list[item['TestItem']] = 'Upper:NA,Lower:NA,Value:FAIL'
                        result_dict['Test Pass/Fail Status'] = 'FAIL'
                time.sleep(0.1)
                i += 1
            except Exception as msg:
                IsSkip = True
                local_data.log.error("Test Item:" + item['TestItem'] + "\nError Message:" + str(msg))
                result_dict[item['TestItem']] = "--FAIL--"
                result_dict['Test Pass/Fail Status'] = 'FAIL'
                self.test_value_signal.emit(i, False, "--FAIL--")
                continue
        # 测试结束，发送退出信号
        for _ in range(3):
            try:
                result_dict['EndTime'] = time.strftime("%Y-%m-%d %H:%M:%S")
                result_dict['SerialNumber'] = local_data.sn
                write_csv('{}/{}.csv'.format('/vault/log', time.strftime("%Y-%m-%d")), result_dict)
                break
            except Exception as e:
                local_data.log.error("Write CSV Error:" + "\nError Message:{}".format(e))
                time.sleep(0.05)
        # 上传MES
        if self.mes_enable and local_data.sn:
            result_dict['List of Failing Tests'] = ';'.join(['{}:({})'.format(k, v) for k, v in fail_list.items()])
            update_mes(result_dict, config)
        if result_dict['Test Pass/Fail Status'] == 'FAIL':
            self.test_result_signal.emit('FAIL')
        else:
            self.test_result_signal.emit('PASS')
