#!/usr/bin/env python


from binance.lib.utils import config_logging
from binance.error import ClientError
from binance.um_futures import UMFutures
from Bots.FutureBot.privateconfig import g_api_key, g_secret_key



if __name__ == "__main__":
    um_futures_client = UMFutures(key=g_api_key, secret=g_secret_key)
    response = um_futures_client.new_order(
        symbol="AVAXUSDT",
        side="BUY",
        type="LIMIT",
        quantity=1,
        timeInForce="GTC",
        price=19.800,
    )

    print(response)
