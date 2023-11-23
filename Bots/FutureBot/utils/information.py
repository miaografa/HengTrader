import pandas as pd
import numpy as np
from Bots.FutureBot.utils.data_utils import get_decimal_precision, seperate_symbol_info_from_dict
from binance.um_futures import UMFutures
from Bots.FutureBot.privateconfig import g_api_key, g_secret_key


class Info_Controller():
    '''信息控制器'''
    def __init__(self, config_dict, client, use_strategy=True):
        self.client = client
        self.use_strategy = use_strategy
        self.account_info = Account_Info(config_dict)
        if self.use_strategy:
            self.strategy_info = Strategy_Info(config_dict)
        self._init_info_all(client)

    def _init_info_all(self, client):
        self.account_info.init_info(client)
        if self.use_strategy:
            self.strategy_info.init_info(client)

    def update_info_all(self, client):
        self.account_info.update_info(client)
        if self.use_strategy:
            self.strategy_info.update_info(client)

    def get_price_now(self, symbol):
        '''
        获取价格信息
        '''
        price_info = self.client.ticker_price(symbol)
        return float(price_info['price'])


class Info_Interface():
    def __init__(self):
        pass

    def init_info(self, client):
        pass

    def update_info(self, client):
        pass


class Account_Info(Info_Interface):
    '''
    账户的信息
    持仓的信息,或者历史持仓信息
    '''
    def __init__(self, config_dict):
        super().__init__()
        self.position_df = None
        self.USDT_value = None
        self.account_value = None

    def init_info(self, client):
        '''
        1. init "position_df"
            1. init "balance"
            2. init "is_hold"
            3. init "bid_price" for the holds
        '''
        account:dict = client.account()  # Get account info

        # 1. USDT value
        self.USDT_value = float(account['availableBalance'])
        self.account_value = account['totalWalletBalance']  # 账户价值

        # 2. account position info
        position_df = pd.DataFrame(account['positions'])
        position_df.set_index('symbol', inplace=True, drop=True)

        # 格式转换
        convert_dict = {
            'unrealizedProfit': float,
            'leverage': float,
            'entryPrice': float,
            'positionAmt': float,
                        }

        position_df = position_df.astype(convert_dict)
        # 计算是否已经持仓
        position_df["is_hold"] = np.where(np.abs(position_df['positionAmt']) > 0, True, False)

        self.position_df = position_df

        return


    def update_info(self, client):
        '''
        update free, locked value
        '''
        account: dict = client.account()  # Get account info

        # 1. USDT value
        self.USDT_value = float(account['availableBalance'])
        self.account_value = account['totalWalletBalance']  # 账户价值

        # 2. account position info
        position_df = pd.DataFrame(account['positions'])
        position_df.set_index('symbol', inplace=True, drop=True)

        # 格式转换
        convert_dict = {
            'unrealizedProfit': float,
            'leverage': float,
            'entryPrice': float,
            'positionAmt': float,
        }

        position_df = position_df.astype(convert_dict)
        # 计算是否已经持仓
        position_df["is_hold"] = np.where(np.abs(position_df['positionAmt']) > 0, True, False)

        self.position_df = position_df
        return

    def get_symbols_held_sets(self):
        # todo
        held_set = set(self.position_df[self.position_df["is_hold"]].index.values)
        un_held_set = set(self.position_df[~self.position_df["is_hold"]].index.values)
        return held_set, un_held_set


class Strategy_Info(Info_Interface):
    '''策略的信息'''
    def __init__(self, config_dict):
        super().__init__()
        self.quote_currency = config_dict['quote_currency']
        self.candidate_symbols = config_dict['candidate_symbols']
        self.base_currencies = [x[:-4] for x in config_dict['candidate_symbols']]
        # 改成大写
        self.candidate_symbols = [x.upper() for x in self.candidate_symbols]
        self.base_currencies = [x.upper() for x in self.base_currencies]
        return


    def init_info(self, client):
        '''
        self.trade_info_df:
            dataframe
            index_col: symbol
            value_col: theta
        self.price_dict:
            {symbol: price_df}
        '''
        self.exchange_info_df = self.update_market_info(client)
        self.check_symbols(client)
        self.exchange_info_df['theta'] = 0.001
        self.price_dict = dict()  # price_dict
        return


    def update_market_info(self, client):
        '''
        更新市场信息
        '''
        exchange_info = client.exchange_info()
        exchange_info_df = pd.DataFrame([seperate_symbol_info_from_dict(x) for x in exchange_info['symbols']])
        exchange_info_df.set_index('symbol', inplace=True)
        exchange_info_df = exchange_info_df[exchange_info_df['quoteAsset'] == 'USDT']
        exchange_info_df = exchange_info_df[exchange_info_df['status'] == 'TRADING']
        return exchange_info_df


    def check_symbols(self, client):
        '''
        检查候选的交易对是否存在于市场交易对象中, 剔除不在市场交易对中的交易对
            self.candidate_symbols
            self.base_currencies
        reuturn:None

        '''
        market_symbols = set(self.exchange_info_df.index.values)
        remove_symbols = []

        # 检查候选的交易对是否存在于市场交易对象中
        symbol_in_market = True
        for symbol in self.candidate_symbols:
            if symbol not in market_symbols:
                print(f"Warning: {symbol} is not in market_symbols")
                remove_symbols.append(symbol)
                symbol_in_market = False
                continue
        if symbol_in_market:
            print("All candidate symbols are in market_symbols")
        else:
            for symbol in remove_symbols:
                self.candidate_symbols.remove(symbol)
                self.base_currencies.remove(symbol[:-4])
        return


    def update_price_dict(self, price_dict):
        self.price_dict = price_dict
        return



if __name__ == "__main__":
    util_config = dict(
        candidate_symbols=['AUTOUSDT', 'ETHBULLUSDT', 'BNBBULLUSDT', 'BNBBEARUSDT', 
        'SUSHIDOWNUSDT', 'TRBUSDT'],
        quote_currency='usdt',
    )
    strategy_config = dict(
        market_t=100,
        fraction=0.3,  # 买入比例
    )
    config_dict = dict()
    config_dict.update(util_config)
    config_dict.update(strategy_config)

    # API key/secret are required for user data endpoints
    client = UMFutures(key=g_api_key, secret=g_secret_key)

    info_c = Info_Controller(config_dict, client)
    print('----------------------------------------------------')
    print(info_c.account_info.position_df)
    print(info_c.account_info.account_value)

    print('----------------------------------------------------')
    symbol = "COMPUSDT"
    print(info_c.account_info.position_df.loc[symbol, 'positionAmt'])
    print(info_c.account_info.position_df.dtypes)
    print(info_c.account_info.position_df.loc[symbol])

    print('----------------------------------------------------')
    info_c.update_info_all(client)  # test update
    # print(info_c.strategy_info.exchange_info_df)
    print(info_c.strategy_info.exchange_info_df.dtypes)
    print(info_c.strategy_info.exchange_info_df.loc[symbol])