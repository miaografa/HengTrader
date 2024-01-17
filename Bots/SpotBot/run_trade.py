from binance.spot import Spot as SpotClient

import sys
sys.path.append(r'C:\Users\Admin\Desktop\\')

from Crypto_Bot.utils.information import Info_Controller
from Crypto_Bot.utils.data_utils import get_market_prices
from Crypto_Bot.utils.trade_utils import create_order
from Crypto_Bot.strategies.strategies import *

# import credentials
from Crypto_Bot.utils.privateconfig import *

import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)

def get_datetime_from_timestamp(timestamp):

    '''
    convert timestamp to datetime
    '''
    if type(timestamp) == str:
        timestamp = int(timestamp)

    return pd.to_datetime(timestamp, utc=True, unit='ms')

def run_trade(config_dict, info_controller, strategy, api_url):
    '''
    Run main trade bot
    '''
    client = SpotClient(api_key=g_api_key, api_secret=g_secret_key, base_url=api_url)

    # 1. Update info every instance
    # Update account info，mainly use newly traded position to update 'position_df'
    info_controller.update_info_all(client)  

    # 2. Get latest market info, don't need api key
    price_dict = dict()

    # 2.1 Get all candidate's price information
    candidate_symbols = info_controller.strategy_info.candidate_symbols

    for symbol in candidate_symbols:
        interval = "15m"
        prices_df = get_market_prices(symbol, interval)  # pd[-1] contains the latest price information (OHLC)
        price_dict[symbol] = prices_df  # Save all candidates price information

    # 2.2 Update BTC and ETH prices every instance
    for symbol in ["BTCUSDT", "ETHUSDT"]:
        interval = "15m"
        prices_df = get_market_prices(symbol, interval)  # pd[-1] contains the latest price information (OHLC)
        price_dict[symbol] = prices_df  # Save all BTC and ETH price information

    info_controller.strategy_info.update_price_dict(price_dict)  # Update prices info

    # 3. Trade or standby
    order_s_list = strategy.get_order_list(info_controller, target_position=config_dict["fraction"])

    for order_s in order_s_list:
        order_id = create_order(info_controller, client, order_s)
        print(order_id)

    return

def before_start(config_dict, api_url):
    '''
    Automatically change the content of config_dict
    '''
    # 1. Initialized config_dict

    client = SpotClient(api_key=g_api_key,
                        api_secret=g_secret_key,
                        base_url=api_url)

    # 1. Get Account information
    # Notification pushed in Mandarin

    for i in range(5):

        try:
            info_controller = Info_Controller(config_dict, client)
            print("获取账户列表第{i}次，成功".format(i=i))
            break

        except:
            print("获取账户列表第{i}次，失败".format(i=i))
            time.sleep(10)
            continue


    # 3. Initialized trading strategy
    # Mean reversion
    strategy = Strategy_mean_reversion() 

    return config_dict, info_controller, strategy

# Run the bot (Test case)
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
            fraction=0.1,  # Buy in portion
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
    
    api_url = API_urls[0]  # Initialized api_url
    config_dict, info_controller, strategy = before_start(config_dict, api_url)

    while True:
        i = 0
        #try:

        api_url = API_urls[i%6]
        time.sleep(1.)
        run_trade(config_dict, info_controller, strategy, api_url)
        print("执行完毕")
        time.sleep(480.)
            
        #except:
        #    api_url = API_urls[i%6]
        #    config_dict, my_spot_account_s, strategy = before_start(config_dict, api_url)
        #    i += 1
        #    continue