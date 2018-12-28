# encoding: UTF-8

from __future__ import division

import os
from collections import OrderedDict

from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE,
                                    PRICETYPE_LIMITPRICE, PRICETYPE_MARKETPRICE,
                                    STATUS_REJECTED, STATUS_CANCELLED, STATUS_ALLTRADED)
from vnpy.trader.uiQt import QtWidgets
from vnpy.trader.app.algoTrading.algoTemplate import AlgoTemplate
from vnpy.trader.app.algoTrading.uiAlgoWidget import AlgoWidget, QtWidgets

from six import text_type


STATUS_FINISHED = set([STATUS_ALLTRADED, STATUS_CANCELLED, STATUS_REJECTED])

from tdexApi import Tdex
import json

REST_HOST = 'https://tl.tdex.com/openapi/v1'
base_dir = os.path.join(os.getcwd())
filePath = os.path.join(base_dir, 'TDEX_connect.json')

f = file(filePath)
setting = json.load(f)

apiKey = str(setting['apiKey'])
apiSecret = str(setting['apiSecret'])
# print(apiKey, apiSecret)

options = {
    'apiKey': apiKey,
    'apiSecret': apiSecret,
    'url': REST_HOST,
}

tdex = Tdex(options)

########################################################################
class DmaAlgo(AlgoTemplate):
    """DMA算法，直接发出限价或者市价委托"""
    
    templateName = u'DMA 直接委托'

    #----------------------------------------------------------------------
    def __init__(self, engine, setting, algoName):
        """Constructor"""
        super(DmaAlgo, self).__init__(engine, setting, algoName)
        
        # 参数，强制类型转换，保证从CSV加载的配置正确
        self.vtSymbol = str(setting['vtSymbol'])            # 合约代码
        self.direction = text_type(setting['direction'])    # 买卖
        self.offset = text_type(setting['offset'])          # 开平
        self.priceType = text_type(setting['priceType'])    # 价格类型
        self.price = float(setting['price'])                # 价格
        self.totalVolume = float(setting['totalVolume'])    # 数量
        
        self.vtOrderID = ''     # 委托号
        self.tradedVolume = 0   # 成交数量
        self.orderStatus = ''   # 委托状态
        if self.vtSymbol == 'BTCUSD.TDEX':
            self.vtSymbol = 'XBTUSD.BITMEX'
        self.subscribe(self.vtSymbol)
        self.paramEvent()
        self.varEvent()
    
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """"""
        # 发出委托
        print('发出dma委托')
        if not self.vtOrderID:
            dataBuy = {}
            if self.direction == DIRECTION_LONG:
                # func = self.buy
                if self.priceType == '限价':
                    dataBuy = {
                        'cid': 1,
                        'side': 0,
                        'scale': 20,
                        'volume': int(self.totalVolume),
                        'visible': -1,
                        'price': int(self.price),
                    }
                else:
                    dataBuy = {
                        'cid': 1,
                        'side': 0,
                        'scale': 20,
                        'volume': int(self.totalVolume),
                        'visible': -1,
                    }
                resBuy = tdex.futuresOpen(dataBuy)
                print(resBuy)
                if resBuy['status'] == 0:
                    self.writeLog(u'委托买入%s，数量%s，价格%s' % (self.vtSymbol, self.totalVolume, self.price))
                    self.stop()
            else:
                # func = self.sell
                if self.priceType == '限价':
                    dataSell = {
                        'cid': 1,
                        'side': 1,
                        'scale': 20,
                        'volume': self.totalVolume,
                        'visible': -1,
                        'price': int(self.price),
                    }
                else:
                    dataSell = {
                        'cid': 1,
                        'side': 1,
                        'scale': 20,
                        'volume': self.totalVolume,
                        'visible': -1,
                    }
                resSell = tdex.futuresOpen(dataSell)
                print(resSell)
                if resSell['status'] == 0:
                    self.writeLog(u'委托卖出%s，数量%s，价格%s' % (self.vtSymbol, str(self.totalVolume), self.price))
                    self.stop()

            # self.vtOrderID = func(self.vtSymbol, self.price, self.totalVolume,
            #                       self.priceType, self.offset)

        # 更新变量
        self.varEvent()
        
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """"""
        pass
    
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """"""
        self.tradedVolume = order.tradedVolume
        self.orderStatus = order.status
        
        if self.orderStatus in STATUS_FINISHED:
            self.stop()
        
        self.varEvent()
    
    #----------------------------------------------------------------------
    def onTimer(self):
        """"""
        pass
        
    #----------------------------------------------------------------------
    def onStop(self):
        """"""
        self.writeLog(u'停止算法')
        self.varEvent()
        
    #----------------------------------------------------------------------
    def varEvent(self):
        """更新变量"""
        d = OrderedDict()
        d[u'算法状态'] = self.active
        d[u'委托号'] = self.vtOrderID
        d[u'成交数量'] = self.tradedVolume
        d[u'委托状态'] = self.orderStatus
        d['active'] = self.active
        self.putVarEvent(d)
    
    #----------------------------------------------------------------------
    def paramEvent(self):
        """更新参数"""
        d = OrderedDict()
        if self.vtSymbol == 'XBTUSD.BITMEX':
            self.vtSymbol = 'BTCUSD.TDEX'
        d[u'代码'] = self.vtSymbol
        d[u'方向'] = self.direction
        d[u'价格'] = self.price
        d[u'数量'] = self.totalVolume
        d[u'价格类型'] = self.priceType
        # d[u'开平'] = self.offset
        self.putParamEvent(d)


########################################################################
class DmaWidget(AlgoWidget):
    """"""
    
    #----------------------------------------------------------------------
    def __init__(self, algoEngine, parent=None):
        """Constructor"""
        super(DmaWidget, self).__init__(algoEngine, parent)
        
        self.templateName = DmaAlgo.templateName
        
    #----------------------------------------------------------------------
    def initAlgoLayout(self):
        """"""
        self.lineSymbol = QtWidgets.QLineEdit()
        
        self.comboDirection = QtWidgets.QComboBox()
        self.comboDirection.addItem(DIRECTION_LONG)
        self.comboDirection.addItem(DIRECTION_SHORT)
        self.comboDirection.setCurrentIndex(0)
        
        self.spinPrice = QtWidgets.QDoubleSpinBox()
        self.spinPrice.setMinimum(0)
        self.spinPrice.setMaximum(1000000000)
        self.spinPrice.setDecimals(8)
        
        self.spinVolume = QtWidgets.QDoubleSpinBox()
        self.spinVolume.setMinimum(0)
        self.spinVolume.setMaximum(1000000000)
        self.spinVolume.setDecimals(6)
        
        self.comboPriceType = QtWidgets.QComboBox()
        self.comboPriceType.addItems([PRICETYPE_LIMITPRICE, PRICETYPE_MARKETPRICE])
        self.comboPriceType.setCurrentIndex(0)
        
        self.comboOffset = QtWidgets.QComboBox()
        self.comboOffset.addItems(['', OFFSET_OPEN, OFFSET_CLOSE])
        self.comboOffset.setCurrentIndex(0)
        
        buttonStart = QtWidgets.QPushButton(u'启动')
        buttonStart.clicked.connect(self.addAlgo)
        buttonStart.setMinimumHeight(100)
        
        Label = QtWidgets.QLabel
        
        grid = QtWidgets.QGridLayout()
        grid.addWidget(Label(u'代码'), 0, 0)
        grid.addWidget(self.lineSymbol, 0, 1)
        grid.addWidget(Label(u'方向'), 1, 0)
        grid.addWidget(self.comboDirection, 1, 1)
        grid.addWidget(Label(u'价格'), 2, 0)
        grid.addWidget(self.spinPrice, 2, 1)
        grid.addWidget(Label(u'数量'), 3, 0)
        grid.addWidget(self.spinVolume, 3, 1)
        grid.addWidget(Label(u'类型'), 4, 0)
        grid.addWidget(self.comboPriceType, 4, 1)
        # grid.addWidget(Label(u'开平'), 5, 0)
        # grid.addWidget(self.comboOffset, 5, 1)
        
        return grid
    
    #----------------------------------------------------------------------
    def getAlgoSetting(self):
        """"""
        setting = OrderedDict()
        setting['templateName'] = DmaAlgo.templateName
        setting['vtSymbol'] = str(self.lineSymbol.text())
        setting['direction'] = text_type(self.comboDirection.currentText())
        setting['price'] = float(self.spinPrice.value())
        setting['totalVolume'] = float(self.spinVolume.value())
        setting['priceType'] = text_type(self.comboPriceType.currentText())
        setting['offset'] = text_type(self.comboOffset.currentText())
        
        return setting
    
    
