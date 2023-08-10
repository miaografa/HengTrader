from huobi.client.market import MarketClient  # market info related
from huobi.constant import *
from huobi.utils import *

import pandas as pd

def get_market_prices(symbol:str, interval, size:int):
    '''获取市场数据，以Dataframe形式返回'''
    market_client = MarketClient(init_log=True)
    list_obj = market_client.get_candlestick(symbol, interval, size)
    # LogInfo.output("---- {interval} candlestick for {symbol} ----".format(interval=interval, symbol=symbol))
    # LogInfo.output_list(list_obj)
    price_df = Candle_2_Dataframe(list_obj)  # 注意时间顺序，第一条记录是最新记录
    price_df = price_df[::-1].reset_index(drop=True)  # 将顺序倒置
    return price_df


def Candle_2_Dataframe(list_obj):
    '''把奇怪的huobi格式转化为Dataframe'''
    df = pd.DataFrame({
        'open':list(map(lambda x: x.open, list_obj)),
        'close': list(map(lambda x: x.close, list_obj)),
        'high': list(map(lambda x: x.high, list_obj)),
        'low': list(map(lambda x: x.low, list_obj)),
        'vol': list(map(lambda x: x.vol, list_obj)),
        'count': list(map(lambda x: x.count, list_obj)),
        'amount': list(map(lambda x: x.amount, list_obj)),
    })
    return df

if __name__ == "__main__":
    symbol = 'xrpusdt'  # todo check whether this currency exist or not.
    interval = CandlestickInterval.MIN1
    size = 100
    get_market_prices(symbol, interval, size)