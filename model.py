"""
当前价格,总资产,
各个持有量,各个持有量占比,总占比,总占比要在800%以下,资金可以下调到700%,
数据包括连续,和分期,

"""
import os
import bisect
import datetime
from matplotlib.dates import date2num


class Contract:
    """
    一份期货合约,需要记录在当前日期下是否有效,需要当前日期下的交易价格
    到期合约要平仓
    要记录合约名,记录历史数据
    """

    def __init__(self, model, name, data):
        self.name = name
        self.data = data
        # 取出日期作为index,用来查询
        self.data_index = [item[0] for item in data]

        # 未开盘的返回None
        self.price = None
        # 设定日期
        self.current_date = 0

        # 绑定newday事件
        #model.event_newday.connect(lambda d: self._setDate(d))

        self.model = model

        # 持有量
        self.hold = 0
        self.hold_ratio = 0

        #标志是否结束平仓,方便ui删除相关widget
        self.over=False
        #是否绘制到matplot,暂时把这个放这里
        self.hidden=True
    def setDate(self, d):
        """
        设定当前日期确定价格,经常性的变动日期,会导致频繁的搜索,是不行的
        2018-01-02 17:01:43 Tue CST
        因为似乎不会有newday意外需要改日期的时候,所以事件绑定后,换成隐藏函数

        如果说设定日期超出,需要用最终日期平仓
        """
        start, end = self.getRange()
        if d < start:
            self.price = None
            self.vol=None
        else:
            index = bisect.bisect_left(self.data_index, d)
            self.price = self.data[index - 1][4]  # 返回收盘价
            self.vol= self.data[index - 1][5]  # 记录成交量方便看出主力盘
            self.position='%d / %d' % (index,len(self.data)) #记录周期的位置,方便看出结束时间

        self.current_date = d

        # 超出日期后自动平仓
        if d > end:
            self.over=True
            self.hidden=True
            if not self.hold == 0:
                model.cash += self.hold * self.price
                self.hold=0

    def getRange(self):
        """
        获取数据范围
        """
        return self.data[0][0], self.data[-1][0]

    def available(self):
        start, end = self.getRange()
        return start <= self.current_date <= end


class Investment:
    """
    现金和买入的合约
    """

    def __init__(self, contracts):
        # 现金
        self.cash = 10000
        # 持有量
        self.holds = {}
        # 各份合约的价格
        self.contracts = contracts

    def getCash(self):
        return self.cash

    def getHold(self, name):
        return self.holds.get(name, 0)

    def getAll(self, d):
        """
        计算时间周期d时期的总资产,
        """
        return sum([self.contracts[name].price * hold for name, hold in self.holds.items()]) + self.cash


from PySide import QtCore


class Model(QtCore.QObject):
    """
    监听事件的枢纽
    2018-01-02 16:57:32 Tue CST
    有一个问题是,我们不知道qt的事件,是否在emit的同时,同步完成所有触发
    否则可能导致代码执行顺序出错
    """
    # 新的一天.把日期作为参数放入?还是在其他地方存放呢?
    #event_newday = QtCore.Signal(int)
    #更新model之后,显示
    newdaydisplay = QtCore.Signal()

    cash = 10000

    def load_contracts(self):
        """
        从文件加载历史交易数据
        """

        p = os.path.expanduser('~/finance/czce/continue.txt')
        quotes = []
        for line in open(p):
            d, _open, high, low, close, vol = line.split()
            d = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:]))
            d = date2num(d)
            quotes.append((d, float(_open), float(high),
                           float(low), float(close), float(vol)))

        data = {'continue':  quotes}

        p = os.path.expanduser('~/finance/czce/all.txt')
        for line in open(p):
            d, name, _open, high, low, close, vol = line.split()
            d = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:]))
            d = date2num(d)
            if name not in data:
                data[name] = []
            data[name].append((d, float(_open), float(high),
                               float(low), float(close), float(vol)))

        for name in data:
            data[name] = Contract(self, name, data[name])
        self.contracts = data
        self.contracts['continue'].hidden=False
        # 显示的起始日期
        self.start_date, _ = data['continue'].getRange()
        # 显示的结束日期,取出continue的第20个周期
        self.end_date = self.start_date + 20
        # 最大显示日期
        self.max_date = self.end_date

        # 记录要显示到matplot的合约
        #self.show_contracts={'continue'}
    def newday(self):
        self.max_date+=1
        #分开以下两个事件,第一个更新model数据,数据更新完毕后,显示出来
        #self.event_newday.emit(self.max_date)
        for contract in self.contracts.values():
            contract.setDate(self.max_date)
        self.newdaydisplay.emit()

class Model1:
    """
    记录当前显示范围,显示合约
    """

    def __init__(self):
        p = os.path.expanduser('~/finance/czce/continue.txt')
        quotes = []
        for line in open(p):
            d, _open, high, low, close, vol = line.split()
            d = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:]))
            d = date2num(d)
            quotes.append((d, float(_open), float(high),
                           float(low), float(close), float(vol)))

        self.data = {'continue':  quotes}

        p = os.path.expanduser('~/finance/czce/all.txt')
        for line in open(p):
            d, name, _open, high, low, close, vol = line.split()
            d = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:]))
            d = date2num(d)
            data = self.data.get(name)
            if not data:
                data = []
                self.data[name] = data
            data.append((d, float(_open), float(high),
                         float(low), float(close), float(vol)))

        for name in self.data:
            self.data[name] = Contract(name, self.data[name])
        # 显示的起始日期
        self.start_date, _ = self.data['continue'].getRange()
        # 显示的结束日期,取出continue的第20个周期
        self.end_date = self.start_date + 20
        # 最大显示日期
        self.max_date = self.end_date

    def newday(self):
        """
        新加一日数据,同时更新价格,以及计算资产量
        这里不需要有跳过多日的api
        """
        self.max_date += 1
        self.end_date += 1
        #   item = self.data[self.max_index]
        #   self.current_price = item[4]
        # self.max_index += 1
        # delta = self.max_index - self.end_index
        # self.move_index(delta, delta)


        # self.label_current.setText('当前价格:%.2f,总资产:%.2f' % (
        # self.current_price,  self.cash + self.hold * self.current_price))
        # self.label_current.update()
        # self.update_invest()

#先用全局变量
model = Model()
model.load_contracts()
if '__main__' == __name__:
    d = Data()
