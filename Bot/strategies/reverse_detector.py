"""
File: reverse_detector.py
Author: Henry Miao
Date Created: 2023-10-03
Last Modified: --
Description: Use machine learning to detect reversion of price.
"""

import pandas as pd
import numpy as np
import pickle
import ta


class Reverse_Detector(object):
    def __init__(self, model_save_path):
        self.model_save_path = model_save_path
        self.xgb_up, self.xgb_down = self.load_xgb_models(model_save_path)

    def read_model(self, model_save_path, model_name):
        with open(model_save_path + model_name, 'rb') as file:
            model = pickle.load(file)
        return model

    def load_xgb_models(self, model_save_path = './models/'):
        xgb_up = self.read_model(model_save_path, 'best_xgboost_reverse_up.pkl')
        xgb_down = self.read_model(model_save_path, 'best_xgboost_reverse_down.pkl')
        return xgb_up, xgb_down

    def get_machine_learning_pridictions(self, factor_df, direction='up'):
        '''
        :param factor_df: 传入的数据，包含了所有的因子
        :param direction: 传入的方向，up 或者 down
        '''
        col_list = ['momentum_rsi', 'theta_close', 'theta_volume', 'theta_volume_vwap',
                    'theta_quote_volume', 'theta_volume_obv', 'trend_cci', 'macd',
                    'trend_adx']
        data_df = factor_df[col_list].copy()
        if direction == 'up':
            y_predict = self.xgb_up.predict_proba(data_df.iloc[-1:, :])
        elif direction == 'down':
            y_predict = self.xgb_down.predict_proba(data_df.iloc[-1:, :])
        return y_predict[0][1]


class Features_Calculator(object):
    def __init__(self):
        pass

    def _add_ta_features(self, factor_df, raw_df):
        '''计算 ta 的技术指标'''
        data_df = raw_df[['open', 'close', 'high', 'low', 'volume']]

        factor_df['trend_adx'] = ta.trend.adx(data_df['high'], data_df['low'], data_df['close'])
        factor_df['trend_cci'] = ta.trend.cci(data_df['high'], data_df['low'], data_df['close'])
        factor_df['macd'] = ta.trend.MACD(data_df['close']).macd()
        factor_df['momentum_rsi'] = ta.momentum.rsi(data_df['close'])
        factor_df['volume_obv'] = ta.volume.on_balance_volume(data_df['close'], data_df['volume'])
        factor_df['volume_vwap'] = ta.volume.volume_weighted_average_price(data_df['high'], data_df['low'],
                                                                           data_df['close'], data_df['volume'])
        return factor_df

    def _calculate_theta(self, factor_df, price_df, interval=20, target_column_list=["close"]):
        '''
        计算theta指标
        factor_df: 用于存放指标的df
        price_df：原始价格的df
        '''
        theta_df = pd.DataFrame()
        for target_column in target_column_list:
            # theta
            theta_df['mean_20_' + target_column] = price_df[[target_column]].ewm(span=interval, adjust=False).mean()
            theta_df['std_20_' + target_column] = price_df[[target_column]].ewm(span=interval, adjust=False).std()
            theta_df[target_column] = price_df[target_column]

            # 计算偏离度 theta = (p - ma) / sigma
            factor_df['theta_' + target_column] = (theta_df[target_column] - theta_df['mean_20_' + target_column]) / \
                                                  theta_df['std_20_' + target_column]

        return factor_df


    def get_all_features(self, price_df):
        # 用一个factor df记录所有factors
        factor_df = pd.DataFrame()
        factor_df = self._add_ta_features(factor_df, price_df)

        # theta 指标 有两类，一类从pricedf计算，另一类在factor_df
        target_columns_list = ['close', 'volume', 'quote_volume']  # 需要计算theta的对应列
        factor_df = self._calculate_theta(factor_df, price_df, interval=20, target_column_list=target_columns_list)
        factor_df = self._calculate_theta(factor_df, factor_df, interval=100,
                                          target_column_list=['volume_obv', 'volume_vwap'])
        factor_df.drop(['volume_obv', 'volume_vwap'], axis=1, inplace=True)

        # dropna
        factor_df.dropna(inplace=True)
        factor_df.reset_index(drop=True, inplace=True)
        price_df = price_df.iloc[-len(factor_df):, :]
        price_df.reset_index(drop=True, inplace=True)

        return factor_df



if __name__ == '__main__':

    from Bot.data_utils import get_market_prices

    price_df = get_market_prices('BTCUSDT', '15m')
    f_c = Features_Calculator()

    print(price_df.head())
    factor_df = f_c.get_all_features(price_df)

    print(factor_df.head())

    model_save_path = '../models/'
    r_d = Reverse_Detector(model_save_path)
    y_predict = r_d.get_machine_learning_pridictions(factor_df, direction='up')
    print(y_predict)

    y_predict = r_d.get_machine_learning_pridictions(factor_df, direction='down')
    print(y_predict)

import pandas as pd
import numpy as np
import pickle
import ta
from ta.utils import dropna


class Reverse_Detector(object):
    def __init__(self, model_save_path):
        self.model_save_path = model_save_path
        self.xgb_up, self.xgb_down = self.load_xgb_models(model_save_path)

    def read_model(self, model_save_path, model_name):
        with open(model_save_path + model_name, 'rb') as file:
            model = pickle.load(file)
        return model

    def load_xgb_models(self, model_save_path = './models/'):
        xgb_up = self.read_model(model_save_path, 'best_xgboost_reverse_up.pkl')
        xgb_down = self.read_model(model_save_path, 'best_xgboost_reverse_down.pkl')
        return xgb_up, xgb_down

    def get_machine_learning_pridictions(self, factor_df, direction='up'):
        '''
        :param factor_df: 传入的数据，包含了所有的因子
        :param direction: 传入的方向，up 或者 down
        '''
        col_list = ['momentum_rsi', 'theta_close', 'theta_volume', 'theta_volume_vwap',
                    'theta_quote_volume', 'theta_volume_obv', 'trend_cci', 'macd',
                    'trend_adx']
        data_df = factor_df[col_list].copy()
        if direction == 'up':
            y_predict = self.xgb_up.predict_proba(data_df.iloc[-1:, :])
        elif direction == 'down':
            y_predict = self.xgb_down.predict_proba(data_df.iloc[-1:, :])
        return y_predict[0][1]


class Features_Calculator(object):
    def __init__(self):
        pass

    def _add_ta_features(self, factor_df, raw_df):
        '''计算 ta 的技术指标'''
        data_df = raw_df[['open', 'close', 'high', 'low', 'volume']]

        factor_df['trend_adx'] = ta.trend.adx(data_df['high'], data_df['low'], data_df['close'])
        factor_df['trend_cci'] = ta.trend.cci(data_df['high'], data_df['low'], data_df['close'])
        factor_df['macd'] = ta.trend.MACD(data_df['close']).macd()
        factor_df['momentum_rsi'] = ta.momentum.rsi(data_df['close'])
        factor_df['volume_obv'] = ta.volume.on_balance_volume(data_df['close'], data_df['volume'])
        factor_df['volume_vwap'] = ta.volume.volume_weighted_average_price(data_df['high'], data_df['low'],
                                                                           data_df['close'], data_df['volume'])
        return factor_df

    def _calculate_theta(self, factor_df, price_df, interval=20, target_column_list=["close"]):
        '''
        计算theta指标
        factor_df: 用于存放指标的df
        price_df：原始价格的df
        '''
        theta_df = pd.DataFrame()
        for target_column in target_column_list:
            # theta
            theta_df['mean_20_' + target_column] = price_df[[target_column]].ewm(span=interval, adjust=False).mean()
            theta_df['std_20_' + target_column] = price_df[[target_column]].ewm(span=interval, adjust=False).std()
            theta_df[target_column] = price_df[target_column]

            # 计算偏离度 theta = (p - ma) / sigma
            factor_df['theta_' + target_column] = (theta_df[target_column] - theta_df['mean_20_' + target_column]) / \
                                                  theta_df['std_20_' + target_column]

        return factor_df


    def get_all_features(self, price_df):
        # 用一个factor df记录所有factors
        factor_df = pd.DataFrame()
        factor_df = self._add_ta_features(factor_df, price_df)

        # theta 指标 有两类，一类从pricedf计算，另一类在factor_df
        target_columns_list = ['close', 'volume', 'quote_volume']  # 需要计算theta的对应列
        factor_df = self._calculate_theta(factor_df, price_df, interval=20, target_column_list=target_columns_list)
        factor_df = self._calculate_theta(factor_df, factor_df, interval=100,
                                          target_column_list=['volume_obv', 'volume_vwap'])
        factor_df.drop(['volume_obv', 'volume_vwap'], axis=1, inplace=True)

        # dropna
        factor_df.dropna(inplace=True)
        factor_df.reset_index(drop=True, inplace=True)
        price_df = price_df.iloc[-len(factor_df):, :]
        price_df.reset_index(drop=True, inplace=True)

        return factor_df



if __name__ == '__main__':

    from Bot.data_utils import get_market_prices

    price_df = get_market_prices('BTCUSDT', '15m')
    f_c = Features_Calculator()

    print(price_df.head())
    factor_df = f_c.get_all_features(price_df)

    print(factor_df.head())

    model_save_path = '../models/'
    r_d = Reverse_Detector(model_save_path)
    y_predict = r_d.get_machine_learning_pridictions(factor_df, direction='up')
    print(y_predict)

    y_predict = r_d.get_machine_learning_pridictions(factor_df, direction='down')
    print(y_predict)
