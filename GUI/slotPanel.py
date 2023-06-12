import sys
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QAbstractItemView, QTableWidgetItem, QPushButton, \
    QLabel, QFormLayout
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
from GUI.UI.UI_slotPanel import Ui_Form
from GUI import style
from Tool import test_plan, runThread


class SlotPanel(QWidget, Ui_Form):
    def __init__(self, slot, config):
        super(SlotPanel, self).__init__()
        self.config = config
        self.mes = True
        self.bt_clear = QPushButton("Clear")
        self.bt_clear.clicked.connect(self.clear_count_qty)
        self.lb_result = QLabel('Wait')
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timer_timeout_func)
        # self.action_timer = QTimer(self)
        # self.action_timer.timeout.connect(self.action_timer_timeout_func)
        self.ui_init()
        self.setStyleSheet(style)
        self.run_thread = runThread.RunThread(self, slot+1)
        self.slot = slot
        self.signal_connect_slot()

    def signal_connect_slot(self):
        self.run_thread.test_value_signal.connect(self.response_thread_test_value_signal_slot)
        self.run_thread.test_result_signal.connect(self.show_result)

    def response_thread_test_value_signal_slot(self, index, result, value):
        color = 'lime' if result else 'red'
        self.add_value(index, 4, value, color)
        self.tabel_select_row(index+1)

    def table_view_init(self):
        herder = ["NO", "TestItem", "Upper", "Lower", "Value"]
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(len(test_plan))
        # 设置行头不可见
        self.tableWidget.verticalHeader().setVisible(False)
        # 设置不可编辑
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置只能选中行
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # 设置列头
        self.tableWidget.setHorizontalHeaderLabels(herder)
        # 设置列宽自动调整
        # self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 设置列宽根据文本内容调整
        # self.tableWidget.resizeColumnsToContents()
        # 设置每行的列宽
        for i, width in enumerate([30, 190, 60, 60, 80]):
            self.tableWidget.setColumnWidth(i, width)
        for x, items in enumerate(test_plan):
            # print(x,items)
            for y, text in enumerate(herder):
                try:
                    item = QTableWidgetItem(items[text])
                except KeyError:
                    item = QTableWidgetItem('')
                item.setTextAlignment(Qt.AlignCenter)
                self.tableWidget.setItem(x, y, item)
                # 设置单元格交叉颜色
                if x % 2 == 0:
                    item.setBackground(QColor('#E4E4E4'))
            # 设置行高为30
            self.tableWidget.setRowHeight(x, 20)

    def ui_init(self):
        self.setupUi(self)
        self.lb_result.setObjectName('lb_result')
        self.bt_clear.setObjectName('bt_clear')
        self.lb_result.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        # self.lb_ct.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.formLayout_2.setWidget(2, QFormLayout.SpanningRole, self.lb_result)
        self.formLayout.setWidget(4, QFormLayout.SpanningRole, self.bt_clear)
        self.table_view_init()
        self.add_pass_qty(0)
        self.add_fail_qty(0)

    def add_value(self, row, column, value, color):
        """
        添加数据到表格中
        :param row: 行号
        :param column: 列号
        :param value: 显示值
        :param color:  字体颜色
        :return:
        """
        Qitem = self.tableWidget.item(row, column)
        Qitem.setText(str(value))
        Qitem.setForeground(QColor(color))

    def tabel_select_row(self, row):
        """
        选择表格的某一行
        :param row: 行数
        :return: None
        """
        self.tableWidget.selectRow(row)

    def tabel_content_clear(self):
        """
        清除表格的测试数据，保留Item和upper、lower
        :return: None
        """
        for index in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(index, 4)
            item.setText('')

    def show_result(self, result):
        if result == 'PASS':
            self.timer.stop()
            self.lb_result.setText("PASS")
            self.lb_result.setStyleSheet('background-color:lime')
            self.pbt_start.setEnabled(True)
            self.add_pass_qty(1)
        elif result == "FAIL":
            self.timer.stop()
            self.lb_result.setStyleSheet("background-color: red;")
            self.lb_result.setText("FAIL")
            self.pbt_start.setEnabled(True)
            self.add_fail_qty(1)
        elif result == "TEST":
            self.lb_result.setStyleSheet("background-color: yellow;")
            self.lb_result.setText("TEST")
            self.pbt_start.setEnabled(False)

    def add_pass_qty(self, qty):
        self.config['passQty'] += qty
        self.label_5.setText(str(self.config['passQty']))
        total = self.config['passQty'] + self.config['failQty']
        if total != 0:
            self.label_8.setText("{:.2f}%".format(self.config['passQty'] / total * 100))
        else:
            self.label_8.setText("100.00%")

    def add_fail_qty(self, qty):
        self.config['failQty'] += qty
        self.label_6.setText(str(self.config['failQty']))
        total = self.config['passQty'] + self.config['failQty']
        if total != 0:
            self.label_8.setText("{:.2f}%".format(self.config['passQty'] / total * 100))
        else:
            self.label_8.setText("100.00%")

    def clear_count_qty(self):
        self.config['failQty'] = 0
        self.config['passQty'] = 0
        self.label_5.setText("0")
        self.label_6.setText("0")
        self.label_8.setText("100%")

    def timer_timeout_func(self):
        ct = float(self.lb_ct.text()) + 0.1
        self.lb_ct.setText('{:.1f}'.format(ct))

    def set_mes_enable(self):
        self.mes = True

    def set_mes_disable(self):
        self.mes = False

    @pyqtSlot()
    def on_pbt_start_clicked(self):
        # self.start_signal.emit(self.ed_sn.text().strip())
        self.lb_ct.setText('0.0')
        self.tabel_content_clear()
        self.timer.start(100)
        self.tabel_select_row(1)
        self.run_thread.set_args(f'SLOT{self.slot+1}', mes_enable=self.mes)
        self.run_thread.start()
