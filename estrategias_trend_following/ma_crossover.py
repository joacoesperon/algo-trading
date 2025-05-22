import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from collections import deque
import warnings

# Suprimir warnings no críticos de numpy y backtesting
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="backtesting")

df_1h = pd.read_csv("data/BNBUSDT_60_full.csv", parse_dates=["timestamp"])
df_1h.set_index("timestamp", inplace=True)

# Funciones para calcular diferentes tipos de MA
def EMA(array, n):
    return pd.Series(array).ewm(span=n, adjust=False).mean()

def WMA(array, n):
    return pd.Series(array).rolling(n).apply(lambda x: np.sum(x * np.arange(1, n + 1)) / np.sum(np.arange(1, n + 1)), raw=True)

def HMA(array, n):
    wma_n = pd.Series(array).rolling(n).apply(lambda x: np.sum(x * np.arange(1, n + 1)) / np.sum(np.arange(1, n + 1)), raw=True)
    wma_half = pd.Series(array).rolling(n // 2).apply(lambda x: np.sum(x * np.arange(1, n // 2 + 1)) / np.sum(np.arange(1, n // 2 + 1)), raw=True)
    hma_input = 2 * wma_half - wma_n
    return hma_input.rolling(int(np.sqrt(n))).apply(lambda x: np.sum(x * np.arange(1, int(np.sqrt(n)) + 1)) / np.sum(np.arange(1, int(np.sqrt(n)) + 1)), raw=True)

def LRC(array, n):
    x = np.arange(n)
    lrc = pd.Series(array).rolling(n).apply(lambda y: np.polyfit(x, y, 1)[1] + np.polyfit(x, y, 1)[0] * (n - 1), raw=True)
    return lrc

def TEMA(array, n):
    ema1 = pd.Series(array).ewm(span=n, adjust=False).mean()
    ema2 = ema1.ewm(span=n, adjust=False).mean()
    ema3 = ema2.ewm(span=n, adjust=False).mean()
    return 3 * ema1 - 3 * ema2 + ema3

def ZLEMA(array, n):
    lag = (n - 1) // 2
    adjusted = pd.Series(array) + (pd.Series(array) - pd.Series(array).shift(lag))
    return adjusted.ewm(span=n, adjust=False).mean()

def KAMA(array, n, fast_sc=0.666, slow_sc=0.0645):
    prices = pd.Series(array)
    kama = np.zeros(len(prices))
    kama[0] = prices[0]
    
    for i in range(1, len(prices)):
        change = abs(prices[i] - prices[i - n if i >= n else 0])
        volatility = sum(abs(prices[j] - prices[j - 1]) for j in range(max(1, i - n + 1), i + 1))
        er = change / volatility if volatility > 0 else 0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        kama[i] = kama[i - 1] + sc * (prices[i] - kama[i - 1])
    
    return pd.Series(kama)

def WVMA(array, n):
    return pd.Series(array).ewm(alpha=1/n, adjust=False).mean()

def SuperSmoother(array, n, poles=2):
    prices = pd.Series(array)
    result = np.zeros(len(prices))
    queue = deque(maxlen=5)
    
    pi = np.pi
    sq2 = np.sqrt(2.0)
    
    a1 = np.exp(-sq2 * pi / n)
    b1 = 2 * a1 * np.cos(sq2 * pi / n)
    coeff1 = 1 - b1 + a1 * a1
    coeff2 = b1
    coeff3 = -a1 * a1
    coeff4 = 0
    
    for i in range(len(prices)):
        queue.append(prices[i] if i < poles else result[i - 1])
        if len(queue) < poles:
            result[i] = prices[i]
        else:
            prev1 = queue[-1]
            prev2 = queue[-2]
            recurrent_part = coeff2 * prev1 + coeff3 * prev2
            result[i] = recurrent_part + coeff1 * prices[i]
    
    return pd.Series(result)

class MACrossoverStrategy(Strategy):
    fast_period = 120
    slow_period = 960
    ma_type = 'EMA'
    poles = 2
    sl_percent = 3.0  # Stop-loss del 3% por defecto

    def init(self):
        ma_functions = {
            'EMA': lambda x, n: EMA(x, n),
            'WMA': lambda x, n: WMA(x, n),
            'HMA': lambda x, n: HMA(x, n),
            'LRC': lambda x, n: LRC(x, n),
            'TEMA': lambda x, n: TEMA(x, n),
            'ZLEMA': lambda x, n: ZLEMA(x, n),
            'KAMA': lambda x, n: KAMA(x, n),
            'WVMA': lambda x, n: WVMA(x, n),
            'SuperSmoother': lambda x, n: SuperSmoother(x, n, self.poles)
        }
        ma_func = ma_functions[self.ma_type]
        
        self.fast_ma = self.I(ma_func, self.data.Close, self.fast_period)
        self.slow_ma = self.I(ma_func, self.data.Close, self.slow_period)
        self.entry_price = None  # Para rastrear precio de entrada

    def next(self):
        if np.isnan(self.fast_ma[-1]) or np.isnan(self.slow_ma[-1]):
            return

        # Verificar SL si hay posición abierta
        if self.position and self.entry_price is not None:
            sl_price = self.entry_price * (1 - self.sl_percent / 100)
            if self.data.Close[-1] <= sl_price:
                self.position.close()
                self.entry_price = None
                return

        # Condiciones de cruce
        if self.fast_ma[-1] > self.slow_ma[-1] and self.fast_ma[-2] <= self.slow_ma[-2]:
            if not self.position:
                self.buy()
                self.entry_price = self.data.Close[-1]
        elif self.fast_ma[-1] < self.slow_ma[-1] and self.fast_ma[-2] >= self.slow_ma[-2]:
            if self.position:
                self.position.close()
                self.entry_price = None

bt = Backtest(df_1h, MACrossoverStrategy, cash=1000000, commission=.00075)

stats = bt.optimize(
    fast_period=[96, 120, 144, 480],  # 4, 5, 6, 20 días
    slow_period=[840, 960, 1080, 1200],  # 35, 40, 45, 50 días
    ma_type=['EMA', 'WMA', 'HMA', 'LRC', 'TEMA', 'ZLEMA', 'KAMA', 'WVMA', 'SuperSmoother'],
    poles=[2],  # Fijar poles a 2
    sl_percent=[2.0, 3.0, 4.0],  # Optimizar SL
    maximize='Return [%]',
    constraint=lambda p: p.fast_period < p.slow_period,
    max_tries=100
)

print(stats)
print("\nMejores parámetros:")
print(f"Fast MA Period: {stats._strategy.fast_period} hours ({stats._strategy.fast_period / 24:.1f} days)")
print(f"Slow MA Period: {stats._strategy.slow_period} hours ({stats._strategy.slow_period / 24:.1f} days)")
print(f"MA Type: {stats._strategy.ma_type}")
print(f"Poles (SuperSmoother): {stats._strategy.poles}")
print(f"Stop-Loss (%): {stats._strategy.sl_percent}")
print("\nTrades detallados:")
print(stats._trades)

total_pnl = stats._trades['PnL'].sum() if not stats._trades.empty else 0
initial_cash = 1000000
final_equity = initial_cash + total_pnl
manual_return = (final_equity - initial_cash) / initial_cash * 100
print(f"\nRetorno manual calculado: {manual_return:.2f}%")
print(f"Equity final manual: ${final_equity:.2f}")