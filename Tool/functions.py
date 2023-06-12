#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   long.hou
@Email   :   long2.hou@luxshare-ict.com
@Ide     :   vscode & conda
@File    :   functions.py
@Time    :   2023/06/07 08:24:37
"""
import glob
import json
import os
import re
import subprocess
import time
from threading import Timer

import requests

from Tool import test_plan, serialPort
from Tool.Common import local_data

BASE_PATH = "/Users/gdlocal/Documents"


def get_config():
    config_path = '/vault/data_collection/test_station_config/gh_station_info.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    return config['ghinfo']


def testItem(func):
    def inner(*args, **kwargs):
        start_time = time.time()
        local_data.log.info(f'Step{local_data.index}  {func.__name__} Start ----------------------->')
        result = func(*args)
        local_data.log.info("Test Result:{}".format(result[1]))
        local_data.log.info('Elapsed Second:{:.2f}'.format(time.time() - start_time))
        local_data.log.info(f'Step{local_data.index}  {func.__name__} End <----------------------')
        local_data.index += 1
        return result

    return inner


def write_csv(file_name, result_dict):
    exist = True
    if not os.path.exists(file_name):
        exist = False
    herder = ['Site', 'Product', 'SerialNumber', 'UnitNumber', 'WorkStationNumber', 'SlotNumber', 'Station ID',
              'Test Pass/Fail Status',
              'StartTime', 'EndTime',
              'Version', 'List of Failing Tests']
    if not exist:
        herder0 = ['']
        herder1 = ['Upper Limit -->', '', '', '', '', '', '', '', '', '', '', '']
        herder2 = ['Lower Limit -->', '', '', '', '', '', '', '', '', '', '', '']
        herder3 = ['Measurement Unit -->', '', '', '', '', '', '', '', '', '', '', '']
    for item in test_plan:
        herder.append(item['TestItem'])
        if not exist:
            herder0.append(' ')
            herder1.append(item['Upper'])
            herder2.append(item['Lower'])
            herder3.append(item['Unit'])
    if not exist:
        with open(file_name, 'w') as csvfile:
            csvfile.write(','.join(herder) + '\n')
            csvfile.write(','.join(herder0) + '\n')
            csvfile.write(','.join(herder1) + '\n')
            csvfile.write(','.join(herder2) + '\n')
            csvfile.write(','.join(herder3) + '\n')
            # writer = csv.writer(csvfile)
            # writer.writerow(herder)
            # writer.writerow(herder0)
            # writer.writerow(herder1)
            # writer.writerow(herder2)
            # writer.writerow(herder3)
    data = []
    for test_item in herder:
        if test_item in result_dict.keys():
            data.append('{}'.format(result_dict[test_item]).replace(',', ' '))
        else:
            data.append('')
    with open(file_name, 'a') as csvfile:
        # writer = csv.writer(csvfile)
        # writer.writerow(data)
        csvfile.write(','.join(data) + '\n')


def RunShellWithTimeout(cmd, timeout=3):
    local_data.log.info("Run Cmd : {} timeout:{}".format(cmd, timeout))
    def process_timeout(process):
        process.kill()
        local_data.log.error("Run Cmd Timeout!")

    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timer = Timer(timeout, process_timeout, [p])  # 设置定时器计算超时时间，超时杀死此线程
    try:  # 尝试运行，出错不停止
        timer.start()
        stdout, stderr = p.communicate()  # 读取终端返回的内容，stdout为返回正常内容。stderr为出错内容
        return_code = p.returncode  # 获取终端返回值，正常返回值为0，异常为其它
        stdout = stdout.decode(errors='ignore')
        stderr = stderr.decode(errors='ignore')
        local_data.log.info("return_code:***********************{}".format(return_code))
        local_data.log.info("stdout:***********stdout*************\n{}\n***********stdout**********".format(stdout))
        local_data.log.info("stderr:************stderr************\n{}\n***********stderr**********".format(stderr))
        return return_code, stdout, stderr
    finally:
        timer.cancel()


@testItem
def Check_Grassninja(*args):
    result = False, "--FAIL--"
    # print('fffffff', local_data.slot)
    try:
        dir_list = [
            '{}/DFU_FWDL_Folders0{}/grassninja/'.format(BASE_PATH, local_data.slot),
            '{}/DFU_FWDL_Folders0{}/goldrestore_fixture.sh'.format(BASE_PATH, local_data.slot),
            '{}/readyDataPysGroup{}'.format(BASE_PATH, local_data.slot),
            '{}/readyDataVirGroup{}'.format(BASE_PATH, local_data.slot)
        ]
        exists_flag = True
        for dir_name in dir_list:
            if not os.path.exists(dir_name):
                exists_flag = False
                local_data.log.error('File not exist,File path:{}'.format(dir_name))
        if exists_flag:
            with open(dir_list[2], 'r') as f:
                serial_port = f.read().strip()
                local_data.log.info('Get Value: serial port,{}'.format(serial_port))
                local_data.serial_port = serial_port
            with open(dir_list[3], 'r') as f:
                kis_port = f.read().strip()[:-1] + '2'
                local_data.log.info('Get Value: Kis port,{}'.format(kis_port))
                local_data.kis_port = kis_port
            result = True, "--PASS--"
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result


@testItem
def FW_Flash(*args):
    result = False, "--FAIL--"
    # 调用终端执行cmd并获取输出内容
    try:
        cmd = "/bin/sh {}/DFU_FWDL_Folders0{}/goldrestore_fixture.sh".format(BASE_PATH, local_data.slot)
        for _ in range(2):
            return_code, stdout, stderr = RunShellWithTimeout(cmd, 180)
            if return_code != 0:
                continue
            if 'SN1234567: success' in stdout:
                local_data.log.info('Get Value: SN1234567: success')
                result = True, "--PASS--"
                break
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    # result = True, "--PASS--"
    return result


@testItem
def open_serial_port(*args):
    result = False, "--FAIL--"
    try:
        term = serialPort.SerialPort(local_data.kis_port, log_driver=local_data.log)
        time.sleep(0.1)
        term.flush_out()
        local_data.term = term
        result = True, "--PASS--"
        local_data.log.info(
            "Get Value: Open Serial Port Successful! Port:{} Baudrate:921600".format(local_data.kis_port))
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result


@testItem
def close_serial_port(*args):
    result = False, '--FAIL--'
    if local_data.term:
        try:
            local_data.term.flush_out()
            time.sleep(0.1)
            local_data.term.close_port()
            result = True, '--PASS--'
            local_data.log.info('Get Value: Close Successful! Port:{}'.format(local_data.kis_port))
        except Exception as e:
            local_data.log.error("Error msg:{}".format(e))
    return result


@testItem
def create_grassninja_port(*args):
    result = False, "--FAIL--"
    # 调用终端执行cmd并获取输出内容
    try:
        cmd = f"/usr/local/bin/python3 {BASE_PATH}/DFU_FWDL_Folders0{local_data.slot}/grassninja/" \
              f"grassninja.py -p {local_data.serial_port} -s on "

        for _ in range(2):
            return_code, stdout, stderr = RunShellWithTimeout(cmd, 10)
            if return_code != 0:
                continue
            stime = time.time()
            while 1:
                port_list = glob.glob("/dev/cu.kis-*-ch-2")
                if time.time() - stime > 5:
                    result = False, "--FAIL--"
                    break
                if local_data.kis_port in port_list:
                    result = True, "--PASS--"
                    break
                time.sleep(0.5)
            local_data.log.info("List Serial Port:\n******kis_port*********\n{}\n***********kis_port***********".format(
                '\n'.join(port_list)))
            local_data.log.info("Target Serial Port:{}".format(local_data.kis_port))
            if result[0]:
                break
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result


@testItem
def close_grassninja(*args):
    result = False, "--FAIL--"
    try:
        cmd = "/usr/local/bin/python3 {}/DFU_FWDL_Folders0{}/grassninja/gn_kis_fwdl.py -p {} -s off".format(
            BASE_PATH,
            local_data.slot,
            local_data.serial_port)
        for i in range(2):
            return_code, stdout, stderr = RunShellWithTimeout(cmd, 30)
            if 'KIS FWDL path disabled' in stdout:
                local_data.log.info('Get Value: KIS FWDL path disabled')
                break
            else:
                time.sleep(0.5)
        result = True, "--PASS--"
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result


@testItem
def read_product_mlb(*args):
    result = False, "--FAIL--"
    try:
        for i in range(3):
            output = local_data.term.send_and_read_until("syscfg print MLB#\n", timeout=1)
            if '> syscfg:ok' in output:
                flag = re.findall(r'syscfg:ok "(.*)?"', output)
                if len(flag) == 1:
                    result = True, flag[0]
                    local_data.sn = flag[0]
                    local_data.log.info('Get Value: {}'.format(flag[0]))
                    break
            else:
                local_data.term.flush_out()
                local_data.log.info('Get Value: Read MLB# Failed')
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result


# 读取产品FW
@testItem
def read_product_fw(*args):
    result = False, "--FAIL--"
    try:
        for i in range(3):
            output = local_data.term.send_and_read_until("ft version\n", timeout=2)
            if '> ft:ok' in output:
                flag = re.findall(r'ft:ok (.*)?\n', output)
                if len(flag) == 1:
                    result = True, flag[0]
                    local_data.log.info('Get Value: {}'.format(flag[0]))
                    break
            else:
                local_data.term.flush_out()
                local_data.log.info('Get Value: None')
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result


@testItem
def mic1_init(*args):
    result = False, "--FAIL--"
    fail_flag = False
    output = ''
    mic1_cmd = [
        'allen configure zor\n',
        'audio config mic1 memory record 16kHz 768kHz 10\n',
        'audio start 0\n',
        'audio stop\n']
    try:
        for cmd in mic1_cmd:
            text = local_data.term.send_and_read_until(cmd, timeout=2)
            output += text
            if 'ok' in text:
                result = True, "PASS"
                local_data.log.info('Get Value: OK')
            else:
                fail_flag = True
                local_data.log.info('Get Value: None')
            local_data.term.flush_out()
    except Exception as e:
        fail_flag = True
        local_data.log.error("Error msg:{}".format(e))
    if fail_flag:
        result = False, "--FAIL--"
    return result


@testItem
def mic2_init(*args):
    result = False, "--FAIL--"
    fail_flag = False
    output = ''
    mic2_cmd = [
        'allen configure zor\n',
        'audio config mic2 memory record 16kHz 768kHz 10\n',
        'audio start 0\n',
        'audio stop\n']
    try:
        for cmd in mic2_cmd:
            text = local_data.term.send_and_read_until(cmd, timeout=2)
            output += text
            if 'ok' in text:
                result = True, "PASS"
                local_data.log.info('Get Value: OK')
            else:
                fail_flag = True
                local_data.log.info('Get Value: None')
            local_data.term.flush_out()
    except Exception as e:
        fail_flag = True
        output += str(e)
        local_data.log.error("Error msg:{}".format(e))
    if fail_flag:
        result = False, "--FAIL--"
    return result


@testItem
def mic1_test(*args):
    result = False, "--FAIL--"
    value = 0
    try:
        output = local_data.term.send_and_read_until("audio dump\n", timeout=5)
        if 'audio:ok' in output:
            results = output.split(":")
            for res in results[-41:-1]:
                for a in range(3):
                    ok1 = res[a * 16: (a + 1) * 16]
                    ok2 = res[(a + 1) * 16:(a + 2) * 16]
                    if ok1 == ok2:
                        value += 1
            if value < 80:
                result = True, "--PASS--"
                local_data.log.info('Get Value: {}'.format(str(value)))
            else:
                local_data.log.info('Get Value: {}'.format(str(value)))
        else:
            local_data.log.info('Get Value: None')
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result


@testItem
def mic2_test(*args):
    result = False, "--FAIL--"
    output = ''
    value = 0
    try:
        output += local_data.term.send_and_read_until("audio dump\n", timeout=5)
        if 'audio:ok' in output:
            results = output.split(":")
            for res in results[-41:-1]:
                for a in range(3):
                    ok1 = res[a * 16: (a + 1) * 16]
                    ok2 = res[(a + 1) * 16:(a + 2) * 16]
                    if ok1 == ok2:
                        value += 1
            if value < 80:
                result = True, "--PASS--"
                local_data.log.info('Get Value: {}'.format(str(value)))
            else:
                local_data.log.info('Get Value: {}'.format(str(value)))
        else:
            local_data.log.info('Get Value: None')
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result
@testItem
def otp_check(*args):
    result = False, "--FAIL--"
    try:
        for i in range(3):
            output = local_data.term.send_and_read_until("ft dump otp 0x1f24 1\n", timeout=2)
            if '> ft:ok' in output:
                flag = re.findall(r'ft:ok (.*)?\n', output)
                if len(flag) == 1:
                    local_data.log.info('Get Value: {}'.format(flag[0]))
                    if flag[0].strip() == '0x00010000':
                        result = True, flag[0]
                        break
                    else:
                        result = False, flag[0]
                else:
                    local_data.log.info('Get Value: {}'.format(len(flag)))
            else:
                local_data.term.flush_out()
                local_data.log.info('Get Value: None')
    except Exception as e:
        local_data.log.error("Error msg:{}".format(e))
    return result

@testItem
def update_mes(test_data, mes_config):
    result = False, "--FAIL--"
    try:
        data = {'result': test_data['Test Pass/Fail Status'], 'audio': 0, 'start_time': test_data['StartTime'],
                'stop_time': test_data['EndTime'], 'sn': test_data['SerialNumber'],
                'fixture_id': test_data['UnitNumber'], 'test_head_id': test_data['SlotNumber'],
                'list_of_failing_tests': test_data['List of Failing Tests'], 'c': 'ADD_RECORD',
                'failure_message': test_data['List of Failing Tests'].split(';')[0],
                'test_station_name': mes_config['GH_STATION_NAME'],
                'station_id': mes_config['STATION_ID'], 'product': mes_config['PRODUCT'],
                'sw_version': mes_config['GHLS_VERSION'], 'mac_address': mes_config['MAC']}
    except Exception as e:
        local_data.log.error(f"{'-' * 20}\nFunction:update_mes,Error Message:{e}")
        return result

    try:
        for i in range(3):
            response = requests.post(url=mes_config['SFC_URL'], data=data, timeout=3)
            local_data.log.info(f"{'-' * 20}\nFunction:update_mes\nRequest URL:{mes_config['SFC_URL']}\nRequest Method: POST\nRequest "
                                f"Date:{data}\n Response Status Code:{response.status_code}\nResponse Text:{response.text}")
            if response.status_code == 200:
                if "SFC_OK" in response.text:
                    local_data.log.info('Get Value: {}'.format(str(response.text)))
                    result = True, "--PASS--"
                    break
                else:
                    local_data.log.info('Get Value: {}'.format(str(response.text)))
            time.sleep(0.1)
    except Exception as e:
        msg = f"{'-' * 20}\nFunction:update_mes\nRequest URL:{mes_config['SFC_URL']}\nRequest Method: POST\nRequest " \
              f"Date:{data}\n Error Message:{e} "
        local_data.log.error(msg)
    return result


def choose_function(func_name, *args):
    return eval(f'{func_name}({args})')
