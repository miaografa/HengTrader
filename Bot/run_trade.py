from huobi.client.account import AccountClient  # account info related
from huobi.client.trade import TradeClient

from Bot.data_utils import *
from Bot.strategies import *
from Bot.trade_utils import Account_Structure, create_order, cancel_order

import pandas as pd

from privateconfig import *  # import the api keys

import time


def get_datetime_from_timestamp(timestamp):
    '''convert timestamp to datetime'''
    if type(timestamp) == str:
        timestamp = int(timestamp)
    return pd.to_datetime(timestamp, utc=True, unit='ms')


def run_trade(config_dict):
    '''运行交易主程序'''
    quote_currency = config_dict['quote_currency']

    # 1. 获取账号信息
    account_client = AccountClient(api_key=g_api_key, secret_key=g_secret_key)

    for i in range(5):
        try:
            account_list = account_client.get_accounts()
            print("获取账户列表第{i}次，成功".format(i=i))
            break
        except:
            print("获取账户列表第{i}次，失败".format(i=i))
            time.sleep(1)
            continue

    # 获取spot账户id
    spot_account = account_list[0]
    assert spot_account.type == 'spot'
    # get balance of spot account
    account_balance_list = account_client.get_balance(spot_account.id)

    # 创建本地的account对象，便于代码调用
    my_spot_account_s = Account_Structure(spot_account.id)

    currency_info_df = config_dict['currency_info']  # 取出info df
    base_currency_list = config_dict['base_currencies']
    for account_balance_obj in account_balance_list:  # record balances of the quote and candidate currencies.
        symbol = account_balance_obj.currency + quote_currency
        if account_balance_obj.currency == quote_currency and account_balance_obj.type == 'trade':
            # balance type 可能是 'trade' or 'frozen'
            balance_quote_currency = float(account_balance_obj.balance)
        if account_balance_obj.currency in base_currency_list and account_balance_obj.type == 'trade':
            # balance type 可能是 'trade' or 'frozen'
            currency_info_df.loc[symbol, "balance"] = float(account_balance_obj.balance)

    my_spot_account_s.balance_quote_currency = balance_quote_currency
    my_spot_account_s.currency_info_df = currency_info_df  # todo 整理这段代码
    my_spot_account_s.candidate_symbols_list = config_dict['candidate_symbols']

    # record account valuation
    account_type = "spot"
    asset_valuation = account_client.get_account_asset_valuation(account_type=account_type, valuation_currency="usd")
    my_spot_account_s.asset_valuation = float(asset_valuation.balance)

    # 2. 获取市场信息 don't need api key
    price_dict = dict()
    for symbol in config_dict['candidate_symbols']:
        interval = CandlestickInterval.MIN1
        size = config_dict["market_t"]
        prices_df = get_market_prices(symbol, interval, size)  # 顺序倒置了，所以pd最下的是最新价格。
        price_dict[symbol] = prices_df  # 保存全部candidate的价格信息

    # 3. Trade or standby
    # strategy = Strategy_trend(my_spot_account_s, config_dict)  # 趋势跟踪策略
    strategy = Strategy_mean_reversion(my_spot_account_s, config_dict)  # mean reversion 策略
    order_s_list = strategy.get_order_list(price_dict, target_position=0.3)  # todo 仓位设置不合理

    trade_client = TradeClient(api_key=g_api_key, secret_key=g_secret_key)

    for order_s in order_s_list:
        order_id = create_order(my_spot_account_s.id, trade_client, order_s)
        print(order_id)

    return


def find_best_k_pair(config_dict):
    '''通过回测寻找最优的k均线组合'''
    interval = CandlestickInterval.MIN1
    symbol = config_dict["symbol"]
    price_df = get_market_prices(symbol, interval, config_dict['backtesting_t'])

    backtesting_trend = Backtest_trend_k()
    (k1, k2) = backtesting_trend.backtesting_all_k_pairs(config_dict['k1_list'], config_dict['k2_list'], price_df)

    return k1, k2


def before_start():
    '''
    交易开始前运行的函数
    会自动修改config_dict的内容
    '''
    global config_dict
    config_dict['base_currencies'] = [x[:-4] for x in config_dict['candidate_symbols']]

    currency_info_df = pd.DataFrame()
    currency_info_df["symbol"] = config_dict['candidate_symbols']
    currency_info_df["base_currency"] = config_dict['base_currencies']
    currency_info_df = currency_info_df.set_index("symbol")
    currency_info_df["balance"] = 0
    currency_info_df["is_hold"] = False
    currency_info_df["theta"] = 0

    config_dict["currency_info"] = currency_info_df



if __name__ == "__main__":
    config_dict = dict(
        candidate_symbols = ['compusdt', 'aaveusdt', 'solusdt', 'bsvusdt', 'aptusdt', 'etcusdt',
       'ordiusdt', 'avaxusdt', 'fxsusdt', 'axsusdt', 'maskusdt',
       'tonusdt', 'filusdt', 'dydxusdt', 'revousdt', 'arbusdt', 'ldousdt',
       'yggusdt', 'xrpusdt', 'maticusdt'],
        market_t = 100,
        quote_currency='usdt',

    )
    before_start()

    while True:
        try:
            time.sleep(10.)
            run_trade(config_dict)
            print("执行完毕")
        except:
            continue
