from binance.spot import Spot as SpotClient

import sys
sys.path.append(r'C:\Users\Admin\Desktop\\')

# import credentials
from Crypto_Bot.utils.privateconfig import *
from Crypto_Bot.utils.information import Info_Controller
from Crypto_Bot.utils.trade_utils import create_order, Order_Structure
from Crypto_Bot.utils.data_utils import get_decimal_precision
from Crypto_Bot.strategies import strategy_utils

import time

def before_start(config_dict, api_url):
    '''
    Before closing all trade positions
    Automatically update config_dict 
    '''
    # 1. Initialized config_dict

    client = SpotClient(api_key=g_api_key,
                        api_secret=g_secret_key,
                        base_url=api_url)

    # 1. Get Account info
    # Notification pushed in Mandarin

    for i in range(5):
        try:
            info_controller = Info_Controller(config_dict, client, use_strategy=False)
            print("获取账户列表第{i}次，成功".format(i=i))
            break
        except:
            print("获取账户列表第{i}次，失败".format(i=i))
            time.sleep(2)
            continue

    return config_dict, info_controller

def get_close_order(symbol, info_controller:Info_Controller, client:SpotClient)-> Order_Structure:
    '''
    Generate each closing trade
    '''
    position_df = info_controller.account_info.position_df
    order = Order_Structure()

    order.symbol = symbol   
    order.direction = 'sell'  
    order.amount = position_df.loc[symbol, "free"]
    stepDecimal = get_decimal(client, symbol)
    order.amount = strategy_utils.np_round_floor(order.amount, stepDecimal) # trade amount

    return order

def get_decimal(client, temp_symbol):
    '''
    Get data precision for each closing trade
    '''
    temp_info_dict = client.exchange_info(symbol=temp_symbol)
    temp_stepSize = temp_info_dict['symbols'][0]['filters'][1]['stepSize']
    temp_decimal_precision = get_decimal_precision(temp_stepSize)

    return temp_decimal_precision

def get_all_orders(info_controller:Info_Controller, client:SpotClient) -> list:
    '''
    Generate all closing orders to close every positions
    '''
    orders = []
    position_df = info_controller.account_info.position_df
    hold_df = position_df[position_df["is_hold"]]
    for symbol in hold_df.index:
        order = get_close_order(symbol, info_controller, client)
        orders.append(order)

    return orders

def close_all(info_controller, api_url):
    '''
    1. Retrieve all position in my account and generate Order Structure()
    2. Generate closing orders for every existing positions
    '''
    client = SpotClient(api_key=g_api_key, api_secret=g_secret_key, base_url=api_url)
    orders = get_all_orders(info_controller, client)
    for order_s in orders:
        order_id = create_order(info_controller, client, order_s)
        print(order_id)

    return

if __name__ == "__main__":
    api_url = "https://api.binance.com"
    config_dict, info_controller = before_start(config_dict=[], api_url=api_url)
    close_all(info_controller, api_url)