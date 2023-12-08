import logging
from binance.error import ClientError
from binance.spot import Spot as SpotClient
from binance.um_futures import UMFutures
from Bots.FutureBot.privateconfig import g_api_key, g_secret_key
from Bots.FutureBot.utils.information import Info_Controller

class Order_Structure(object):
    '''Order的结构体'''
    def __init__(self, symbol:str='', quantity:float=0., side:str='', type:str='LIMIT', price:float=0.):
        self.symbol = symbol
        self.quantity = quantity
        self.type = type
        self.side = side
        self.price = price
        self.valid = True  # 是否需作为有效订单执行

    def print_info(self):
        print('------Order info-------')
        print('symbol:', self.symbol)
        print('quantity:', self.quantity)
        print('side:', self.side)
        print('type:', self.type)
        print('price:', self.price)

    def selfcheck(self):
        if self.valid:
            assert self.symbol != '', 'Order_Structure Error: symbol is empty'
            assert self.quantity != 0., 'Order_Structure Error: quantity is 0'
            assert self.type in ['MARKET', 'LIMIT'], 'Order_Structure Error: type is not in [MARKET, LIMIT]'
            if self.type == 'LIMIT':
                assert self.price != 0., 'Order_Structure Error: price is 0, and type is LIMIT'


def create_order(trade_client, info_controller:Info_Controller, order_s: Order_Structure,):
    '''接受order structure，创建订单'''
    if not order_s.valid:
        return None

    check_order(trade_client, info_controller, order_s.symbol)

    params = {
        "symbol": order_s.symbol,
        "side": order_s.side.upper(),
        "type": order_s.type.upper(),
        "timeInForce": "GTC",
        "quantity": order_s.quantity,
    }

    if order_s.type == 'LIMIT':
        params['price'] = order_s.price

    logging.info('---------------------------')
    logging.info("symbol: {}".format(params['symbol']))
    logging.info("type: {}".format(params['type']))
    logging.info("quantity: {}".format(params['quantity']))
    logging.info("side: {}".format(params['side']))
    if order_s.type == 'LIMIT':
        logging.info("price: {}".format(params['price']))
    logging.info('---------------------------')

    try:
        response = trade_client.new_order(**params)
        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return None

    return response


def cancel_order(trade_client, order_id, symbol):
    pass


def check_order(trade_client, info_controller, symbol):
    '''
    1. 检查是否有未完成的订单
    2. 检查杠杆率是否正常
    3. margin 类应该型是isolated
    '''

    # todo 检查是否有未完成的订单

    if info_controller.account_info.position_df.loc[symbol, 'leverage'] != 5:
        change_leverage(trade_client, symbol)

    if info_controller.account_info.position_df.loc[symbol, 'isolated'] != True:
        change_margin_type(trade_client, symbol)

    return

def change_leverage(trade_client, symbol):
    '''调整杠杆率'''
    try:
        response = trade_client.change_leverage(
            symbol=symbol, leverage=5, recvWindow=6000
        )
        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
    return

def change_margin_type(trade_client, symbol):
    '''调整margin type为 isolated'''
    try:
        response = trade_client.change_margin_type(
            symbol=symbol, marginType="ISOLATED", recvWindow=6000
        )
        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
    return

if __name__ == "__main__":
    params = {
        "symbol": "OMGUSDT",
        "side": "SELL",
        "type": "LIMIT",
        "quantity": 10,
        "price": 0.6123,
    }

    order_s = Order_Structure(**params)
    order_s.print_info()
    order_s.selfcheck()

    client = UMFutures(g_api_key, g_secret_key)

    try:
        response = create_order(client, order_s)
        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )



