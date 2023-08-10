from huobi.client.account import AccountClient
from huobi.client.trade import TradeClient
from huobi.constant import *
from huobi.utils import *

class Order_Structure(object):
    '''Order的结构体'''
    def __init__(self, symbol:int='', amount:float=0., direction:int=''):
        self.symbol = symbol
        self.amount = amount
        self.direction = direction

    def print_info(self):
        print('------Order info-------')
        print('symbol:', self.symbol)
        print('amount:', self.amount)
        print('direction:', self.direction)


class Account_Structure(object):
    '''Account的结构体'''
    def __init__(self, id, quote_currency='usdt', balance_quote_currency=0, candidate_symbols_list = []):
        self.id = id
        self.quote_currency = quote_currency
        self.balance_quote_currency = balance_quote_currency
        self.candidate_symbols_list = candidate_symbols_list
        self.currency_info_df = None
        self.asset_valuation = 0

    def print_info(self):
        print('spot_account_id: ', self.id)
        print('balance_quote_currency:', self.balance_quote_currency)


def create_order(account_id, trade_client, order_s:Order_Structure):
    # todo 目前设置的都是按照Market 买入卖出
    symbol = order_s.symbol
    amount = order_s.amount
    direction = order_s.direction
    if direction=='buy':
        print(symbol)
        order_id = trade_client.create_order(symbol=symbol, account_id=account_id, order_type=OrderType.BUY_MARKET,
                                          source=OrderSource.API, amount=amount, price=None)
        LogInfo.output("created buy order id : {id}".format(id=order_id))

    elif direction=='sell':
        order_id = trade_client.create_order(symbol=symbol, account_id=account_id, order_type=OrderType.SELL_MARKET,
                                             source=OrderSource.API, amount=amount, price=None)
        LogInfo.output("created sell order id : {id}".format(id=order_id))

    elif direction=='hold':
        order_id = None
    return order_id


def cancel_order(trade_client, order_id, symbol):
    canceled_order_id = trade_client.cancel_order(symbol, order_id)
    if canceled_order_id == order_id:
        LogInfo.output("cancel order {id} done".format(id=canceled_order_id))
    else:
        LogInfo.output("cancel order {id} fail".format(id=canceled_order_id))





