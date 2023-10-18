import pandas as pd
import numpy as np
import random
import logging

from Bot.trade_utils import Order_Structure
from Bot.strategies.reverse_detector import Reverse_Detector, Features_Calculator
from strategy_utils import calculate_position_value, np_round_floor



class StrategyInterface(object):
    def __init__(self ):
        pass

    def get_order_list(self,):
        '''输入数据，得到交易订单'''
        pass

    def get_order(self):
        pass




class Strategy_mean_reversion(StrategyInterface):
    '''均值复归策略'''
    def __init__(self):
        super().__init__()
        self.reverse_detector = Reverse_Detector(model_save_path='./models/')
        self.features_calculator = Features_Calculator()


    def get_theta(self, data_df):
        Boll_df = pd.DataFrame(index=data_df.index)

        Boll_df['mean_20'] = data_df[['close']].ewm(span=20, adjust=False).mean()
        Boll_df['std_20'] = data_df[['close']].ewm(span=20, adjust=False).std()
        Boll_df['close'] = data_df['close']

        Boll_df.dropna(inplace=True)

        # 计算偏离度 theta = (p - ma) / sigma
        Boll_df['theta'] = (Boll_df['close'] - Boll_df['mean_20']) / Boll_df['std_20']
        return Boll_df['theta'].values[-1]


    def update_info(self, info_controller):
        '''
            1. 对于info_controller的信息进行更新
        '''
        data_dict = info_controller.strategy_info.price_dict
        candidate_symbols = info_controller.strategy_info.candidate_symbols

        for symbol in candidate_symbols:
            data_df = data_dict[symbol]
            theta = self.get_theta(data_df)
            info_controller.strategy_info.theta_info_df.loc[symbol,"theta"] = np.round(theta,4)

        # 1. 买入逻辑
        # 先判断是否持仓
        held_set, unheld_set = info_controller.account_info.get_symbols_held_sets()

        info_controller.strategy_info.theta_info_df["is_hold"] = False
        for symbol in candidate_symbols:
            if symbol in held_set:
                info_controller.strategy_info.theta_info_df.loc[symbol, "is_hold"] = True
            else:
                info_controller.strategy_info.theta_info_df.loc[symbol, "is_hold"] = False

        return info_controller

    def get_order_list(self, info_controller, target_position=1.):

        order_list = []
        # 1. 更新 inforcontroller 的 ishold 信息
        info_controller = self.update_info(info_controller)

        data_dict = info_controller.strategy_info.price_dict
        theta_info_df = info_controller.strategy_info.theta_info_df

        # 2. 更新并且记录btc 和 eth的features
        self.features_calculator.save_market_coin_data(data_dict["BTCUSDT"], coin_name="btc")
        self.features_calculator.save_market_coin_data(data_dict["ETHUSDT"], coin_name="eth")

        unhold_currency_df = theta_info_df[theta_info_df["is_hold"] == False]
        unhold_currency_df = unhold_currency_df.sort_values(by="theta", ascending=True)  # 用theta进行排序
        # 1. 选择theta较小的coin 作为交易对象
        target_unhold_currency_df = unhold_currency_df[unhold_currency_df["theta"] < -1]
        for target_symbol in target_unhold_currency_df.index:
            target_symbol_price = data_dict[target_symbol]['close'].values[-1]
            order = self.get_buy_order(target_symbol, unhold_currency_df.loc[target_symbol, "theta"],
                                   target_position, symbol_price=target_symbol_price, info_controller=info_controller)
            order_list.append(order)
        order = None

        # 2. 卖出逻辑
        hold_currency_df = theta_info_df[theta_info_df["is_hold"] == True]

        if len(hold_currency_df):  # 如果有持仓，对于所有持仓的进行判断是否需要出售
            for target_symbol in hold_currency_df.index:
                target_symbol_price = data_dict[target_symbol]['close'].values[-1]
                order = self.get_sell_order(target_symbol, hold_currency_df.loc[target_symbol, "theta"],
                                       target_position, symbol_price=target_symbol_price, info_controller=info_controller)
                order_list.append(order)
                order = None

        return order_list


    def get_buy_order(self, symbol, theta, target_position, symbol_price, info_controller):
        '''
            买入逻辑
            包括买入判断和买入量的计算
            return order
        '''
        order = Order_Structure()
        order.symbol = symbol

        is_buy = self.judge_buy(theta, symbol, info_controller)  # 买入逻辑
        if is_buy:
            order.direction = 'buy'
        else:
            order.direction = 'hold'

        # 计算买入量
        if order.direction == 'buy':  # buy base currency
            balance = info_controller.account_info.USDT_value
            if balance > 250:
                order.amount = 100.
            elif balance > 50:
                order.amount = 50.
            else:
                order.amount = 0.
                order.direction = 'hold'  # Too little cash to buy anything

            order.amount = np_round_floor(order.amount, 4)  # devided by the price!!!

            logging.info('--------------------------------------------------------')
            logging.info("order.symbol:{}".format(order.symbol))
            logging.info("target_position:{}".format(target_position))
            logging.info("balance:{}".format(balance))
            logging.info("balance * target_position:{}".format(balance * target_position))
            logging.info("symbol_price: {}".format(symbol_price))
            logging.info('--------------------------------------------------------')

        elif order.direction == 'hold':  # buy base currency
            order.amount = 0

        return order


    def get_sell_order(self, symbol, theta, target_position, symbol_price, info_controller):
        '''
        当前版本target_position 没有用到
        '''
        order = Order_Structure()
        order.symbol = symbol
        # 判断交易方向
        bid_price = info_controller.account_info.position_df.loc[symbol, "bid_price"]
        is_sell = self.judge_sell(symbol, theta, symbol_price, bid_price, info_controller)  # 卖出逻辑
        if is_sell:
            order.direction = 'sell'
        else:
            order.direction = 'hold'

        if order.direction == 'sell':  # sell base currency
            order.amount = info_controller.account_info.position_df.loc[symbol, "free"]
            stepDecimal = info_controller.strategy_info.theta_info_df.loc[symbol,"stepDecimal"]
            order.amount = np_round_floor(order.amount, stepDecimal)

        elif order.direction == 'hold':  # buy base currency
            order.amount = 0

        return order


    def judge_buy(self, theta, symbol, info_controller):
        '''买入判断'''
        ml_pred = self.get_ml_prediction(symbol, info_controller)
        if theta < -1 and ml_pred > 0.622:
            return True
        else:
            return False


    def judge_sell(self, symbol, theta, symbol_price, bid_price, info_controller):
        '''卖出判断'''
        ml_pred = self.get_ml_prediction(symbol, info_controller)

        current_rtn = (symbol_price - bid_price) / bid_price

        # logging.info('--------------------judge_sell---------------------------')
        # logging.info("symbol:{}".format(symbol))
        # logging.info("current_rtn:{}".format(current_rtn))
        # logging.info('---------------------------------------------------------')

        if current_rtn < -0.05:  # 止损平仓
            return True
        elif theta > 1. and ml_pred < 0.34:  # 止盈平仓s
            return True
        else:
            return False


    def get_ml_prediction(self, symbol, info_controller):

        price_df = info_controller.strategy_info.price_dict[symbol]

        factor_df = self.features_calculator.get_all_features_add_market_coin(price_df)
        factor_df = factor_df[self.features_calculator.all_X_cols]

        prediction = self.reverse_detector.get_machine_learning_pridictions(factor_df)
        logging.info('--------------------get_ml_prediction---------------------------')
        logging.info("symbol:{}".format(symbol))
        logging.info("prediction:{}".format(prediction))
        logging.info('---------------------------------------------------------')
        return prediction
