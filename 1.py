import sys
import os.path
import datetime
from PySide.QtGui import *
from chart import Chart


class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        layout = QHBoxLayout()
        self.chart=Chart(self)

        leftpanel = QVBoxLayout()
        leftpanel.addLayout(self.chart)
        self.init_rangepanel()
        leftpanel.addLayout(self.rangepanel)
        # leftpanel.addWidget(self.button)
        layout.addLayout(leftpanel)
        self.init_rightpanel()
        layout.addLayout(self.rightpanel)
        self.setLayout(layout)
        # self.init_data()



    def getData(self):
        return self.data[self.name]
    def init_rangepanel(self):
        # 范围控制面板
        self.rangepanel = QHBoxLayout()
        for fun in [
                lambda i:(i, 0),
                lambda i:(i, i),
                lambda i:(0, i), ]:
            lpanel = QVBoxLayout()
            l = QLabel('移动范围')
            l.setMaximumHeight(20)
            lpanel.addWidget(l)
            lspanel = QHBoxLayout()
            lpanel.addLayout(lspanel)
            for i in [-10, -5, -1, 1, 5, 10]:
                label = str(i) if i < 0 else '+' + str(i)
                btn = QPushButton(label)
                btn.setMinimumWidth(5)
                btn.clicked.connect(lambda j=i, f=fun: model.move_index(*f(j)))
                lspanel.addWidget(btn)

            self.rangepanel.addLayout(lpanel)

    def init_rightpanel(self):
        self.rightpanel = QVBoxLayout()
        # 占位空label
        self.rightpanel.addWidget(QLabel())


        asserts_view=AssetsView()

        self.contractsview = ContractsView()
        self.rightpanel.addLayout(self.contractsview)
        self.rightpanel.addWidget(asserts_view)


        btn = QPushButton('新的一天')
        btn.clicked.connect(self.newday)
        self.rightpanel.addWidget(btn)
    def newday(self):
        """
        新加一日数据,同时更新价格,以及计算资产量
        这里不需要有跳过多日的api
        """
        model.newday()


from model import model
from view import *

app = QApplication(sys.argv)

main = Window()

#调整字体大小
main.setStyleSheet(open('./app.css').read())
main.show()

sys.exit(app.exec_())
