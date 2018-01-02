from model import model
from PySide.QtGui import *


class ContractButton(QPushButton):
    def __init__(self, name):
        super(ContractButton, self).__init__(name)
        self.setCheckable(True)
        if not model.contracts[name].hidden:
            self.setChecked(True)
        self.clicked.connect(self.click)
        self.name = name

    def click(self):
        model.contracts[name].hidden = not self.isChecked()


class ContractsView(QVBoxLayout):
    """在这里更新contracts相关的信息
    """

    def __init__(self, parent=None):
        super(ContractsView, self).__init__(parent)
        self.contractviews = {name: ContractView(
            contract) for name, contract in model.contracts.items()}

        model.newdaydisplay.connect(self.update_contractsview)
        # self.update()

    def update_contractsview(self):
        """
        更新显示contract信息
        """

        for view in self.contractviews.values():
            view.setParent(None)

        namelist = [n for n in self.contractviews]
        namelist.sort()
        for name in namelist:
            if model.contracts[name].available():
                self.contractviews[name].update_view()
                self.addLayout(self.contractviews[name])
            elif model.contracts[name].over:
                # 删除widget
                w = self.contractviews.pop(name)
                w.destroy()


class ContractView(QHBoxLayout):
    """这里显示单独一条Contract"""

    def __init__(self, contract, parent=None):
        super(ContractView, self).__init__(parent)
        self.name = ContractButton(contract.name)
        self.price = QLabel()
        self.hold = QDoubleSpinBox()
        self.hold.setPrefix('$')
        self.hold_ratio = QDoubleSpinBox()
        self.hold_ratio.setSuffix('%')
        self.vol = QLabel()
        self.position = QLabel()

        self.addWidget(self.name)
        self.addWidget(self.price)
        self.addWidget(self.vol)
        self.addWidget(self.hold)
        self.addWidget(self.hold_ratio)
        self.addWidget(self.position)

        self.contract = contract

        self.hold.valueChanged.connect(self.change_hold)
        self.hold_ratio.valueChanged.connect(self.change_hold_ratio)
    def change_hold(self,value):
        """
        通过setValue也会触发这里,但是如果数值不变,就不会有问题.但是有小数的情况下,或许会出现死循环?
        为了避免死循环,可以在这里传入name参数,跳过这个spinbox不变动
        """
        print(value)
    def change_hold_ratio(self,value):
        print(value)

    def update_view(self):
        self.price.setText('$%.2f' % self.contract.price)
        self.hold.setValue(self.contract.hold)
        self.hold_ratio.setValue(self.contract.hold_ratio)
        self.vol.setText('%d' % self.contract.vol)
        self.position.setText(self.contract.position)
        self.price.update()
        self.hold.update()
        self.vol.update()
        self.position.update()

    def destroy(self):
        self.price.deleteLater()
        self.hold.deleteLater()
        self.hold_ratio.deleteLater()
        self.vol.deleteLater()
        self.name.deleteLater()
        self.position.deleteLater()
