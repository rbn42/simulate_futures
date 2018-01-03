"""
当前价格,总资产,
各个持有量,各个持有量占比,总占比,总占比要在800%以下,资金可以下调到700%,
数据包括连续,和分期,

"""
import os
import bisect
import datetime
from matplotlib.dates import date2num
from PySide.QtCore import Signal, QObject


class Contract:
    """
    一份期货合约,需要记录在当前日期下是否有效,需要当前日期下的交易价格
    到期合约要平仓
    要记录合约名,记录历史数据
    """

    def __init__(self,  name, data):
        self.name = name
        self.data = data
        # 取出日期作为index,用来查询
        self.data_index = [item[0] for item in data]

        # 未开盘的返回None
        self.price = None
        # 设定日期
        self.current_date = 0

        # 持有量
        self.hold = 0
        self.hold_ratio = 0

        # 标志是否结束平仓,方便ui删除相关widget
        self.over = False
        # 是否绘制到matplot,暂时把这个放这里
        self.hidden = True

    def setDate(self, d):
        """
        设定当前日期确定价格,经常性的变动日期,会导致频繁的搜索,是不行的
        2018-01-02 17:01:43 Tue CST
        因为似乎不会有newday意外需要改日期的时候,所以事件绑定后,换成隐藏函数

        如果说设定日期超出,需要用最终日期平仓

        会需要随日期变动的,应该只有和price相关的,所以这里也可以理解为一个setPrice函数
        """
        start, end = self.getRange()
        if d < start:
            self.price = None
            self.vol = None
        else:
            index = bisect.bisect_left(self.data_index, d)
            self.price = self.data[index - 1][4]  # 返回收盘价
            self.vol = self.data[index - 1][5]  # 记录成交量方便看出主力盘
            # 记录周期的位置,方便看出结束时间
            self.position = '%d / %d' % (index, len(self.data))

        self.current_date = d

        # 超出日期后自动平仓
        if d > end:
            self.over = True
            self.hidden = True
            if not self.hold == 0:
                model.cash += self.hold * self.price
                self.hold = 0

    def update_limitation(self):
        """
        2018-01-03 06:56:51 Wed CST
        根据cash数量,设定最大,最小持有量
        这里要加入杠杆

        我们在这里设计一个简单的杠杆,但是应该只能用于多头
        因为我们在这里,允许持有量到达总资产的800%,也就是现金量到达总资产的-700%
        如果加入空头,总资产数目不会变,但是现金量会互相抵消.但是实际情况是,双方各需要维持一份独立的资产,限制现金占比在-700% 和 800% 之间,是不能互相抵消的.爆仓也因此是独立计算的.
        按照这样的体系来计算,将会需要和现实中一样,加入一个变量设定绑定的资金,这样就很麻烦了.
        既然空头用处不大,所以现在放弃空头,而使用以上这个简单的体系
        """
        min_cash_ratio = 1 - model.max_hold_ratio
        max_cash_ratio = 1 - model.min_hold_ratio
        cash_ratio = model.cash / model.assets

        self.min_hold = 0
        self.min_hold_ratio = 0

        if self.price is not None and self.price > 0:
            self.hold_ratio = self.hold * self.price / model.assets
            self.max_hold_ratio = self.hold_ratio + cash_ratio - min_cash_ratio
            self.max_hold = self.max_hold_ratio * model.assets / self.price
        else:
            self.max_hold = 0
            self.max_hold_ratio = 0
            self.hold_ratio = 0

    def getRange(self):
        """
        获取数据范围
        """
        return self.data[0][0], self.data[-1][0]

    def available(self):
        start, end = self.getRange()
        return start <= self.current_date <= end


class Model(QObject):
    """
    监听事件的枢纽
    2018-01-02 16:57:32 Tue CST
    有一个问题是,我们不知道qt的事件,是否在emit的同时,同步完成所有触发
    否则可能导致代码执行顺序出错
    """
    # 新的一天.把日期作为参数放入?还是在其他地方存放呢?
    #event_newday = Signal(int)
    # 更新model之后,显示
    event_newday_display = Signal()
    # 投资改变后的显示调整
    event_invest_display = Signal()
    # UI中chart显示范围的变动
    event_display_range = Signal()

    cash = 10000

    # 不允许空头,原因见上
    min_hold_ratio = 0
    max_hold_ratio = 8

    def invest(self, name):
        """
        除了name以外的,根据投资调整上限,另外还要调整cash.name自身跳过,不然会有死循环
        """

    def move_index(self,start_delta,end_delta):
        start_new = self.start_date+ start_delta
        end_new = self.end_date+ end_delta
        if end_new - start_new < 10:
            return
        if end_new - start_new > 100:
            return
        self.start_date= start_new
        self.end_date= end_new

        self.event_display_range.emit()


    def get_show_data(self):
        contract = self.contracts[self.show_contract]
        start_index = bisect.bisect_left(contract.data_index, self.start_date,)
        end_index = bisect.bisect_right(contract.data_index, self.end_date,)
        return contract.data[start_index:end_index]

    def calculate_assets(self):
        """
        计算总资产,在新的一天价格变动后进行计算.之后以这个总资产为依据调整各个合约的占比和现金
        """
        self.assets = self.cash
        for contract in self.contracts.values():
            if contract.available():
                self.assets += contract.price * contract.hold

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
            data[name] = Contract(name, data[name])
        self.contracts = data
        self.contracts['continue'].hidden = False
        # 显示的起始日期
        self.start_date, _ = data['continue'].getRange()
        # 显示的结束日期,取出continue的第20个周期
        self.end_date = self.start_date + 20
        # 最大显示日期
        self.max_date = self.end_date

        # 记录要显示到matplot的合约
        # self.show_contracts={'continue'}
        # 默认显示continue,现在只显示一个
        self.show_contract = 'continue'

    def newday(self):
        self.max_date += 1

        # 移动显示的区域
        delta = self.max_date - self.end_date
        self.start_date += delta
        self.end_date += delta

        # 分开以下两个事件,第一个更新model数据,数据更新完毕后,显示出来
        # self.event_newday.emit(self.max_date)
        for contract in self.contracts.values():
            contract.setDate(self.max_date)
        # 重新计算资产
        self.calculate_assets()
        # 计算总资产后调整允许持有范围
        for contract in self.contracts.values():
            contract.update_limitation()

        self.event_newday_display.emit()
        self.event_display_range.emit()


# 先用全局变量
model = Model()
model.load_contracts()
