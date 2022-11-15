import pandas as pd
import yfinance as yf
from datetime import date,datetime,timedelta
from pathlib import Path


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

    def __init__(self, start, end, amount,symbols_daily_df,symbols_weekly_df,symbols_monthly_df, exposure = 0.25,
                 ftc=0.0, ptc=0.0, verbose=True):
        self.daily_df = symbols_daily_df
        self.weekly_df = symbols_weekly_df
        self.monthly = symbols_monthly_df
        self.start = start
        self.end = end
        self.initial_amount = amount
        self.amount = amount
        self.cash = amount
        self.exposure = exposure
        self.leverage_amount = 0.01 * self.initial_amount
        self.price_gap_precent = 0.001
        self.ptc = ptc
        self.ftc = ftc
        self.position_money_size = exposure * amount
        self.position_half_size = (exposure/2) * amount
        self.position = 0
        self.trades = 0
        self.total_gain = 0
        self.avg_gain = 0
        self.win_trades = 0
        self.verbose = verbose
        self.stoploss = 0
        self.entry_price = 0
        self.total_days_hold = 0
        benchmark_start = pd.DataFrame(yf.download(tickers='spy', start=start, end= start + timedelta(days=3),interval='1d',progress=False)).dropna()
        benchmark_end = pd.DataFrame(yf.download(tickers='spy', start=end, end= end + timedelta(days=3),interval='1d',progress=False)).dropna()
        self.benchmark_yield =  (benchmark_end.iloc[0]['Open'] -benchmark_start.iloc[0]['Open'])/ benchmark_start.iloc[0]['Open']*100
        self.holdings = {}
        self.today = None
        self.trade_log = pd.DataFrame(columns=['Date','Buy\Sell','Ticker','Position','Buy\Sell Price','Trade Return','Days Hold',
        'Cash','Net Wealth','Total Trades','Portfolio Yield','Hold Yield','Avg Gain','Avg Days Hold','Win Rate','Rules'])


    def print_balance(self, entry_date):
        print(f'{entry_date} | current cash {self.cash:.2f}')

    def print_net_wealth(self, entry_date,net_wealth):
        print(f'{entry_date} | current net wealth(cash + holdings) {net_wealth:.2f}')

    def place_buy_order(self, symbol, entry_date,entry_price,buy_rules,position_size = 1):
        new_row = {}
            
        entry_price = entry_price + (self.price_gap_precent*entry_price)
        position = int((self.position_money_size*position_size) / entry_price)
        position_cost = (position * entry_price) + (position * self.ptc) + self.ftc
        if(position_cost < self.leverage_amount) : 
            position = int(self.cash / entry_price)
        self.cash -= (position * entry_price) + (position * self.ptc) + self.ftc
        if(symbol in self.holdings):
            last_size = self.holdings[symbol]['Position']
            avg_price = ((self.holdings[symbol]['Avg Price'] * last_size) + (entry_price * position)) / (last_size+position)
            dates = [self.holdings[symbol]['Entry Date']]
            dates.append(entry_date)
            position_size = self.holdings[symbol]['Position Size'] + position_size
            self.holdings[symbol] = {'Avg Price': avg_price, 'Entry Date': dates, 'Position':last_size+position, 'Red Weeks': 0, 'Position Size': position_size}
        else: self.holdings[symbol] = {'Avg Price': entry_price, 'Entry Date': entry_date, 'Position':position, 'Red Weeks': 0, 'Position Size': position_size}
        net_wealth = self.get_new_wealth()
        new_row['Ticker'] = symbol
        new_row['Date'] = entry_date
        new_row['Buy\Sell'] = 'Buy'
        new_row['Position'] = position
        new_row['Buy\Sell Price'] = entry_price
        new_row['Cash'] = self.cash
        new_row['Net Wealth'] = net_wealth
        new_row['Rules'] = buy_rules
        self.trade_log = self.trade_log.append(new_row, ignore_index=True)
        self.trade_log.to_csv(results_path / f"seq_strategy_daily.csv")
        if self.verbose:
            print(f'{entry_date} | buying {symbol}, {position} units at {entry_price:.2f}')
            self.print_balance(entry_date)
            self.print_net_wealth(entry_date,net_wealth)

    def place_sell_order(self, symbol,selling_date,selling_price,sell_rules="",position_size=1):
        new_row = {}
        selling_price = selling_price - (self.price_gap_precent*selling_price)
        try: days_hold = (selling_date - self.holdings[symbol]['Entry Date']).days
        except: days_hold = (selling_date - self.holdings[symbol]['Entry Date'][0]).days
        self.total_days_hold += days_hold
        position = int(self.holdings[symbol]['Position']*position_size)
        self.holdings[symbol]['Position'] = self.holdings[symbol]['Position'] - position
        self.holdings[symbol]['Position Size'] = position_size
        self.cash += (position * selling_price) - (position * self.ptc) + self.ftc
        self.trades += 1
        if(self.holdings[symbol]['Avg Price'] < selling_price):
            self.win_trades += 1
        trade_return = (selling_price - self.holdings[symbol]['Avg Price'])/self.holdings[symbol]['Avg Price']*100
        new_row['Trade Return'] = trade_return
        self.total_gain += trade_return
        self.avg_gain = self.total_gain / self.trades
        new_row['Avg Gain'] = self.avg_gain
        if(self.holdings[symbol]['Position'] == 0): del self.holdings[symbol]
        net_wealth = self.get_new_wealth()
        self.position_money_size = self.exposure * net_wealth
        self.leverage_amount = 0.02 * net_wealth
        new_row['Days Hold'] = days_hold
        new_row['Avg Days Hold'] = self.total_days_hold / self.trades
        new_row['Ticker'] = symbol
        new_row['Date'] = self.today
        new_row['Buy\Sell'] = 'Sell'
        new_row['Position'] = position
        new_row['Buy\Sell Price'] = selling_price
        new_row['Cash'] = self.cash
        new_row['Net Wealth'] = net_wealth
        new_row['Total Trades'] = self.trades
        new_row['Portfolio Yield'] = (net_wealth - self.initial_amount)/self.initial_amount*100
        new_row['Rules'] = sell_rules
        try:
            new_row['Win Rate'] = self.win_trades/self.trades*100
        except:    
            new_row['Win Rate'] = 0
        self.trade_log = self.trade_log.append(new_row, ignore_index=True)
        self.trade_log.to_csv(results_path / f"seq_strategy_daily.csv")
        if self.verbose:
            print(f'{self.today} | selling {symbol}, {position} units at {selling_price:.2f}')
            self.print_balance(self.today)
            self.print_net_wealth(self.today,net_wealth)

    def close_out(self,day):
        symbol_to_sell =[]
        for symbol in self.holdings.items():
            symbol_to_sell.append(symbol[0])
        for symbol in symbol_to_sell:
            sell_price = self.daily_df[symbol[0]].loc[str(self.today),'Open']
            self.place_sell_order(symbol,day,sell_price)
        new_row = {}
        new_row['Hold Yield'] = self.benchmark_yield
        self.trade_log = self.trade_log.append(new_row, ignore_index=True)
        self.trade_log.to_csv(results_path / f"seq_strategy_daily.csv")



    def get_new_wealth(self):
        money_inside = 0
        for symbol in self.holdings.items():
            today_price =  self.daily_df[symbol[0]].loc[str(self.today),'Open']
            position = symbol[1]['Position']
            money_inside += today_price*position
        return money_inside + self.cash

