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
import pandas_ta
from pandas_ta.core import adx, cci, macd, rsi, obv, vwap

from strategy_utils import X_cols, co_diff_target_cols, all_X_cols, \
    btc_X_cols, eth_X_cols, co_diff_target_cols_btc, co_diff_target_cols_eth



class Reverse_Detector(object):
    def __init__(self, model_save_path):
        self.model_save_path = model_save_path
        self.xgb_model = self.load_xgb_models(model_save_path)

    def read_model(self, model_save_path, model_name):
        with open(model_save_path + model_name, 'rb') as f:
            model = pickle.load(f)
        return model

    def load_xgb_models(self, model_save_path = './models/'):
        xgb_model = self.read_model(model_save_path, 'best_xgboost_10_2023.pkl')
        return xgb_model


    def get_machine_learning_pridictions(self, factor_df):
        '''
        :param factor_df: 传入的数据，包含了所有的因子
        :param direction: 传入的方向，up 或者 down
        '''
        data_df = factor_df.copy()
        y_predict = self.xgb_model.predict_proba(data_df.iloc[-1:, :])
        return y_predict[0][1]


class Features_Calculator(object):
    def __init__(self):
        self.X_cols = X_cols

        self.co_diff_target_cols = co_diff_target_cols
        self.co_diff_target_cols_btc = co_diff_target_cols_btc
        self.co_diff_target_cols_eth = co_diff_target_cols_eth

        self.btc_X_cols = btc_X_cols
        self.eth_X_cols = eth_X_cols

        self.all_X_cols = all_X_cols
        return

    def save_market_coin_data(self, data_df, coin_name):
        '''
        Step 1 先保存market coin data

        '''
        factor_df = self.get_all_features(data_df)
        factor_df.columns = factor_df.columns + '_' + coin_name

        if coin_name == 'btc':
            self.btc_factor_data = factor_df
        elif coin_name == 'eth':
            self.eth_factor_data = factor_df
        return

    def add_ta_features(self, factor_df, raw_df):
        data_df = raw_df[['open', 'close', 'high', 'low', 'volume']]
        data_df.index = pd.to_datetime(raw_df.open_time, unit='ms')

        temp_factor_df = pd.DataFrame()  # 暂存特征，避免index不一致导致的错误
        temp_factor_df['trend_adx'] = adx(data_df['high'], data_df['low'], data_df['close'])['ADX_14']
        temp_factor_df['trend_cci'] = cci(data_df['high'], data_df['low'], data_df['close'])
        temp_factor_df['macd'] = macd(data_df['close'])['MACD_12_26_9']
        temp_factor_df['momentum_rsi'] = rsi(data_df['close'])
        temp_factor_df['volume_obv'] = obv(data_df['close'], data_df['volume'])
        temp_factor_df['volume_vwap'] = vwap(data_df['high'], data_df['low'], data_df['close'], data_df['volume'])

        temp_factor_df.reset_index(drop=True, inplace=True)

        factor_df = pd.concat([factor_df, temp_factor_df], axis=1)
        return factor_df


    def _calculate_theta(self, target_column, price_df, theta_interval):
        '''计算单个theta'''
        theta_df = pd.DataFrame()
        # theta
        theta_df['mean_20_' + target_column] = price_df[[target_column]].ewm(span=theta_interval, adjust=False).mean()
        theta_df['std_20_' + target_column] = price_df[[target_column]].ewm(span=theta_interval, adjust=False).std()
        theta_df[target_column] = price_df[target_column]

        target_column_theta = (theta_df[target_column] - theta_df['mean_20_' + target_column]) / theta_df[
            'std_20_' + target_column]
        return target_column_theta


    def calculate_theta_all(self, factor_df, price_df, theta_interval_list=[], target_column_list=["close"]):
        '''
        计算theta指标
        factor_df: 用于存放指标的df
        price_df：原始价格的df
        '''
        for i in range(len(target_column_list)):
            if len(theta_interval_list) != 0:
                theta_interval = theta_interval_list[i]
            else:
                theta_interval = 20
            target_column = target_column_list[i]

            # 计算偏离度 theta = (p - ma) / sigma
            factor_df['theta_' + target_column] = self._calculate_theta(target_column, price_df, theta_interval)

        return factor_df


    def add_rtn_feature(self, factor_df, raw_df):
        '''
        计算前一天的return作为一列
        '''
        factor_df['rtn_1'] = (raw_df['close'] - raw_df['close'].shift(1)) / raw_df['close'].shift(1)
        return factor_df


    def add_OCHL_feature(self, factor_df, raw_df):
        '''
        计算OCHL_range 作为波动幅度
        '''
        factor_df['OCHL_range'] = (raw_df['close'] - raw_df['open']) / (raw_df['high'] - raw_df['low'])
        factor_df['OCHL_range'].fillna(1e-4, inplace=True)
        return factor_df


    def add_all_diff_features(self, factor_df: pd.DataFrame, target_columns):
        '''
        给需要的列做一个diff作为差值特征
            diff_theta_volume
            diff_theta_volume_obv
            diff_rtn_1
            diff_OCHL
            diff_theta_close
            diff_adx
            diff_cci
            diff_momentum_rsi
            diff_macd
        '''
        for feature_name in target_columns:
            factor_df['diff_' + feature_name] = factor_df[feature_name] - factor_df[feature_name].shift(1)  # todo改回1

        return factor_df


    def add_large_volume_features(self, factor_df, raw_df):
        '''
            成交量的相对大小构成的因子。
                vol_rank：交易量大小在之前500个时间戳的序数
                large_vol_90_bwd_rtn_5： 大单（>90）在之前一段时间的累计价格变化
                其他数值以此类推。

        '''

        def cal_rolling_rank(series):
            return series.rank(pct=True).values[-1]

        def log_return(series):
            return np.log(series).diff()

        rolling_rank = raw_df['quote_volume'].rolling(500).apply(cal_rolling_rank)  # rolling_rank 是一个分数
        rolling_rank.fillna(0.5, inplace=True)

        log_rtn = raw_df[['close']].apply(log_return).fillna(0)
        bwd_rtn_5 = log_rtn.rolling(5).sum().fillna(0)  # 之前5个interval的累计收益
        bwd_rtn_5 = bwd_rtn_5['close']  # 取出值

        factor_df['vol_rank'] = rolling_rank  # rank因子

        factor_df['vol_rank_X_bwd_rtn_5'] = rolling_rank * bwd_rtn_5  # rank因子
        exp_roll_rank = np.exp(10 * rolling_rank) / np.exp(10)
        factor_df['vol_rank_X_bwd_rtn_5_exp'] = exp_roll_rank * bwd_rtn_5

        return factor_df


    def get_all_features(self, data_df):
        '''
            BTC ETH和原始货币都会先利用这个计算全部技术指标。
            计算全部独立的技术指标：
            1. 原始指标（部分不会直接用到）
            2. 原始指标的 theta 指标 （归一化）
            3. 原始指标的 diff 指标

            return factor_df
        '''

        raw_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_volume', 'open_time']
        data_df = data_df[raw_cols].copy()

        factor_df = pd.DataFrame()

        # 1 原始指标
        ### OCHL_range 和 rtn
        factor_df = self.add_rtn_feature(factor_df, data_df)
        factor_df = self.add_OCHL_feature(factor_df, data_df)

        ### ta 的技术指标
        factor_df = self.add_ta_features(factor_df, data_df)

        ### 1.1 Theta指标
        target_columns_list = ['close', 'volume', 'quote_volume']  # 需要计算theta的对应列
        factor_df = self.calculate_theta_all(factor_df, data_df, target_column_list=target_columns_list)
        factor_df = self.calculate_theta_all(factor_df, factor_df, [20, 20], target_column_list=['rtn_1', 'OCHL_range'])
        factor_df = self.calculate_theta_all(factor_df, factor_df, [20, 20], target_column_list=['volume_obv', 'volume_vwap'])

        factor_df.drop(['volume_obv', 'volume_vwap'], axis=1, inplace=True)

        ### 1.2 大额订单对应的features
        factor_df = self.add_large_volume_features(factor_df, data_df)

        ### 1.3 diff 指标
        diff_target_columns = ['theta_volume',
                               'theta_volume_obv',
                               'rtn_1',
                               'OCHL_range',
                               'theta_close',
                               'trend_adx',
                               'trend_cci',
                               'momentum_rsi',
                               'macd']
        factor_df = self.add_all_diff_features(factor_df, diff_target_columns)

        assert data_df.shape[0] == factor_df.shape[0]

        factor_df['close'] = data_df['close']
        factor_df.dropna(inplace=True)

        return factor_df


    def combine_features(self, factor_df, btc_data, eth_data):
        concat_df = pd.concat([factor_df, btc_data, eth_data], axis=1)
        return concat_df


    def add_co_diff_features_market_coin(self, factor_df):
        '''
        加入互相关关系的因子，也就是coin和btc eth的差值
        Step3 加入互相关因子
        '''
        for feature_name in self.co_diff_target_cols:
            factor_df['co_diff_' + feature_name + "_btc"] = factor_df[feature_name] - factor_df[feature_name + "_btc"]
            factor_df['co_diff_' + feature_name + "_eth"] = factor_df[feature_name] - factor_df[feature_name + "_eth"]
        return factor_df


    def get_all_features_add_market_coin(self, data_df):
        '''
            Setp 2 全部计算
            计算全部技术指标
            然后将该货币的指标，以及btc，eth指标进行合并

            return factor_df
        '''
        factor_df = self.get_all_features(data_df)
        factor_df = self.combine_features(factor_df, self.btc_factor_data, self.eth_factor_data)  # 合并
        factor_df = self.add_co_diff_features_market_coin(factor_df)  # 加入互相关因子
        return factor_df[self.all_X_cols]


if __name__ == '__main__':

    from Bots.FutureBot.utils.data_utils import get_market_prices

    btc_price_df = get_market_prices('BTCUSDT', '15m')
    eth_price_df = get_market_prices('ETHUSDT', '15m')

    print(btc_price_df.head())
    f_c = Features_Calculator()

    f_c.save_market_coin_data(btc_price_df, coin_name='btc' )
    f_c.save_market_coin_data(eth_price_df, coin_name='eth' )

    price_df = get_market_prices('AXSUSDT', '15m')

    factor_df = f_c.get_all_features_add_market_coin(price_df)[f_c.all_X_cols]

    print(factor_df.head())


    # # 测试预测部分
    model_save_path = '../models/'
    r_d = Reverse_Detector(model_save_path)
    y_predict = r_d.get_machine_learning_pridictions(factor_df)
    print(y_predict)
