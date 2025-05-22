# Joaquin Esperon Trading Bot Repository

# RBI FrameWork
    
    RBI - Research, Backtest, Implement
    
    Research: research trading strategies and alpha generation techniques (google scholar, books, podcasts, youtube)
    Backtest: use ohlcv data in order to backtest the strategy
    Implement: if the backtest is profitable, implement into a trading bot with tiny size & scale slowly

# Useful tips

    para instalar todas las dependencias: pip install -r requirements.txt
    para desisntalar todas las dependencias: pip uninstall -r requirements.txt -y

    para ver los datos descargados el tradingview es bybit, perpetual contracts y zona horaria utc (londres)

# TO-DO
Lista de estrategias con parámetros
A continuación, presento las siete estrategias de trend following mencionadas, con sus parámetros, lógica, y detalles adicionales:

1. MA Crossover (rx_xma)
Descripción: Genera señales basadas en el cruce de dos medias móviles (MA): una rápida y una lenta. Una señal de compra ocurre cuando la MA rápida cruza por encima de la MA lenta, y una señal de venta cuando cruza por debajo.
Parámetros:
Fast MA: 5 días
Slow MA: 40 días
Tipos de MA probados:
EMA (Exponential Moving Average)
LRC (Linear Regression Curve)
HMA (Hull Moving Average)
WMA (Weighted Moving Average)
KAMA (Kaufman Adaptive Moving Average)
SuperSmoother
WVMA (Wilder's Variable Moving Average)
TEMA (Triple Exponential Moving Average)
ZLEMA (Zero Lag Exponential Moving Average)
Lógica:
Compra: Fast MA > Slow MA (cruce alcista).
Venta: Fast MA < Slow MA (cruce bajista).
Notas: La estrategia prueba múltiples tipos de MA para determinar cuál ofrece el mejor rendimiento. Cada tipo de MA tiene un cálculo diferente, afectando la sensibilidad a los cambios de precio.
2. Supertrend (SupertrendXm)
Descripción: Utiliza la banda de Supertrend, basada en el Average True Range (ATR), para identificar tendencias. Una señal de compra se genera cuando el precio cruza por encima de la banda superior, y una señal de venta cuando cruza por debajo de la banda inferior.
Parámetros:
Periodo del ATR: 5 días
Multiplicador de la banda: 1.5, 2, 2.5
Tamaño de la vela: 1440 minutos (1 día)
Lógica:
Compra: Close > Upper Band.
Venta: Close < Lower Band.
La banda superior/inferior se calcula como: Media ± Multiplicador × ATR.
Notas: El multiplicador ajusta la sensibilidad de las bandas. Un valor menor (1.5) genera más señales, mientras que un valor mayor (2.5) filtra señales en mercados ruidosos. El código específico está en Gekko Supertrend Strategy.
3. Bollinger Bands Breakout (rx_bb_bout)
Descripción: Usa las bandas de Bollinger para detectar breakouts. Una señal de compra se genera cuando el precio cruza por encima de la banda superior, y una señal de venta cuando cruza por debajo de la banda inferior.
Parámetros:
Periodo de las bandas: 3 días, 5 días
Desviación estándar: 2
Tipo de MA para la banda central:
EMA
LRC
SuperSmoother
Lógica:
Compra: Close > Upper Band (MA + 2 × StdDev).
Venta: Close < Lower Band (MA - 2 × StdDev).
Notas: La banda central es una MA, y se probaron diferentes tipos para evaluar su impacto. Los períodos más cortos (3 días) son más sensibles a movimientos rápidos.
4. High/Low Breakout (hilo)
Descripción: Identifica breakouts basados en los máximos y mínimos de un período determinado. Una señal de compra ocurre cuando el precio cierra por encima del máximo de los últimos N días, y una señal de venta cuando cierra por debajo del mínimo.
Parámetros:
Periodo: 5 días, 10 días
Lógica:
Compra: Close > Máximo de los últimos N días.
Venta: Close < Mínimo de los últimos N días.
Notas: Es una estrategia pura de acción del precio, ideal para mercados volátiles como cripto, ya que no depende de indicadores con retraso.
5. Linear Regression Slope (expreg_slope)
Descripción: Usa la pendiente de una línea de regresión lineal sobre el precio de cierre para determinar la tendencia. Una pendiente positiva indica una tendencia alcista (compra), y una pendiente negativa indica una tendencia bajista (venta).
Parámetros:
Periodo de regresión: 5 días, 10 días, 15 días
Lógica:
Compra: Pendiente > 0.
Venta: Pendiente < 0.
Notas: La pendiente mide la dirección y fuerza de la tendencia. Períodos más largos (15 días) son menos sensibles al ruido.
6. Single MA/Price Crossover (rx_xma_single)
Descripción: Genera señales basadas en el cruce del precio con una sola MA. Una señal de compra ocurre cuando el precio cruza por encima de la MA, y una señal de venta cuando cruza por debajo.
Parámetros:
Periodo de la MA: 30 días
Tipos de MA probados:
EMA
LRC
HMA
WMA
KAMA
SuperSmoother
WVMA
TEMA
ZLEMA
Lógica:
Compra: Close > MA.
Venta: Close < MA.
Notas: Similar a MA Crossover, pero usa una sola MA, lo que simplifica la lógica.
7. Single MA Slope (rx_xma_slope)
Descripción: Usa la pendiente de una sola MA para determinar la tendencia. Una pendiente positiva indica una tendencia alcista (compra), y una pendiente negativa indica una tendencia bajista (venta).
Parámetros:
Periodo de la MA: 20 días
Periodo de la pendiente: 1 día
Tipos de MA probados:
EMA
LRC
HMA
WMA
KAMA
SuperSmoother
WVMA
TEMA
ZLEMA
Lógica:
Compra: Pendiente de la MA > 0.
Venta: Pendiente de la MA < 0.
Notas: La pendiente se calcula como la diferencia de la MA en un día, lo que mide la dirección de la tendencia.

# Estrategias probadas

## MA Crossover
optimizado con:
stats = bt.optimize(
    fast_period=[96, 120, 144, 480],  # 4, 5, 6, 20 días
    slow_period=[840, 960, 1080, 1200],  # 35, 40, 45, 50 días
    ma_type=['EMA', 'WMA', 'HMA', 'LRC', 'TEMA', 'ZLEMA', 'KAMA', 'WVMA', 'SuperSmoother'],
    poles=[2],
    sl_percent=[3.0, 4.0, 5.0],  # Optimizar SL
    maximize='Return [%]',
    constraint=lambda p: p.fast_period < p.slow_period,
    max_tries=100
)
### BTC
(.venv) joacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/ma_crossover.py
Start                     2020-03-25 10:00:00
End                       2025-05-03 15:00:00
Duration                   1865 days 05:00:00
Exposure Time [%]                   49.796721
Equity Final [$]              24959722.847075
Equity Peak [$]               27109025.486525
Return [%]                        2395.972285
Buy & Hold Return [%]             1362.034438
Return (Ann.) [%]                   87.474232
Volatility (Ann.) [%]               81.704158
Sharpe Ratio                         1.070622
Sortino Ratio                        3.564153
Calmar Ratio                         2.343765
Max. Drawdown [%]                  -37.322102
Avg. Drawdown [%]                   -2.960206
Max. Drawdown Duration      518 days 21:00:00
Avg. Drawdown Duration        7 days 16:00:00
#Trades                                   33
Win Rate [%]                        39.393939
Best Trade [%]                     402.319716
Worst Trade [%]                     -4.730466
Avg. Trade [%]                      10.260462
Max. Trade Duration         194 days 00:00:00
Avg. Trade Duration          28 days 03:00:00
Profit Factor                       10.111785
Expectancy [%]                       18.29575
SQN                                  2.022112
_strategy                 MACrossoverStrat...
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object

Mejores parámetros:
Fast MA Period: 144 hours (6.0 days)
Slow MA Period: 840 hours (35.0 days)
MA Type: EMA
Poles (SuperSmoother): 2
Stop-Loss (%): 3.0

### ETH
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/ma_crossover.py
Start                     2021-03-15 00:00:00
End                       2025-05-03 15:00:00
Duration                   1510 days 15:00:00
Exposure Time [%]                   29.879192
Equity Final [$]               5333904.809998
Equity Peak [$]                5836188.071665
Return [%]                         433.390481
Buy & Hold Return [%]               -2.220267
Return (Ann.) [%]                   49.839536
Volatility (Ann.) [%]               63.380822
Sharpe Ratio                          0.78635
Sortino Ratio                        2.096536
Calmar Ratio                         1.538993
Max. Drawdown [%]                  -32.384509
Avg. Drawdown [%]                   -3.183115
Max. Drawdown Duration      504 days 08:00:00
Avg. Drawdown Duration       10 days 10:00:00
#Trades                                   60
Win Rate [%]                        31.666667
Best Trade [%]                       80.14277
Worst Trade [%]                     -6.812036
Avg. Trade [%]                       2.829949
Max. Trade Duration          49 days 00:00:00
Avg. Trade Duration           7 days 12:00:00
Profit Factor                        2.654683
Expectancy [%]                       3.920429
SQN                                  1.396647
_strategy                 MACrossoverStrat...
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object

Mejores parámetros:
Fast MA Period: 144 hours (6.0 days)
Slow MA Period: 960 hours (40.0 days)
MA Type: KAMA
Poles (SuperSmoother): 2
Stop-Loss (%): 3.0

### SOL
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/ma_crossover.py
Start                     2021-10-15 00:00:00
End                       2025-05-15 07:00:00
Duration                   1308 days 07:00:00
Exposure Time [%]                   38.656051
Equity Final [$]              21286651.056122
Equity Peak [$]               32439497.527837
Return [%]                        2028.665106
Buy & Hold Return [%]                15.26122
Return (Ann.) [%]                  128.474449
Volatility (Ann.) [%]              163.887945
Sharpe Ratio                         0.783916
Sortino Ratio                        3.637218
Calmar Ratio                         3.125826
Max. Drawdown [%]                   -41.10096
Avg. Drawdown [%]                   -5.125695
Max. Drawdown Duration      173 days 18:00:00
Avg. Drawdown Duration        8 days 20:00:00
#Trades                                   74
Win Rate [%]                        35.135135
Best Trade [%]                     116.596208
Worst Trade [%]                     -7.009387
Avg. Trade [%]                       4.219138
Max. Trade Duration          31 days 14:00:00
Avg. Trade Duration           6 days 20:00:00
Profit Factor                        3.176915
Expectancy [%]                       5.771135
SQN                                  1.949093
_strategy                 MACrossoverStrat...
_equity_curve                             ...
_trades                         Size  Entr...
dtype: object

Mejores parámetros:
Fast MA Period: 96 hours (4.0 days)
Slow MA Period: 840 hours (35.0 days)
MA Type: TEMA
Poles (SuperSmoother): 2
Stop-Loss (%): 4.0

### XRP
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/ma_crossover.py
Start                     2021-05-13 09:00:00
End                       2025-05-15 07:00:00
Duration                   1462 days 22:00:00
Exposure Time [%]                   28.743129
Equity Final [$]              27576422.809319
Equity Peak [$]               29043171.435219
Return [%]                        2657.642281
Buy & Hold Return [%]               96.747903
Return (Ann.) [%]                  128.639103
Volatility (Ann.) [%]              158.513698
Sharpe Ratio                         0.811533
Sortino Ratio                        5.333536
Calmar Ratio                         3.300637
Max. Drawdown [%]                  -38.974023
Avg. Drawdown [%]                    -5.68512
Max. Drawdown Duration      316 days 02:00:00
Avg. Drawdown Duration       15 days 03:00:00
#Trades                                   72
Win Rate [%]                             25.0
Best Trade [%]                      318.30761
Worst Trade [%]                     -5.176164
Avg. Trade [%]                       4.714657
Max. Trade Duration          33 days 20:00:00
Avg. Trade Duration           5 days 20:00:00
Profit Factor                        5.529648
Expectancy [%]                       7.907247
SQN                                  1.642112
_strategy                 MACrossoverStrat...
_equity_curve                             ...
_trades                           Size  En...
dtype: object

Mejores parámetros:
Fast MA Period: 144 hours (6.0 days)
Slow MA Period: 1200 hours (50.0 days)
MA Type: HMA
Poles (SuperSmoother): 2
Stop-Loss (%): 2.0

### BNB
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/ma_crossover.py
Start                     2021-06-29 07:00:00
End                       2025-05-15 07:00:00
Duration                   1416 days 00:00:00
Exposure Time [%]                   36.398411
Equity Final [$]               4223234.189237
Equity Peak [$]                5264802.176275
Return [%]                         322.323419
Buy & Hold Return [%]              117.498314
Return (Ann.) [%]                   44.808715
Volatility (Ann.) [%]               48.483751
Sharpe Ratio                         0.924201
Sortino Ratio                        2.401964
Calmar Ratio                         1.473025
Max. Drawdown [%]                  -30.419515
Avg. Drawdown [%]                   -3.780625
Max. Drawdown Duration      374 days 23:00:00
Avg. Drawdown Duration       12 days 10:00:00
#Trades                                   62
Win Rate [%]                        33.870968
Best Trade [%]                      62.901351
Worst Trade [%]                     -4.627245
Avg. Trade [%]                       2.350948
Max. Trade Duration          35 days 05:00:00
Avg. Trade Duration           8 days 07:00:00
Profit Factor                        2.472284
Expectancy [%]                       2.909696
SQN                                  1.730458
_strategy                 MACrossoverStrat...
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object

Mejores parámetros:
Fast MA Period: 144 hours (6.0 days)
Slow MA Period: 960 hours (40.0 days)
MA Type: TEMA
Poles (SuperSmoother): 2
Stop-Loss (%): 3.0

## Supertrend
unica estrategia con velas de 1D

optimizado con:
stats = bt.optimize(
    atr_period=[3, 5, 7, 14],  # Días, inspirado en Gekko y artículo
    multiplier=[1.5, 2.0, 2.5, 3.0],
    stop_loss=[0.02, 0.05, 0.08, 0.10],  # 2%, 5%, 8%, 10%
    maximize='Return [%]',
    max_tries=100
)
### BTC
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/supertrend.py
Start                     2020-03-25 00:00:00
End                       2025-05-20 00:00:00
Duration                   1882 days 00:00:00
Exposure Time [%]                   73.234201
Equity Final [$]              25171233.820425
Equity Peak [$]               25383077.620425
Return [%]                        2417.123382
Buy & Hold Return [%]             1471.429424
Return (Ann.) [%]                   86.874823
Volatility (Ann.) [%]               98.368389
Sharpe Ratio                         0.883158
Sortino Ratio                        2.810872
Calmar Ratio                         1.652246
Max. Drawdown [%]                  -52.579825
Avg. Drawdown [%]                   -7.253759
Max. Drawdown Duration      842 days 00:00:00
Avg. Drawdown Duration       32 days 00:00:00
#Trades                                   52
Win Rate [%]                        28.846154
Best Trade [%]                     396.265712
Worst Trade [%]                    -11.814506
Avg. Trade [%]                       6.415059
Max. Trade Duration         222 days 00:00:00
Avg. Trade Duration          26 days 00:00:00
Profit Factor                        5.147634
Expectancy [%]                      12.130066
SQN                                  1.726948
_strategy                 SupertrendStrate...
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object

Mejores parámetros:
ATR Period: 3 days
Multiplier: 2.0
Stop Loss: 2.0%

### ETH
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/supertrend.py
Start                     2021-03-15 00:00:00
End                       2025-05-20 00:00:00
Duration                   1527 days 00:00:00
Exposure Time [%]                    61.84555
Equity Final [$]               5963192.130335
Equity Peak [$]                7579468.522382
Return [%]                         496.319213
Buy & Hold Return [%]               39.487937
Return (Ann.) [%]                   53.194083
Volatility (Ann.) [%]               94.826343
Sharpe Ratio                         0.560963
Sortino Ratio                        1.445008
Calmar Ratio                         1.055111
Max. Drawdown [%]                  -50.415616
Avg. Drawdown [%]                   -9.086714
Max. Drawdown Duration      264 days 00:00:00
Avg. Drawdown Duration       38 days 00:00:00
#Trades                                   66
Win Rate [%]                        22.727273
Best Trade [%]                      92.245628
Worst Trade [%]                    -14.785815
Avg. Trade [%]                       2.743119
Max. Trade Duration          85 days 00:00:00
Avg. Trade Duration          14 days 00:00:00
Profit Factor                        2.281589
Expectancy [%]                       4.141752
SQN                                  1.107435
_strategy                 SupertrendStrate...
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object

Mejores parámetros:
ATR Period: 7 days
Multiplier: 1.5
Stop Loss: 2.0%

### SOL
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/supertrend.py
Start                     2021-10-15 00:00:00
End                       2025-05-20 00:00:00
Duration                   1313 days 00:00:00
Exposure Time [%]                   70.319635
Equity Final [$]              10296348.261861
Equity Peak [$]               24663867.771941
Return [%]                         929.634826
Buy & Hold Return [%]                1.847483
Return (Ann.) [%]                   91.117693
Volatility (Ann.) [%]              180.305935
Sharpe Ratio                          0.50535
Sortino Ratio                        1.864695
Calmar Ratio                         1.309193
Max. Drawdown [%]                  -69.598369
Avg. Drawdown [%]                   -15.56813
Max. Drawdown Duration      434 days 00:00:00
Avg. Drawdown Duration       47 days 00:00:00
#Trades                                   37
Win Rate [%]                        27.027027
Best Trade [%]                     765.054867
Worst Trade [%]                    -20.597764
Avg. Trade [%]                       6.504924
Max. Trade Duration         183 days 00:00:00
Avg. Trade Duration          24 days 00:00:00
Profit Factor                         5.40347
Expectancy [%]                       22.59603
SQN                                  0.662947
_strategy                 SupertrendStrate...
_equity_curve                             ...
_trades                         Size  Entr...
dtype: object

Mejores parámetros:
ATR Period: 14 days
Multiplier: 1.5
Stop Loss: 5.0%

### XRP
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/supertrend.py
Start                     2021-05-13 00:00:00
End                       2025-05-20 00:00:00
Duration                   1468 days 00:00:00
Exposure Time [%]                   70.728387
Equity Final [$]               4040173.143684
Equity Peak [$]                7902325.379115
Return [%]                         304.017314
Buy & Hold Return [%]               71.701847
Return (Ann.) [%]                    41.47223
Volatility (Ann.) [%]              128.960793
Sharpe Ratio                         0.321588
Sortino Ratio                        0.979959
Calmar Ratio                         0.640533
Max. Drawdown [%]                  -64.746434
Avg. Drawdown [%]                  -17.297056
Max. Drawdown Duration     1167 days 00:00:00
Avg. Drawdown Duration      126 days 00:00:00
#Trades                                   56
Win Rate [%]                        19.642857
Best Trade [%]                     375.399908
Worst Trade [%]                    -18.849794
Avg. Trade [%]                       2.524715
Max. Trade Duration          91 days 00:00:00
Avg. Trade Duration          18 days 00:00:00
Profit Factor                         3.04099
Expectancy [%]                       7.169041
SQN                                  0.582529
_strategy                 SupertrendStrate...
_equity_curve                             ...
_trades                          Size  Ent...
dtype: object

Mejores parámetros:
ATR Period: 5 days
Multiplier: 1.5
Stop Loss: 2.0%

### BNB
.venvjoacoesperon@GAMEROS-E2S95OR:~/algo_trading$ /home/joacoesperon/algo_trading/.venv/bin/python /home/joacoesperon/algo_trading/supertrend.py
Start                     2021-06-29 00:00:00
End                       2025-05-20 00:00:00
Duration                   1421 days 00:00:00
Exposure Time [%]                   90.365682
Equity Final [$]               3322228.095075
Equity Peak [$]                3841427.968325
Return [%]                          232.22281
Buy & Hold Return [%]               113.19156
Return (Ann.) [%]                   36.094599
Volatility (Ann.) [%]               82.323719
Sharpe Ratio                         0.438447
Sortino Ratio                        0.954881
Calmar Ratio                         0.653926
Max. Drawdown [%]                  -55.196757
Avg. Drawdown [%]                  -10.437837
Max. Drawdown Duration      849 days 00:00:00
Avg. Drawdown Duration       78 days 00:00:00
#Trades                                   12
Win Rate [%]                        33.333333
Best Trade [%]                     143.580679
Worst Trade [%]                    -17.590743
Avg. Trade [%]                      10.523662
Max. Trade Duration         328 days 00:00:00
Avg. Trade Duration         107 days 00:00:00
Profit Factor                        3.973328
Expectancy [%]                      16.624565
SQN                                  1.163411
_strategy                 SupertrendStrate...
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object

Mejores parámetros:
ATR Period: 3 days
Multiplier: 3.0
Stop Loss: 5.0%

## Bollinger Bands
stats = bt.optimize(
    bb_period=[72, 120],  # 3 días (72 velas de 1h), 5 días (120 velas de 1h)
    bb_stddev=[2.0],  # Fijo en 2, según artículo
    ma_type=['EMA', 'LRC', 'SuperSmoother'],
    stop_loss=[0.0, 0.05, 0.08],  # 0.0 = sin stop-loss, más 5%, 8%
    maximize='Return [%]',
    max_tries=100
)

### BTC
Resultados para BTCUSDT:
Start                     2020-03-25 10:00:00
End                       2025-05-03 15:00:00
Duration                   1865 days 05:00:00
Exposure Time [%]                   42.407184
Equity Final [$]              20450394.851225
Equity Peak [$]                24916632.45365
Return [%]                        1945.039485
Buy & Hold Return [%]             1362.034438
Return (Ann.) [%]                   80.459836
Volatility (Ann.) [%]               72.248901
Sharpe Ratio                         1.113648
Sortino Ratio                        3.716428
Calmar Ratio                         1.829654
Max. Drawdown [%]                   -43.97544
Avg. Drawdown [%]                   -2.867018
Max. Drawdown Duration      513 days 06:00:00
Avg. Drawdown Duration        7 days 13:00:00
#Trades                                  104
Win Rate [%]                        46.153846
Best Trade [%]                      56.345764
Worst Trade [%]                     -6.840995
Avg. Trade [%]                       2.948312
Max. Trade Duration          36 days 06:00:00
Avg. Trade Duration           7 days 14:00:00
Profit Factor                        2.982131
Expectancy [%]                       3.486415
SQN                                  2.089683
_strategy                 BollingerBandsBr...
_equity_curve                             ...
_trades                        Size  Entry...
dtype: object

Mejores parámetros:
BB Period: 120 hours (5.0 days)
BB Stddev: 2.0
MA Type: LRC
Stop Loss: 5.0%


### ETH
Resultados para ETHUSDT:
Start                     2021-03-15 00:00:00
End                       2025-05-03 15:00:00
Duration                   1510 days 15:00:00
Exposure Time [%]                   41.568292
Equity Final [$]                4158541.01104
Equity Peak [$]                7471285.682085
Return [%]                         315.854101
Buy & Hold Return [%]               -2.220267
Return (Ann.) [%]                     41.0953
Volatility (Ann.) [%]               67.143462
Sharpe Ratio                         0.612052
Sortino Ratio                        1.488112
Calmar Ratio                         0.897218
Max. Drawdown [%]                  -45.803018
Avg. Drawdown [%]                   -3.198274
Max. Drawdown Duration      424 days 01:00:00
Avg. Drawdown Duration        9 days 03:00:00
#Trades                                  126
Win Rate [%]                         40.47619
Best Trade [%]                       56.43854
Worst Trade [%]                    -15.150657
Avg. Trade [%]                       1.137664
Max. Trade Duration          16 days 22:00:00
Avg. Trade Duration           4 days 23:00:00
Profit Factor                        1.684562
Expectancy [%]                       1.543587
SQN                                  0.856845
_strategy                 BollingerBandsBr...
_equity_curve                             ...
_trades                        Size  Entry...
dtype: object

Mejores parámetros:
BB Period: 72 hours (3.0 days)
BB Stddev: 2.0
MA Type: LRC
Stop Loss: 0.0%


### SOL
Resultados para SOLUSDT:
Start                     2021-10-15 00:00:00
End                       2025-05-15 07:00:00
Duration                   1308 days 07:00:00
Exposure Time [%]                   44.659236
Equity Final [$]              12316326.573698
Equity Peak [$]               15462986.226038
Return [%]                        1131.632657
Buy & Hold Return [%]                15.26122
Return (Ann.) [%]                  101.404179
Volatility (Ann.) [%]               146.92169
Sharpe Ratio                         0.690192
Sortino Ratio                        2.725976
Calmar Ratio                         1.970893
Max. Drawdown [%]                  -51.450891
Avg. Drawdown [%]                   -4.955577
Max. Drawdown Duration      433 days 06:00:00
Avg. Drawdown Duration       10 days 02:00:00
#Trades                                   75
Win Rate [%]                             44.0
Best Trade [%]                     133.912408
Worst Trade [%]                       -9.8607
Avg. Trade [%]                       3.404596
Max. Trade Duration          36 days 07:00:00
Avg. Trade Duration           7 days 18:00:00
Profit Factor                        2.661609
Expectancy [%]                       4.935317
SQN                                   1.87569
_strategy                 BollingerBandsBr...
_equity_curve                             ...
_trades                        Size  Entry...
dtype: object

Mejores parámetros:
BB Period: 120 hours (5.0 days)
BB Stddev: 2.0
MA Type: LRC
Stop Loss: 8.0%

### XRP
Resultados para XRPUSDT:
Start                     2021-05-13 09:00:00
End                       2025-05-15 07:00:00
Duration                   1462 days 22:00:00
Exposure Time [%]                   36.891572
Equity Final [$]               2835456.000087
Equity Peak [$]                3445851.369013
Return [%]                           183.5456
Buy & Hold Return [%]               96.747903
Return (Ann.) [%]                   29.672105
Volatility (Ann.) [%]               83.149493
Sharpe Ratio                         0.356853
Sortino Ratio                         0.91249
Calmar Ratio                         0.473736
Max. Drawdown [%]                  -62.634274
Avg. Drawdown [%]                   -7.688764
Max. Drawdown Duration     1172 days 04:00:00
Avg. Drawdown Duration       41 days 06:00:00
#Trades                                   84
Win Rate [%]                             25.0
Best Trade [%]                     337.232207
Worst Trade [%]                    -11.945057
Avg. Trade [%]                       1.248447
Max. Trade Duration          33 days 19:00:00
Avg. Trade Duration           6 days 10:00:00
Profit Factor                        2.167394
Expectancy [%]                       3.976333
SQN                                  0.812977
_strategy                 BollingerBandsBr...
_equity_curve                             ...
_trades                          Size  Ent...
dtype: object

Mejores parámetros:
BB Period: 120 hours (5.0 days)
BB Stddev: 2.0
MA Type: LRC
Stop Loss: 5.0%

### BNB
Resultados para BNBUSDT:
Start                     2021-06-29 07:00:00
End                       2025-05-15 07:00:00
Duration                   1416 days 00:00:00
Exposure Time [%]                    38.31102
Equity Final [$]               2552177.783737
Equity Peak [$]                3129378.985862
Return [%]                         155.217778
Buy & Hold Return [%]              117.498314
Return (Ann.) [%]                   27.295995
Volatility (Ann.) [%]               45.786214
Sharpe Ratio                         0.596162
Sortino Ratio                        1.252714
Calmar Ratio                         0.629709
Max. Drawdown [%]                  -43.346978
Avg. Drawdown [%]                   -4.302914
Max. Drawdown Duration      317 days 22:00:00
Avg. Drawdown Duration       14 days 01:00:00
#Trades                                  100
Win Rate [%]                             41.0
Best Trade [%]                      22.627041
Worst Trade [%]                     -7.704959
Avg. Trade [%]                       0.941422
Max. Trade Duration          23 days 21:00:00
Avg. Trade Duration           5 days 10:00:00
Profit Factor                        1.643002
Expectancy [%]                       1.118568
SQN                                    1.3898
_strategy                 BollingerBandsBr...
_equity_curve                             ...
_trades                       Size  EntryB...
dtype: object

Mejores parámetros:
BB Period: 72 hours (3.0 days)
BB Stddev: 2.0
MA Type: LRC
Stop Loss: 0.0%

## High/Low Breakout

### BTC

### ETH

### SOL

### XRP

### BNB