import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy

# Cargar los datos de 1H y 5M
df_1h = pd.read_csv("data/BTCUSDT_60.csv", parse_dates=["timestamp"])
df_5m = pd.read_csv("data/BTCUSDT_5.csv", parse_dates=["timestamp"])

# Calcular el máximo y mínimo del día anterior
df_1h["date"] = df_1h["timestamp"].dt.date
daily_levels = df_1h.groupby("date").agg({"High": "max", "Low": "min"}).shift(1)

df_5m["date"] = df_5m["timestamp"].dt.date
df_5m = df_5m.merge(daily_levels, on="date", how="left", suffixes=("", "_prev"))

# Establecer timestamp como índice para backtesting.py
df_5m.set_index("timestamp", inplace=True)

class BreakoutStrategy(Strategy):
    risk_per_trade = 0.01  # 1% del capital

    def init(self):
        pass

    def next(self):
        # Verificar si hay datos de niveles anteriores
        if np.isnan(self.data.High_prev[-1]) or np.isnan(self.data.Low_prev[-1]):
            return
        
        capital = self.equity  # Capital disponible
        entry_price = self.data.Close[-2]  # Precio de entrada basado en la vela anterior
        
        # Configurar TP y SL
        tp_long = entry_price * 1.02  # 2% arriba
        sl_long = entry_price * 0.99  # 1% abajo

        tp_short = entry_price * (1 - 0.02)  # 2% debajo del precio de entrada
        sl_short = entry_price * (1 + 0.01)  # 1% encima del precio de entrada


        # Cálculo del tamaño de la posición para arriesgar solo el 1% de la cuenta
        risk_amount = capital * self.risk_per_trade
        
        # Evitar división por cero
        size_long = risk_amount / abs(entry_price - sl_long) if abs(entry_price - sl_long) > 0 else 0
        size_short = risk_amount / abs(entry_price - sl_short) if abs(entry_price - sl_short) > 0 else 0
        
        # Asegurar que el tamaño sea entero
        size_long = max(1, round(size_long))
        size_short = max(1, round(size_short))

        # Confirmación de ruptura con vela completa
        if (self.data.Close[-2] > self.data.High_prev[-1]) and (self.data.Open[-2] > self.data.High_prev[-1]):
            self.buy(size=size_long, sl=sl_long, tp=tp_long)
        elif (self.data.Close[-2] < self.data.Low_prev[-1]) and (self.data.Open[-2] < self.data.Low_prev[-1]):
            self.sell(size=size_short, sl=sl_short, tp=tp_short)

# Ejecutar el backtest
bt = Backtest(df_5m, BreakoutStrategy, cash=1000000, commission=.00075)
results = bt.run()
print(results)

# Graficar los resultados
bt.plot()
