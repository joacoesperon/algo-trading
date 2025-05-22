# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# Multiple Time Frames
# ============
#
# Best trading strategies that rely on technical analysis might take into account price action on multiple time frames.
# This tutorial will show how to do that with _backtesting.py_, offloading most of the work to
# [pandas resampling](http://pandas.pydata.org/pandas-docs/stable/timeseries.html#resampling).
# It is assumed you're already familiar with
# [basic framework usage](https://kernc.github.io/backtesting.py/doc/examples/Quick%20Start%20User%20Guide.html).
#
# We will put to the test this long-only, supposed
# [400%-a-year trading strategy](https://web.archive.org/web/20180515044054/http://jbmarwood.com/stock-trading-strategy-300/),
# which uses daily and weekly
# [relative strength index](https://en.wikipedia.org/wiki/Relative_strength_index)
# (RSI) values and moving averages (MA).
#
# In practice, one should use functions from an indicator library, such as
# [TA-Lib](https://github.com/mrjbq7/ta-lib) or
# [Tulipy](https://tulipindicators.org),
# but among us, let's introduce the two indicators we'll be using.

# +
import pandas as pd


def SMA(array, n):
    """Simple moving average"""
    return pd.Series(array).rolling(n).mean()


def RSI(array, n):
    """Relative strength index"""
    # Approximate; good enough
    gain = pd.Series(array).diff()
    loss = gain.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    rs = gain.ewm(n).mean() / loss.abs().ewm(n).mean()
    return 100 - 100 / (1 + rs)


# -

# The strategy roughly goes like this:
#
# Buy a position when:
# * weekly RSI(30) $\geq$ daily RSI(30) $>$ 70
# * Close $>$ MA(10) $>$ MA(20) $>$ MA(50) $>$ MA(100)
#
# Close the position when:
# * Daily close is more than 2% _below_ MA(10)
# * 8% fixed stop loss is hit
#
# We need to provide bars data in the _lowest time frame_ (i.e. daily) and resample it to any higher time frame (i.e. weekly) that our strategy requires.

# +
from backtesting import Strategy, Backtest
from backtesting.lib import resample_apply


class System(Strategy):
    d_rsi = 30  # Daily RSI lookback periods
    w_rsi = 30  # Weekly
    level = 70
    
    def init(self):
        # Compute moving averages the strategy demands
        self.ma10 = self.I(SMA, self.data.Close, 10)
        self.ma20 = self.I(SMA, self.data.Close, 20)
        self.ma50 = self.I(SMA, self.data.Close, 50)
        self.ma100 = self.I(SMA, self.data.Close, 100)
        
        # Compute daily RSI(30)
        self.daily_rsi = self.I(RSI, self.data.Close, self.d_rsi)
        
        # To construct weekly RSI, we can use `resample_apply()`
        # helper function from the library
        self.weekly_rsi = resample_apply(
            'W-FRI', RSI, self.data.Close, self.w_rsi)
        
        
    def next(self):
        price = self.data.Close[-1]
        
        # If we don't already have a position, and
        # if all conditions are satisfied, enter long.
        if (not self.position and
            self.daily_rsi[-1] > self.level and
            self.weekly_rsi[-1] > self.level and
            self.weekly_rsi[-1] > self.daily_rsi[-1] and
            self.ma10[-1] > self.ma20[-1] > self.ma50[-1] > self.ma100[-1] and
            price > self.ma10[-1]):
            
            # Buy at market price on next open, but do
            # set 8% fixed stop loss.
            self.buy(sl=.92 * price)
        
        # If the price closes 2% or more below 10-day MA
        # close the position, if any.
        elif price < .98 * self.ma10[-1]:
            self.position.close()
# -

# Let's see how our strategy fares replayed on nine years of Google stock data.

# +
from backtesting.test import GOOG

backtest = Backtest(GOOG, System, commission=.002)
backtest.run()
# -

# Meager four trades in the span of nine years and with zero return? How about if we optimize the parameters a bit?

# +
# %%time

backtest.optimize(d_rsi=range(10, 35, 5),
                  w_rsi=range(10, 35, 5),
                  level=range(30, 80, 10))
# -

backtest.plot()

# Better. While the strategy doesn't perform as well as simple buy & hold, it does so with significantly lower exposure (time in market).
#
# In conclusion, to test strategies on multiple time frames, you need to pass in OHLC data in the lowest time frame, then resample it to higher time frames, apply the indicators, then resample back to the lower time frame, filling in the in-betweens.
# Which is what the function [`backtesting.lib.resample_apply()`](https://kernc.github.io/backtesting.py/doc/backtesting/lib.html#backtesting.lib.resample_apply) does for you.

# Learn more by exploring further
# [examples](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#tutorials)
# or find more framework options in the
# [full API reference](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#header-submodules).
--------------------------
# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# Parameter Heatmap
# ==========
#
# This tutorial will show how to optimize strategies with multiple parameters and how to examine and reason about optimization results.
# It is assumed you're already familiar with
# [basic _backtesting.py_ usage](https://kernc.github.io/backtesting.py/doc/examples/Quick%20Start%20User%20Guide.html).
#
# First, let's again import our helper moving average function.
# In practice, one should use functions from an indicator library, such as
# [TA-Lib](https://github.com/mrjbq7/ta-lib) or
# [Tulipy](https://tulipindicators.org).

from backtesting.test import SMA

# Our strategy will be a similar moving average cross-over strategy to the one in
# [Quick Start User Guide](https://kernc.github.io/backtesting.py/doc/examples/Quick%20Start%20User%20Guide.html),
# but we will use four moving averages in total:
# two moving averages whose relationship determines a general trend
# (we only trade long when the shorter MA is above the longer one, and vice versa),
# and two moving averages whose cross-over with daily _close_ prices determine the signal to enter or exit the position.

# +
from backtesting import Strategy
from backtesting.lib import crossover


class Sma4Cross(Strategy):
    n1 = 50
    n2 = 100
    n_enter = 20
    n_exit = 10
    
    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)
        self.sma_enter = self.I(SMA, self.data.Close, self.n_enter)
        self.sma_exit = self.I(SMA, self.data.Close, self.n_exit)
        
    def next(self):
        
        if not self.position:
            
            # On upwards trend, if price closes above
            # "entry" MA, go long
            
            # Here, even though the operands are arrays, this
            # works by implicitly comparing the two last values
            if self.sma1 > self.sma2:
                if crossover(self.data.Close, self.sma_enter):
                    self.buy()
                    
            # On downwards trend, if price closes below
            # "entry" MA, go short
            
            else:
                if crossover(self.sma_enter, self.data.Close):
                    self.sell()
        
        # But if we already hold a position and the price
        # closes back below (above) "exit" MA, close the position
        
        else:
            if (self.position.is_long and
                crossover(self.sma_exit, self.data.Close)
                or
                self.position.is_short and
                crossover(self.data.Close, self.sma_exit)):
                
                self.position.close()


# -

# It's not a robust strategy, but we can optimize it.
#
# [Grid search](https://en.wikipedia.org/wiki/Hyperparameter_optimization#Grid_search)
# is an exhaustive search through a set of specified sets of values of hyperparameters. One evaluates the performance for each set of parameters and finally selects the combination that performs best.
#
# Let's optimize our strategy on Google stock data using _randomized_ grid search over the parameter space, evaluating at most (approximately) 200 randomly chosen combinations:

# +
# %%time 

from backtesting import Backtest
from backtesting.test import GOOG


backtest = Backtest(GOOG, Sma4Cross, commission=.002)

stats, heatmap = backtest.optimize(
    n1=range(10, 110, 10),
    n2=range(20, 210, 20),
    n_enter=range(15, 35, 5),
    n_exit=range(10, 25, 5),
    constraint=lambda p: p.n_exit < p.n_enter < p.n1 < p.n2,
    maximize='Equity Final [$]',
    max_tries=200,
    random_state=0,
    return_heatmap=True)
# -

# Notice `return_heatmap=True` parameter passed to
# [`Backtest.optimize()`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest.optimize).
# It makes the function return a heatmap series along with the usual stats of the best run.
# `heatmap` is a pandas Series indexed with a MultiIndex, a cartesian product of all permissible (tried) parameter values.
# The series values are from the `maximize=` argument we provided.

heatmap

# This heatmap contains the results of all the runs,
# making it very easy to obtain parameter combinations for e.g. three best runs:

heatmap.sort_values().iloc[-3:]

# But we use vision to make judgements on larger data sets much faster.
# Let's plot the whole heatmap by projecting it on two chosen dimensions.
# Say we're mostly interested in how parameters `n1` and `n2`, on average, affect the outcome.

hm = heatmap.groupby(['n1', 'n2']).mean().unstack()
hm = hm[::-1]
hm

# Let's plot this table as a heatmap:

# +
# %matplotlib inline

import matplotlib.pyplot as plt

fig, ax = plt.subplots()
im = ax.imshow(hm, cmap='viridis')
_ = (
    ax.set_xticks(range(len(hm.columns)), labels=hm.columns),
    ax.set_yticks(range(len(hm)), labels=hm.index),
    ax.set_xlabel('n2'),
    ax.set_ylabel('n1'),
    ax.figure.colorbar(im, ax=ax),
)
# -

# We see that, on average, we obtain the highest result using trend-determining parameters `n1=30` and `n2=100` or `n1=70` and `n2=80`,
# and it's not like other nearby combinations work similarly well — for our particular strategy, these combinations really stand out.
#
# Since our strategy contains several parameters, we might be interested in other relationships between their values.
# We can use
# [`backtesting.lib.plot_heatmaps()`](https://kernc.github.io/backtesting.py/doc/backtesting/lib.html#backtesting.lib.plot_heatmaps)
# function to plot interactive heatmaps of all parameter combinations simultaneously.
#
# <a id=plot-heatmaps></a>

# +
from backtesting.lib import plot_heatmaps


plot_heatmaps(heatmap, agg='mean')
# -

# ## Model-based optimization
#
# Above, we used _randomized grid search_ optimization method. Any kind of grid search, however, might be computationally expensive for large data sets. In the follwing example, we will use
# [_SAMBO Optimization_](https://sambo-optimization.github.io)
# package to guide our optimization better informed using forests of decision trees.
# The hyperparameter model is sequentially improved by evaluating the expensive function (the backtest) at the next best point, thereby hopefully converging to a set of optimal parameters with **as few evaluations as possible**.
#
# So, with `method="sambo"`:

# +
# %%capture

# ! pip install sambo  # This is a run-time dependency

# +
# #%%time

stats, heatmap, optimize_result = backtest.optimize(
    n1=[10, 100],      # Note: For method="sambo", we
    n2=[20, 200],      # only need interval end-points
    n_enter=[10, 40],
    n_exit=[10, 30],
    constraint=lambda p: p.n_exit < p.n_enter < p.n1 < p.n2,
    maximize='Equity Final [$]',
    method='sambo',
    max_tries=40,
    random_state=0,
    return_heatmap=True,
    return_optimization=True)
# -

heatmap.sort_values().iloc[-3:]

# Notice how the optimization runs somewhat slower even though `max_tries=` is lower. This is due to the sequential nature of the algorithm and should actually perform quite comparably even in cases of _much larger parameter spaces_ where grid search would effectively blow up, likely reaching a better optimum than a simple randomized search would.
# A note of warning, again, to take steps to avoid
# [overfitting](https://en.wikipedia.org/wiki/Overfitting)
# insofar as possible.
#
# Understanding the impact of each parameter on the computed objective function is easy in two dimensions, but as the number of dimensions grows, partial dependency plots are increasingly useful.
# [Plotting tools from _SAMBO_](https://sambo-optimization.github.io/doc/sambo/plot.html)
# take care of the more mundane things needed to make good and informative plots of the parameter space.
#
# Note, because SAMBO internally only does _minimization_, the values in `optimize_result` are negated (less is better).

# +
from sambo.plot import plot_objective

names = ['n1', 'n2', 'n_enter', 'n_exit']
_ = plot_objective(optimize_result, names=names, estimator='et')

# +
from sambo.plot import plot_evaluations

_ = plot_evaluations(optimize_result, names=names)
# -

# Learn more by exploring further
# [examples](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#tutorials)
# or find more framework options in the
# [full API reference](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#header-submodules).
---------------------
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# _Backtesting.py_ Quick Start User Guide
# =======================
#
# This tutorial shows some of the features of *backtesting.py*, a Python framework for [backtesting](https://www.investopedia.com/terms/b/backtesting.asp) trading strategies.
#
# _Backtesting.py_ is a small and lightweight, blazing fast backtesting framework that uses state-of-the-art Python structures and procedures (Python 3.6+, Pandas, NumPy, Bokeh). It has a very small and simple API that is easy to remember and quickly shape towards meaningful results. The library _doesn't_ really support stock picking or trading strategies that rely on arbitrage or multi-asset portfolio rebalancing; instead, it works with an individual tradeable asset at a time and is best suited for optimizing position entrance and exit signal strategies, decisions upon values of technical indicators, and it's also a versatile interactive trade visualization and statistics tool.
#
#
# ## Data
#
# _You bring your own data._ Backtesting ingests _all kinds of 
# [OHLC](https://en.wikipedia.org/wiki/Open-high-low-close_chart)
# data_ (stocks, forex, futures, crypto, ...) as a
# [pandas.DataFrame](https://pandas.pydata.org/pandas-docs/stable/10min.html)
# with columns `'Open'`, `'High'`, `'Low'`, `'Close'` and (optionally) `'Volume'`.
# Such data is widely obtainable, e.g. with packages:
# * [pandas-datareader](https://pandas-datareader.readthedocs.io/en/latest/),
# * [Quandl](https://www.quandl.com/tools/python),
# * [findatapy](https://github.com/cuemacro/findatapy),
# * [yFinance](https://github.com/ranaroussi/yfinance),
# * [investpy](https://investpy.readthedocs.io/),
#   etc.
#
# Besides these columns, **your data frames can have additional columns which are accessible in your strategies in a similar manner**.
#
# DataFrame should ideally be indexed with a _datetime index_ (convert it with [`pd.to_datetime()`](https://pandas.pydata.org/pandas-docs/stable/generated/pandas.to_datetime.html));
# otherwise a simple range index will do.

# +
# Example OHLC daily data for Google Inc.
from backtesting.test import GOOG

GOOG.tail()
# -

# ## Strategy
#
# Let's create our first strategy to backtest on these Google data, a simple [moving average (MA) cross-over strategy](https://en.wikipedia.org/wiki/Moving_average_crossover).
#
# _Backtesting.py_ doesn't ship its own set of _technical analysis indicators_. Users favoring TA should probably refer to functions from proven indicator libraries, such as
# [TA-Lib](https://github.com/TA-Lib/ta-lib-python) or
# [Tulipy](https://tulipindicators.org),
# but for this example, we can define a simple helper moving average function ourselves:

# +
import pandas as pd


def SMA(values, n):
    """
    Return simple moving average of `values`, at
    each step taking into account `n` previous values.
    """
    return pd.Series(values).rolling(n).mean()


# -

# A new strategy needs to extend 
# [`Strategy`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy)
# class and override its two abstract methods:
# [`init()`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy.init) and
# [`next()`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy.next).
#
# Method `init()` is invoked before the strategy is run. Within it, one ideally precomputes in efficient, vectorized manner whatever indicators and signals the strategy depends on.
#
# Method `next()` is then iteratively called by the
# [`Backtest`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest)
# instance, once for each data point (data frame row), simulating the incremental availability of each new full candlestick bar.
#
# Note, _backtesting.py_ cannot make decisions / trades _within_ candlesticks — any new orders are executed on the next candle's _open_ (or the current candle's _close_ if
# [`trade_on_close=True`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest.__init__)).
# If you find yourself wishing to trade within candlesticks (e.g. daytrading), you instead need to begin with more fine-grained (e.g. hourly) data.

# +
from backtesting import Strategy
from backtesting.lib import crossover


class SmaCross(Strategy):
    # Define the two MA lags as *class variables*
    # for later optimization
    n1 = 10
    n2 = 20
    
    def init(self):
        # Precompute the two moving averages
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)
    
    def next(self):
        # If sma1 crosses above sma2, close any existing
        # short trades, and buy the asset
        if crossover(self.sma1, self.sma2):
            self.position.close()
            self.buy()

        # Else, if sma1 crosses below sma2, close any existing
        # long trades, and sell the asset
        elif crossover(self.sma2, self.sma1):
            self.position.close()
            self.sell()


# -

# In `init()` as well as in `next()`, the data the strategy is simulated on is available as an instance variable
# [`self.data`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy.data).
#
# In `init()`, we declare and **compute indicators indirectly by wrapping them in 
# [`self.I()`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy.I)**.
# The wrapper is passed a function (our `SMA` function) along with any arguments to call it with (our _close_ values and the MA lag). Indicators wrapped in this way will be automatically plotted, and their legend strings will be intelligently inferred.
#
# In `next()`, we simply check if the faster moving average just crossed over the slower one. If it did and upwards, we close the possible short position and go long; if it did and downwards, we close the open long position and go short. Note, we don't adjust order size, so _Backtesting.py_ assumes _maximal possible position_. We use
# [`backtesting.lib.crossover()`](https://kernc.github.io/backtesting.py/doc/backtesting/lib.html#backtesting.lib.crossover)
# function instead of writing more obscure and confusing conditions, such as:

# + magic_args="echo" language="script"
#
#     def next(self):
#         if (self.sma1[-2] < self.sma2[-2] and
#                 self.sma1[-1] > self.sma2[-1]):
#             self.position.close()
#             self.buy()
#
#         elif (self.sma1[-2] > self.sma2[-2] and    # Ugh!
#               self.sma1[-1] < self.sma2[-1]):
#             self.position.close()
#             self.sell()
# -

# In `init()`, the whole series of points was available, whereas **in `next()`, the length of `self.data` and all declared indicators is adjusted** on each `next()` call so that `array[-1]` (e.g. `self.data.Close[-1]` or `self.sma1[-1]`) always contains the most recent value, `array[-2]` the previous value, etc. (ordinary Python indexing of ascending-sorted 1D arrays).
#
# **Note**: `self.data` and any indicators wrapped with `self.I` (e.g. `self.sma1`) are NumPy arrays for performance reasons. If you prefer pandas Series or DataFrame objects, use `Strategy.data.<column>.s` or `Strategy.data.df` accessors respectively. You could also construct the series manually, e.g. `pd.Series(self.data.Close, index=self.data.index)`.
#
# We might avoid `self.position.close()` calls if we primed the
# [`Backtest`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest)
# instance with `Backtest(..., exclusive_orders=True)`.

# ## Backtesting
#
# Let's see how our strategy performs on historical Google data. The
# [`Backtest`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest)
# instance is initialized with OHLC data and a strategy _class_ (see API reference for additional options), and we begin with 10,000 units of cash and set broker's commission to realistic 0.2%.

# +
from backtesting import Backtest

bt = Backtest(GOOG, SmaCross, cash=10_000, commission=.002)
stats = bt.run()
stats
# -

# [`Backtest.run()`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest.run)
# method returns a pandas Series of simulation results and statistics associated with our strategy. We see that this simple strategy makes almost 600% return in the period of 9 years, with maximum drawdown 33%, and with longest drawdown period spanning almost two years ...
#
# [`Backtest.plot()`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest.plot)
# method provides the same insights in a more visual form.

bt.plot()

# ## Optimization
#
# We hard-coded the two lag parameters (`n1` and `n2`) into our strategy above. However, the strategy may work better with 15–30 or some other cross-over. **We declared the parameters as optimizable by making them [class variables](https://docs.python.org/3/tutorial/classes.html#class-and-instance-variables)**.
#
# We optimize the two parameters by calling
# [`Backtest.optimize()`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest.optimize)
# method with each parameter a keyword argument pointing to its pool of possible values to test. Parameter `n1` is tested for values in range between 5 and 30 and parameter `n2` for values between 10 and 70, respectively. Some combinations of values of the two parameters are invalid, i.e. `n1` should not be _larger than_ or equal to `n2`. We limit admissible parameter combinations with an _ad hoc_ constraint function, which takes in the parameters and returns `True` (i.e. admissible) whenever `n1` is less than `n2`. Additionally, we search for such parameter combination that maximizes return over the observed period. We could instead choose to optimize any other key from the returned `stats` series.

# +
# %%time

stats = bt.optimize(n1=range(5, 30, 5),
                    n2=range(10, 70, 5),
                    maximize='Equity Final [$]',
                    constraint=lambda param: param.n1 < param.n2)
stats
# -

# We can look into `stats['_strategy']` to access the Strategy _instance_ and its optimal parameter values (10 and 15).

stats._strategy

bt.plot(plot_volume=False, plot_pl=False)

# Strategy optimization managed to up its initial performance _on in-sample data_ by almost 50% and even beat simple
# [buy & hold](https://en.wikipedia.org/wiki/Buy_and_hold).
# In real life optimization, however, do **take steps to avoid
# [overfitting](https://en.wikipedia.org/wiki/Overfitting)**.

# ## Trade data
#
# In addition to backtest statistics returned by
# [`Backtest.run()`](https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Backtest.run)
# shown above, you can look into _individual trade returns_ and the changing _equity curve_ and _drawdown_ by inspecting the last few, internal keys in the result series.

stats.tail()

# The columns should be self-explanatory.

stats['_equity_curve']  # Contains equity/drawdown curves. DrawdownDuration is only defined at ends of DD periods.

stats['_trades']  # Contains individual trade data

# Learn more by exploring further
# [examples](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#tutorials)
# or find more framework options in the
# [full API reference](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#header-submodules).
--------------------------
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.5.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# Library of Composable Base Strategies
# ======================
#
# This tutorial will show how to reuse composable base trading strategies that are part of _backtesting.py_ software distribution.
# It is, henceforth, assumed you're already familiar with
# [basic package usage](https://kernc.github.io/backtesting.py/doc/examples/Quick%20Start%20User%20Guide.html).
#
# We'll extend the same moving average cross-over strategy as in
# [Quick Start User Guide](https://kernc.github.io/backtesting.py/doc/examples/Quick%20Start%20User%20Guide.html),
# but we'll rewrite it as a vectorized signal strategy and add trailing stop-loss.
#
# Again, we'll use our helper moving average function.

from backtesting.test import SMA

# Part of this software distribution is
# [`backtesting.lib`](https://kernc.github.io/backtesting.py/doc/backtesting/lib.html)
# module that contains various reusable utilities for strategy development.
# Some of those utilities are composable base strategies we can extend and build upon.
#
# We import and extend two of those strategies here:
# * [`SignalStrategy`](https://kernc.github.io/backtesting.py/doc/backtesting/lib.html#backtesting.lib.SignalStrategy)
#   which decides upon a single signal vector whether to buy into a position, akin to
#   [vectorized backtesting](https://www.google.com/search?q=vectorized+backtesting)
#   engines, and
# * [`TrailingStrategy`](https://kernc.github.io/backtesting.py/doc/backtesting/lib.html#backtesting.lib.TrailingStrategy)
#   which automatically trails the current price with a stop-loss order some multiple of
#   [average true range](https://en.wikipedia.org/wiki/Average_true_range)
#   (ATR) away.

# +
import pandas as pd
from backtesting.lib import SignalStrategy, TrailingStrategy


class SmaCross(SignalStrategy,
               TrailingStrategy):
    n1 = 10
    n2 = 25
    
    def init(self):
        # In init() and in next() it is important to call the
        # super method to properly initialize the parent classes
        super().init()
        
        # Precompute the two moving averages
        sma1 = self.I(SMA, self.data.Close, self.n1)
        sma2 = self.I(SMA, self.data.Close, self.n2)
        
        # Where sma1 crosses sma2 upwards. Diff gives us [-1,0, *1*]
        signal = (pd.Series(sma1) > sma2).astype(int).diff().fillna(0)
        signal = signal.replace(-1, 0)  # Upwards/long only
        
        # Use 95% of available liquidity (at the time) on each order.
        # (Leaving a value of 1. would instead buy a single share.)
        entry_size = signal * .95
                
        # Set order entry sizes using the method provided by 
        # `SignalStrategy`. See the docs.
        self.set_signal(entry_size=entry_size)
        
        # Set trailing stop-loss to 2x ATR using
        # the method provided by `TrailingStrategy`
        self.set_trailing_sl(2)


# -

# Note, since the strategies in `lib` may require their own intialization and next-tick logic, be sure to **always call `super().init()` and `super().next()` in your overridden methods**.
#
# Let's see how the example strategy fares on historical Google data.

# +
from backtesting import Backtest
from backtesting.test import GOOG

bt = Backtest(GOOG, SmaCross, commission=.002)

bt.run()
bt.plot()
# -

# Notice how managing risk with a trailing stop-loss secures our gains and limits our losses.
#
# For other strategies of the sort, and other reusable utilities in general, see
# [**_backtesting.lib_ module reference**](https://kernc.github.io/backtesting.py/doc/backtesting/lib.html).

# Learn more by exploring further
# [examples](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#tutorials)
# or find more framework options in the
# [full API reference](https://kernc.github.io/backtesting.py/doc/backtesting/index.html#header-submodules).
