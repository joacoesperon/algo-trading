import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy

# Cargar los datos de 1H y 15M
df_1h = pd.read_csv("data/BTCUSDT_60.csv", parse_dates=["timestamp"])
df_15m = pd.read_csv("data/BTCUSDT_15.csv", parse_dates=["timestamp"])  # Ajusta el nombre del archivo según lo que descargaste

# Calcular el rango de breakout en 1H
df_1h["date"] = df_1h["timestamp"].dt.date
df_1h["range_high"] = df_1h["High"].rolling(window=24).max().shift(1)  # Máximo de 24h
df_1h["range_low"] = df_1h["Low"].rolling(window=24).min().shift(1)    # Mínimo de 24h

# Combinar con datos de 15M
df_15m["date"] = df_15m["timestamp"].dt.date
df_15m = df_15m.merge(df_1h[["timestamp", "range_high", "range_low"]], left_on="timestamp", right_on="timestamp", how="left").ffill()

# Calcular volumen promedio
df_15m["vol_avg"] = df_15m["Volume"].rolling(window=20).mean()

# Establecer timestamp como índice
df_15m.set_index("timestamp", inplace=True)

class BreakoutStrategy(Strategy):
    risk_per_trade = 0.01  # 1% del capital
    rr_ratio = 2          # Relación riesgo/recompensa 2:1

    def init(self):
        self.range_high = self.data.range_high
        self.range_low = self.data.range_low
        self.vol_avg = self.data.vol_avg

    def next(self):
        if np.isnan(self.range_high[-1]) or np.isnan(self.range_low[-1]):
            return

        capital = self.equity
        entry_price = self.data.Close[-1]

        # Evitar operar si ya hay una posición abierta
        if self.position:
            return

        # Condición de ruptura alcista (LONG)
        vela_1_close = self.data.Close[-1]
        vela_1_volume = self.data.Volume[-1]
        vela_1_low = self.data.Low[-1]
        range_high = self.range_high[-1]

        if (vela_1_close > range_high) and (vela_1_volume > self.vol_avg[-1]):
            sl_long = vela_1_low  # SL en el Low de vela 1
            risk = abs(entry_price - sl_long)
            if risk <= 0 or entry_price <= sl_long:
                return

            risk_amount = capital * self.risk_per_trade
            size_long = risk_amount / risk
            size_long = max(1, round(size_long))
            tp_long = entry_price + (risk * self.rr_ratio)

            if tp_long > 0:
                self.buy(size=size_long, sl=sl_long, tp=tp_long)

        # Condición de ruptura bajista (SHORT)
        vela_1_high = self.data.High[-1]
        range_low = self.range_low[-1]

        if (vela_1_close < range_low) and (vela_1_volume > self.vol_avg[-1]):
            sl_short = vela_1_high  # SL en el High de vela 1
            risk = abs(sl_short - entry_price)
            if risk <= 0 or entry_price >= sl_short:
                return

            risk_amount = capital * self.risk_per_trade
            size_short = risk_amount / risk
            size_short = max(1, round(size_short))
            tp_short = entry_price - (risk * self.rr_ratio)

            if tp_short > 0:
                self.sell(size=size_short, sl=sl_short, tp=tp_short)

# Ejecutar el backtest
bt = Backtest(df_15m, BreakoutStrategy, cash=1000000, commission=.00075)
results = bt.run()
print(results)

# Graficar con resolución de 1 hora
bt.plot(resample="1h")