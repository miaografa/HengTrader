import logging
from binance.error import ClientError
from binance.spot import Spot as SpotClient
import sys

sys.path.append(r'C:\Users\Admin\Desktop\\')
from Crypto_Bot.utils.privateconfig import *


class Order_Structure(object):
    
    # For 'symbol' and 'direction' to be empty string as default

    def __init__(self, symbol:str='', amount:float=0., direction:int=''):
        self.symbol = symbol
        self.amount = amount
        self.direction = direction

    def print_info(self):
        print('------Order info-------')
        print('symbol:', self.symbol)
        print('amount:', self.amount)
        print('direction:', self.direction)

def create_order(info_controller, trade_client, order_s:Order_Structure):

    # Buy and Sell order are following current market price (Only amount manipulation)
    symbol = order_s.symbol
    amount = order_s.amount
    side = order_s.direction

    logging.info('---------------------------')
    logging.info("symbol: {}".format(symbol))
    logging.info("amount: {}".format(amount) )
    logging.info("side: {}".format(side),)
    logging.info('---------------------------')

    params = {
        "symbol": symbol,
        "side": side.upper(),
        "type": "MARKET",
    }

    try:
        if side == 'buy':

            # Extracting Price dictionary from Binance
            price_dict = info_controller.strategy_info.price_dict

            # Buy amount is calculated from quoteOrderQty
            params["quoteOrderQty"] = amount  
            response = trade_client.new_order(**params) # unpack order
            
            # Renew each position cost
            info_controller.account_info.position_df.loc[symbol, "bid_price"] = price_dict[symbol]['close'].values[-1]
            
        elif side == 'sell':

            # Sell amount
            params["quantity"] = amount
            response = trade_client.new_order(**params)

            # Renew each position cost
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

## Example (Run on local code)

if __name__ == "__main__":

    params = {
    "symbol": "SOLUSDT",
    "side": "sell",
    "type": "MARKET",
    "quantity": 0.09,
    }

    client = SpotClient(g_api_key, g_secret_key, base_url="https://api2.binance.com")

    try:

        response = client.new_order(**params)
        logging.info(response)

    except ClientError as error:

        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
