import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta, UTC

# Parámetros generales
BATCH_SIZE = 1000  # Máximo de Bybit por request
MAX_RETRIES = 3
API_URL = "https://api.bybit.com/v5/market/kline"

def get_ohlcv(symbol: str, interval: str):
    """
    Descarga todos los datos OHLCV disponibles desde la API de Bybit.
    
    :param symbol: Par de trading (ejemplo: 'BTCUSDT')
    :param interval: Timeframe ('60' para 1 hora)
    :return: DataFrame con los datos OHLCV
    """
    end_time = datetime.now(UTC)
    start_time = end_time  # Empezamos desde el presente y retrocedemos
    earliest_time = datetime(2018, 1, 1, tzinfo=UTC)  # Fecha inicial aproximada

    all_data = []
    
    print(f"\n📡 Descargando datos de {symbol} en timeframe {interval}")
    print(f"🕒 Desde el inicio (~2021) hasta {end_time}")

    while start_time > earliest_time:
        start_ts = int((start_time - timedelta(days=7)).timestamp() * 1000)  # Descargamos 7 días por iteración
        end_ts = int(start_time.timestamp() * 1000)

        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "limit": BATCH_SIZE,
            "start": start_ts,
            "end": end_ts
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(API_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if 'result' in data and 'list' in data['result']:
                    chunk = data['result']['list']
                    if not chunk:
                        print("🚨 No se recibieron más datos, deteniendo descarga.")
                        start_time = earliest_time  # Salir del bucle
                        break

                    all_data.extend(chunk)
                    earliest_candle = datetime.fromtimestamp(int(chunk[-1][0])/1000, UTC)
                    print(f"✅ Descargadas {len(chunk)} velas ({earliest_candle} - {datetime.fromtimestamp(int(chunk[0][0])/1000, UTC)})")
                    time.sleep(0.2)  # Evitar rate limits
                    break
                else:
                    print(f"⚠️ Respuesta inesperada: {data}")
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Error en la solicitud (intento {attempt + 1}): {e}")
                time.sleep(1)

        start_time -= timedelta(days=7)  # Retrocedemos 7 días

    if not all_data:
        print("❌ No se obtuvieron datos.")
        return None

    # Crear DataFrame
    df = pd.DataFrame(all_data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', '_'])
    df = df.drop(columns=['_'])
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
    df = df.sort_values(by='timestamp', ascending=True)

    # Crear carpeta si no existe
    os.makedirs("data", exist_ok=True)

    # Cargar datos previos si existen
    file_path = f'data/{symbol}_{interval}_full.csv'
    if os.path.exists(file_path):
        df_prev = pd.read_csv(file_path)
        df_prev['timestamp'] = pd.to_datetime(df_prev['timestamp'])
        df = pd.concat([df_prev, df]).drop_duplicates(subset=['timestamp']).sort_values(by='timestamp')

    # Guardar en CSV
    df.to_csv(file_path, index=False)
    print(f"📁 Datos guardados en {file_path} ({len(df)} filas)")

    return df

if __name__ == "__main__":
    symbol = "XRPUSDT"
    
    # Obtener datos de 1H
    df_1h = get_ohlcv(symbol, "D")
    if df_1h is not None:
        print("📊 Datos de 1 hora guardados")