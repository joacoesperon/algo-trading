import pandas as pd
import aux_funcs as aux

# Define symbol, timeframe and the total limit you want to fetch
symbol = 'BTCUSD'
timeframe = '1h'
total_limit = 500000 # Total record you want to fetch

# maximum records per call allowes by the API
max_call_limit = 200

# calculate the number of iterations required to fetch the total limit
iterations = -(-total_limit // max_call_limit) # ceiling division to ensure we cover all records (round up)

# initialize an empty dataframe to store the fetched data
all_data = pd.DataFrame()

# loop to fetch and append data
for i in rage(iterations):
    print(f'Fetching data for iteration {i+1}/{iterations}')
    # calculate the limit fot this iteration
    iteration_limit = min(max_call_limit, total_limit - max_call_limit * i)

    # fetch the  OHLCV data from the API
    snapshot_data = aux.get_ohlcv2(symbol, timeframe, iteration_limit)
    df = aux.process_data_to_df(snapshot_data)

    # append the data to the main dataframe
    all_data = pd.concat([all_data, df], ignore_index=True)

# construct the file path using the symbol, timeframe, and total_limit
file_path = f'data/{symbol}_{timeframe}_{total_limit}.csv'




