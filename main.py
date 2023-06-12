#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Author  :   long.hou
@Email   :   long2.hou@luxshare-ict.com
@Ide     :   vscode & conda
@File    :   main.py
@Time    :   2023/06/06 14:18:02
'''
import os
import plistlib
import sys
from GUI.mainPanel import MainPanel
from PyQt5.QtWidgets import QApplication, QMainWindow

BASE_DIR = os.getcwd().replace('\\', '/')


def read_plist(file_path):
    with open(file_path, 'rb') as f:
        pl = plistlib.load(f)
    return pl


def save_plist(data):
    with open('{}/Config/config.plist'.format(BASE_DIR), 'wb') as f:
        plistlib.dump(data, f)


def close(data):
    save_plist(data)


if __name__ == "__main__":
    config = read_plist('{}/Config/config.plist'.format(BASE_DIR))
    # print(config)
    app = QApplication(sys.argv)
    main = MainPanel(config)
    main.close_signal.connect(close)
    main.show()
    sys.exit(app.exec_())
