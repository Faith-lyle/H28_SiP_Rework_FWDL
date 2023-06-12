#!/usr/bin/python3
# -- coding: utf-8 --
# @Author : Long.Hou
# @Email : Long2.Hou@luxshare-ict.com
# @File : serialPort.py
# @Project : H28_SiP_Rework_FWDL
# @Time : 2023/6/8 10:32
# -------------------------------
import serial
import time


class SerialPort:

    def __init__(self, port_name, log_driver):
        self.log_driver = log_driver
        self.port = serial.Serial(port_name, baudrate=921600, timeout=3)

    def send_and_read(self, cmd, timeout):
        self.send_cmd(cmd)
        time.sleep(timeout)
        res = self.read_all()
        time.sleep(0.1)
        return res

    def read_until(self, terminator, timeout, nextline_check=True):
        timeout_happen = False
        line = ""
        begin = time.time()
        while True:
            c = self.port.read_all().decode()
            if c:
                line += c
                if line.rfind(terminator) > 0:
                    if nextline_check:
                        if line.split('\n')[-1].strip() == ']':
                            break
                    else:
                        break
                time.sleep(0.005)
            if time.time() - begin > timeout:
                timeout_happen = True
                break
        if timeout_happen:
            timeout_content = '*' * 15 + '\ntimeout' + '\ntimeout\n' + '*' * 15
            line += timeout_content
            # raise RuntimeError("Error: timeout %s", line)
        return line

    def send_and_read_until(self, cmd, timeout=3, terminator='> '):
        self.send_cmd(cmd)
        content = self.read_until(terminator=terminator, timeout=timeout)
        self.log_driver.info("Receive Content:\n {}".format(content))
        return content

    def flush_out(self):
        self.port.flushInput()
        self.port.flushOutput()

    def send_cmd(self, cmd):
        if self.port.is_open:
            self.port.write(cmd.encode('utf-8'))    # 发送数据
            self.log_driver.info('Send Cmd: {}'.format(cmd))
            # self.log_driver.send_log(cmd)
        else:
            self.log_driver.info('Send Cmd: Cmd send error, port not open: {}'.format(self.port.name))

    def read_all(self):
        if self.port.is_open:
            try:
                res = self.port.read_all().decode('utf-8')
                self.log_driver.info("Receive Content:\n {}".format(res))
            except Exception as e:
                self.log_driver.info("Receive Content:\n Cmd send error %s, error message: {}".format(self.port.name, e))
                res = None
            return res

    def open_port(self):
        if not self.port.is_open:
            try:
                self.port.open()
                return True
            except Exception as e:
                self.log_driver.info('Send Error: Open serial port error: {},error:{}'.format(self.port.name,e))
                return False
        else:
            return True

    def close_port(self):
        if self.port.is_open:
            try:
                self.port.close()
                return True
            except:
                self.log_driver.info('Send Error: Close serial port error: {}'.format(self.port.name))
                return False
