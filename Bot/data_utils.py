from binance.spot import Spot as SpotClient
import pandas as pd

def get_market_prices(symbol:str, interval):
    '''获取市场数据，以Dataframe形式返回'''
    spot_client = SpotClient(base_url="https://api2.binance.com")

    price_df = pd.DataFrame(spot_client.klines(symbol, interval))

    k_line_cols = ["Kline_open_time", "open", "high", "low", "close", "volume", "Kline_Close_time", "Quote_asset_volume",
                   "Number_of_trades", "Taker_buy_base_asset_volume", "Taker_buy_quote_asset_volume", "ignore"]

    price_df.columns = k_line_cols

    # 格式转换
    convert_dict = {'open': float,
                    'high': float,
                    'low': float,
                    'close':float,
                    'volume':float,
                    "Quote_asset_volume":float,
                    }
    price_df = price_df.astype(convert_dict)

    # 重命名列
    price_df.rename(columns={"Quote_asset_volume": "quote_volume"}, inplace=True)

    return price_df[["open", "high", "low", "close", "volume", "quote_volume"]]




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



if __name__ == "__main__":
    symbol = 'ETHUSDT'.upper()
    interval = "15m"
    price_df = get_market_prices(symbol, interval)
    print(price_df)