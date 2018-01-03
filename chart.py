from PySide.QtGui import *
import os.path
import numpy as np
import datetime
from matplotlib.dates import date2num
from matplotlib.dates import num2date
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.finance import *

from model import model

from matplotlib.dates import DateFormatter, WeekdayLocator,\
    DayLocator, MONDAY


mondays = WeekdayLocator(MONDAY)        # major ticks on the mondays
alldays = DayLocator()              # minor ticks on the days
weekFormatter = DateFormatter('%m-%d')  # e.g., Jan 12
dayFormatter = DateFormatter('%d')      # e.g., 12


class Chart(QVBoxLayout):

    def __init__(self, parentwindow, parent=None):
        super(Chart, self).__init__(parent)
        self.parent = parentwindow

        self.init_canvas()
        self.addWidget(self.toolbar)
        self.addWidget(self.canvas)
        # 显示坐标的label,之后会加入价格
        # leftpanel.addWidget(self.statusbar_label)

        self.label_displayrange = QLabel()
        self.label_displayrange.setMaximumHeight(20)
        self.addWidget(self.label_displayrange)

        model.event_display_range.connect(self._update)


    def init_canvas(self):
        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.ax2 = self.ax.twinx()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.parent)

        #self.statusbar_label = QLabel()
        # self.statusbar_label.setFixedHeight(20)
        # self.toolbar.message.connect(self.statusbar_label.setText)

    def _update(self):
        """
        绑定到model中显示范围改变的事件
        """
        data = model.get_show_data()
        self.plot(data)

    def plot(self, data):
        ax1 = self.ax
        ax1.clear()
        ax2 = self.ax2
        ax2.clear()

        self.ax.xaxis.set_major_locator(mondays)
        self.ax.xaxis.set_minor_locator(alldays)
        self.ax.xaxis.set_major_formatter(weekFormatter)

        d1=num2date(model.start_date).strftime('%Y-%m-%d')
        d2=num2date(model.end_date).strftime('%Y-%m-%d')
        d3=num2date(model.max_date).strftime('%Y-%m-%d')
        n=model.show_contract
        self.label_displayrange.setText(
                '从%s到%s,现在时间:%s,显示的合约:%s' %  (d1,d2,d3,n))

        candles = candlestick_ohlc(ax1, [item[:5] for item in data],
                                   width=0.6, colorup='g')

        """
        2018-01-03 09:28:38 Wed CST
        volume_overlay不可靠,所以自己画
        """

        dates = [x[0] for x in data]
        dates = np.asarray(dates)
        volume = [x[5] for x in data]
        volume = np.asarray(volume)

        ax2.plot(dates, volume, color='gray')

        self.canvas.draw()
