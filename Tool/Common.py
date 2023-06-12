#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Author  :   long.hou
@Email   :   long2.hou@luxshare-ict.com
@Ide     :   vscode & conda
@File    :   Common.py
@Time    :   2023/06/06 14:22:32
'''

import datetime
import logging, threading
import os
from os import path

DEBUG = True


class ConsolePanelHandler(logging.Handler):

    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.parent = parent

    def emit(self, record):
        """输出格式可以按照自己的意思定义HTML格式"""
        record_dict = record.__dict__
        asctime = record_dict['asctime'] + " >> "
        line = record_dict['filename'] + " -> line:" + str(record_dict['lineno']) + " | "
        pid = f"(pid: {+record_dict['process']},tid: {record_dict['thread']})"
        levelname = record_dict['levelname']
        message = record_dict['message'].replace('\n', '<br>')
        if levelname == 'ERROR':
            color = "#FF0000"
        elif levelname == 'WARNING':
            color = "#FFD700"
        else:
            color = "#008000"
        html = f'''
        <div >
            <span>{asctime}</span>
            <span style="color:#4e4848;">{line}</span>
            <span style="color: {color};">{levelname}</span>
            <span style="color:	#696969;">: {message}</span>
        </div>
        '''
        self.parent.write(html)  # 将日志信息传给父类 write 函数 需要在父类定义一个write函数


class Log:
    def __init__(self,file_name,name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level=20)
        file_log = logging.FileHandler(file_name, encoding='utf-8',mode='w')
        formatter = logging.Formatter(
            '%(name)s %(asctime)s >> (pid: %(process)s,tid: %(thread)s (%(filename)s[line:%(lineno)d]) | %(levelname)s: %('
            'message)s')
        file_log.setFormatter(formatter)
        self.logger.addHandler(file_log)
        if DEBUG:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

    def set_file_log_path(self, file_path):
        for hand in self.logger.handlers:
            if type(hand) == logging.FileHandler:
                self.logger.removeHandler(hand)
        file_log = logging.FileHandler(file_path, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s >> (pid: %(process)s,tid: %(thread)s <%(filename)s [line:%(lineno)d]> | %(levelname)s: %('
            'message)s ')
        file_log.setFormatter(formatter)
        self.logger.addHandler(file_log)

    def get_log(self):
        return self.logger


# logger = Log().get_log()  # 全局能访问
local_data = threading.local()



