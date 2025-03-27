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

# Breakout_1d
    estrategia de scalping que consiste en:
    - marcar en h1 el maximo o minimo del dia anterior
    - ver en 5min si una vela rompe el maximo/minimo del dia anterior y cierra por encima/debajo
    - ejemplo con maximo: si una vela cierra por encima del maximo(llamemosle vela 1) esperamos a que la siguiente vela (llamemosle vela 2) tambien cierre por encima del maximo
    - una vez que vela 1 y vela 2 cierran por encima del maximo del dia anterior, nosotros abrimos un long en el cierre de vela 2,
    - con stop loss en maximo dia anterior? o open de vela 1?
    - arriesgando 1% y buscando un RR2:1
    - luego abria que ir optimizando pero esto seria lo basico de la estrategia