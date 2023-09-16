import logging
from binance.error import ClientError

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


def create_order(info_controller, trade_client, order_s:Order_Structure):
    # todo 目前设置的都是按照Market 买入卖出

    symbol = order_s.symbol
    amount = order_s.amount
    side = order_s.direction

    params = {
        "symbol": symbol,
        "side": side.upper(),
        "type": "MARKET",
        "timeInForce": "GTC",
        "quantity": amount,
    }

    price_dict = info_controller.strategy_info.price_dict
    try:
        if side == 'buy':
            response = trade_client.new_order(**params)
            # 更新持仓成本
            info_controller.account_info.position_df.loc[symbol, "bid_price"] = price_dict[symbol]['close'].values[-1]
        elif side == 'sell':
            response = trade_client.new_order(**params)
            # 更新持仓成本
            info_controller.account_info.position_df.loc[symbol, "bid_price"] = 0
        elif side == 'hold':
            response = None

        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

    return response


def cancel_order(trade_client, order_id, symbol):
    pass





