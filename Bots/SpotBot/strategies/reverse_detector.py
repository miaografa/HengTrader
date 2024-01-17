import pandas as pd
import pickle
import ta
import os
import sys
import xgboost as xgb

sys.path.append('c:\\Users\\Admin\\Desktop')

class Reverse_Detector(object):

    def __init__(self, model_save_path):

        self.model_save_path = model_save_path
        self.xgb_model = self.load_xgb_models(model_save_path)
    
    def read_model(self, model_path):

        with open(model_path, 'rb') as f:
            model = pickle.load(f)

        return model
    
    def load_xgb_models(self, model_save_path = 'C:\\Users\\Admin\\Desktop\\Crypto_Bot\\models\\'):

        model_name = 'best_xgboost_rich_model_60_full_data.pkl'
        model_path = os.path.join(model_save_path, model_name)

        xgb_model = self.read_model(model_path)

        return xgb_model
    
    def get_machine_learning_predictions(self, factor_df):
        '''
        :param factor_df: transferred data, including all alphas
        :param direction: transferred direction, up/down
        '''
        data_df = factor_df.copy()
        y_predict = self.xgb_model.predict_proba(data_df.iloc[-1:, :])

        return y_predict[0][1]
    
class Features_Calculator(object):

    def __init__(self):

        # Feature X(s) based on ta
        self.X_cols = [
            'rtn_1', 'OCHL_range', 'trend_adx', 'trend_cci', 'macd', 'momentum_rsi',
            'theta_close', 'theta_volume', 'theta_quote_volume', 'theta_rtn_1',
            'theta_OCHL_range', 'theta_volume_obv', 'theta_volume_vwap',
            'diff_theta_volume', 'diff_theta_volume_obv', 'diff_rtn_1',
            'diff_OCHL_range', 'diff_theta_close', 'diff_trend_adx',
            'diff_trend_cci', 'diff_momentum_rsi', 'diff_macd',
        ]

        self.co_diff_target_cols = ['momentum_rsi', 'theta_volume_obv', 'macd', 'trend_cci', 'trend_adx']

        # Create 5 new cols for both btc and eth-based diff targets ('momentum_rsi', 'theta_volume_obv', 'macd', 'trend_cci', 'trend_adx')
        self.co_diff_target_cols_btc = ['co_diff_' + x + "_btc" for x in self.co_diff_target_cols]
        self.co_diff_target_cols_eth = ['co_diff_' + x + "_eth" for x in self.co_diff_target_cols]

        self.btc_X_cols = [x + "_btc" for x in self.X_cols]
        self.eth_X_cols = [x + "_eth" for x in self.X_cols]

        # Total X columns for ML model
        self.all_X_cols = self.X_cols + self.btc_X_cols + self.eth_X_cols + self.co_diff_target_cols_btc + self.co_diff_target_cols_eth
        return

    def save_market_coin_data(self, data_df, coin_name):

        factor_df = self.get_all_features(data_df)[self.X_cols]
        factor_df.columns = factor_df.columns + '_' + coin_name

        if coin_name == 'btc':
            self.btc_factor_data = factor_df

        elif coin_name == 'eth':
            self.eth_factor_data = factor_df

        return
    
    def add_ta_features(self, factor_df, raw_df):
        data_df = raw_df[['open', 'close', 'high','low', 'volume']]

        factor_df['trend_adx'] = ta.trend.adx(data_df['high'], data_df['low'], data_df['close'])
        factor_df['trend_cci'] = ta.trend.cci(data_df['high'], data_df['low'], data_df['close'])
        factor_df['macd'] = ta.trend.MACD(data_df['close']).macd()
        factor_df['momentum_rsi'] = ta.momentum.rsi(data_df['close'])
        factor_df['volume_obv'] = ta.volume.on_balance_volume(data_df['close'],data_df['volume'])
        factor_df['volume_vwap'] = ta.volume.volume_weighted_average_price(data_df['high'], data_df['low'],
                                                                           data_df['close'],data_df['volume'])

        return factor_df
    
    def _calculate_theta(self, target_column, price_df, theta_interval):
        '''Calculate each theta'''

        theta_df = pd.DataFrame()

        # Calculate theta based on EMA
        # target_column = closing price
        theta_df['mean_20_' + target_column] = price_df[[target_column]].ewm(span=theta_interval, adjust=False).mean()
        theta_df['std_20_' + target_column] = price_df[[target_column]].ewm(span=theta_interval, adjust=False).std()
        theta_df[target_column] = price_df[target_column]

        target_column_theta = (theta_df[target_column] - theta_df['mean_20_' + target_column]) / theta_df['std_20_' + target_column]

        return target_column_theta

    def calculate_theta_all(self, factor_df, price_df, theta_interval_list=[], target_column_list=["close"]):
        '''
        Calculating theta value
        factor_df: dataframe that stored theta 
        price_df：dataframe that stored price data
        '''
        for i in range(len(target_column_list)):

            if len(theta_interval_list) != 0:
                theta_interval = theta_interval_list[i]
            else:
                theta_interval = 20
            target_column = target_column_list[i]

            # calculate theta = (p - ma) / sigma
            factor_df['theta_' + target_column] = self._calculate_theta(target_column, price_df, theta_interval)

        return factor_df

    def add_rtn_feature(self, factor_df, raw_df):
        '''
        calculate 15 mins relative return based on prior row - "close" column
        '''
        factor_df['rtn_1'] = (raw_df['close'] - raw_df['close'].shift(1)) / raw_df['close'].shift(1)

        return factor_df

    def add_OCHL_feature(self, factor_df, raw_df):
        '''
        calculate OCHL_range to determine volatility range
        '''
        factor_df['OCHL_range'] = (raw_df['close'] - raw_df['open']) / (raw_df['high'] - raw_df['low'])
        factor_df['OCHL_range'].fillna(1e-4, inplace=True)

        return factor_df

    def add_all_diff_features(self, factor_df: pd.DataFrame, target_columns):
        '''
        Create a diff col for each features to de-noise

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
            factor_df['diff_' + feature_name] = factor_df[feature_name] - factor_df[feature_name].shift(1)

        return factor_df

    def get_all_features(self, data_df):
        '''
            计算全部独立的技术指标：
            1. 原始指标（部分不会直接用到）
            2. 原始指标的 theta 指标 （归一化）
            3. 原始指标的 diff 指标

            return factor_df
        '''

        raw_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_volume', ]
        data_df = data_df[raw_cols].copy()

        factor_df = pd.DataFrame()

        # 1 原始指标
        ### OCHL_range 和 rtn (data_df = raw_df)
        factor_df = self.add_rtn_feature(factor_df, data_df)
        factor_df = self.add_OCHL_feature(factor_df, data_df)

        ### ta 的技术指标 (data_df = raw_df)
        factor_df = self.add_ta_features(factor_df, data_df)

        ### 1.1 Theta指标
        target_columns_list = ['close', 'volume', 'quote_volume']  # 需要计算theta的对应列
        factor_df = self.calculate_theta_all(factor_df, data_df, target_column_list=target_columns_list)
        factor_df = self.calculate_theta_all(factor_df, factor_df, [20, 20], target_column_list=['rtn_1', 'OCHL_range'])
        factor_df = self.calculate_theta_all(factor_df, factor_df, [20, 20], target_column_list=['volume_obv', 'volume_vwap'])

        factor_df.drop(['volume_obv', 'volume_vwap'], axis=1, inplace=True)

        ### 1.2 diff 指标
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
        '''
        for feature_name in self.co_diff_target_cols:
            factor_df['co_diff_' + feature_name + "_btc"] = factor_df[feature_name] - factor_df[feature_name + "_btc"]
            factor_df['co_diff_' + feature_name + "_eth"] = factor_df[feature_name] - factor_df[feature_name + "_eth"]
        return factor_df

    def get_all_features_add_market_coin(self, data_df):
        '''
            计算全部技术指标
            然后将该货币的指标，以及btc，eth指标进行合并

            return factor_df
        '''
        factor_df = self.get_all_features(data_df)[self.X_cols]
        factor_df = self.combine_features(factor_df, self.btc_factor_data, self.eth_factor_data)  # 合并
        factor_df = self.add_co_diff_features_market_coin(factor_df)  # 加入互相关因子
        return factor_df[self.all_X_cols]

## Example
if __name__ == '__main__':

    from Crypto_Bot.utils.data_utils import get_market_prices

    btc_price_df = get_market_prices('BTCUSDT', '15m')
    eth_price_df = get_market_prices('ETHUSDT', '15m')


    print(btc_price_df.head())
    f_c = Features_Calculator()

    f_c.save_market_coin_data(btc_price_df, coin_name='btc' )
    f_c.save_market_coin_data(eth_price_df, coin_name='eth' )

    price_df = get_market_prices('AXSUSDT', '15m')

    factor_df = f_c.get_all_features_add_market_coin(price_df)[f_c.all_X_cols]

    print(factor_df.head())


    # 测试预测部分
    # Older pandas version (1.5.0)
    # Older xgboost version (1.2.0)
    model_save_path = 'C:/Users/Admin/Desktop/Crypto_Bot/models/'
    r_d = Reverse_Detector(model_save_path)
    y_predict = r_d.get_machine_learning_predictions(factor_df)
    print(y_predict)
