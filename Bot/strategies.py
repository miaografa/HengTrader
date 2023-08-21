import pandas as pd
import numpy as np
import random

# import cufflinks
# cufflinks.set_config_file(offline=True, theme='white')

from Bot.trade_utils import Order_Structure,Account_Structure
from Bot.strategy_utils import calculate_position_value, np_round_floor
from Bot.backtest import Backtest_trend_k


class StrategyInterface(object):
    def __init__(self, account):
        self.account = account
        pass

    def get_order_list(self, data, my_spot_account_s, target_position=1.):
        '''输入数据，得到交易订单'''
        pass

    def get_order(self):
        pass

class Strategy_Random(StrategyInterface):
    '''随机交易策略'''
    def __init__(self, account):
        super().__init__(account)

    def get_orders(self, data_df, target_position=1.):

        order = Order_Structure()
        order.symbol = self.account.base_currency + self.account.quote_currency

        position_value = calculate_position_value(price=data_df.close.values[-1], amount=self.account.balance_base_currency)
        is_hold = position_value > 0.1   # 判断是否持仓，价值大于0.1usd就是持有。

        if is_hold:
            order.direction = random.choice(['sell', 'hold'])
        else:
            order.direction = random.choice(['buy', 'hold'])

        if order.direction == 'buy':  # buy base currency
            balance = self.account.balance_quote_currency
            last_close = data_df.close.values[-1]
            order.amount = balance / last_close * target_position
            order.amount = np_round_floor(order.amount, 8)


        elif order.direction == 'sell':  # sell base currency
            order.amount = self.account.balance_base_currency
            order.amount = np_round_floor(order.amount, 2)

        elif order.direction == 'hold':  # buy base currency
            order.amount = 0

        return order


class Strategy_Test(StrategyInterface):
    '''随机交易策略'''
    def __init__(self, account):
        super().__init__(account)
        pass

    def get_order(self, data_df, target_position=1.):

        order = Order_Structure()
        order.symbol = self.account.base_currency + self.account.quote_currency

        position_value = calculate_position_value(price=data_df.close.values[-1], amount=self.account.balance_base_currency)

        order.direction = 'buy'
        if order.direction == 'buy':  # buy base currency
            balance = self.account.balance_quote_currency
            order.amount = balance * target_position
            order.amount = np_round_floor(order.amount, 8)

        elif order.direction == 'sell':  # sell base currency
            order.amount = self.account.balance_base_currency
            order.amount = np_round_floor(order.amount, 2)

        elif order.direction == 'hold':  # buy base currency
            order.amount = 0

        return order


class Strategy_trend(StrategyInterface):
    '''趋势跟踪策略'''

    def __init__(self, account, config_dict):
        super().__init__(account)
        self.k_1 = config_dict['k_1']
        self.k_2 = config_dict['k_2']


    def get_order(self, data_df, target_position=1.):
        '''趋势跟踪策略'''

        order = Order_Structure()
        order.symbol = self.account.base_currency + self.account.quote_currency

        position_value = calculate_position_value(price=data_df.close.values[-1],
                                                  amount=self.account.balance_base_currency)
        is_hold = position_value > 0.5  # 判断是否持仓，价值大于0.5 usd就是持有。

        # 初始化features表格
        features_df = pd.DataFrame()
        features_df['SMA_k_1'] = data_df['close'].rolling(self.k_1).mean()
        features_df['SMA_k_2'] = data_df['close'].rolling(self.k_2).mean()
        features_df['close'] = data_df['close']

        is_below_avg_prev = features_df['SMA_k_1'].values[-2] < features_df['SMA_k_2'].values[-2]
        is_below_avg_now = features_df['SMA_k_1'].values[-1] < features_df['SMA_k_2'].values[-1]

        # 判断交易方向
        if not is_hold:
            if is_below_avg_prev and not is_below_avg_now:  # 价格上穿5日均线
                order.direction = 'buy'
            else:
                order.direction = 'hold'
        else:  # is hold
            if not is_below_avg_prev and is_below_avg_now:  # 价格下穿5日均线
                order.direction = 'sell'
            else:
                order.direction = 'hold'

        # 计算买入量
        if order.direction == 'buy':  # buy base currency
            balance = self.account.balance_quote_currency
            order.amount = balance * target_position
            order.amount = np_round_floor(order.amount, 8)

        elif order.direction == 'sell':  # sell base currency
            order.amount = self.account.balance_base_currency
            order.amount = np_round_floor(order.amount, 2)

        elif order.direction == 'hold':  # buy base currency
            order.amount = 0

        return order


class Strategy_mean_reversion(StrategyInterface):
    '''均值复归策略'''
    def __init__(self, account):
        super().__init__(account)

    def get_theta(self, data_df):
        Boll_df = pd.DataFrame(index=data_df.index)

        Boll_df['mean_20'] = data_df[['close']].ewm(span=20, adjust=False).mean()
        Boll_df['std_20'] = data_df[['close']].ewm(span=20, adjust=False).std()
        Boll_df['close'] = data_df['close']

        Boll_df.dropna(inplace=True)

        # 计算偏离度 theta = (p - ma) / sigma
        Boll_df['theta'] = (Boll_df['close'] - Boll_df['mean_20']) / Boll_df['std_20']
        return Boll_df['theta'].values[-1]


    def get_order_list(self, data_dict, target_position=1.):
        '''趋势跟踪策略'''
        order_list = []

        currency_info_df = self.account.currency_info_df
        for symbol in self.account.candidate_symbols_list:
            data_df = data_dict[symbol]
            # 计算当前的持仓仓位
            position_value = calculate_position_value(price=data_df.close.values[-1],
                                                      amount=currency_info_df.loc[symbol, "balance"])
            is_hold = position_value > 0.5  # 判断是否持仓，价值大于0.5 usd就是持有。
            currency_info_df.loc[symbol, "is_hold"] = is_hold

            theta =  self.get_theta(data_df)
            currency_info_df.loc[symbol, "theta"] = theta

        # 买入逻辑
        unhold_currency_df:pd.DataFrame = currency_info_df[currency_info_df["is_hold"] == False]
        unhold_currency_df = unhold_currency_df.sort_values(by="theta", ascending=True)  # 用theta进行排序
        # 1. 选择theta最小的symbol作为交易对象
        target_symbol = unhold_currency_df.index[0]
        order = self.get_order(target_symbol, unhold_currency_df.loc[target_symbol, "theta"],
                               unhold_currency_df.loc[target_symbol, "is_hold"], target_position)
        order_list.append(order)
        # 2. 选择theta最大的symbol作为交易对象
        target_symbol = unhold_currency_df.index[-1]  # 选择theta最小的symbol作为交易对象
        order = self.get_order(target_symbol, unhold_currency_df.loc[target_symbol, "theta"],
                               unhold_currency_df.loc[target_symbol, "is_hold"], target_position)
        order_list.append(order)
        order = None

        # 卖出逻辑
        hold_currency_df = currency_info_df[currency_info_df["is_hold"] == True]
        if len(hold_currency_df):  # 如果有持仓，对于所有持仓的进行判断是否需要出售
            for target_symbol in hold_currency_df.index:
                target_symbol_price = data_dict[target_symbol]['close'].values[-1]
                order = self.get_order(target_symbol, hold_currency_df.loc[target_symbol, "theta"],
                                       hold_currency_df.loc[target_symbol, "is_hold"], target_position,symbol_price=target_symbol_price, data_df=hold_currency_df)
                order_list.append(order)
                order = None

        return order_list

    def get_order(self, symbol, theta, is_hold, target_position, symbol_price=None, data_df=None):

        order = Order_Structure()
        order.symbol = symbol
        # 判断交易方向

        if not is_hold:
            is_buy = self.judge_buy(theta, )  # 买入逻辑
            if is_buy:
                order.direction = 'buy'
            else:
                order.direction = 'hold'
        else:  # is hold
            bid_price = data_df.loc[symbol, "bid_price"]
            is_sell = self.judge_sell(symbol_price, bid_price)  # 卖出逻辑
            if is_sell:
                order.direction = 'sell'
            else:
                order.direction = 'hold'

        # 计算买入量
        if order.direction == 'buy':  # buy base currency
            balance = self.account.balance_quote_currency
            order.amount = self.account.asset_valuation * target_position
            if order.amount > balance:  # the planed amount is greater than balance, make the planed amount smaller.
                if balance > 10:
                    order.amount = balance
                else:
                    order.direction == 'hold'  # Too little cash to buy anything

            order.amount = np_round_floor(order.amount, 8)

        elif order.direction == 'sell':  # sell base currency
            order.amount = data_df.loc[symbol, "balance"]
            order.amount = np_round_floor(order.amount, 2)

        elif order.direction == 'hold':  # buy base currency
            order.amount = 0

        return order

    def judge_buy(self, theta):
        '''买入判断'''
        if theta < -2 or theta > 2:
            return True
        else:
            return False

    def judge_sell(self, symbol_price, bid_price):
        '''卖出判断'''
        current_rtn = (symbol_price - bid_price) / bid_price
        if current_rtn < -0.002:  # 止损平仓
            return True
        elif current_rtn > 0.006: # 止盈平仓  # todo 加入持仓时间的平仓
            return True
        else:
            return False


