import pandas as pd

def calculate_position_value(price, amount):
    '''计算base currency持仓的价值'''
    return price * amount

def np_round_floor(f_str, n):
    f_str = str(f_str)      # f_str = '{}'.format(f_str) 也可以转换为字符串
    a, b, c = f_str.partition('.')
    c = (c+"0"*n)[:n]       # 如论传入的函数有几位小数，在字符串后面都添加n为小数0
    return float(".".join([a, c]))

def pandas_fill(arr):
    df = pd.DataFrame(arr)
    df.fillna(0, axis=0, inplace=True)
    out = df[0].values
    return out


X_cols = [
    'rtn_1', 'OCHL_range', 'trend_adx', 'trend_cci', 'macd', 'momentum_rsi',
       'theta_close', 'theta_volume', 'theta_quote_volume', 'theta_rtn_1',
       'theta_OCHL_range', 'theta_volume_obv', 'theta_volume_vwap',
       'diff_theta_volume', 'diff_theta_volume_obv', 'diff_rtn_1',
       'diff_OCHL_range', 'diff_theta_close', 'diff_trend_adx',
       'diff_trend_cci', 'diff_momentum_rsi', 'diff_macd',
]
large_vol_cols = [
    'vol_rank', 'vol_rank_X_bwd_rtn_5', 'vol_rank_X_bwd_rtn_5_exp'
]

co_diff_target_cols = ['momentum_rsi', 'theta_volume_obv', 'macd', 'trend_cci', 'trend_adx']
co_diff_target_cols_btc = ['co_diff_'+x+"_btc" for x in co_diff_target_cols]
co_diff_target_cols_eth = ['co_diff_'+x+"_eth" for x in co_diff_target_cols]

btc_X_cols = [x+"_btc" for x in X_cols]
eth_X_cols = [x+"_eth" for x in X_cols]

all_X_cols = X_cols + btc_X_cols + eth_X_cols + co_diff_target_cols_btc + co_diff_target_cols_eth + large_vol_cols

# 所有y_cols
y_cols = ['PE_1_bool']
for i in [2,5,10,20,50,100]:
    y_cols.append('PE_'+str(i)+'_mean_bool')