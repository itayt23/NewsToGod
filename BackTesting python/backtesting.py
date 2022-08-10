from ast import excepthandler
from importlib.metadata import entry_points
from msilib import sequence
from pickle import EMPTY_DICT
from re import T
from sqlite3 import threadsafety
from tabnanny import verbose
from timeit import repeat
import traceback
from mybacktestingbase import *
from sequencing import SequenceMethod
import talib as ta
from pathlib import Path
from datetime import date,datetime,timedelta
from concurrent.futures import ThreadPoolExecutor

class Backtest(MyBacktestBase):

    def run_seq_strategy(self):
        symbols = ['IYZ','XLY','XHB', 'PEJ','XLP','PBJ','XLE','XES','ICLN','XLF','KIE','KCE','KRE','XLV','PPH','XLI','IGF',
                'XLK','FDN','XLU','FIW','FAN','XLRE','XLB','PYZ','XME','HAP','MXI','IGE','MOO','WOOD','COPX','FXZ','URA','LIT']
    
        trading_days = pd.DataFrame(yf.download('qqq', period='max',interval='1d',progress=False)).dropna()
        trading_days = trading_days.index.to_list()
        for i in range(len(trading_days)):
            trading_days[i] = trading_days[i].date()
        trading_days = trading_days[4260:]
        symbol_data_month = pd.DataFrame(yf.download(tickers=symbols, period='max',interval='1mo',progress=False,group_by = 'ticker',threads = True)).dropna()
        symbol_data_weekly = pd.DataFrame(yf.download(tickers=symbols, period='max',interval='1wk',progress=False,group_by = 'ticker',threads = True)).dropna()
        symbol_data_month = symbol_data_month.T
        symbol_data_weekly = symbol_data_weekly.T
        symbols_winners = {}
        for day in trading_days:
            portfolio.check_portfolio()
            if(portfolio.cash >= portfolio.trade_money_investing):
                symbols_winners = get_best_fit(symbols,day,symbol_data_month,symbol_data_weekly)
                if(len(symbols_winners) != 0):
                    for symbol in symbols_winners.items():
                        portfolio.place_buy_order(symbol)

    def check_portfolio(self):
        pass
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
    return int(previous_row['Sequence'])

def check_seq_by_date_daily(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] < date):
            previous_row = row
            first = False
        else: break
    if(first): return index,  0
    return int(previous_row['Sequence'])

def run_strategies():
    # xlc.run_seq_strategy_trades(13, 5)
    pass
        
data_output = pd.DataFrame(columns=['Symbol','Period','Strategy Yield','Hold Yield','Trades','Win Rate'])
data_output_trades = pd.DataFrame(columns=['Date','Buy\Sell','Price','Trade Yield','Days Hold'])

def get_best_fit(symbols,day,symbol_data_month,symbol_data_weekly):
    symbols_winners = {}
    data_monthly = pd.DataFrame()
    data_weekly = pd.DataFrame()
    start_week = day - timedelta(days=day.weekday())
    for symbol in symbols:
        data_monthly = symbol_data_month.loc[symbol].T
        data_weekly = symbol_data_weekly.loc[symbol].T
        symbol_sequence_monthly = SequenceMethod(data_monthly,'monthly')
        print(day)
        if(check_seq_by_date_monthly(symbol_sequence_monthly.get_seq_df(),day) != 1):
            continue
        # symbol_data_weekly = pd.DataFrame(yf.download(symbol, period='max',interval='1wk',progress=False)).dropna()
        symbol_sequence_weekly = SequenceMethod(data_weekly,'weekly')
        if(check_seq_by_date_weekly(symbol_sequence_weekly.get_seq_df(),day) != 1):
            continue
        try:
            data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
            data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
        except Exception:
            print(traceback.print_exc())
            continue
        if(data_weekly.loc[str(start_week),'SMA13'] < data_weekly.loc[str(start_week),'SMA5']):
            continue
        try:
            data_daily = yf.download(symbol,start = day, end= (day +timedelta(days=1)))
            entry_price = data_daily['Open'][0]
            symbols_winners[symbol] = {'Entry Date': day,'Entry Price': entry_price}
        except:
            continue
    return symbols_winners

        

if __name__ == '__main__':
    results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Strategy'
    if not results_path.exists():
        results_path.mkdir(parents=True)
    portfolio = Backtest(amount=1000000,start='2016-01-01',end='2022-08-05',ptc=0.005)
    portfolio.run_seq_strategy()
            
    # for day in trading_days:
    #     with ThreadPoolExecutor(max_workers=8) as executor:
    #         all_prints = executor.map(get_best_fit, symbols)
    #         executor.shutdown(wait=True)
    #     print(day)




        # get_best_fit(symbols,day)
    # xlc = BacktestLongOnly('XLC', '2000-1-1', '2022-08-05',1000000, ptc=0.005, verbose=True)
    # run_strategies()
    # data_output_trades.to_csv(results_path / f"XLC_trades.csv")

    