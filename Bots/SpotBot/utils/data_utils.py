# Always remember to install (pip install binance-connector)
from binance.spot import Spot as SpotClient
import pandas as pd

## Function 1

def get_market_prices(symbol:str, interval):

    spot_client = SpotClient(base_url="https://api2.binance.com")

    price_df = pd.DataFrame(spot_client.klines(symbol, interval))

    k_line_cols = ["Kline_open_time", "open", "high", "low", "close", "volume", "Kline_Close_time", "Quote_asset_volume", "Number_of_trades", "Taker_buy_base_asset_volume", "Taker_buy_quote_asset_volume", "ignore"]

    price_df.columns = k_line_cols

    # Convert data types to float for each columns
    convert_dict = {'open': float,
                    'high': float,
                    'low': float,
                    'close':float,
                    'volume':float,
                    "Quote_asset_volume":float,
                    }

    price_df = price_df.astype(convert_dict)

    # Rename the col (Quote_asset_volume to quote_volume)
    price_df.rename(columns={"Quote_asset_volume": "quote_volume"}, inplace=True)
    return price_df[["open", "high", "low", "close", "volume", "quote_volume"]]


## Function 2

def get_decimal_precision(number_str):
    
    if '.' in number_str:

        # If there is a decimal point in data

        decimal_part = number_str.strip("0").split('.')[1]
        return len(decimal_part)
    
    else:
        return 0
    
## Example
## Using Ethereum prices as test case
if __name__ == "__main__":
    symbol = 'ETHUSDT'.upper()
    interval = "15m"
    price_df = get_market_prices(symbol, interval)
    print(price_df)    