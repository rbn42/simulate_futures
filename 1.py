import sys
import os.path
import datetime
from matplotlib.dates import date2num
import random
from PySide.QtGui import *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from matplotlib.finance import *


class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.init_data()
        self.init_invest()
        self.init_canvas()
        layout = QHBoxLayout()

        leftpanel = QVBoxLayout()
        leftpanel.addWidget(self.toolbar)
        leftpanel.addWidget(self.canvas)
        # 显示坐标的label,之后会加入价格
        # leftpanel.addWidget(self.statusbar_label)
        self.init_rangepanel()
        leftpanel.addLayout(self.rangepanel)
        # leftpanel.addWidget(self.button)
        layout.addLayout(leftpanel)
        self.init_rightpanel()
        layout.addLayout(self.rightpanel)
        self.setLayout(layout)
        # self.init_data()

    def init_invest(self):
        # 初始资金
        self.cash = 10000
        # 持有量
        self.hold = 0

    def update_invest(self):
        self.label_invest.setText('资金量:%.2f,持有量:%.2f' %
                                  (self.cash, self.hold, ))
        self.label_invest.update()

        self.update_ratio()

    def update_ratio(self):
        # 持有比例
        ratio = 100 * self.hold / (self.cash / self.current_price + self.hold)
        self.label_ratio.setText('持有比例:%.2f%%' % ratio)
        self.label_ratio.update()

    def buy(self, cash):
        if cash < 0:
            return
        # 在这里加入杠杆,换成总资产比例,杠杆为800%
        # if cash > self.cash:
        #    return
        _all = self.cash + self.hold * self.current_price
        if self.hold * self.current_price + cash > _all * 8:
            return
        self.cash -= cash
        self.hold += cash / self.current_price
        self.update_invest()

    def sell(self, hold):
        if hold < 0:
            return
        if hold > self.hold:
            return
        self.hold -= hold
        self.cash += hold * self.current_price
        self.update_invest()

    def getData(self):
        return self.data[self.name]

    def init_data(self):

        p = os.path.expanduser('~/finance/czce/continue.txt')
        quotes = []
        for line in open(p):
            d, _open, high, low, close, vol = line.split()
            d = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:]))
            d = date2num(d)
            quotes.append((d, float(_open), float(high),
                           float(low), float(close), float(vol)))

        p = os.path.expanduser('~/finance/czce/all.txt')
        self.data = quotes
        self.start_index = 0
        self.end_index = min(20, len(quotes))
        self.max_index = min(20, len(quotes))

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
                btn.clicked.connect(lambda j=i, f=fun: self.move_index(*f(j)))
                lspanel.addWidget(btn)

            self.rangepanel.addLayout(lpanel)

    def init_rightpanel(self):
        self.rightpanel = QVBoxLayout()
        # 占位空label
        self.rightpanel.addWidget(QLabel())


        self.label_current = QLabel()
        self.label_current.setMaximumHeight(20)
        self.label_invest = QLabel()
        self.label_invest.setMaximumHeight(20)

        self.contractsview = ContractsView()
        self.rightpanel.addLayout(self.contractsview)
        self.rightpanel.addWidget(self.label_current)
        self.rightpanel.addWidget(self.label_invest)

        invest_panel = QHBoxLayout()
        btn = QPushButton('买入100元')
        btn.clicked.connect(lambda: self.buy(100))
        invest_panel.addWidget(btn)
        btn = QPushButton('卖出1手')
        btn.clicked.connect(lambda: self.sell(1))
        invest_panel.addWidget(btn)
        self.rightpanel.addLayout(invest_panel)

        self.label_ratio = QLabel()
        self.label_ratio.setMaximumHeight(20)
        self.rightpanel.addWidget(self.label_ratio)
        spin = QDoubleSpinBox()
        self.rightpanel.addWidget(spin)

        self.label_displayrange = QLabel()
        self.label_displayrange.setMaximumHeight(20)
        self.rightpanel.addWidget(self.label_displayrange)

        btn = QPushButton('新的一天')
        btn.clicked.connect(self.newday)
        self.rightpanel.addWidget(btn)

    def init_canvas(self):
        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.ax2 = self.ax.twinx()
        self.canvas = FigureCanvas(self.figure)
        # self.plot()
        #self.button = QPushButton('显示')
        # self.button.clicked.connect(self.plot)
        self.toolbar = NavigationToolbar(self.canvas, self)

        #self.statusbar_label = QLabel()
        # self.statusbar_label.setFixedHeight(20)
        # self.toolbar.message.connect(self.statusbar_label.setText)
    def plot(self):
        ''' plot some random stuff '''
        # create an axis
        ax = self.ax
        # discards the old graph
        ax.clear()
        # plot data
        self._plot(ax)
        # refresh canvas
        self.canvas.draw()

    def move_index(self, start_delta, end_delta):
        """
        移动显示的范围
        """
        start_new = self.start_index + start_delta
        end_new = self.end_index + end_delta
        if start_new < 0:
            start_new = 0
        if end_new > self.max_index:
            end_new = self.max_index
        if end_new - start_new < 10:
            return
        if end_new - start_new > 100:
            return
        self.start_index = start_new
        self.end_index = end_new
        self.plot()

    def newday(self):
        """
        新加一日数据,同时更新价格,以及计算资产量
        这里不需要有跳过多日的api
        """
        if self.max_index < len(self.data):
            item = self.data[self.max_index]
            self.current_price = item[4]
            self.max_index += 1
            delta = self.max_index - self.end_index
            self.move_index(delta, delta)

            self.label_current.setText('当前价格:%.2f,总资产:%.2f' % (
                self.current_price,  self.cash + self.hold * self.current_price))
            self.label_current.update()
            self.update_invest()

            model.newday()

    def _plot(self, ax1):

        self.label_displayrange.setText(
            '显示范围: %d-%d / %d' % (self.start_index, self.end_index, self.max_index))

        data = self.data[self.start_index:self.end_index]
        ds, opens, closes, highs, lows, volumes = zip(*data)

        candles = candlestick2_ohlc(ax1, opens, closes, highs, lows,
                                    width=0.6, colorup='g')

        #candlestick_ohlc(ax1, quotes, width=1)
        # Add a seconds axis for the volume overlay
        ax2 = self.ax2
        ax2.clear()

        # Plot the volume overlay
        bc = volume_overlay(ax2, opens, closes, volumes,
                            colorup='black', alpha=0.1, width=1)
        ax2.add_collection(bc)


from model import model
from view import *

app = QApplication(sys.argv)

main = Window()

main.show()

sys.exit(app.exec_())
