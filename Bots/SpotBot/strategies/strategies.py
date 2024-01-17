import pandas as pd
import numpy as np
import logging
import sys

sys.path.append(r'C:\Users\Admin\Desktop\\')

from Crypto_Bot.strategies import reverse_detector
from Crypto_Bot.strategies import strategy_utils
from Crypto_Bot.utils.trade_utils import Order_Structure

class StrategyInterface(object):
    def __init__(self ):
        pass

    def get_order_list(self,):
        '''
        Enter data to obtain order list
        '''
        pass

    def get_order(self):
        pass


class Strategy_mean_reversion(StrategyInterface):
    '''
    Mean Reversion Strategy
    '''

    def __init__(self):

        super().__init__()
        self.reverse_detector = reverse_detector.Reverse_Detector(model_save_path='C:/Users/Admin/Desktop/Crypto_Bot/models')
        self.features_calculator = reverse_detector.Features_Calculator()


    def get_theta(self, data_df):
        Boll_df = pd.DataFrame(index=data_df.index)

        Boll_df['mean_20'] = data_df[['close']].ewm(span=20, adjust=False).mean()
        Boll_df['std_20'] = data_df[['close']].ewm(span=20, adjust=False).std()
        Boll_df['close'] = data_df['close']

        Boll_df.dropna(inplace=True)

        # Calculate theta = (p - ma) / sigma
        Boll_df['theta'] = (Boll_df['close'] - Boll_df['mean_20']) / Boll_df['std_20']
        return Boll_df['theta'].values[-1]
    
    def update_info(self, info_controller):
        '''
            1. Update info in the info_controller
        '''
        data_dict = info_controller.strategy_info.price_dict
        candidate_symbols = info_controller.strategy_info.candidate_symbols

        for symbol in candidate_symbols:
            data_df = data_dict[symbol]
            theta = self.get_theta(data_df)
            info_controller.strategy_info.theta_info_df.loc[symbol,"theta"] = np.round(theta,4)

        # 1. Buy Logic
        # Determine if the symbol is already in position
    
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

        # 1. Update info_controller's "ishold" 
        info_controller = self.update_info(info_controller)

        data_dict = info_controller.strategy_info.price_dict
        theta_info_df = info_controller.strategy_info.theta_info_df

        # 2. Update and record down both BTC and ETH features
        self.features_calculator.save_market_coin_data(data_dict["BTCUSDT"], coin_name="btc")
        self.features_calculator.save_market_coin_data(data_dict["ETHUSDT"], coin_name="eth")

        unhold_currency_df = theta_info_df[theta_info_df["is_hold"] == False]
        unhold_currency_df = unhold_currency_df.sort_values(by="theta", ascending=True)  # theta in ascending order (smallest - biggest)

        # 3. Choose coins that have smaller theta value as trading target
        logging.info("unhold_currency_df:{}".format(unhold_currency_df))
        target_unhold_currency_df = unhold_currency_df[unhold_currency_df["theta"] < -1.2]
        logging.info("target_unhold_currency_df:{}".format(target_unhold_currency_df.index))

        for target_symbol in target_unhold_currency_df.index:

            target_symbol_price = data_dict[target_symbol]['close'].values[-1]
            order = self.get_buy_order(target_symbol, unhold_currency_df.loc[target_symbol, "theta"],
                                   target_position, symbol_price=target_symbol_price, info_controller=info_controller)
            
            order_list.append(order)

        order = None

        # 4. Selling Logic
        hold_currency_df = theta_info_df[theta_info_df["is_hold"] == True]

        if len(hold_currency_df):

            # In there are coins in position, determine if we need to sell
            for target_symbol in hold_currency_df.index:

                target_symbol_price = data_dict[target_symbol]['close'].values[-1]

                order = self.get_sell_order(target_symbol, hold_currency_df.loc[target_symbol, "theta"],
                                       target_position, symbol_price=target_symbol_price, info_controller=info_controller)
                order_list.append(order)
                order = None

        return order_list
    
    def get_buy_order(self, symbol, theta, target_position, symbol_price, info_controller):
        '''
            Buy Logic
            Including Buy decision making and total num of position
            return order
        '''
        order = Order_Structure()
        order.symbol = symbol

        # Buy in Logic
        is_buy = self.judge_buy(theta, symbol, info_controller)  

        if is_buy:
            order.direction = 'buy'
        else:
            order.direction = 'hold'

        # Calculate total number of position to buy
        # Buy base currency (BTC of BTCUSDT)
            
        if order.direction == 'buy': 

            balance = info_controller.account_info.USDT_value

            if balance > 50:
                order.amount = 25.
            else:
                # Too little cash to buy anything
                order.amount = 0.
                order.direction = 'hold'  

            order.amount = strategy_utils.np_round_floor(order.amount, 4)  # divided by the price!!!

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
        I will ignore the var 'target_position' for this bot version
        Reserved for future bot
        '''
        order = Order_Structure()
        order.symbol = symbol
        
        # Determine trade direction
        # In my case, bid_price = cost price
        bid_price = info_controller.account_info.position_df.loc[symbol, "bid_price"]

        # Sell logic
        is_sell = self.judge_sell(symbol, theta, symbol_price, bid_price, info_controller)

        if is_sell:
            order.direction = 'sell'
        else:
            order.direction = 'hold'

        if order.direction == 'sell': 

            # sell base currency, get quote currency
            order.amount = info_controller.account_info.position_df.loc[symbol, "free"]
            stepDecimal = info_controller.strategy_info.theta_info_df.loc[symbol,"stepDecimal"]
            order.amount = strategy_utils.np_round_floor(order.amount, stepDecimal)

        elif order.direction == 'hold':  # buy base currency
            order.amount = 0

        return order
    
    def judge_buy(self, theta, symbol, info_controller):

        '''
        Buy in decision making
        '''
        ml_pred = self.get_ml_prediction(symbol, info_controller)

        logging.info('--------------------judge_buy---------------------------')
        logging.info("symbol:{}".format(symbol))
        logging.info("ml_pred:{}".format(ml_pred))
        logging.info('---------------------------------------------------------')

        if theta < -1.4 and ml_pred > 0.617:
            return True
        else:
            return False
        
    def judge_sell(self, symbol, theta, symbol_price, bid_price, info_controller):
        '''
        Sell out decision making (Empty position)
        '''
        ml_pred = self.get_ml_prediction(symbol, info_controller)

        current_rtn = (symbol_price - bid_price) / bid_price

        logging.info('--------------------judge_sell---------------------------')
        logging.info("symbol:{}".format(symbol))
        logging.info("ml_pred:{}".format(ml_pred))
        logging.info("current_rtn:{}".format(current_rtn))
        logging.info('---------------------------------------------------------')

        # If the price down 5 percent less than cost, sell the position at a loss
        if current_rtn < -0.05:
            return True
        
        # If the price hitting profit threshold, sell the position for profit
        elif theta > 1.4 and ml_pred < 0.368:
            return True
        
        else:
            return False
        
    def get_ml_prediction(self, symbol, info_controller):

        price_df = info_controller.strategy_info.price_dict[symbol]

        factor_df = self.features_calculator.get_all_features_add_market_coin(price_df)
        factor_df = factor_df[self.features_calculator.all_X_cols]

        prediction = self.reverse_detector.get_machine_learning_predictions(factor_df)
        return prediction
        
    