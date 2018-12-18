# encoding: UTF-8

from __future__ import division

import os
from collections import OrderedDict

import math

from vnpy.trader.vtConstant import (DIRECTION_LONG, DIRECTION_SHORT,
                                    OFFSET_OPEN, OFFSET_CLOSE)
from vnpy.trader.uiQt import QtWidgets
from vnpy.trader.app.algoTrading.algoTemplate import AlgoTemplate
from vnpy.trader.app.algoTrading.uiAlgoWidget import AlgoWidget, QtWidgets

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


class StAlgo(AlgoTemplate):
    """自成交算法（self trade），用于刷成交量"""

    templateName = u'SelfTrade 刷单'

    # ----------------------------------------------------------------------
    def __init__(self, engine, setting, algoName):
        """Constructor"""
        super(StAlgo, self).__init__(engine, setting, algoName)

        # 参数，强制类型转换，保证从CSV加载的配置正确
        self.vtSymbol = str(setting['vtSymbol'])  # 合约代码
        self.orderVolume = float(setting['orderVolume'])  # 委托数量
        self.interval = int(setting['interval'])  # 运行间隔
        self.minTickSpread = int(setting['minTickSpread'])  # 最小价差

        self.count = 0  # 定时计数
        self.tradedVolume = 0  # 总成交数量

        self.subscribe(self.vtSymbol)
        self.paramEvent()
        self.varEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """"""
        pass

        # ----------------------------------------------------------------------

    def onTrade(self, trade):
        """"""
        self.tradedVolume += trade.volume
        self.varEvent()

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """"""
        pass

    # ----------------------------------------------------------------------
    def cancelTdexOrder(self):
        print('cancel-策略')
        orderObj = {}
        res = tdex.futuresGetOrders()
        orderList = []
        dataList = []
        data = {}
        try:
            if not res['data']['list']:
                return
        except:
            print('接口异常',res)

        if res['status'] == 0:
            orderList = res['data']['list']
            for item in orderList:
                orderObj = {
                    'cid': 1,
                    'id': item['id']
                }
                dataList.append(orderObj)

            data['list'] = dataList
            cancelRes = tdex.futuresCloseOrder(data)
            print(cancelRes)

    def onTimer(self):
        """"""
        self.count += 1
        if self.count == self.interval:
            self.count = 0

            # 全撤委托
            self.cancelTdexOrder()

            if self.vtSymbol == 'BTCUSD.TDEX':
                print('进入TDEX刷单')
                self.vtSymbol = 'BTCUSD.BITMEX'

            data = {
                'depth': 1,
            }

            depthData = tdex.orderBook(data)

            # 获取行情
            if not depthData or depthData['status'] != 0:
                self.writeLog('获取TDEX行情接口异常')
                print(depthData)
                return

            depthData = depthData['data']
            contract = self.getContract(self.vtSymbol)
            if not contract:
                return

            newAsk = float(depthData['asks'][0]['price'])
            newBid = float(depthData['bids'][0]['price'])
            tickSpread = (newAsk - newBid) / 1
            if tickSpread < self.minTickSpread:
                self.writeLog(u'当前价差为%s个Tick，小于算法设置%s，不执行刷单' % (tickSpread, self.minTickSpread))
                return

            midPrice = newBid + contract.priceTick * int(tickSpread / 2)

            dataBuy = {
                'cid': 1,
                'side': 0,
                'scale': 20,
                'volume': int(self.orderVolume),
                'visible': -1,
                'price': int(midPrice),
            }
            dataSell = {
                'cid': 1,
                'side': 1,
                'scale': 20,
                'volume': int(self.orderVolume),
                'visible': -1,
                'price': int(midPrice),
            }
            resBuy = tdex.futuresOpen(dataBuy)
            resSell = tdex.futuresOpen(dataSell)


            if resBuy['status'] != 0 or resSell['status'] != 0:
                self.writeLog(u'发出刷单买卖委托接口异常')
            else:
                self.writeLog(u'发出刷单买卖委托，价格：%s，数量：%s' % (midPrice, self.orderVolume))
                resMerge = tdex.futuresGetPosition()
                if resMerge['status'] != 0 or not resMerge['data']['list'] or len(resMerge['data']['list']) <= 1:
                    print('不需要合并仓位')
                    return

                dataList = []
                positionList = resMerge['data']['list']
                for item in positionList:
                    dataList.append(item['id'])

                mergeData = {
                    'cid': 1,
                    'list': dataList
                }

                resMerge = tdex.futuresMerge(mergeData)
                print(resMerge)
                print('合仓成功')



        self.varEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """"""
        self.writeLog(u'停止算法')
        self.varEvent()

    # ----------------------------------------------------------------------
    def varEvent(self):
        """更新变量"""
        d = OrderedDict()
        d[u'算法状态'] = self.active
        d[u'成交数量'] = self.tradedVolume
        d[u'定时计数'] = self.count
        d['active'] = self.active
        self.putVarEvent(d)

    # ----------------------------------------------------------------------
    def paramEvent(self):
        """更新参数"""
        d = OrderedDict()
        d[u'代码'] = self.vtSymbol
        d[u'单次委托数量'] = self.orderVolume
        d[u'执行间隔'] = self.interval
        d[u'最小价差Tick'] = self.minTickSpread
        self.putParamEvent(d)


########################################################################
class StWidget(AlgoWidget):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, algoEngine, parent=None):
        """Constructor"""
        super(StWidget, self).__init__(algoEngine, parent)

        self.templateName = StAlgo.templateName

    # ----------------------------------------------------------------------
    def initAlgoLayout(self):
        """"""
        self.lineSymbol = QtWidgets.QLineEdit()

        self.spinVolume = QtWidgets.QDoubleSpinBox()
        self.spinVolume.setMinimum(0)
        self.spinVolume.setMaximum(1000000000)
        self.spinVolume.setDecimals(6)

        self.spinInterval = QtWidgets.QSpinBox()
        self.spinInterval.setMinimum(20)
        self.spinInterval.setMaximum(3600)

        self.spinMinTickSpread = QtWidgets.QSpinBox()
        self.spinMinTickSpread.setMinimum(0)
        self.spinMinTickSpread.setMaximum(1000)

        Label = QtWidgets.QLabel

        grid = QtWidgets.QGridLayout()
        grid.addWidget(Label(u'代码'), 0, 0)
        grid.addWidget(self.lineSymbol, 0, 1)
        grid.addWidget(Label(u'单次刷单量'), 1, 0)
        grid.addWidget(self.spinVolume, 1, 1)
        grid.addWidget(Label(u'执行间隔'), 2, 0)
        grid.addWidget(self.spinInterval, 2, 1)
        grid.addWidget(Label(u'最小价差Tick'), 3, 0)
        grid.addWidget(self.spinMinTickSpread, 3, 1)

        return grid

    # ----------------------------------------------------------------------
    def getAlgoSetting(self):
        """"""
        setting = OrderedDict()
        setting['templateName'] = StAlgo.templateName
        setting['vtSymbol'] = str(self.lineSymbol.text())
        setting['orderVolume'] = float(self.spinVolume.value())
        setting['interval'] = int(self.spinInterval.value())
        setting['minTickSpread'] = int(self.spinMinTickSpread.value())

        return setting
