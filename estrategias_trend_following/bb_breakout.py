import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import warnings

# Suprimir warnings no críticos
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="backtesting")

# Activo a probar
crypto = 'BTCUSDT'

# Cargar datos (velas de 1h)
df_1h = pd.read_csv(f"data/{crypto}_60_full.csv", parse_dates=["timestamp"])
df_1h.set_index("timestamp", inplace=True)

# Función para calcular EMA
def EMA(series, period):
    series = pd.Series(series)
    return series.ewm(span=period, adjust=False).mean()

# Función para calcular LRC (Linear Regression Curve)
def LRC(series, period):
    series = pd.Series(series)
    x = np.arange(period)
    lrc = np.zeros(len(series))
    for i in range(period - 1, len(series)):
        y = series[i-period+1:i+1]
        coeffs = np.polyfit(x, y, 1)
        lrc[i] = np.polyval(coeffs, period - 1)
    return pd.Series(lrc, index=series.index).bfill()

# Función para calcular SuperSmoother
def SuperSmoother(series, poles=2):
    series = pd.Series(series)
    a = np.exp(-1.414 * np.pi / 10)
    b = 2 * a * np.cos(np.radians(1.414 * 180 / 10))
    c = a * a
    d = 1 - b + c
    ss = np.zeros(len(series))
    for i in range(2, len(series)):
        ss[i] = d * series[i] + b * ss[i-1] - c * ss[i-2]
    return pd.Series(ss, index=series.index).bfill()

# Función para calcular Bandas de Bollinger
def BollingerBands(close, period, stddev, ma_type):
    close = pd.Series(close)
    if ma_type == 'EMA':
        ma = EMA(close, period)
    elif ma_type == 'LRC':
        ma = LRC(close, period)
    else:  # SuperSmoother
        ma = SuperSmoother(close)
    
    std = close.rolling(window=period).std()
    upper_band = ma + (stddev * std)
    lower_band = ma - (stddev * std)
    return ma, upper_band, lower_band

class BollingerBandsBreakoutStrategy(Strategy):
    bb_period = 120  # Default: 5 días (120 velas de 1h)
    bb_stddev = 2.0  # Default: desviación estándar
    ma_type = 'EMA'  # Default: tipo de MA
    stop_loss = 0.0  # Default: sin stop-loss (como el artículo)
    use_trailing_stop = False  # Cambiar a True para usar trailing stop

    def init(self):
        ma, upper_band, lower_band = BollingerBands(
            self.data.Close, self.bb_period, self.bb_stddev, self.ma_type
        )
        self.ma = self.I(lambda x: x, ma)
        self.upper_band = self.I(lambda x: x, upper_band)
        self.lower_band = self.I(lambda x: x, lower_band)
        self.bought = False
        self.entry_price = None
        self.highest_price = None
        self.trailing_stop_price = None

    def next(self):
        if np.isnan(self.upper_band[-1]) or np.isnan(self.ma[-1]):
            return

        current_price = self.data.Close[-1]

        # Entrar en posición long (precio cruza banda superior, con confirmación)
        if not self.bought and current_price > self.upper_band[-1] and self.data.Close[-2] > self.upper_band[-2]:
            self.buy()
            self.bought = True
            self.entry_price = current_price
            if self.use_trailing_stop:
                self.highest_price = current_price
                self.trailing_stop_price = current_price * (1 - self.stop_loss)

        # Salir de posición
        elif self.bought:
            if self.use_trailing_stop and self.highest_price is not None:
                # Actualizar trailing stop
                self.highest_price = max(self.highest_price, current_price)
                self.trailing_stop_price = max(self.trailing_stop_price, self.highest_price * (1 - self.stop_loss))
                # Salir por trailing stop-loss
                if current_price <= self.trailing_stop_price:
                    self.position.close()
                    self.bought = False
                    self.entry_price = None
                    self.highest_price = None
                    self.trailing_stop_price = None
            else:
                # Salir por cruze de banda inferior o stop-loss (si stop_loss > 0)
                if current_price < self.lower_band[-1]:
                    self.position.close()
                    self.bought = False
                    self.entry_price = None
                elif self.stop_loss > 0 and (self.entry_price - current_price) / self.entry_price >= self.stop_loss:
                    self.position.close()
                    self.bought = False
                    self.entry_price = None

# Ejecutar backtest
bt = Backtest(df_1h, BollingerBandsBreakoutStrategy, cash=1000000, commission=0.00075)
stats = bt.optimize(
    bb_period=[72, 120],  # 3 días (72 velas de 1h), 5 días (120 velas de 1h)
    bb_stddev=[2.0],  # Fijo en 2, según artículo
    ma_type=['EMA', 'LRC', 'SuperSmoother'],
    stop_loss=[0.0, 0.05, 0.08],  # 0.0 = sin stop-loss, más 5%, 8%
    maximize='Return [%]',
    max_tries=100
)

# Imprimir resultados
print(f"\nResultados para {crypto}:")
print(stats)
print("\nMejores parámetros:")
print(f"BB Period: {stats._strategy.bb_period} hours ({stats._strategy.bb_period/24:.1f} days)")
print(f"BB Stddev: {stats._strategy.bb_stddev}")
print(f"MA Type: {stats._strategy.ma_type}")
print(f"Stop Loss: {stats._strategy.stop_loss*100:.1f}%")
print("\nTrades detallados:")
print(stats._trades.head(5))  # Primeras 5 filas
print(stats._trades.tail(5))  # Últimas 5 filas