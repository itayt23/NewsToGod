from distutils.dep_util import newer_group
from importlib.metadata import SelectableGroups
from turtle import position
from types import new_class
import numpy as np
import pandas as pd
from pylab import mpl, plt
import yfinance as yf
from sequencing import SequenceMethod
from datetime import date,datetime,timedelta
from pathlib import Path
plt.style.use('seaborn')
mpl.rcParams['font.family'] = 'serif'

results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Strategy'
if not results_path.exists():
    results_path.mkdir(parents=True)

class MyBacktestBase(object):
    ''' Base class for event-based backtesting of trading strategies.

    Attributes
    ==========
    symbol: str
        TR RIC (financial instrument) to be used
    start: str
        start date for data selection
    end: str
        end date for data selection
    amount: float
        amount to be invested either once or per trade
    ftc: float
        fixed transaction costs per trade (buy or sell)
    ptc: float
        proportional transaction costs per trade (buy or sell)

    Methods
    =======
    get_data:
        retrieves and prepares the base data set
    plot_data:
        plots the closing price for the symbol
    get_date_price:
        returns the date and price for the given bar
    print_balance:
        prints out the current (cash) balance
    print_net_wealth:
        prints auf the current net wealth
    place_buy_order:
        places a buy order
    place_sell_order:
        places a sell order
    close_out:
        closes out a long or short position
    '''

    def __init__(self, start, end, amount, exposure = 0.25,
                 ftc=0.0, ptc=0.0, verbose=True):
        self.start = start
        self.end = end
        self.initial_amount = amount
        self.amount = amount
        self.cash = amount
        self.exposure = exposure
        self.ptc = ptc
        self.ftc = ftc
        self.trade_money_investing = exposure * amount
        self.position = 0
        self.trades = 0
        self.win_trades = 0
        self.verbose = verbose
        self.stoploss = 0
        self.entry_price = 0
        self.days_hold = 0
        self.holdings = {}
        self.today = None
        self.trade_log = pd.DataFrame(columns=['Date','Buy\Sell','Ticker','Position','Buy\Sell Price','Cash','Net Wealth','Total Trades','Portfolio Yield','Win Rate'])

    def plot_data(self, cols=None):
        ''' Plots the closing prices for symbol.
        '''
        if cols is None:
            cols = ['price']
        self.data['price'].plot(figsize=(10, 6), title=self.symbol)

    def get_date_price(self, bar):
        ''' Return date and price for bar.
        '''
        date = str(self.symbol_data_1d.index[bar])[:10]
        price = self.symbol_data_1d.Open.iloc[bar]
        return date, price

    def print_balance(self, entry_date):
        print(f'{entry_date} | current cash {self.cash:.2f}')

    def print_net_wealth(self, entry_date):
        net_wealth = self.get_new_wealth()
        print(f'{entry_date} | current net wealth(cash + holdings) {net_wealth:.2f}')

    def place_buy_order(self, symbol):
        new_row = {}
        entry_price = symbol[1]['Entry Price']
        entry_date =  symbol[1]['Entry Date']
        position = int(self.trade_money_investing / entry_price)
        self.cash -= (position * entry_price) + (position * self.ptc) + self.ftc
        self.holdings[symbol[0]] = {'Avg Price': entry_price, 'Entry Date': entry_date, 'Position':position}
        new_row['Ticker'] = symbol[0]
        new_row['Date'] = entry_date
        new_row['Buy\Sell'] = 'Buy'
        new_row['Position'] = position
        new_row['Buy\Sell Price'] = entry_price
        new_row['Cash'] = self.cash
        new_row['Net Wealth'] = self.get_new_wealth()
        self.trade_log = self.trade_log.append(new_row, ignore_index=True)
        self.trade_log.to_csv(results_path / f"seq_strategy.csv")
        if self.verbose:
            print(f'{entry_date} | buying {symbol[0]}, {position} units at {entry_price:.2f}')
            self.print_balance(entry_date)
            self.print_net_wealth(entry_date)

    def place_sell_order(self, symbol,daily_price):
        new_row = {}
        selling_price = daily_price
        position = self.holdings[symbol]['Position']
        self.cash += (position * selling_price) - (position * self.ptc) + self.ftc
        self.trades += 1
        if(self.holdings[symbol]['Avg Price'] < selling_price):
            self.win_trades += 1
        del self.holdings[symbol]
        new_row['Ticker'] = symbol
        new_row['Date'] = self.today
        new_row['Buy\Sell'] = 'Sell'
        new_row['Position'] = position
        new_row['Buy\Sell Price'] = selling_price
        new_row['Cash'] = self.cash
        new_row['Net Wealth'] = self.get_new_wealth()
        new_row['Total Trades'] = self.trades
        new_row['Portfolio Yield'] = (self.get_new_wealth() - self.initial_amount)/self.initial_amount*100
        try:
            new_row['Win Rate'] = self.win_trades/self.trades*100
        except:    
            new_row['Win Rate'] = 0
        self.trade_log = self.trade_log.append(new_row, ignore_index=True)
        self.trade_log.to_csv(results_path / f"seq_strategy.csv")
        if self.verbose:
            print(f'{self.today} | selling {symbol}, {position} units at {selling_price:.2f}')
            self.print_balance(self.today)
            self.print_net_wealth(self.today)

    def close_out(self):
        for symbol in self.holdings.items():
            data_daily = yf.download(symbol[0],start = self.today, end= (self.today +timedelta(days=3)),progress=False)
            daily_price = data_daily['Open'][0]
            self.place_sell_order(symbol[0],daily_price)
       


    def get_new_wealth(self):
        money_inside = 0
        for symbol in self.holdings.items():
            data_daily = yf.download(symbol[0],start = self.today, end= (self.today +timedelta(days=3)),progress=False)
            today_price = data_daily['Open'][0]
            position = symbol[1]['Position']
            money_inside += today_price*position
        return money_inside + self.cash

