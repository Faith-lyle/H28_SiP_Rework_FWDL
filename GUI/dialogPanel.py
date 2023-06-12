#!/usr/bin/python3
# -- coding: utf-8 --
# @Author : Long.Hou
# @Email : Long2.Hou@luxshare-ict.com
# @File : dialogPanel.py
# @Project : H28_SiP_Rework_FWDL
# @Time : 2023/6/12 08:51
# -------------------------------
import sys
import time

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QAbstractItemView, QTableWidgetItem, QPushButton, \
    QLabel, QFormLayout, QDialog
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
from GUI.UI.UI_Dialog import Ui_Dialog
from Tool.runThread import InitThread


class DialogPanel(QDialog, Ui_Dialog):

    def __init__(self, master=None):
        super(DialogPanel, self).__init__(parent=master)
        self.setupUi(self)
        self.buttonBox.setVisible(False)
        self.timer = QTimer(self)
        self.timer.start(500)
        self.timer.timeout.connect(self.timer_time_out_func)
        self.len = 3
        self.index = 0
        for i in range(1, 5):
            t = InitThread(self, i)
            t.result_signal.connect(self.show_result)
            t.start()

    def show_result(self, result, text):
        self.index += 1
        if result:
            color = '#00FF00'
        else:
            color = '#FF0000'
        html = f'''
        <div >
            <span>{time.strftime("%Y-%m-%d %H:%M:%S")}</span>
            <span style="color:	{color};">: {text}</span>
        </div>
        '''
        self.textEdit.append(html)
        if self.index == 4:
            self.label.setVisible(False)
            self.timer.stop()
            self.buttonBox.setVisible(True)

    def timer_time_out_func(self):
        if self.len == 3:
            self.len = 1
        else:
            self.len += 1
        self.label.setText("请等待" + '.' * self.len)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = DialogPanel()
    main.show()
    sys.exit(app.exec_())
