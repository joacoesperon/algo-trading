import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import warnings

# Suprimir warnings no críticos
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
warnings.filterwarnings("ignore", category=RuntimeWarning, module="backtesting")

# Cargar datos (cambiar para cada cripto)
df_1d = pd.read_csv("data/SOLUSDT_D_full.csv", parse_dates=["timestamp"])
df_1d.set_index("timestamp", inplace=True)

# Función para calcular ATR en velas de 1d
def ATR(high, low, close, period):
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)
    tr = pd.DataFrame({
        'tr1': high - low,
        'tr2': abs(high - close.shift()),
        'tr3': abs(low - close.shift())
    }).max(axis=1)
    return tr.rolling(window=period).mean()

# Función para calcular Supertrend (basada en Gekko)
def Supertrend(high, low, close, atr_period, multiplier, index):
    high = pd.Series(high, index=index)
    low = pd.Series(low, index=index)
    close = pd.Series(close, index=index)
    
    atr = ATR(high, low, close, atr_period)
    
    # Calcular bandas básicas
    hl2 = (high + low) / 2
    upper_band_basic = hl2 + (multiplier * atr)
    lower_band_basic = hl2 - (multiplier * atr)
    
    # Inicializar Supertrend
    upper_band = pd.Series(np.nan, index=index)
    lower_band = pd.Series(np.nan, index=index)
    supertrend = pd.Series(np.nan, index=index)
    trend = pd.Series(0, index=index)
    
    # Primer valor
    if not pd.isna(atr.iloc[atr_period]):
        upper_band.iloc[atr_period] = upper_band_basic.iloc[atr_period]
        lower_band.iloc[atr_period] = lower_band_basic.iloc[atr_period]
        supertrend.iloc[atr_period] = lower_band.iloc[atr_period]
        trend.iloc[atr_period] = 1 if close.iloc[atr_period] > supertrend.iloc[atr_period] else 0
    
    # Lógica de Gekko
    for i in range(atr_period + 1, len(close)):
        if pd.isna(atr.iloc[i]):
            continue
            
        # Actualizar upper_band
        if upper_band_basic.iloc[i] < upper_band.iloc[i-1] or close.iloc[i-1] > upper_band.iloc[i-1]:
            upper_band.iloc[i] = upper_band_basic.iloc[i]
        else:
            upper_band.iloc[i] = upper_band.iloc[i-1]
        
        # Actualizar lower_band
        if lower_band_basic.iloc[i] > lower_band.iloc[i-1] or close.iloc[i-1] < lower_band.iloc[i-1]:
            lower_band.iloc[i] = lower_band_basic.iloc[i]
        else:
            lower_band.iloc[i] = lower_band_basic.iloc[i-1]
        
        # Actualizar supertrend
        if supertrend.iloc[i-1] == upper_band.iloc[i-1] and close.iloc[i] <= upper_band.iloc[i]:
            supertrend.iloc[i] = upper_band.iloc[i]
        elif supertrend.iloc[i-1] == upper_band.iloc[i-1] and close.iloc[i] >= upper_band.iloc[i]:
            supertrend.iloc[i] = lower_band.iloc[i]
        elif supertrend.iloc[i-1] == lower_band.iloc[i-1] and close.iloc[i] >= lower_band.iloc[i]:
            supertrend.iloc[i] = lower_band.iloc[i]
        elif supertrend.iloc[i-1] == lower_band.iloc[i-1] and close.iloc[i] <= lower_band.iloc[i]:
            supertrend.iloc[i] = upper_band.iloc[i]
        else:
            supertrend.iloc[i] = supertrend.iloc[i-1]
        
        # Determinar tendencia
        trend.iloc[i] = 1 if close.iloc[i] > supertrend.iloc[i] else 0
    
    return supertrend, trend

class SupertrendStrategy(Strategy):
    atr_period = 7  # Default inspirado en Gekko (días)
    multiplier = 3.0  # Default del código Gekko
    stop_loss = 0.05  # Default 5% stop-loss

    def init(self):
        supertrend, trend = Supertrend(
            self.data.High, self.data.Low, self.data.Close,
            self.atr_period, self.multiplier, self.data.index
        )
        self.supertrend = self.I(lambda x: x, supertrend)
        self.trend = self.I(lambda x: x, trend)
        self.bought = False
        self.entry_price = None

    def next(self):
        if np.isnan(self.supertrend[-1]) or np.isnan(self.trend[-1]):
            return

        # Entrar en posición long
        if self.trend[-1] == 1 and not self.bought:
            self.buy()
            self.bought = True
            self.entry_price = self.data.Close[-1]
        
        # Salir de posición (por Supertrend o stop-loss)
        elif self.bought:
            # Salir por Supertrend
            if self.trend[-1] == 0:
                self.position.close()
                self.bought = False
                self.entry_price = None
            # Salir por stop-loss
            elif self.entry_price is not None:
                current_price = self.data.Close[-1]
                if (self.entry_price - current_price) / self.entry_price >= self.stop_loss:
                    self.position.close()
                    self.bought = False
                    self.entry_price = None

bt = Backtest(df_1d, SupertrendStrategy, cash=1000000, commission=0.00075)

stats = bt.optimize(
    atr_period=[3, 5, 7, 14],  # Días, inspirado en Gekko y artículo
    multiplier=[1.5, 2.0, 2.5, 3.0],
    stop_loss=[0.02, 0.05, 0.08, 0.10],  # 2%, 5%, 8%, 10%
    maximize='Return [%]',
    max_tries=100
)

print(stats)
print("\nMejores parámetros:")
print(f"ATR Period: {stats._strategy.atr_period} days")
print(f"Multiplier: {stats._strategy.multiplier}")
print(f"Stop Loss: {stats._strategy.stop_loss*100:.1f}%")
print("\nTrades detallados:")
print(stats._trades)

total_pnl = stats._trades['PnL'].sum() if not stats._trades.empty else 0
initial_cash = 1000000
final_equity = initial_cash + total_pnl
manual_return = (final_equity - initial_cash) / initial_cash * 100
print(f"\nRetorno manual calculado: {manual_return:.2f}%")
print(f"Equity final manual: ${final_equity:.2f}")