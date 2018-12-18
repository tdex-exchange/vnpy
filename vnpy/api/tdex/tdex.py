# encoding: UTF-8

from __future__ import print_function
import hashlib
import hmac
import json
import ssl
import threading
import traceback

import thread

from queue import Queue, Empty
from multiprocessing.dummy import Pool
import time
import datetime
from urlparse import urlparse
from copy import copy, deepcopy
from urllib import urlencode
from threading import Thread

from six.moves import input

import requests
import websocket

from tdexApi import Tdex
import gzip
from cStringIO import StringIO

REST_HOST = 'https://tl.tdex.com/openapi/v1'
WEBSOCKET_HOST = 'wss://tl.tdex.com/realtime'
ws = None
tdex = None
_apiKey = ''
_apiSecret = ''
accoundId = 0

positionObj = {u'ordStatus': u'New', u'exDestination': u'XBME',
               u'text': u'Submission from testnet.tdex.com',
               u'timeInForce': u'GoodTillCancel', u'currency': u'USD', u'pegPriceType': u'',
               u'simpleLeavesQty': 0.0002,
               u'ordRejReason': u'', u'transactTime': u'2018-10-24T06:54:33.602Z', u'clOrdID': u'',
               u'settlCurrency': u'XBt',
               u'cumQty': 3, u'displayQty': None, u'avgPx': None, u'price': 6017.5,
               u'simpleOrderQty': None,
               u'contingencyType': u'', u'triggered': u'', u'timestamp': u'2018-10-24T06:54:33.602Z',
               u'symbol': u'BTCUSD',
               u'pegOffsetValue': None, u'execInst': u'', u'simpleCumQty': 0,
               u'orderID': u'8ab6f630-3cdf-c3be-e25c-9909f00f5d6b',
               u'multiLegReportingType': u'SingleSecurity',
               u'account': 141309, u'stopPx': None, u'leavesQty': 1, u'orderQty': 2,
               u'workingIndicator': True,
               u'ordType': u'Limit', u'clOrdLinkID': u'', u'side': u'Sell'}

dataPosition = {u'keys': [u'orderID'], u'filter': {u'account': 123456},
                u'attributes': {u'orderID': u'grouped', u'workingIndicator': u'grouped',
                                u'account': u'grouped',
                                u'ordStatus': u'grouped'}, u'action': u'partial', u'table': u'order',
                u'data': [],
                u'foreignKeys': {u'symbol': u'TDEX', u'side': u'side', u'ordStatus': u'ordStatus'}}

dataOrder = deepcopy(dataPosition)

accountObj = {u'availableMargin': 967741, u'prevState': u'', u'grossComm': -3, u'taxableMargin': 0,
              u'confirmedDebit': 0, u'marginUsedPcnt': 0.0323, u'grossOpenPremium': 0,
              u'currency': u'XBt',
              u'indicativeTax': 0, u'prevRealisedPnl': 0, u'syntheticMargin': 0,
              u'riskLimit': 1000000000000L,
              u'marginBalancePcnt': 1, u'targetExcessMargin': 0, u'commission': None, u'state': u'',
              u'walletBalance': 1000003, u'marginLeverage': 0.015553517840946931,
              u'grossLastValue': 15554,
              u'grossMarkValue': 15554, u'maintMargin': 15634, u'grossExecCost': 0,
              u'grossOpenCost': 16618,
              u'timestamp': u'2018-10-24T09:00:35.473Z', u'marginBalance': 1000031, u'pendingDebit': 0,
              u'unrealisedProfit': 0, u'initMargin': 16656, u'withdrawableMargin': 967741,
              u'varMargin': 0,
              u'account': 141309, u'pendingCredit': 0, u'riskValue': 32172, u'excessMargin': 967741,
              u'prevUnrealisedPnl': 0, u'amount': 1000000, u'realisedPnl': 3, u'action': u'',
              u'unrealisedPnl': 28, u'excessMarginPcnt': 1, u'sessionMargin': 0}

dataAccount = {u'keys': [u'account', u'currency'], u'filter': {u'account': 141309},
               u'attributes': {u'currency': u'grouped', u'account': u'sorted'}, u'action': u'partial',
               u'table': u'margin',
               u'data': [],
               u'foreignKeys': {}}

dataHold = {u'keys': [u'account', u'symbol', u'currency'], u'filter': {u'account': 141309},
            u'attributes': {u'quoteCurrency': u'grouped', u'currency': u'grouped', u'account': u'sorted',
                            u'underlying': u'grouped', u'symbol': u'grouped'}, u'action': u'partial',
            u'table': u'position', u'data': [
        {u'currentComm': -13, u'unrealisedTax': 0, u'openOrderBuyQty': 1, u'realisedCost': 0,
         u'lastPrice': 6387.92,
         u'timestamp': u'2018-10-25T01:54:35.395Z', u'simpleValue': 1, u'posMaint': 104, u'simpleCost': 2,
         u'posCost': -15582, u'openOrderSellCost': 0, u'underlying': u'XBT', u'unrealisedRoePcnt': -0.0047,
         u'grossOpenPremium': 0, u'initMarginReq': 1, u'execCost': 0, u'simplePnlPcnt': 0,
         u'riskLimit': 20000000000L,
         u'targetExcessMargin': 0, u'posState': u'', u'rebalancedPnl': 3, u'currentCost': -15582,
         u'crossMargin': False,
         u'homeNotional': 0.00015655, u'execComm': 0, u'lastValue': -15655, u'openingComm': -13,
         u'prevUnrealisedPnl': 0, u'unrealisedGrossPnl': -73, u'taxableMargin': 0, u'unrealisedCost': -15582,
         u'realisedPnl': 13, u'unrealisedPnl': -73, u'execSellQty': 0, u'simpleQty': 0.0002,
         u'quoteCurrency': u'USD',
         u'initMargin': 16656, u'liquidationPrice': 3216, u'execQty': 0, u'indicativeTax': 0, u'posComm': 24,
         u'posLoss': 2, u'openOrderSellPremium': 0, u'prevRealisedPnl': 0, u'execSellCost': 0, u'leverage': 1,
         u'openOrderSellQty': 0, u'commission': 0.00075, u'markValue': -15655, u'openingCost': -15582,
         u'bankruptPrice': 3208, u'openOrderBuyPremium': 0, u'grossExecCost': 0, u'grossOpenCost': 16618,
         u'posInit': 15582, u'currentQty': 0, u'unrealisedPnlPcnt': -0.0047, u'deleveragePercentile': 2,
         u'account': 141309, u'simplePnl': 0, u'riskValue': 32273, u'marginCallPrice': 3216,
         u'posCost2': -15580,
         u'posCross': 14, u'maintMarginReq': 0.005, u'markPrice': 6387.92, u'indicativeTaxRate': 0,
         u'execBuyCost': 0,
         u'currency': u'XBt', u'longBankrupt': 0, u'prevClosePrice': 6421.49, u'realisedTax': 0,
         u'openingQty': 5,
         u'posAllowance': 0, u'currentTimestamp': u'2018-10-25T01:54:35.395Z', u'breakEvenPrice': 6411.5,
         u'openOrderBuyCost': -16618, u'realisedGrossPnl': 0, u'maintMargin': 15545, u'isOpen': True,
         u'taxBase': 0,
         u'symbol': u'BTCUSD', u'foreignNotional': -1, u'posMargin': 15618, u'shortBankrupt': 0,
         u'varMargin': 0,
         u'avgCostPrice': 6417.5, u'openingTimestamp': u'2018-10-25T01:00:00.000Z', u'execBuyQty': 0,
         u'sessionMargin': 0, u'avgEntryPrice': 6417.5}],
            u'foreignKeys': {u'symbol': u'instrument'}}


def exchange(item):
    res = item.split('=')

    return res


def changeInt(list):
    for index, i in enumerate(list):
        for cIndex, cI in enumerate(i):
            i[cIndex] = float(cI)


########################################################################
class TdexRestApi(object):
    """REST API"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.apiKey = ''
        self.apiSecret = ''

        self.active = False
        self.reqid = 0
        self.queue = Queue()
        self.pool = None
        self.sessionDict = {}  # 会话对象字典

        self.header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

    # ----------------------------------------------------------------------
    def init(self, apiKey, apiSecret):
        """初始化"""
        global _apiKey
        global _apiSecret
        self.apiKey = apiKey
        self.apiSecret = apiSecret
        _apiKey = apiKey
        _apiSecret = apiSecret

    # ----------------------------------------------------------------------
    def start(self, n=3):
        """启动"""
        if self.active:
            return

        self.active = True
        self.pool = Pool(n)
        self.pool.map_async(self.run, range(n))

    # ----------------------------------------------------------------------
    def close(self):
        """关闭"""
        self.active = False

        if self.pool:
            self.pool.close()
            self.pool.join()

    # ----------------------------------------------------------------------
    def addReq(self, method, path, callback, params=None, postdict=None):
        """添加请求"""
        self.reqid += 1
        req = (method, path, callback, params, postdict, self.reqid)
        self.queue.put(req)
        return self.reqid

    # ----------------------------------------------------------------------
    def processReq(self, req, i):
        """处理请求"""
        method, path, callback, params, postdict, reqid = req
        url = REST_HOST + path
        expires = int(time() + 5)

        rq = requests.Request(url=url, data=postdict)
        p = rq.prepare()

        header = copy(self.header)
        header['api-expires'] = str(expires)
        header['api-key'] = self.apiKey
        header['api-signature'] = self.generateSignature(method, path, expires, params, body=p.body)

        # 使用长连接的session，比短连接的耗时缩短80%
        session = self.sessionDict[i]
        resp = session.request(method, url, headers=header, params=params, data=postdict)

        # resp = requests.request(method, url, headers=header, params=params, data=postdict)

        code = resp.status_code
        d = resp.json()

        if code == 200:
            callback(d, reqid)
        else:
            self.onError(code, d)

    # ----------------------------------------------------------------------
    def run(self, i):
        """连续运行"""
        self.sessionDict[i] = requests.Session()

        while self.active:
            try:
                req = self.queue.get(timeout=1)
                self.processReq(req, i)
            except Empty:
                pass

    # ----------------------------------------------------------------------
    def generateSignature(self, method, path, expires, params=None, body=None):
        """生成签名"""
        # 对params在HTTP报文路径中，以请求字段方式序列化
        if params:
            query = urlencode(sorted(params.items()))
            path = path + '?' + query

        if body is None:
            body = ''

        msg = method + '/api/v1' + path + str(expires) + body
        signature = hmac.new(self.apiSecret, msg,
                             digestmod=hashlib.sha256).hexdigest()
        return signature

    # ----------------------------------------------------------------------
    def onError(self, code, error):
        """错误回调"""
        print('on error')
        print(code, error)

    # ----------------------------------------------------------------------
    def onData(self, data, reqid):
        """通用回调"""
        print('on data')
        print(data, reqid)


########################################################################
class TdexWebsocketApi(object):
    """Websocket API"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.ws = None
        self.thread = None
        self.active = False

    # ----------------------------------------------------------------------
    def start(self):
        """启动"""
        global ws
        global tdex
        global positionObj

        options = {
            'apiKey': _apiKey,
            'apiSecret': _apiSecret,
            'url': REST_HOST,
        }
        print(options)
        tdex = Tdex(options)
        ws = websocket.WebSocketApp(WEBSOCKET_HOST,
                                    on_data=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        ws.on_open = self.on_open
        th = threading.Thread(target=ws.run_forever)
        th.start()

        # PositionLength = self.getPosition()
        res = tdex.futuresGetOrders()
        if res['status'] != 0 or not res['data']['list']:
            return

        self.getTdexOrder()
        print('持有订单个数：', len(res['data']['list']))
        # print(PositionLength)
        # print(type(PositionLength))
        # 有订单的状态才查询账号余额和持仓
        if len(res['data']['list']) > 0:
            self.getWalletBlance()
            self.getHold()

    # ----------------------------------------------------------------------

    def reconnect(self):
        """重连"""
        self.start()

    # ----------------------------------------------------------------------

    def gzip_uncompress(self, c_data):
        buf = StringIO(c_data)
        f = gzip.GzipFile(mode='rb', fileobj=buf)
        try:
            r_data = f.read()
        finally:
            f.close()
        return r_data

    # 获取持仓列表
    def getPosition(self, arrList=[]):
        global dataPosition
        if len(arrList) > 0:
            print('delete-position')
            # print(arrList)
            # for item in arrList:
            #     for cItem in dataPosition['data']:
            #         # print(item['ID'], cItem['orderID'])
            #         # print(item['ID'] == cItem['orderID'])
            #         if str(cItem['orderID']) == str(item['ID']):
            #             cItem['ordStatus'] = 'Filled'

        else:
            position = tdex.futuresGetPosition()
            positionList = position['data']['list']
            dataPosition['data'] = []
            if positionList == None:
                return 0
            listLength = len(positionList)
            # if position['status'] == 0 and positionList != None and len(positionList) > 0:
            #     for item in positionList:
            #         data = copy(positionObj)
            #         data['orderID'] = str(item['id'])
            #         data['cumQty'] = item['volume']  # 成交数量
            #         # data['cumQty'] = 2
            #         data['orderQty'] = item['volume']  # 委托数量
            #         data['price'] = item['price']
            #         data['side'] = 'Buy' if item['side'] == 0 else 'Sell'
            #         timeStamp = item['createdAt'].replace(' ', 'T')
            #         data['timestamp'] = timeStamp
            #         # print(data['side'])
            #         dataPosition['data'].append(data)
            # print('position')

        # print(dataPosition)
        # self.onData(dataPosition)
        if listLength > 0:
            return listLength
        else:
            return 0

    def getTdexOrder(self, arrList=[]):
        global dataOrder
        if len(arrList) > 0:
            lastItemId = ''
            for item in arrList:
                if item['Event'] == 'Create':
                    dataObj = copy(positionObj)
                    dataObj['orderID'] = str(item['ID'])
                    dataObj['cumQty'] = item['Filled']
                    dataObj['orderQty'] = item['Volume']
                    changePrice1 = str(item['Price']).split('.')
                    if changePrice1[0] == '0':
                        dataObj['price'] = '市价'
                    else:
                        dataObj['price'] = changePrice1[0]
                    dataObj['side'] = 'Buy' if item['Side'] == 0 else 'Sell'
                    timeStamp = item['CreatedAt'].replace(' ', 'T')
                    dataObj['timestamp'] = timeStamp
                    dataObj['ordStatus'] = 'Partially filled' if item['Filled'] != 0 else 'New'
                    dataOrder['data'].append(dataObj)
                else:
                    for cItem in dataOrder['data']:
                        if str(cItem['orderID']) == str(item['ID']):
                            if item['Event'] == 'Delete' and not 'Triggered' in item and lastItemId != str(item['ID']):
                                cItem['ordStatus'] = 'Canceled'
                            # elif item['Event'] == 'Delete' and not 'Triggered' in item and lastItemId == str(item['ID']):
                            #     cItem['ordStatus'] = 'Filled'
                            #     cItem['cumQty'] = item['Filled']
                            elif item['Event'] == 'Update' and 'Filled' in item:
                                cItem['cumQty'] = item['Filled']
                                if cItem['cumQty'] < cItem['orderQty']:
                                    cItem['ordStatus'] = 'Partially filled'
                                else:
                                    cItem['ordStatus'] = 'Filled'
                lastItemId = str(item['ID'])
        else:
            res = tdex.futuresGetOrders()
            print('更新order')
            print(res)
            orderList = []
            dataOrder['data'] = []
            if res['status'] != 0 or not res['data']['list']:
                return

            if res['status'] == 0:
                orderList = res['data']['list']

            if len(orderList) > 0:
                for item in orderList:
                    data = copy(positionObj)
                    data['orderID'] = str(item['id'])
                    data['cumQty'] = item['filled']  # 成交数量
                    # data['cumQty'] = 2
                    data['orderQty'] = item['volume']  # 委托数量
                    # data['price'] = filter(str.isdigit, item['price'].encode('utf-8'))
                    changePrice = str(item['price']).split('.')
                    data['price'] = changePrice[0]
                    data['side'] = 'Buy' if item['side'] == 0 else 'Sell'
                    timeStamp = item['createdAt'].replace(' ', 'T')
                    data['timestamp'] = timeStamp
                    # print(type(item['filled']))
                    data['ordStatus'] = 'Partially filled' if item['filled'] != 0 else 'New'
                    # print(data['side'])
                    dataOrder['data'].append(data)
                    # print('position')

        self.onData(dataOrder)

    def getWalletBlance(self):
        global dataAccount
        global accountObj
        global accoundId
        data = {
            "currency": 1,
            "type": 1,
        }
        blance = tdex.walletBalance(data)
        if accoundId == 0:
            res_info = tdex.userInfo()
            accoundId = res_info['data']['accountId']
        # print(blance)
        # print(res_info)
        dataAccount['data'] = []
        accountObj['availableMargin'] = blance['data']['available']
        accountObj['marginBalance'] = blance['data']['quantity']
        accountObj['account'] = accoundId

        dataAccount['data'].append(accountObj)
        self.onData(dataAccount)

    def getHold(self):
        global dataHold
        position = tdex.futuresGetPosition()
        positionList = position['data']['list']
        if not positionList:
            return
        num = len(positionList)
        dataHold['data'][0]['currentQty'] = num
        self.onData(dataHold)

    def on_message(self, argument_obj, argument_message, type):
        global dataPosition
        # print("收到消息: ")
        data = None
        if argument_message == 1:
            data = json.loads(argument_obj)
        else:
            r_data = self.gzip_uncompress(argument_obj)
            data = json.loads(r_data)

        # print(data)
        date1 = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        day1 = time.strftime('%H:%M:%S', time.localtime(time.time()))
        utcTime = '%sT%s' % (date1, day1)

        if 'depth' in data:
            bidsBid = data['depth']['depthbid'].split(',')
            bidsAsk = data['depth']['depthask'].split(',')
            resBid = map(exchange, bidsBid)
            resAsk = map(exchange, bidsAsk)
            # print(resBid[:6])
            # print(resAsk[:6])
            changeInt(resBid)
            changeInt(resAsk)
            depDataDict = {
                'action': 'update',
                'table': 'orderBook10',
                'price': 7777,
                'data': [{
                    'timestamp': utcTime,
                    'symbol': 'BTCUSD',
                    'bids': resAsk[:5],
                    'asks': resBid[:5],
                }],
            }
            # depDataDict = json.dumps(depDataDict)

            self.onData(depDataDict)

        if data['ch'] == 'BTCUSD_MARKET_TICKER':
            # print('market***********')
            lastPrice = data['ticker']['last']
            changePrice = str(lastPrice).split('.')
            data1 = {u'keys': [], u'filter': {}, u'attributes': {u'timestamp': u'sorted', u'symbol': u'grouped'},
                     u'action': u'partial', u'table': u'trade', u'data': [
                    {u'homeNotional': 0.00031944, u'trdMatchID': u'ef11c5af-38fc-f4ee-6c26-3aa506cf95eb',
                     u'timestamp': utcTime, u'price': changePrice[0],
                     u'foreignNotional': 2,
                     u'grossValue': 31944, u'side': u'Buy', u'tickDirection': u'ZeroPlusTick', u'symbol': u'BTCUSD',
                     u'size': 2}],
                     u'types': {u'homeNotional': u'float', u'trdMatchID': u'guid', u'timestamp': u'timestamp',
                                u'price': u'float', u'foreignNotional': u'float', u'grossValue': u'long',
                                u'side': u'symbol', u'tickDirection': u'symbol', u'symbol': u'symbol',
                                u'size': u'long'}, u'foreignKeys': {u'symbol': u'instrument', u'side': u'side'}}
            self.onData(data1)

        if data['ch'] == 'ACCOUNT_INFO_UPDATE':
            orderFlag = False
            if data['event'] == 'FUTURES_POSITION' and data['content'] and len(data['content']) > 0:
                if data['content'][0]['Event'] == 'Delete':
                    # self.getPosition(data['content'])
                    self.getWalletBlance()
                    self.getHold()
                else:
                    # self.getPosition()
                    self.getWalletBlance()
                    self.getHold()
            if str(data['event']) == 'FUTURES_ORDER':
                if not data['content'] or len(data['content']) == 0:
                    return

                self.getTdexOrder(data['content'])
                # for item in data['content']:
                #     if item['Event'] == 'Create':
                #         orderFlag = True
                # if data['content'][0]['Event'] == 'Delete':
                #     print('订单删除1')
                #     self.getTdexOrder(data['content'])
                # elif len(data['content']) > 1 and data['content'][-1]['Event'] == 'Delete':
                #     print('订单删除2')
                #     self.getTdexOrder(data['content'])
                # else:
                #     print('进入订单更新')
                #     self.getTdexOrder()
                # if orderFlag:
                #     print('进入订单更新2')
                #     self.getTdexOrder()

                self.getWalletBlance()
                self.getHold()

    def on_error(ws, error):
        print(error)

    def on_close(ws):
        print("### closed ###")

    def on_open(self, *args):
        self.writeLog('websocket 连接成功')
        global ws
        global tdex

        def run(*args):
            mes_dep = {
                "id": "1524707635007",
                "sub": "BTCUSD_DEPTH_DATA",
                "cnt": 5,
            }
            market_mes = {
                "id": "1524724272995",
                "sub": "BTCUSD_MARKET_TICKER"
            }
            ws.send(json.dumps(mes_dep))
            ws.send(json.dumps(market_mes))

            res_info = tdex.userInfo()
            res = tdex.getToken()
            # print(res_info)
            # print(res)
            uid = res_info['data']['uid']
            token = res['data']['token']
            tokenTime = res['data']['time']

            user_mes = {
                "uid": uid,
                "time": tokenTime,
                "token": token,
                "id": "1524707635023",
                "sub": "ACCOUNT_INFO_UPDATE",
                "ssid": _apiKey
            }
            # print(user_mes)
            ws.send(json.dumps(user_mes))

        thread.start_new_thread(run, ())

    def run(self):
        """运行"""
        while self.active:
            try:
                stream = self.ws.recv()
                data = json.loads(stream)
                print('输出信息: ')
                print(data)
                data1 = {u'keys': [u'orderID'], u'filter': {u'account': 141309},
                         u'attributes': {u'orderID': u'grouped', u'workingIndicator': u'grouped',
                                         u'account': u'grouped',
                                         u'ordStatus': u'grouped'}, u'action': u'partial', u'table': u'order',
                         u'data': [
                             {u'ordStatus': u'New', u'exDestination': u'XBME',
                              u'text': u'Submission from testnet.tdex.com',
                              u'timeInForce': u'GoodTillCancel', u'currency': u'USD', u'pegPriceType': u'',
                              u'simpleLeavesQty': 0.0002,
                              u'ordRejReason': u'', u'transactTime': u'2018-10-24T06:54:33.602Z', u'clOrdID': u'',
                              u'settlCurrency': u'XBt',
                              u'cumQty': 1, u'displayQty': None, u'avgPx': None, u'price': 6017.5,
                              u'simpleOrderQty': None,
                              u'contingencyType': u'', u'triggered': u'', u'timestamp': u'2018-10-24T06:54:33.602Z',
                              u'symbol': u'BTCUSD',
                              u'pegOffsetValue': None, u'execInst': u'', u'simpleCumQty': 0,
                              u'orderID': u'8ab6f630-3cdf-c3be-e25c-9909f00f5d6b',
                              u'multiLegReportingType': u'SingleSecurity',
                              u'account': 141309, u'stopPx': None, u'leavesQty': 1, u'orderQty': 1,
                              u'workingIndicator': True,
                              u'ordType': u'Limit', u'clOrdLinkID': u'', u'side': u'Sell'}],
                         u'foreignKeys': {u'symbol': u'TDEX', u'side': u'side', u'ordStatus': u'ordStatus'}}
                data2 = {u'action': u'update', u'table': u'orderBook10', u'data': [
                    {u'timestamp': u'2018-10-24T07:26:34.799Z', u'symbol': u'BTCUSD',
                     u'lastPrice': 10020,
                     u'bids': [[6416.5, 10718], [6416, 60750], [6415.5, 1193], [6415, 40333], [6414.5, 305],
                               [6414, 812],
                               [6413.5, 14423], [6413, 11272], [6412.5, 11932], [6412, 14459]],
                     u'asks': [[6417, 4627], [6417.5, 245], [6418, 194], [6418.5, 4960], [6419, 1300], [6419.5, 560],
                               [6420, 68],
                               [6420.5, 470], [6421, 50], [6421.5, 68]]}]}

                data3 = {u'keys': [u'account', u'currency'], u'filter': {u'account': 141309},
                         u'attributes': {u'currency': u'grouped', u'account': u'sorted'}, u'action': u'partial',
                         u'table': u'margin',
                         u'data': [
                             {u'availableMargin': 967741, u'prevState': u'', u'grossComm': -3, u'taxableMargin': 0,
                              u'confirmedDebit': 0, u'marginUsedPcnt': 0.0323, u'grossOpenPremium': 0,
                              u'currency': u'XBt',
                              u'indicativeTax': 0, u'prevRealisedPnl': 0, u'syntheticMargin': 0,
                              u'riskLimit': 1000000000000L,
                              u'marginBalancePcnt': 1, u'targetExcessMargin': 0, u'commission': None, u'state': u'',
                              u'walletBalance': 1000003, u'marginLeverage': 0.015553517840946931,
                              u'grossLastValue': 15554,
                              u'grossMarkValue': 15554, u'maintMargin': 15634, u'grossExecCost': 0,
                              u'grossOpenCost': 16618,
                              u'timestamp': u'2018-10-24T09:00:35.473Z', u'marginBalance': 1000031, u'pendingDebit': 0,
                              u'unrealisedProfit': 0, u'initMargin': 16656, u'withdrawableMargin': 967741,
                              u'varMargin': 0,
                              u'account': 141309, u'pendingCredit': 0, u'riskValue': 32172, u'excessMargin': 967741,
                              u'prevUnrealisedPnl': 0, u'amount': 1000000, u'realisedPnl': 3, u'action': u'',
                              u'unrealisedPnl': 28, u'excessMarginPcnt': 1, u'sessionMargin': 0}],
                         u'foreignKeys': {u'symbol': u'instrument'}}

                data4 = {u'keys': [u'account', u'symbol', u'currency'], u'filter': {u'account': 141309},
                         u'attributes': {u'quoteCurrency': u'grouped', u'currency': u'grouped', u'account': u'sorted',
                                         u'underlying': u'grouped', u'symbol': u'grouped'}, u'action': u'partial',
                         u'table': u'position', u'data': [
                        {
                            u'leverage': 1,
                            u'openOrderSellQty': 0, u'commission': 0.00075, u'markValue': -15655,
                            u'openingCost': -15582,
                            u'bankruptPrice': 3208, u'openOrderBuyPremium': 0, u'grossExecCost': 0,
                            u'grossOpenCost': 16618,
                            u'posInit': 15582, u'currentQty': 2, u'unrealisedPnlPcnt': -0.0047,
                            u'deleveragePercentile': 1,
                            u'account': 141309, u'simplePnl': 0, u'riskValue': 32273, u'marginCallPrice': 3216,
                            u'posCost2': -15580,
                            u'posCross': 14, u'maintMarginReq': 0.005, u'markPrice': 6387.92, u'indicativeTaxRate': 0,
                            u'execBuyCost': 0,
                            u'currency': u'XBt', u'longBankrupt': 0, u'prevClosePrice': 6421.49, u'realisedTax': 0,
                            u'openingQty': 1,
                            u'posAllowance': 0, u'currentTimestamp': u'2018-10-25T01:54:35.395Z',
                            u'breakEvenPrice': 6411.5,
                            u'openOrderBuyCost': -16618, u'realisedGrossPnl': 0, u'maintMargin': 15545, u'isOpen': True,
                            u'taxBase': 0,
                            u'symbol': u'TDEX', u'foreignNotional': -1, u'posMargin': 15618, u'shortBankrupt': 0,
                            u'varMargin': 0,
                            u'avgCostPrice': 6417.5, u'openingTimestamp': u'2018-10-25T01:00:00.000Z', u'execBuyQty': 0,
                            u'sessionMargin': 0, u'avgEntryPrice': 6417.5
                        }],
                         u'foreignKeys': {u'symbol': u'instrument'}
                         }

                # websocket连接

                self.onData(data1)
                self.onData(data2)
                self.onData(data3)
                self.onData(data4)
                # self.onData(data)
            except:
                msg = traceback.format_exc()
                self.onError(msg)
                self.reconnect()

    # ----------------------------------------------------------------------
    def close(self):
        """关闭"""
        self.active = False

        if self.thread:
            self.thread.join()

    # ----------------------------------------------------------------------
    def onConnect(self):
        """连接回调"""
        print('connected')

    # ----------------------------------------------------------------------
    def onData(self, data):
        """数据回调"""
        print('-' * 30)
        l = data.keys()
        l.sort()
        for k in l:
            print(k, data[k])

    # ----------------------------------------------------------------------
    def onError(self, msg):
        """错误回调"""
        print(msg)

    # ----------------------------------------------------------------------
    def sendReq(self, req):
        """发出请求"""
        self.ws.send(json.dumps(req))

        # if __name__ == '__main__':
        # API_KEY = ''
        # API_SECRET = ''
        #
        # ## REST测试
        # rest = TdexRestApi()
        # rest.init(API_KEY, API_SECRET)
        # rest.start(3)
        #
        # data = {
        #     'symbol': 'BTCUSD'
        # }
        # rest.addReq('POST', '/position/isolate', rest.onData, postdict=data)
        # rest.addReq('GET', '/instrument', rest.onData)

        # WEBSOCKET测试
        # ws = BitmexWebsocketApi()
        # ws.start()

        # req = {"op": "subscribe", "args": ['order', 'trade', 'position', 'margin']}
        # ws.sendReq(req)

        # expires = int(time())
        # method = 'GET'
        # path = '/realtime'
        # msg = method + path + str(expires)
        # signature = hmac.new(API_SECRET, msg, digestmod=hashlib.sha256).hexdigest()

        # req = {
        # 'op': 'authKey',
        # 'args': [API_KEY, expires, signature]
        # }

        # ws.sendReq(req)

        # req = {"op": "subscribe", "args": ['order', 'execution', 'position', 'margin']}
        # req = {"op": "subscribe", "args": ['instrument']}
        # ws.sendReq(req)

        # input()
