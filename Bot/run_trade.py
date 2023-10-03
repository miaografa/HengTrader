from binance.spot import Spot as SpotClient

import sys

sys.path.append('.')

from Bot.information import Info_Controller
from Bot.data_utils import get_market_prices
from Bot.strategies.strategies import *
from Bot.trade_utils import create_order

from privateconfig import *  # import the api keys

import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)


def get_datetime_from_timestamp(timestamp):
    '''convert timestamp to datetime'''
    if type(timestamp) == str:
        timestamp = int(timestamp)
    return pd.to_datetime(timestamp, utc=True, unit='ms')


def run_trade(config_dict, info_controller, strategy, api_url):
    '''运行交易主程序'''
    client = SpotClient(api_key=g_api_key, api_secret=g_secret_key, base_url=api_url)

    # 1. 更新信息
    info_controller.update_info_all(client)  # 更新账户信息，主要是用新的持仓情况更新position_df


    # 2. 获取市场信息 don't need api key
    price_dict = dict()
    candidate_symbols = info_controller.strategy_info.candidate_symbols
    for symbol in candidate_symbols:
        interval = "15m"
        prices_df = get_market_prices(symbol, interval)  # pd最下的是最新价格
        price_dict[symbol] = prices_df  # 保存全部candidate的价格信息
    info_controller.strategy_info.update_price_dict(price_dict)  # 更新价格信息

    # 3. Trade or standby
    order_s_list = strategy.get_order_list(info_controller, target_position=config_dict["fraction"])

    for order_s in order_s_list:
        order_id = create_order(info_controller, client, order_s)
        print(order_id)

    return


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
        candidate_symbols= ['TRBUSDT', 'CREAMUSDT', 'QNTUSDT', 'MLNUSDT', 'KP3RUSDT', 'AAVEUSDT', 
        'ALCXUSDT', 'GMXUSDT', 'COMPUSDT', 'LTCUSDT', 'EGLDUSDT', 'AUCTIONUSDT', 'ZECUSDT', 'LINKUSDT', 
        'DASHUSDT', 'ANTUSDT', 'FXSUSDT', 'SOLUSDT', 'APTUSDT', 'SSVUSDT', 'UNFIUSDT', 'MOVRUSDT', 
        'MULTIUSDT', 'WINGUSDT', 'NEOUSDT', 'XVSUSDT', 'INJUSDT', 'ETCUSDT', 'CVXUSDT', 'AVAXUSDT', 
        'OGUSDT', 'AXSUSDT', 'LPTUSDT', 'WLDUSDT', 'FTTUSDT', 'ATOMUSDT', 'CYBERUSDT', 'SNXUSDT', 
        'FORTHUSDT', 'MASKUSDT', 'FRONTUSDT', 'PYRUSDT', 'RNDRUSDT', 'ARKUSDT', 'BONDUSDT', 'GLMRUSDT', 
        'KNCUSDT', 'UNIUSDT', 'LUNAUSDT', 'AGLDUSDT', 'MTLUSDT', 'RUNEUSDT', 'HIFIUSDT', 'ICPUSDT', 
        'STORJUSDT', 'BELUSDT', 'FILUSDT', 'IMXUSDT', 'DOTUSDT', 'CRVUSDT', 'LQTYUSDT', 'WAVESUSDT', 
        'TOMOUSDT', 'MCUSDT', 'HIGHUSDT', 'GALUSDT', 'API3USDT', 'OPUSDT', 'DYDXUSDT', 'FISUSDT', 
        'HOOKUSDT', 'FLMUSDT', 'COMBOUSDT', 'PENDLEUSDT', 'THETAUSDT', 'PHBUSDT', 'NEARUSDT', 
        'LOOMUSDT', 'SUSHIUSDT', 'LDOUSDT', 'GTCUSDT', 'WTCUSDT', 'ARBUSDT', 'PNTUSDT', 'MAGICUSDT', 
        'POLSUSDT', 'EDUUSDT', 'CELOUSDT', 'BURGERUSDT', 
        'SXPUSDT', 'ARKMUSDT', 'APEUSDT', 'BLZUSDT', 'YGGUSDT', 'LITUSDT', 'EOSUSDT', 'CAKEUSDT', 
        'PROSUSDT', 'STGUSDT', 'STXUSDT', 'PERPUSDT', 'PHAUSDT', 'RDNTUSDT', 'XRPUSDT', 'STPTUSDT', 
        'DREPUSDT', 'MAVUSDT', 'ONTUSDT', 'OCEANUSDT', 'ELFUSDT', 'OAXUSDT', 'MATICUSDT', 'SYNUSDT', 
        'MINAUSDT', 'KAVAUSDT', '1INCHUSDT', 'GFTUSDT', 'SUIUSDT', 'FETUSDT', 'ENJUSDT', 'C98USDT', 
        'FLOWUSDT', 'FIDAUSDT', 'EURUSDT', 'ZRXUSDT', 'HARDUSDT', 'SEIUSDT', 'ALGOUSDT', 'MANAUSDT', 
        'SANDUSDT', 'JOEUSDT', 'BSWUSDT', 'ATAUSDT', 'BAKEUSDT', 'QUICKUSDT', 'IDUSDT', 'AGIXUSDT', 
        'CFXUSDT', 'KLAYUSDT', 'DUSKUSDT', 'DARUSDT', 'OGNUSDT', 'GMTUSDT', 'ASTRUSDT', 'XLMUSDT', 
        'TRUUSDT', 'WOOUSDT', 'ACAUSDT', 'FTMUSDT', 'ADAUSDT'],
        quote_currency='usdt',
    )

    strategy_config = dict(
        market_t=100,
        fraction=0.1,  # 买入比例
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
    
    api_url = API_urls[0]  # 初始化api_url
    config_dict, info_controller, strategy = before_start(config_dict, api_url)

    while True:
        i = 0
        try:
            api_url = API_urls[i%6]
            time.sleep(1.)
            run_trade(config_dict, info_controller, strategy, api_url)
            print("执行完毕")
            time.sleep(60.)
        except:
            api_url = API_urls[i%6]
            config_dict, my_spot_account_s, strategy = before_start(config_dict, api_url)
            i += 1
            continue


