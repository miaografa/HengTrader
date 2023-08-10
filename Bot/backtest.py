import numpy as np
import pandas as pd

class Backtest_trend_k():
    def __init__(self):
        return

    def backtesting_k_pair(self, k_1, k_2, price_df):
        '''
        只是均线策略的backtest
        对于一组k_1, k_2, 返回在price_df的时间范围内其收益情况
        return:
            rtn
            len(buy_list)
        '''

        if k_1 == k_2:
            return 1., 0.

        # 初始化features表格
        features_df = pd.DataFrame()
        features_df['close'] = price_df['close']
        if k_1 == 1:
            features_df['SMA_k_1'] = price_df['close']
        else:
            features_df['SMA_k_1'] = price_df['close'].rolling(k_1).mean()

        if k_2 == 1:  # 这里保持了k_2 与 k_1 的对称性。深层含义是反趋势交易。
            features_df['SMA_k_2'] = price_df['close']
        else:
            features_df['SMA_k_2'] = price_df['close'].rolling(k_2).mean()

        features_df['is_below_avg5_prev'] = features_df['SMA_k_1'].shift(1) < features_df['SMA_k_2'].shift(1)
        features_df['is_below_avg5_now'] = features_df['SMA_k_1'] < features_df['SMA_k_2']

        features_df = features_df.dropna()

        buy_list = []
        sell_list = []
        for i in range(1, len(features_df)):
            is_below_avg5_prev = features_df.iloc[i, 3]
            is_below_avg5_now = features_df.iloc[i, 4]
            if is_below_avg5_prev and not is_below_avg5_now:  # 价格k1上穿均线k2
                buy_list.append(features_df.iloc[i, 0])
            if not is_below_avg5_prev and is_below_avg5_now and len(buy_list) > len(sell_list):  # 价格k1下穿均线k2
                sell_list.append(features_df.iloc[i, 0])

        buy_list = buy_list[:len(sell_list)]
        rtn_arr = (1 + (np.array(sell_list) - np.array(buy_list)) / np.array(buy_list))
        rtn = np.cumprod(rtn_arr)[-1]

        return rtn, len(buy_list)

    def backtesting_all_k_pairs(self, k1_list, k2_list, price_df):
        '''
        回测所有的 k均线组合，从中选取出最有效的pair
        '''
        n = len(k1_list)
        final_rtns = np.zeros((n, n))
        buy_times = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                rtn, count_buy = self.backtesting_k_pair(k1_list[i], k2_list[j], price_df)
                final_rtns[i, j] = rtn
                buy_times[i, j] = count_buy
        final_rtns = (np.round(final_rtns, 6) - 1) * 100
        rtns_pooled = (final_rtns[1:-1, 1:-1] + final_rtns[0:-2, 1:-1] +\
                       final_rtns[2:, 1:-1] + final_rtns[1:-1, 2:] + final_rtns[1:-1, 0:-2]) / 5


        (k1_ind, k2_ind) = np.unravel_index(np.argmax(rtns_pooled, axis=None), rtns_pooled.shape)
        best_k1 = k1_list[k1_ind + 1]  # todo 此处的加一到底如何处理
        best_k2 = k2_list[k2_ind + 1]
        print("更新k1: {k1},k2: {k2} ".format(k1=best_k1, k2=best_k2))
        return best_k1, best_k2


# if __name__ == "__main__":
#