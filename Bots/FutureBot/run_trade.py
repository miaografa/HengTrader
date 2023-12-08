
import sys
sys.path.append('../')
from utils.information import Info_Controller
from utils.data_utils import get_market_prices
from utils.trade_utils import create_order
from strategies.strategies import *
from binance.um_futures import UMFutures
from Bots.FutureBot.privateconfig import g_api_key, g_secret_key


import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)


def get_datetime_from_timestamp(timestamp):
    '''convert timestamp to datetime'''
    if type(timestamp) == str:
        timestamp = int(timestamp)
    return pd.to_datetime(timestamp, utc=True, unit='ms')


def run_trade(config_dict, info_controller, strategy, hedge_strategy, api_url=None):
    '''运行交易主程序'''
    client = UMFutures(key=g_api_key, secret=g_secret_key)

    # 1. 更新信息
    info_controller.update_info_all(client)  # 更新账户信息，主要是用新的持仓情况更新position_df

    # 2. 获取市场信息 don't need api key
    price_dict = dict()

    # 2.1 获取全部candidate的价格信息
    candidate_symbols = info_controller.strategy_info.candidate_symbols
    for symbol in candidate_symbols:
        interval = "15m"
        prices_df = get_market_prices(symbol, interval)  # pd最下的是最新价格
        price_dict[symbol] = prices_df  # 保存全部candidate的价格信息

    # 2.2 更新BTC ETH 价格信息
    for symbol in ["BTCUSDT", "ETHUSDT"]:
        interval = "15m"
        prices_df = get_market_prices(symbol, interval)  # pd最下的是最新价格
        price_dict[symbol] = prices_df  # 保存全部candidate的价格信息

    info_controller.strategy_info.update_price_dict(price_dict)  # 更新价格信息

    # 3. Trade or standby
    order_s_list = strategy.get_order_list(info_controller, target_position=config_dict["fraction"])

    # 4. 对冲
    hedge_order_s_list = hedge_strategy.get_order_list(info_controller)

    for order_s in order_s_list:
        if order_s:
            order_id = create_order(client, info_controller, order_s)
            print(order_id)

    for order_s in hedge_order_s_list:
        if order_s:
            order_id = create_order(client, info_controller, order_s)
            print(order_id)

    return


def before_start(config_dict, api_url=None):
    '''
    交易开始前运行的函数
    会自动修改config_dict的内容
    '''
    # 1. 初始化config_dict

    client = UMFutures(key=g_api_key, secret=g_secret_key)

    # 1. 初始化infoController
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

    # 4. 对冲仓位控制
    hedge_strategy = Hedge_Strategy()  # 对冲策略

    return config_dict, info_controller, strategy, hedge_strategy


if __name__ == "__main__":
    util_config = dict(
        candidate_symbols= ['ETHUSDT', 'BCHUSDT', 'XRPUSDT', 'EOSUSDT', 'LTCUSDT',
       'TRXUSDT', 'ETCUSDT', 'LINKUSDT', 'XLMUSDT', 'ADAUSDT', 'XMRUSDT',
       'DASHUSDT', 'ZECUSDT', 'XTZUSDT', 'BNBUSDT', 'ATOMUSDT', 'ONTUSDT',
       'IOTAUSDT', 'BATUSDT', 'VETUSDT', 'NEOUSDT', 'QTUMUSDT',
       'IOSTUSDT', 'THETAUSDT', 'ALGOUSDT', 'ZILUSDT', 'KNCUSDT',
       'ZRXUSDT', 'COMPUSDT', 'OMGUSDT', 'DOGEUSDT', 'SXPUSDT',
       'KAVAUSDT', 'BANDUSDT', 'RLCUSDT', 'WAVESUSDT', 'MKRUSDT',
       'SNXUSDT', 'DOTUSDT', 'DEFIUSDT', 'YFIUSDT', 'BALUSDT', 'CRVUSDT',
       'TRBUSDT', 'RUNEUSDT', 'SUSHIUSDT', 'EGLDUSDT', 'SOLUSDT',
       'ICXUSDT', 'STORJUSDT', 'BLZUSDT', 'UNIUSDT', 'AVAXUSDT',
       'FTMUSDT', 'ENJUSDT', 'FLMUSDT', 'RENUSDT', 'KSMUSDT', 'NEARUSDT',
       'AAVEUSDT', 'FILUSDT', 'RSRUSDT', 'LRCUSDT', 'MATICUSDT',
       'OCEANUSDT', 'BELUSDT', 'CTKUSDT', 'AXSUSDT', 'ALPHAUSDT',
       'ZENUSDT', 'SKLUSDT', 'GRTUSDT', '1INCHUSDT', 'CHZUSDT',
       'SANDUSDT', 'ANKRUSDT', 'LITUSDT', 'UNFIUSDT', 'REEFUSDT',
       'RVNUSDT', 'SFPUSDT', 'XEMUSDT', 'COTIUSDT', 'CHRUSDT', 'MANAUSDT',
       'ALICEUSDT', 'HBARUSDT', 'ONEUSDT', 'LINAUSDT', 'STMXUSDT',
       'DENTUSDT', 'CELRUSDT', 'HOTUSDT', 'MTLUSDT', 'OGNUSDT', 'NKNUSDT',
       'DGBUSDT', '1000SHIBUSDT', 'BAKEUSDT', 'GTCUSDT', 'BTCDOMUSDT',
       'IOTXUSDT', 'AUDIOUSDT', 'C98USDT', 'MASKUSDT', 'ATAUSDT',
       'DYDXUSDT', '1000XECUSDT', 'GALAUSDT', 'CELOUSDT', 'ARUSDT',
       'KLAYUSDT', 'ARPAUSDT', 'CTSIUSDT', 'LPTUSDT', 'ENSUSDT',
       'PEOPLEUSDT', 'ANTUSDT', 'ROSEUSDT', 'DUSKUSDT', 'FLOWUSDT',
       'IMXUSDT', 'API3USDT', 'GMTUSDT', 'APEUSDT', 'WOOUSDT',
       'JASMYUSDT', 'DARUSDT', 'GALUSDT', 'OPUSDT', 'INJUSDT', 'STGUSDT',
       'FOOTBALLUSDT', 'SPELLUSDT', '1000LUNCUSDT', 'LUNA2USDT',
       'LDOUSDT', 'CVXUSDT', 'ICPUSDT', 'APTUSDT', 'QNTUSDT',
       'BLUEBIRDUSDT', 'FETUSDT', 'FXSUSDT', 'HOOKUSDT', 'MAGICUSDT',
       'TUSDT', 'RNDRUSDT', 'HIGHUSDT', 'MINAUSDT', 'ASTRUSDT',
       'AGIXUSDT', 'PHBUSDT', 'GMXUSDT', 'CFXUSDT', 'STXUSDT', 'BNXUSDT',
       'ACHUSDT', 'SSVUSDT', 'CKBUSDT', 'PERPUSDT', 'TRUUSDT', 'LQTYUSDT',
       'USDCUSDT', 'IDUSDT', 'ARBUSDT', 'JOEUSDT', 'TLMUSDT', 'AMBUSDT',
       'LEVERUSDT', 'RDNTUSDT', 'HFTUSDT', 'XVSUSDT', 'BLURUSDT',
       'EDUUSDT', 'IDEXUSDT', 'SUIUSDT', '1000PEPEUSDT', '1000FLOKIUSDT',
       'UMAUSDT', 'RADUSDT', 'KEYUSDT', 'COMBOUSDT', 'NMRUSDT', 'MAVUSDT',
       'MDTUSDT', 'XVGUSDT', 'WLDUSDT', 'PENDLEUSDT', 'ARKMUSDT',
       'AGLDUSDT', 'YGGUSDT', 'DODOXUSDT', 'BNTUSDT', 'OXTUSDT',
       'SEIUSDT', 'BTCUSDT_231229', 'ETHUSDT_231229', 'CYBERUSDT',
       'HIFIUSDT', 'ARKUSDT', 'FRONTUSDT', 'GLMRUSDT', 'BICOUSDT',
       'BTCUSDT_240329', 'ETHUSDT_240329', 'STRAXUSDT', 'LOOMUSDT',
       'BIGTIMEUSDT', 'BONDUSDT', 'ORBSUSDT', 'STPTUSDT', 'WAXPUSDT',
       'BSVUSDT', 'RIFUSDT', 'POLYXUSDT', 'GASUSDT', 'POWRUSDT',
       'SLPUSDT', 'TIAUSDT', 'SNTUSDT', 'CAKEUSDT', 'MEMEUSDT', 'TWTUSDT',
       'TOKENUSDT', 'ORDIUSDT', 'STEEMUSDT', 'BADGERUSDT', 'ILVUSDT',
       'NTRNUSDT', 'MBLUSDT', 'KASUSDT', 'BEAMXUSDT', '1000BONKUSDT',
       'PYTHUSDT'],
        quote_currency='usdt',
    )

    strategy_config = dict(
        market_t=100,
        fraction=0.1,  # 买入比例
    )

    config_dict = dict()
    config_dict.update(util_config)
    config_dict.update(strategy_config)

    config_dict, info_controller, strategy, hedge_strategy = before_start(config_dict)

    while True:
        print('开始执行')
        try:
            time.sleep(2.)
            run_trade(config_dict, info_controller, strategy, hedge_strategy)
            print("执行完毕")
            time.sleep(480.)
        except:
            config_dict, my_spot_account_s, strategy, hedge_strategy = before_start(config_dict)
            continue


