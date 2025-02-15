from eth_account.signers.local import LocalAccount
import eth_account
import json
import time
#from hyperliquid.info import Info
#from hyperliquid.exchange import Exchange  
#from hyperliquid.utils import constants
import ccxt
import pandas as pd
import datetime
import schedule
import requests
from datetime import datetime, timedelta
import pandas_ta as ta
prints('ONLY WORKS ON 3.8.5 QUANT INTERPRETER')

symbol = 'BTCUSD'
timeframe = '15m'

max_loss = -1
targets = 5
pos_size = 200
leverage = 10
vol_multiplier = 3
rounding = 4

cb_symbol = symbol + '/USDT' # ver para bybit

def get_ohlcv2(symbol, interval, lookback_days):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=lookback_days)

    url = ''


def process_data_to_df(snapshot_data):
    if snapshot_data:
        # assuming the response contains a list of candles
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        data = []
        for snapshot in snapshot_data:
            timestamp = datetime.fromtimestamp(snapshot['t'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            open_price = snapshot['o']
            high_price = snapshot['h']
            low_price = snapshot['l']
            close_price = snapshot['c']
            volume = snapshot['v']
            data.append([timestamp, open_price, high_price, low_price, close_price, volume])

        df = pd.DataFrame(data, columns=columns)

        # calculate support and resistanc, excluding the last 2 rows for the calculation
        if len(df) > 2: #check if dataframe has more than 2 rows to avoid errors
             df['support']= df[:-2]['close'].min()
             df['resis']= df[:-2]['close'].max()
        else: # if dataframe has 2 or fewer rows, use the available 'close' price for calculation
            df['support'] = df['close'].min()
            df['resis'] = df['close'].max()

        return df
    else:
        return pd.DataFrame() # return empty dataframe if no data is fetched

def find_max_sizes(df):
    

def find_before_biggest(df,max_price, col_name, is_bid=True):
    # print(f'finding before biggest for {col_name}')
    # print(df)
    if is_bid:
        sorted_df = df.sort_values(by=col_name, ascending=True)
        before_biggest_df = sorted_df[sorted_df[col_name] > max_price]
    else:
        sorted_df = df.sort_values(by=col_name, ascending=False)
        before_biggest_df = sorted_df[sorted_df[col_name] < max_price]

    #print(f'sorted_df: {sorted_df}')

    if before_biggest_df.empty:
        return None, None
    else:
        before_biggest_row = before_biggest_df.iloc[0]
        return before_biggest_row[col_name], before_biggest_row[col_name + ' Size']
    



# funciones para get_data

def history_file_name(index, exchange, symbol):
    """
    generates a filename for a history file base on index, exchange and symbol, 
    args:
        index (int): the index of the history file
        exchange (str): the exchange name
        symbol (str): the trading symbol
    returns:
        str: the formatted filename
    """
    return f'./history/{exchange}/{symbol}_M1_{index}.json'

import re

def load_existing_history(exchange, symbol):
    """
    loads existing history data from files.
    args:
        exchange (str): ther exchange name
        symbol (str): the trading symbol
        
    returns: 
        list: loaded history data or an empty list if no file found
    """
    loadedData = []
    directory = f'./history/{exchange}/'

    try:
        # get a list of all files in the specified directory
        file_list = os.listdir(directory)

        # define a custom sorting function
        def numericalSort(value):
            parts = re.split(r'(\d+)', value)
            parts[1::2] = map(int, parts[1::2])
            return parts

        # sort the filenames numerically
        sorted_files = sorted(file_list, key=numericalSort)

        cnt = 0
        for filename in sorted_files:
            if filename.startswith(f'{symbol}_M1_') and filename.endswith('.json'):
                # load data from each valid history file
                with open(os.path.join(directory, filename), 'r') as file:
                    file_data = json.load(file)
                    if len(file_data) > 0:
                        loadedData += file_data
                        cnt += 1
        if not loadedData:
            print(f'No history files found for {exchange} - {symbol}. Starting fresh.')

    except FileNotFoundError:
        print(f'Directory {directory} not found.')

    return [loadedData, cnt]    

def is_future_time(start_time, milli):
    """
    checks if the given time is in the future compared to the current time(minus two last minutes).
    
    ars:
        start_time (int): the time to be checked, in seconds or milliseconds.
        
    returns:
        true if the time is in the future, false otherwise.
    """
    if milli:
        time_now = int(datetime.now().timestamp()*1000) - 120000
    else:
        time_now = int(datetime.now().timestamp()) - 120

    return start_time > time_now
        