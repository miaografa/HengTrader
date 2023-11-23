#!/usr/bin/env python
import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
from Bots.FutureBot.privateconfig import g_api_key, g_secret_key

config_logging(logging, logging.DEBUG)



if  __name__ == '__main__':
    um_futures_client = UMFutures(key=g_api_key, secret=g_secret_key)

    # 调整杠杆
    try:
        response = um_futures_client.change_leverage(
            symbol="OMGUSDT", leverage=1, recvWindow=6000
        )
        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

    # 调整margin type为 isolated
    try:
        response = um_futures_client.change_margin_type(
            symbol="OMGUSDT", marginType="ISOLATED", recvWindow=6000
        )
        logging.info(response)
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )