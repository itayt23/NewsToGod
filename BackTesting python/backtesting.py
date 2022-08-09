from importlib.metadata import entry_points
from msilib import sequence
from re import T
from sqlite3 import threadsafety
from tabnanny import verbose
from timeit import repeat
import traceback
from backtestingbase import *
from sequencing import SequenceMethod
import talib as ta
from pathlib import Path
from datetime import date,datetime,timedelta
from concurrent.futures import ThreadPoolExecutor

class Backtest(BacktestBase):

    def run_seq_strategy(self, SMA1, SMA2):
        global data_output
        ''' Backtesting a SMA-based strategy.

        Parameters
        ==========
        SMA1, SMA2: int
            shorter and longer term simple moving average (in days)
        '''
        msg = f'\n\nRunning SEQ strategy | SMA1={SMA1} & SMA2={SMA2}'
        msg += f'\nfixed costs {self.ftc} | '
        msg += f'proportional costs {self.ptc}'
        print(msg)
        print('=' * 55)
        new_row ={}
        avg_weekly_trend = self.sequence.get_avg_up_return('week')
        self.position = 0  # initial neutral position
        self.trades = 0  # no trades yet
        self.amount = self.initial_amount  # reset initial capital
        no_trades = True
        try:
            self.symbol_data_1d[f'SMA {SMA1}'] = ta.SMA(self.symbol_data_1d['Close'],timeperiod=13)
            self.symbol_data_1d[f'SMA {SMA2}'] = ta.SMA(self.symbol_data_1d[f'SMA {SMA1}'], timeperiod=5)
            self.symbol_data_1wk[f'SMA {SMA1}'] = ta.SMA(self.symbol_data_1wk['Close'],timeperiod=13)
            self.symbol_data_1wk[f'SMA {SMA2}'] = ta.SMA(self.symbol_data_1wk[f'SMA {SMA1}'], timeperiod=5)
            self.symbol_data_1mo[f'SMA {SMA1}'] = ta.SMA(self.symbol_data_1mo['Close'],timeperiod=13)
            self.symbol_data_1mo[f'SMA {SMA2}'] = ta.SMA(self.symbol_data_1mo[f'SMA {SMA1}'], timeperiod=5)
            self.symbol_data_1d = self.symbol_data_1d.dropna()
        except Exception:
            print(f'Problem with SMA datas, Details: \n {traceback.format_exc()}')
        trade_yield = 0
        for bar in range(SMA2, len(self.symbol_data_1d)):
            last_close = self.symbol_data_1d.Close.iloc[bar]
            seq_month = check_seq_by_date_monthly(self, self.symbol_data_1d.index[bar])
            index_week,seq_week = check_seq_by_date_weekly(self, self.symbol_data_1d.index[bar])
            index_day, seq_day = check_seq_by_date_daily(self, self.symbol_data_1d.index[bar])
            if self.position == 0:
                if(seq_month == 1 and seq_week == 1 and seq_day == 1): 
                    no_trades = False
                    self.place_buy_order(bar, amount=self.amount)
                    self.position = 1  # long position
                    self.stoploss = self.sequence.sequence_1wk.loc[index_week,'Entry Price']
                    self.entry_price = last_close
            elif self.position == 1:
                trade_yield = (last_close - self.entry_price)/self.entry_price*100

                if (seq_month == -1 and seq_week == -1 or trade_yield >= avg_weekly_trend*0.8):
                    if(trade_yield > 0):
                        self.win_trades += 1
                    self.place_sell_order(bar, units=self.units)
                    self.position = 0  # market neutral
        self.close_out(bar)
        new_row["Strategy Yield"] = ((self.amount - self.initial_amount) /self.initial_amount * 100)
        new_row["Symbol"] = self.symbol
        new_row["Period"] = self.start_test
        new_row["Hold Yield"] = self.hold_yield
        if no_trades:
            new_row["Trades"] = 0 
            new_row["Win Rate"] = 0
        else: 
            new_row["Trades"] = self.trades
            new_row["Win Rate"] = ((self.win_trades/self.trades)*100)
        data_output = data_output.append(new_row, ignore_index=True)

def check_seq_by_date_monthly(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] < date ):
            previous_row = row
            first = False
        else: break
    if(first): return 0
    return int(previous_row['Sequence'])

def check_seq_by_date_weekly(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] < date):
            previous_row = row
            first = False
        else: break
    if(first): return index, 0
    return index, int(previous_row['Sequence'])

def check_seq_by_date_daily(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] < date):
            previous_row = row
            first = False
        else: break
    if(first): return index,  0
    return index, int(previous_row['Sequence'])

def run_strategies():
    # xlc.run_seq_strategy_trades(13, 5)
    pass
        
data_output = pd.DataFrame(columns=['Symbol','Period','Strategy Yield','Hold Yield','Trades','Win Rate'])
data_output_trades = pd.DataFrame(columns=['Date','Buy\Sell','Price','Trade Yield','Days Hold'])


def get_best_fit(symbols,day,symbol_data_month,symbol_data_weekly):
    for symbol in symbols:
        data_monthly = symbol_data_month.loc[symbol].T
        data_weekly = symbol_data_weekly.loc[symbol].T
        print(data_monthly)
        test = pd.DataFrame(yf.download('IYZ', period='max',interval='1mo')).dropna()
        print(test)
        # symbol_data_month = pd.DataFrame(yf.download(symbol, period='max',interval='1mo',progress=False)).dropna()
        symbol_sequence_monthly = SequenceMethod(data_monthly,'monthly')
        print(symbol_sequence_monthly.get_seq_df())
        if(check_seq_by_date_monthly(symbol_sequence_monthly.get_seq_df(),day) != 1):
            continue
        # symbol_data_weekly = pd.DataFrame(yf.download(symbol, period='max',interval='1wk',progress=False)).dropna()
        symbol_sequence_weekly = SequenceMethod(data_weekly,'weekly')
        if(check_seq_by_date_weekly(symbol_sequence_weekly.get_seq_df(),day) != 1):
            continue
        try:
            data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
            data_weekly['SMA5'] = ta.SMA(data_weekly['SMA5'], timeperiod=5)
        except:
            continue
        print(data_weekly)
        return 1

        

if __name__ == '__main__':
    results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Strategy'
    if not results_path.exists():
        results_path.mkdir(parents=True)
    symbols = ['IYZ','XLY','XHB', 'PEJ','XLP','KXI','PBJ','XLE','XES','ICLN','XLF','KIE','KCE','KRE','XLV','PPH','XLI','IGF',
                'XLK','FDN','XLU','FIW','FAN','XLRE','XLB','PYZ','XME','HAP','MXI','IGE','MOO','WOOD','COPX','FXZ','URA','LIT']
    
    trading_days = pd.DataFrame(yf.download('qqq', period='max',interval='1d',progress=False)).dropna()
    trading_days = trading_days.index.to_list()
    for i in range(len(trading_days)):
        trading_days[i] = trading_days[i].date()
    trading_days = trading_days[920:]
    symbol_data_month = pd.DataFrame(yf.download(tickers=symbols, period='max',interval='1mo',progress=False,group_by = 'ticker',threads = True)).dropna()
    symbol_data_weekly = pd.DataFrame(yf.download(tickers=symbols, period='max',interval='1wk',progress=False,group_by = 'ticker',threads = True)).dropna()
    symbol_data_month = symbol_data_month.T
    symbol_data_weekly = symbol_data_weekly.T
    for day in trading_days:
        get_best_fit(symbols,day,symbol_data_month,symbol_data_weekly)
    # for day in trading_days:
    #     with ThreadPoolExecutor(max_workers=8) as executor:
    #         all_prints = executor.map(get_best_fit, symbols)
    #         executor.shutdown(wait=True)
    #     print(day)




        # get_best_fit(symbols,day)
    # xlc = BacktestLongOnly('XLC', '2000-1-1', '2022-08-05',1000000, ptc=0.005, verbose=True)
    # run_strategies()
    # data_output_trades.to_csv(results_path / f"XLC_trades.csv")

    