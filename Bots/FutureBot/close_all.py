# 全部平仓代码，用于策略调试
# 1. 初始化info controller
# 2. 获取全部持仓标的
# 3. 遍历全部持仓标的，平仓
from binance.spot import Spot as SpotClient
from privateconfig import *  # import the api keys

from utils.information import Info_Controller
from utils.trade_utils import create_order, Order_Structure
from utils.data_utils import get_decimal_precision
from strategies import strategy_utils

import time

def before_start(config_dict, api_url):
    '''
    交易开始前运行的函数
    会自动修改config_dict的内容
    '''
    # 1. 初始化config_dict

    client = SpotClient(api_key=g_api_key,
                        api_secret=g_secret_key,
                        base_url=api_url)

    # 1. 获取账号信息
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
    生成单个平仓订单
    '''
    position_df = info_controller.account_info.position_df
    order = Order_Structure()

    order.symbol = symbol   # 标的
    order.direction = 'sell'  # 交易方向
    order.amount = position_df.loc[symbol, "free"]
    stepDecimal = get_decimal(client, symbol)
    order.amount = strategy_utils.np_round_floor(order.amount, stepDecimal) # 交易数量

    return order


def get_decimal(client, temp_symbol):
    '''获取标的的交易精度'''
    temp_info_dict = client.exchange_info(symbol=temp_symbol)
    temp_stepSize = temp_info_dict['symbols'][0]['filters'][1]['stepSize']
    temp_decimal_precision = get_decimal_precision(temp_stepSize)
    return temp_decimal_precision


def get_all_orders(info_controller:Info_Controller, client:SpotClient) -> list:
    '''
    生成所有需要平仓的订单
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
    1. 获取全部持仓标的，生成Order Structure
    2. 生成订单
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

