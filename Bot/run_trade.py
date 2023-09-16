from binance.spot import Spot as SpotClient

from information import Info_Controller
from Bot.data_utils import get_market_prices
from Bot.strategies import *
from Bot.trade_utils import create_order, cancel_order

import pandas as pd

from privateconfig import *  # import the api keys

import time


def get_datetime_from_timestamp(timestamp):
    '''convert timestamp to datetime'''
    if type(timestamp) == str:
        timestamp = int(timestamp)
    return pd.to_datetime(timestamp, utc=True, unit='ms')


def run_trade(config_dict, info_controller, strategy):
    '''运行交易主程序'''


    client = SpotClient(api_key=g_api_key, api_secret=g_secret_key, base_url=API_urls[3])

    # 1. 更新信息
    info_controller.update_info_all(client)  # 更新账户信息，主要是用新的持仓情况更新position_df


    # 2. 获取市场信息 don't need api key
    price_dict = dict()
    candidate_symbols = info_controller.strategy_info.candidate_symbols
    for symbol in candidate_symbols:
        interval = "1m"
        prices_df = get_market_prices(symbol, interval)  # pd最下的是最新价格
        price_dict[symbol] = prices_df  # 保存全部candidate的价格信息
    info_controller.strategy_info.update_price_dict(price_dict)  # 更新价格信息

    # 3. Trade or standby
    order_s_list = strategy.get_order_list(info_controller, target_position=config_dict["fraction"])


    for order_s in order_s_list:
        order_id = create_order(info_controller, client, order_s)
        print(order_id)

    return


def before_start(config_dict):
    '''
    交易开始前运行的函数
    会自动修改config_dict的内容
    '''
    # 1. 初始化config_dict

    client = SpotClient(api_key=g_api_key,
                        api_secret=g_secret_key,
                        base_url=API_urls[3])

    # 1. 获取账号信息
    for i in range(5):
        try:
            info_controller = Info_Controller(config_dict, client)
            print("获取账户列表第{i}次，成功".format(i=i))
            break
        except:
            print("获取账户列表第{i}次，失败".format(i=i))
            time.sleep(10)
            continue


    # 3. 初始化交易策略
    strategy = Strategy_mean_reversion()  # mean reversion 策略

    return config_dict, info_controller, strategy


if __name__ == "__main__":
    util_config = dict(
        candidate_symbols=['compusdt', 'aaveusdt', 'solusdt', 'bsvusdt', 'aptusdt', 'etcusdt',
                           'ordiusdt', 'avaxusdt', 'fxsusdt', 'axsusdt', 'maskusdt',
                           'tonusdt', 'filusdt', 'dydxusdt', 'revousdt', 'arbusdt', 'ldousdt',
                           'yggusdt', 'xrpusdt', 'maticusdt'],
        quote_currency='usdt',
    )

    strategy_config = dict(
        market_t=100,
        fraction=0.3,  # 买入比例
    )

    config_dict = dict()
    config_dict.update(util_config)
    config_dict.update(strategy_config)

    API_urls = ["https://api.binance.com",
                "https://api-gcp.binance.com",
                "https://api1.binance.com",
                "https://api2.binance.com",
                "https://api3.binance.com",
                "https://api4.binance.com"]


    config_dict, info_controller, strategy = before_start(config_dict)

    while True:
        # try:
        time.sleep(1.)
        run_trade(config_dict, info_controller, strategy)
        print("执行完毕")
        time.sleep(30.)
        # except:
        #     config_dict, my_spot_account_s, strategy = before_start(config_dict)
        #     continue
