from dontshareconfig import key  
#key = 'klhjklhjklhjklhjk' -- this is whats in the dontshareconfig.py (private key, keep safe af)

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
# print('ONLY WORKS ON 3.8.5 QUANT INTERPRETER')

symbol = 'BTCUSD'
timeframe = '15m'

max_loss = -1
targets = 5
pos_size = 200
leverage = 10
vol_multiplier = 3
rounding = 4

cb_symbol = symbol + '/USDT' # ver para bybit

def get_sz_px_decimals(symbol):

    '''
    this is succesfully returns Size decimals and Price decimals

    this outputs the size decimals for a given symbol
    which is - the SIZE you can buy or sell at
    ex. if sz decimal == 1 then you can buy/sell 1.4
    if sz decimal == 2 then you can buy/sell 1.45
    if sz decimal == 3 then you can buy/sell 1.456

    if size isnt right, we get this error. to avoid it use the sz decimal func
    {'error': 'Invalid order size'}
    '''
    url = 'https://api.hyperliquid.xyz/info'
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'meta'}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        # Success
        data = response.json()
        #print(data)
        symbols = data['universe']
        symbol_info = next((s for s in symbols if s['name'] == symbol), None)
        if symbol_info:
            sz_decimals = symbol_info['szDecimals']
            
        else:
            print('Symbol not found')
    else:
        # Error
        print('Error:', response.status_code)

    ask = ask_bid(symbol)[0]
    #print(f'this is the ask {ask}')

    # Compute the number of decimal points in the ask price
    ask_str = str(ask)
    if '.' in ask_str:
        px_decimals = len(ask_str.split('.')[1])
    else:
        px_decimals = 0

    print(f'{symbol} this is the price {sz_decimals} decimal(s)')

    return sz_decimals, px_decimals

def limit_order(coin, is_buy, sz, limit_px, reduce_only, account):
    
    #account: LocalAccount = eth_account.Account.from_key(key)
    exchange = Exchange(account, constants.MAINNET_API_URL)
    # info = Info(constants.MAINNET_API_URL, ski_ws=True)
    # user_state = info.user_state(account.address)
    # print(f'this is current account value: {user_state['marginSummary']['accountValue']}') 

    rounding = get_sz_px_decimals(coin)[0]
    sz = round(sz, rounding)
    print(f'coin: {coin}, type: {type(coin)}')
    print(f'is_buy: {is_buy}, type: {type(is_buy)}')
    print(f'sz: {sz}, type: {type(sz)}')
    print(f'limit_px: {limit_px}, type: {type(limit_px)}')
    print(f'reduce_only: {reduce_only}, type: {type(reduce_only)}')


    #limit_px = str(limit_px)
    # sz = str(sz)
    # print(f'limit_px: {limit_px}, type: {type(limit_px)}')
    # print(f'sz: {sz}, type: {type(sz)}')
    print(f'placing limit order for {coin} {sz} @ {limit_px}')
    order_result = exchange.order(coin,is_buy, sz, limit_px, {"limit:": {"tif": "Gtc"}}, reduce_only=reduce_only)

    if is_buy == True:
        print(f'limit BUY order placed thanks joaco, resting: {order_result['response']['data']['statuses']}')
    else:
        print(f'limit SELL order placed thanks joaco, resting: {order_result['response']['data']['statuses']}')

    return order_result

def adjust_leverage_size_signal(symbol, level, account):
    
    """
    this calculates size based off what we want
    95% of balance
    """

    print('leverage:',leverage)

    #account: LocalAccount = eth_account.Account.from_key(key)
    exchange = Exchange(account, constants.MAINNET_API_URL)
    info = Info(constants.MAINNET_API_URL, ski_ws=True)
    
    #get the user state and print out leverage information for ETH
    user_state = info.user_state(account.address)
    acct_value = user_state['marginSummary']['accountValue']
    acct_value = float(acct_value)
    #print(acct_value)
    acct_val95 = acct_value * .95

    print(exchange.update_leverage(leverage, symbol))

    price = ask_bid(symbol)[0]

    # size == balance / price * leverage
    # INJ 6.95 ... at 10x lev... 10 INJ == $cost 6.95
    size = (acct_val95 / price) * leverage
    size = float(size)
    rounding = get_sz_px_decimals(symbol)[0]
    size = round(size, rounding)
    # print(f'this is the size we can use 95% fo acct val {size}')

    user_state = info.user_state(account.address)

    return leverage,size

def adjust_leverage(symbol, leverage):
    account= LocalAccount = eth_account.Account.from_key(key)
    exchange = Exchange(account, constants.MAINNET_API_URL)
    info = Info(constants.MAINNET_API_URL, ski_ws=True)

    print('leverage', leverage)

    exchange.update_leverage(leverage, symbol)

def get_ohlcv(cb_symbol, timeframe, limit):

    coinbase  = ccxt.kraken()

    ohlcv = coinbase.fetch_ohlcv(cb_symbol, timeframe, limit)
    #print(ohlcv)

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'],unit='ms')

    df = df.tail(limit)

    df['support'] = df[:-2]['close'].min()
    df['resis'] = df[:-2]['close'].max()

    # save the dataframe to a CSV file 
    df.to_csv('ohlcv_data.csv', index=False)

    return df

def get_ohlcv2(symbol, interval, lookback_days):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=lookback_days)

    url = 'https://api.hyperliquid.xyz/info'
    headers = {'Content-Type': 'application/json'}
    data = {
        'type': 'candleSnapshot',
        'req': {
            "coin": symbol,
            'interval': interval,
            'startTime': int(start_time.timestamp() * 1000),
            'endTime': int(end_time.timestamp() * 1000)
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        snapshot_data = response.json()
        return snapshot_data
    else:
        print(f'error fetching data for {symbol}: {response.status_code}')
        return None

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

def calculate_vwap_with_symbol(symbol):
    # Fetch and process data
    snapshot_data = get_ohlcv2(symbol, '15m', 300)
    df = process_data_to_df(snapshot_data)

    # Convert the 'timestamp' column to datetime and set it as the index 
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # Ensure all columns used for VWAP calculation are of numeric type
    numeric_columns = ['high', 'low', 'close', 'volume']
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors = 'coerce') # coerce will set errors to NaN

    # drop rows with NaN created dring type conversion(if any)
    df.dropna(subset=numeric_columns, inplace=True)

    # ensure the DataFrame is ordered by datetime
    df.sort_index(inplace=True)

    # calculate VWAP and add it as a new column
    df['VWAP'] = ta.vwap(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])

    # retieve the latest VWAP value from the DataFrame
    latest_vwap = df['VWAP'].iloc[-1]

    return df, latest_vwap 

def supply_demand_zones_hl(symbo, timeframe, limit):

    print('starting joacos supply and demand zone calculations...')

    sd_df = pd.DataFrame()

    snapshot_data = get_ohlcv2(symbol, timeframe, limit)
    df = process_data_to_df(snapshot_data)


    supp = df.iloc[-1]['support']
    resis = df.iloc[-1]['resis']
    #print(f'this is joacos support for 1h {supp_1h} this is resis: {resis_1h}')

    df['supp_lo'] = df[:-2]['low'].min()
    supp_lo = df.iloc[-1]['supp_lo']

    df['res_hi'] = df[:-2]['high'].max()
    res_hi = df.iloc[-1]['res_hi']

    print(df)


    sd_df[f'{timeframe}_dz'] = [supp_lo, supp]
    sd_df[f'{timeframe}_sz'] = [res_hi, resis]

    print('here are joaco supply and demand zones')
    print(sd_df)

    return sd_df

def get_position(symbol,account):

    """
    gets the current position info, like size, etc.
    """

    #account = LocalAccount = eth_account.Account.from_key(key)
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)
    print(f'this is current account value: {user_state["marginSummary"]["accountValue"]}')
    positions = []
    print(f'this is the symbol {symbol}')
    print(user_state["assetPositions"])
    for position in user_state["assetPositions"]:
        if (position["position"]["coin"] == symbol) and float(position["position"]["szi"]) != 0:
            positions.append(position["position"])
            in_pos = True
            size = float(position["position"]["szi"])
            pos_sym = position["position"]["coin"]
            entry_px = float(position["position"]["entryPx"])
            pnl_perc = float(position["position"]["returnOnEquity"])*100
            print(f'this is the pnl perc {pnl_perc}')
            break
    else:
        in_pos = False
        size = 0
        pos_sym = None
        entry_px = 0
        pnl_perc = 0
    
    if size > 0:
        long = True
    elif size < 0:
        long = False
    else:
        long = None



    

def create_combined_df(ob, exchange):
    bids_df = pd.DataFrame(ob['bids'], columns=['Bid', 'Bid Size'])
    asks_df = pd.DataFrame(ob['asks'], columns=['Ask', 'Ask Size'])
    if exchange == 'coinbasepro' and len(bids_df) > 100:
        bids_df = bids_df.head(100)
        asks_df = asks_df.head(100)
    return pd.concat([asks_df.reset_index(drop=True), bids_df.reset_index(drop=True)], axis=1)


def find_max_sizes(df):
    max_bid_size_row = df.loc[df['Bid Size'].idxmax()]
    max_ask_size_row = df.loc[df['Ask Size'].idxmax()]
    return max_bid_size_row['Bid'], max_bid_size_row['Bid Size'], max_ask_size_row['Ask'], max_ask_size_row['Ask Size']

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
    



# funciones para get_data.py
import os
import re


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
        