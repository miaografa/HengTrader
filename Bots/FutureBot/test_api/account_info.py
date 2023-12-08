#!/usr/bin/env python

from binance.lib.utils import config_logging
from binance.error import ClientError
from binance.um_futures import UMFutures
from Bots.FutureBot.privateconfig import g_api_key, g_secret_key
from Bots.FutureBot.utils.data_utils import convert_df_type

import pandas as pd


if __name__ == '__main__':
    # 测试获取账户的设置信息
    um_futures_client = UMFutures(key=g_api_key, secret=g_secret_key)
    # position_mode = um_futures_client.get_position_mode()  # 1: 单向持仓模式 2: 双向持仓模式
    # multi_asset_mode = um_futures_client.get_multi_asset_mode()  # 1: 全仓模式 2: 逐仓模式
    # position_margin_history = um_futures_client.get_position_margin_history('SOLUSDT')
    # leverage_brackets = um_futures_client.leverage_brackets(symbol='SOLUSDT')
    #
    # print("position_mode: ", position_mode)
    # print("multi_asset_mode: ", multi_asset_mode)
    # print("position_margin_history: ", position_margin_history)
    # print("leverage_brackets: ", leverage_brackets)


    # 账户相关信息
    account = um_futures_client.account()

    # print("USDT balance: ", account['availableBalance'])
    print("available balance: ", account['availableBalance'])  # 可用余额
    print("total Wallet Balance: ", account['totalWalletBalance'])  # 账户价值
    print("total Margin Balance: ", account['totalMarginBalance'])

    positions = account['positions']  # 各种合约的持仓信息
    positions_df = convert_df_type(pd.DataFrame(positions))

    print(positions_df)

    print(positions_df.dtypes)

    positions_df.set_index('symbol', inplace=True)
    # print(positions_df.loc['OMGUSDT'])
    print(positions_df['notional'])
    print(positions_df['notional'].sum())

