from ast import excepthandler
from importlib.metadata import entry_points
from lib2to3.pygram import Symbols
from msilib import sequence
from pickle import EMPTY_DICT
from re import M, T
from sqlite3 import threadsafety
from tabnanny import verbose
from timeit import repeat
import traceback
from xmlrpc.server import SimpleXMLRPCRequestHandler
from mybacktestingbase import *
from sequencing import SequenceMethod
import talib as ta
from pathlib import Path
from datetime import date,datetime,timedelta
from concurrent.futures import ThreadPoolExecutor
import requests
import os
import calendar

class Backtest(MyBacktestBase):

    def run_seq_strategy(self):
        symbol = 'QQQ'
        sell_rank = 0
        buy_rank = 0
        symbol_data_month = pd.DataFrame(yf.download(tickers=symbol, period='max',interval='1mo',progress=False)).dropna()
        symbol_data_weekly = pd.DataFrame(yf.download(tickers=symbol, period='max',interval='1wk',progress=False)).dropna()
        self.hold_entry_price = symbol_data_weekly.iloc[0]['Open']
        trading_weeks = symbol_data_weekly.index.to_list()
        for i in range(len(trading_weeks)):
            trading_weeks[i] = trading_weeks[i].date()
        # trading_weeks = trading_weeks[100:]
        # trading_weeks.pop()
        for week in trading_weeks:
            self.today = week
            if(self.is_holding(symbol)):
                sell_rank = self.sell_rate(symbol_data_month,symbol_data_weekly,symbol,week)
                if(sell_rank >= 4):
                    data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=3)),progress=False)
                    daily_price = data_daily['Open'][0]
                    trade_yield = (daily_price - self.holdings[symbol]['Avg Price'])/self.holdings[symbol]['Avg Price']*100
                    # if(trade_yield >=4 or trade_yield < 0):
                    self.place_sell_order(symbol,daily_price)
            if(self.cash > self.leverage_amount): 
                buy_rank = self.buy_rate(symbol_data_month,symbol_data_weekly,symbol,week)
                if(buy_rank >= 4):
                    data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=3)),progress=False)
                    self.place_buy_order(symbol,data_daily)
            # for symbol in symbols:
            #     portfolio.check_sell(symbol_data_month,symbol_data_weekly,symbol,week)
            #     portfolio.check_buy(symbol_data_month,symbol_data_weekly,symbol,week)
            # portfolio.check_portfolio(symbols,week,symbol_data_month,symbol_data_weekly)
        self.close_out()
        update_hold_yield(self,symbol)
       

    def buy_rate(self,symbol_data_month,symbol_data_weekly,symbol,week):
        rank = 0
        seq_month, seq_weekly = get_sequence_month_week(symbol,symbol_data_month,symbol_data_weekly,week)
        avg_weekly_move = seq_weekly.get_avg_up_return()
        start_move_price = check_seq_price_by_date_weekly(seq_weekly.get_seq_df(),week)
        try:
            data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=3)),progress=False)
            daily_price = data_daily['Open'][0]
        except:
            daily_price = None
        if(daily_price != None and start_move_price != None): move_return = (daily_price - start_move_price)/start_move_price*100
        else: move_return = None
        data_weekly = symbol_data_weekly
        data_monthly = symbol_data_month
        data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
        data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
        data_monthly['SMA13'] = ta.SMA(data_monthly['Close'],timeperiod=13)
        data_monthly['SMA5'] = ta.SMA(data_monthly['SMA13'], timeperiod=5)
        data_monthly = data_monthly.dropna()
        data_weekly = data_weekly.dropna()
        first_monthly_date = data_monthly.index[0].date()
        first_weekly_date = data_weekly.index[0].date()
        month = week.replace(day=1)
        pre_week = week - timedelta(days=7*4)
        last_month = month - timedelta(days=1) 
        last_month = last_month.replace(day = 1)
        pre_month = week.replace(day =1)
        for i in range(3):
            pre_month = pre_month - timedelta(days=1)
            pre_month = pre_month.replace(day = 1)
        if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),week) == 1):
            rank += 1
        else : return rank
        if(check_seq_by_date_monthly(seq_month.get_seq_df(),week) == 1):
            rank += 2
        try:
            if(first_weekly_date <= week and data_weekly.loc[str(week),'SMA13'] > data_weekly.loc[str(week),'SMA5']):
                rank += 1
        except:
            rank += 0
        try:
            if(first_monthly_date <= last_month and data_monthly.loc[str(last_month),'SMA13'] > data_monthly.loc[str(last_month),'SMA5']):
                rank += 1
        except:
            rank += 0
        if(is_moving_away_weekly(data_weekly,week,pre_week)):
            rank += 1
        if(is_moving_away_monthly(data_monthly,last_month,pre_month)):
            rank += 1
        if(move_return != None and move_return <= avg_weekly_move/2):
            rank += 1
        # if(rank>=4):
        #     # print(f"AVG UP WEEKLY IS: {avg_weekly_move}")
        return rank

    def sell_rate(self,symbol_data_month,symbol_data_weekly,symbol,week):
        rank = 0
        seq_month, seq_weekly = get_sequence_month_week(symbol,symbol_data_month,symbol_data_weekly,week)
        avg_weekly_move = seq_weekly.get_avg_up_return()
        avg_weekly_down_move = seq_weekly.get_avg_down_return()
        start_move_price = check_seq_price_by_date_weekly(seq_weekly.get_seq_df(),week)
        try:
            data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=3)),progress=False)
            daily_price = data_daily['Open'][0]
        except:
            daily_price = None
        if(daily_price != None): trade_yield = (daily_price - self.holdings[symbol]['Avg Price'])/self.holdings[symbol]['Avg Price']*100
        else: trade_yield = None
        data_weekly = symbol_data_weekly
        data_monthly = symbol_data_month
        data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
        data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
        data_monthly['SMA13'] = ta.SMA(data_monthly['Close'],timeperiod=13)
        data_monthly['SMA5'] = ta.SMA(data_monthly['SMA13'], timeperiod=5)
        data_monthly = data_monthly.dropna()
        data_weekly = data_weekly.dropna()
        first_monthly_date = data_monthly.index[0].date()
        first_weekly_date = data_weekly.index[0].date()
        month = week.replace(day=1)
        pre_week = week - timedelta(days=7*4)
        last_month = month - timedelta(days=1) 
        last_month = last_month.replace(day = 1)
        pre_month = week.replace(day =1)
        for i in range(3):
            pre_month = pre_month - timedelta(days=1)
            pre_month = pre_month.replace(day = 1)
        if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),week) == -1):
            rank += 1
        else : return rank
        if(check_seq_by_date_monthly(seq_month.get_seq_df(),week) == -1):
            rank += 1
        try:
            if(first_weekly_date <= week and data_weekly.loc[str(week),'SMA13'] < data_weekly.loc[str(week),'SMA5']):
                rank += 1
        except:
            rank += 1
        try:
            if(first_monthly_date <= last_month and data_monthly.loc[str(last_month),'SMA13'] < data_monthly.loc[str(last_month),'SMA5']):
                rank += 1
        except:
            rank += 1
        if(trade_yield != None and trade_yield >= avg_weekly_move):
            rank += 1
        if(trade_yield != None and trade_yield >= avg_weekly_move*1.25):
            rank += 1
        if(trade_yield != None and trade_yield >= avg_weekly_move*1.5):
            rank += 1
        if(trade_yield != None and trade_yield >= avg_weekly_move*2):
            rank += 1
        # if(trade_yield != None and trade_yield <= avg_weekly_down_move*1.5):
        #     rank += 1
        # if(trade_yield != None and trade_yield <= avg_weekly_down_move*1.75):
        #     rank += 1
        # print(f"AVG DOWN WEEKLY IS: {avg_weekly_down_move}")
        return rank
            
    def check_buy(self,symbol_data_month,symbol_data_weekly,symbol,week):
        if(self.cash - self.trade_money_investing >= ((-1)*self.leverage_amount) and not self.is_holding(symbol)):
            seq_month, seq_weekly = get_seq_month_week(symbol,week,symbol_data_month,symbol_data_weekly)
            data_weekly = symbol_data_weekly.loc[symbol].T
            data_monthly = symbol_data_month.loc[symbol].T
            try:
                data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
                data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
                # data_monthly['SMA13'] = ta.SMA(data_monthly['Close'],timeperiod=13)
                # data_monthly['SMA5'] = ta.SMA(data_monthly['SMA13'], timeperiod=5)
                # # print(data_monthly.head(30))
                if(seq_month == 1 and seq_weekly == 1 and data_weekly.loc[str(week),'SMA13'] > data_weekly.loc[str(week),'SMA5']):
                    data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=3)),progress=False)
                    self.place_buy_order(symbol,data_daily)
            except Exception:
                print('No Sma DATA')

    def check_sell(self,symbol_data_month,symbol_data_weekly,symbol,week):
        if(self.is_holding(symbol)):
            data_weekly = symbol_data_weekly.loc[symbol].T
            data_monthly = symbol_data_month.loc[symbol].T
            data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
            data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
            seq_month, seq_weekly = get_seq_month_week(symbol,week,symbol_data_month,symbol_data_weekly)
            if(seq_weekly == -1  and data_weekly.loc[str(week),'SMA5'] > data_weekly.loc[str(week),'SMA13']):
                data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=3)),progress=False)
                daily_price = data_daily['Open'][0]
                trade_yield = (daily_price - self.holdings[symbol]['Avg Price'])/self.holdings[symbol]['Avg Price']*100
                if(trade_yield > 7 or trade_yield < 0 or seq_month == -1):
                    portfolio.place_sell_order(symbol,daily_price)
 
    def check_sell2(self,symbol_data_month,symbol_data_weekly,symbol,week):
        if(self.is_holding(symbol)):
            data_weekly = symbol_data_weekly.loc[symbol].T
            data_monthly = symbol_data_month.loc[symbol].T
            data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
            data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
            seq_month, seq_weekly = get_seq_month_week(symbol,week,symbol_data_month,symbol_data_weekly)
            if(seq_month == -1 and seq_weekly == -1):
                data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=3)),progress=False)
                daily_price = data_daily['Open'][0]
                portfolio.place_sell_order(symbol,daily_price)

    def is_holding(self,symbol):
        for ticker in self.holdings.items():
            if(ticker[0] == symbol): return True
        return False

    def check_portfolio(self,symbols,week,symbol_data_month,symbol_data_weekly):
        symbols_winners = {}
        data_monthly = pd.DataFrame()
        data_weekly = pd.DataFrame()
        # start_week = day - timedelta(days=day.weekday())
        print(week)
        for symbol in symbols:
            in_protfolio = False
            data_monthly = symbol_data_month.loc[symbol].T
            data_weekly = symbol_data_weekly.loc[symbol].T
            symbol_sequence_monthly = SequenceMethod(data_monthly,'monthly')
            seq_month = check_seq_by_date_monthly(symbol_sequence_monthly.get_seq_df(),week)
            if(seq_month != 1):
                if(seq_month == 0):
                    continue
                if(not self.is_holding(symbol)):
                    continue
                in_protfolio = True
            # symbol_data_weekly = pd.DataFrame(yf.download(symbol, period='max',interval='1wk',progress=False)).dropna()
            symbol_sequence_weekly = SequenceMethod(data_weekly,'weekly')
            data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=3)),progress=False)
            daily_price = data_daily['Open'][0]
            seq_weekly = check_seq_by_date_weekly(symbol_sequence_weekly.get_seq_df(),week)
            if(seq_weekly != 1):
                if(seq_weekly == 0):
                    continue
                if(in_protfolio):
                    self.place_sell_order(symbol,daily_price)
                continue
            try:
                data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
                data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
            except Exception:
                print(traceback.print_exc())
                continue
            if(data_weekly.loc[str(week),'SMA13'] < data_weekly.loc[str(week),'SMA5']):
                continue
            try:
                symbols_winners[symbol] = {'Entry Date': week,'Entry Price': daily_price}
            except:
                continue
        if(len(symbols_winners) != 0):
                for symbol in symbols_winners.items():
                    if(self.cash - portfolio.trade_money_investing >= (-20000) and not self.is_holding(symbol[0])):
                        self.place_buy_order(symbol)


def update_hold_yield(self,symbol):
    data_daily = yf.download(symbol,start = self.today, end= (self.today +timedelta(days=3)),progress=False)
    daily_price = data_daily['Open'][0]
    new_row = {}
    new_row['Hold Yield'] = (daily_price - self.hold_entry_price)/self.hold_entry_price*100
    self.trade_log = self.trade_log.append(new_row, ignore_index=True)
    self.trade_log.to_csv(results_path / f"seq_strategy.csv")

def is_moving_away_weekly(data_weekly,week,pre_week):
    try:
        if((data_weekly.loc[str(week),'SMA13'] - data_weekly.loc[str(week),'SMA5']) > (data_weekly.loc[str(week),'SMA13'] - data_weekly.loc[str(week),'SMA5'])):
            return True
    except:
        return False
    return False
def is_moving_away_monthly(data_monthly,last_month,pre_month):
    try:
        if((data_monthly.loc[str(last_month),'SMA13'] - data_monthly.loc[str(last_month),'SMA5']) > (data_monthly.loc[str(pre_month),'SMA13'] - data_monthly.loc[str(pre_month),'SMA5'])):
            return True
    except:
        return False
    return False

def get_sa_rank(symbol):
    try:
        url = "https://seeking-alpha.p.rapidapi.com/symbols/get-ratings"
        querystring = {"symbol":symbol}
        headers = {'x-rapidapi-host': "seeking-alpha.p.rapidapi.com",
                'x-rapidapi-key': os.getenv('sa_api_key')} 
        response = requests.request("GET", url, headers=headers, params=querystring)
        ranking = response.json()
    except Exception as e:
        print("Problem with SeekingAlpha WebSite: "+str(e))
    try:
        quant_rating = ranking['data'][0]['attributes']['ratings']['quantRating']
    except:
        quant_rating = 0
    return quant_rating

def get_seq_month_week(symbol,week,symbol_data_month,symbol_data_weekly):
    data_monthly = symbol_data_month
    data_weekly = symbol_data_weekly
    symbol_sequence_monthly = SequenceMethod(data_monthly,'monthly')
    seq_month = check_seq_by_date_monthly(symbol_sequence_monthly.get_seq_df(),week)
    symbol_sequence_weekly = SequenceMethod(data_weekly,'weekly')
    seq_weekly = check_seq_by_date_weekly(symbol_sequence_weekly.get_seq_df(),week)
    return seq_month, seq_weekly

def get_sequence_month_week(symbol,symbol_data_month,symbol_data_weekly,week):
    data_monthly = symbol_data_month
    data_weekly = symbol_data_weekly
    symbol_sequence_monthly = SequenceMethod(data_monthly,'monthly',week)
    symbol_sequence_weekly = SequenceMethod(data_weekly,'weekly',week)
    return symbol_sequence_monthly, symbol_sequence_weekly

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
    if(first): return 0
    return int(previous_row['Sequence'])

def check_seq_price_by_date_monthly(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] < date ):
            previous_row = row
            first = False
        else: break
    if(first): return 0
    return (previous_row['Entry Price'])

def check_seq_price_by_date_weekly(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] < date):
            previous_row = row
            first = False
        else: break
    if(first): return None
    return (previous_row['Entry Price'])

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

if __name__ == '__main__':
    results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Strategy'
    if not results_path.exists():
        results_path.mkdir(parents=True)
    portfolio = Backtest(amount=1000000,start='2016-01-01',end='2022-08-05',ptc=0.005,exposure=1)
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

    