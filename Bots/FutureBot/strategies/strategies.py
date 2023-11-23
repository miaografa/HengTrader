import pandas as pd
import numpy as np
import logging
# sys.path.append("../")
from . import reverse_detector
from . import strategy_utils
from Bots.FutureBot.utils.trade_utils import Order_Structure
from Bots.FutureBot.utils.information import Info_Controller


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
        self.reverse_detector = reverse_detector.Reverse_Detector(model_save_path='/home/ec2-user/HengTrader/Bots/FutureBot/models/')
        self.features_calculator = reverse_detector.Features_Calculator()


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

        # 1. 更新theta信息
        for symbol in candidate_symbols:
            data_df = data_dict[symbol]
            theta = self.get_theta(data_df)
            info_controller.strategy_info.exchange_info_df.loc[symbol,"theta"] = np.round(theta,4)

        return info_controller


    def get_order_list(self, info_controller:Info_Controller, target_position=1.):

        order_list = []
        # 1. 更新 inforcontroller 的 ishold 信息
        info_controller = self.update_info(info_controller)

        data_dict = info_controller.strategy_info.price_dict
        exchange_info_df = info_controller.strategy_info.exchange_info_df

        # 2. 更新并且记录btc 和 eth的features
        self.features_calculator.save_market_coin_data(data_dict["BTCUSDT"], coin_name="btc")
        self.features_calculator.save_market_coin_data(data_dict["ETHUSDT"], coin_name="eth")

        # 1. 判断是否持有
        held_set, un_held_set = info_controller.get_symbols_held_sets()
        for symbol in held_set:  # 对于持有的币种，进行判断是否需要平仓
            temp_order = self.held_set_logic(symbol, info_controller)
            if temp_order:
                order_list.append(temp_order)

        for symbol in un_held_set: # 对于未持有的币种，进行判断是否需要开仓
            temp_order = self.un_held_set_logic(symbol, info_controller)
            if temp_order:
                order_list.append(temp_order)

        return order_list


    def held_set_logic(self, symbol, info_controller:Info_Controller):
        '''
        对于持有的币种，进行判断是否需要平仓
        1. 判断止损
        2. 判断theta

        return order
        '''
        # 1. 判断是否需要止损
        unrealizedProfit = info_controller.account_info.position_df.loc[symbol, "unrealizedProfit"]
        if unrealizedProfit < -0.05:  # todo 加入设置中
            order = self.get_close_order(symbol, info_controller=info_controller)
            return order

        # 2. 判断theta
        theta = info_controller.strategy_info.exchange_info_df.loc[symbol,"theta"]
        if np.abs(theta) > 1.4:
            # 结合机器学习，判断是否需要平仓
            judge_close = self.judge_close(symbol, info_controller)
            if judge_close:
                order = self.get_close_order(symbol, info_controller=info_controller)
                return order
            else:
                return None
        else:
            return None


    def un_held_set_logic(self, symbol, info_controller):
        '''
        未持有的币种，进行判断是否需要开仓
        '''
        # 1. 判断theta
        theta = info_controller.strategy_info.exchange_info_df.loc[symbol, "theta"]
        if np.abs(theta) > 1.4:
            # 结合机器学习，判断是否需要开仓
            side = self.judge_open_side(symbol, info_controller)
            if side == 'HOLD':
                return None
            else:
                order = self.get_open_order(symbol, side=side, info_controller=info_controller)
                return order
        else:
            return None


    def get_open_order(self, symbol, side, info_controller):
        '''
            开仓逻辑，由ml判断是否开仓，以及开仓的方向
            return order
        '''
        def cal_buy_quantity(info_controller, price):
            '''
            计算买入量
            '''
            balance = info_controller.account_info.USDT_value
            if balance > 100:
                quantity = 50. / price
            elif balance > 50:
                quantity = 20. / price
            else:
                quantity = 0.
            return quantity

        order = Order_Structure()
        order.symbol = symbol
        order.side = side
        # 获取挂单价格 price
        order.price = info_controller.get_price_now(symbol)
        # 计算买入量 quantity
        quantity = cal_buy_quantity(info_controller, order.price)
        if quantity == 0:
            return None
        # 保留小数点位数
        stepDecimal = info_controller.strategy_info.exchange_info_df.loc[symbol, "quantityPrecision"]
        order.quantity = strategy_utils.np_round_floor(quantity, stepDecimal)

        return order


    def get_close_order(self, symbol, info_controller):
        '''
            close 平仓。
            交易方向总是和持仓方向相反
        '''
        order = Order_Structure()
        order.symbol = symbol

        positionAmt = info_controller.account_info.position_df.loc[symbol, "positionAmt"]
        stepDecimal = info_controller.strategy_info.exchange_info_df.loc[symbol, "quantityPrecision"]
        order.quantity = strategy_utils.np_round_floor(positionAmt, stepDecimal)
        if order.quantity < 0:
            order.quantity = -order.quantity

        # 判断交易方向，总是和持仓方向相反
        if positionAmt > 0:
            order.side = 'SELL'
        elif positionAmt < 0:
            order.side = 'BUY'

        # 获取挂单价格
        order.price = info_controller.get_price_now(symbol)

        try:
            order.selfcheck()
        except AssertionError as e:
            logging.info('-----------------AssertionError-----------------------')
            logging.info(f"AssertionError:{e}".format(order.symbol))
            logging.info('------------------------------------------------------')
            return None

        return order


    def judge_open_side(self, symbol, info_controller) -> str:
        '''
        判断是否需要开仓
        return side
            - 'BUY'
            - 'SELL'
            - 'HOLD'
        '''
        side = self.get_ml_trade_derection(symbol, info_controller)
        return side


    def judge_close(self, symbol, info_controller) -> bool:
        '''
        判断是否需要平仓
        '''
        side = self.get_ml_trade_derection(symbol, info_controller)
        if side == 'HOLD':
            return False
        else:
            positionAmt = info_controller.account_info.position_df.loc[symbol, "positionAmt"]
            if side == 'SELL' and positionAmt > 0:  # 持多仓且模型预测结果为卖出
                return True
            elif side == 'BUY' and positionAmt < 0:  # 持空仓且模型预测结果为买入
                return True
            else:
                return False


    def get_ml_trade_derection(self, symbol, info_controller):
        '''
        由机器学习判断交易方向
        '''
        ml_pred = self.get_ml_prediction(symbol, info_controller)

        logging.info('--------------------judge_buy---------------------------')
        logging.info("symbol:{}".format(symbol))
        logging.info("ml_pred:{}".format(ml_pred))
        logging.info('---------------------------------------------------------')

        if ml_pred > 0.5532:
            return 'BUY'
        elif ml_pred < 0.4713:
            return 'SELL'
        else:
            return "HOLD"


    def get_ml_prediction(self, symbol, info_controller):
        '''获取机器学习的预测结果'''
        price_df = info_controller.strategy_info.price_dict[symbol]
        factor_df = self.features_calculator.get_all_features_add_market_coin(price_df)
        factor_df = factor_df[self.features_calculator.all_X_cols]
        prediction = self.reverse_detector.get_machine_learning_pridictions(factor_df)
        return prediction
