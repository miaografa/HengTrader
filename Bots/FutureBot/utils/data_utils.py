from binance.um_futures import UMFutures
import pandas as pd

def get_market_prices(symbol:str, interval):
    '''获取市场数据，以Dataframe形式返回'''
    future_client = UMFutures()

    price_df = pd.DataFrame(future_client.klines(symbol, interval))

    k_line_cols = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'count',
                   'taker_buy_volume', 'taker_buy_quote_volume', 'ignore']

    price_df.columns = k_line_cols

    # 格式转换
    convert_dict = {'open': float,
                    'high': float,
                    'low': float,
                    'close':float,
                    'volume':float,
                    "quote_volume":float,
                    }
    price_df = price_df.astype(convert_dict)

    return price_df


def get_decimal_precision(number_str):
    # 判断是否有小数部分
    if '.' in number_str:
        # 获取小数部分
        decimal_part = number_str.strip("0").split('.')[1]
        # 返回小数部分的位数
        return len(decimal_part)
    else:
        # 没有小数部分，精度为0
        return 0


def seperate_symbol_info_from_dict(symbol_info: dict):
    '''工具函数从一个字典分分离出一个子字典'''
    output_dict = dict()
    target_cols = [
        'symbol',
        'pair',
        'contractType',
        'status',
        'baseAsset',
        'quoteAsset',
        'pricePrecision',
        'quantityPrecision',
    ]
    for col in target_cols:
        output_dict[col] = symbol_info[col]

    return output_dict

def convert_df_type(df):
    # 选择需要转换的列
    columns_to_convert = ['initialMargin', 'maintMargin', 'unrealizedProfit',
                          'positionInitialMargin', 'openOrderInitialMargin',
                          'leverage', 'entryPrice', 'breakEvenPrice',
                          'maxNotional', 'positionAmt', 'notional',
                          'isolatedWallet', 'bidNotional', 'askNotional']

    # 使用pd.to_numeric()将选定列转换为float
    df[columns_to_convert] = df[columns_to_convert].apply(pd.to_numeric, errors='coerce')

    return df

if __name__ == "__main__":
    symbol = 'ETHUSDT'.upper()
    interval = "15m"
    price_df = get_market_prices(symbol, interval)
    print(price_df)