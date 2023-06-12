#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Author  :   long.hou
@Email   :   long2.hou@luxshare-ict.com
@Ide     :   vscode & conda
@File    :   mainPanel.py
@Time    :   2023/06/06 14:21:52
'''

import sys
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QGroupBox,QDialog
from GUI.UI.Ui_mainPanel import Ui_MainWindow
from GUI.slotPanel import SlotPanel
from GUI.dialogPanel import DialogPanel


class MainPanel(QMainWindow, Ui_MainWindow):
    close_signal = pyqtSignal(dict)

    def __init__(self, config):
        super(MainPanel, self).__init__()
        self.config = config
        self.setupUi(self)
        self.slot_widget_list = []
        self.ui_init()
        self.setWindowTitle("H28 SiP FWDL")
        self.move(50, 50)
        self.resize(1250, 630)
        if self.config['MesEnabled']:
            [slot_widget.set_mes_enable() for slot_widget in self.slot_widget_list]
            self.setStyleSheet('.QFrame{background-color:#F7F7F7;}')
        else:
            self.setStyleSheet('.QFrame{background-color:rgb(200, 61, 34);}')
            [slot_widget.set_mes_disable() for slot_widget in self.slot_widget_list]


    def ui_init(self):
        slot = 0
        for widget in self.frame_2.children():
            if type(widget) == QGroupBox:
                slot_widget = SlotPanel(slot=slot, config=self.config['slot{}'.format(slot + 1)])
                self.slot_widget_list.append(slot_widget)
                horizontalLayout = QHBoxLayout(widget)
                horizontalLayout.setContentsMargins(5, 5, 5, 5)
                horizontalLayout.setSpacing(0)
                horizontalLayout.setObjectName("horizontalLayout")
                horizontalLayout.addWidget(slot_widget)
                slot += 1

    @pyqtSlot()
    def on_actionDisable_triggered(self):
        self.config['MesEnabled'] = False
        self.setStyleSheet('.QFrame{background-color:rgb(200, 61, 34);}')
        [slot_widget.set_mes_disable() for slot_widget in self.slot_widget_list]

    @pyqtSlot()
    def on_actionEnable_triggered(self):
        """
        PDCA 开启
        :return:
        """
        # self.lb_Pdca.setText("PDCA")
        [slot_widget.set_mes_enable() for slot_widget in self.slot_widget_list]
        self.config['MesEnabled'] = True
        self.setStyleSheet('.QFrame{background-color:#F7F7F7;}')

    @pyqtSlot()
    def on_actionEnable_kis_triggered(self):
        # print('kis')
        Dialog = DialogPanel(self)
        Dialog.exec()

    def closeEvent(self, a0):
        for i, slot in enumerate(self.slot_widget_list):
            self.config[f'slot{i + 1}'] = slot.config
        self.close_signal.emit(self.config)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = MainPanel()
    main.show()
    sys.exit(app.exec_())
