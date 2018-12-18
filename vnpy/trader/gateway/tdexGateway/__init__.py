# encoding: UTF-8

from vnpy.trader import vtConstant
from .tdexGateway import TdexGateway

gatewayClass = TdexGateway
gatewayName = 'TDEX'
gatewayDisplayName = 'TDEX'
gatewayType = vtConstant.GATEWAYTYPE_BTC
gatewayQryEnabled = False