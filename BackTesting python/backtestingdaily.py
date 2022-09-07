import traceback
from mybacktestingbase import *
from sequencing import SequenceMethod
import talib as ta
from pathlib import Path
from datetime import date,datetime,timedelta
import requests
import os
import calendar


SELL_RANK = 5     ##### sell 4 and buy 5 -------> 180%, not so good
BUY_RANK = 4

# get start of week -> start_week = date - timedelta(days=date.weekday())
#Add counter of consective red weeks for sell rate
#ADd 0.75 from weekly move +1
#dont buy week after week
# add IUSV ETF? and xlu
#stochastin low rank + 1 in buy rate?
#maybe add option to not sell 1 week apart
#add opposite new daily sell term
class Backtest(MyBacktestBase):

    def run_seq_strategy(self):
        symbols = ['QQQ','XLI','XLE','XLF','XLP','XLV','SOXX','XLU']#HACK is soxx bad?
        symbols_sell_ratings = {}
        symbols_buy_ratings = {}
        symbol_data_weekly = pd.DataFrame(yf.download(tickers='HACK', period='max',interval='1wk',progress=False)).dropna()
        trading_weeks = symbol_data_weekly.index.to_list()
        for i in range(len(trading_weeks)):
            trading_weeks[i] = trading_weeks[i].date()
        trading_weeks = trading_weeks[112:]
        for week in trading_weeks:
            self.today = week
            sold_symbols = []
            symbols_sell_ratings = get_sell_rating(self,week)
            if(symbols_sell_ratings != None):
                for symbol in symbols_sell_ratings.items():
                    if(symbol[1]['rank'] >= SELL_RANK):
                        try:
                            day_str = str(symbol[1]['day'].date())
                        except:
                            day_str = str(symbol[1]['day'])
                        day = datetime.strptime(day_str,'%Y-%m-%d')
                        sold_symbols.append(symbol[0])
                        data_daily = yf.download(symbol[0],start=day_str, end=(day +timedelta(days=4)).strftime('%Y-%m-%d'),interval='1d',progress=False)
                        if(symbol[1]['today']):
                            sell_price = data_daily['Open'][0]
                        else:
                            sell_price = data_daily['Open'][1]
                        self.place_sell_order(symbol[0],data_daily,sell_price)
            if(self.cash > self.leverage_amount): 
                symbols_buy_ratings = get_buy_ratings(self,symbols,week)
                symbols_buy_ratings = {key:value for key, value in sorted(symbols_buy_ratings.items(), key=lambda x: x[1]['rank'],reverse=True)}
                for symbol in symbols_buy_ratings.items():
                    if(symbol[1]['rank'] >= BUY_RANK and not self.is_holding(symbol[0]) and self.cash > self.leverage_amount and (symbol[0] not in sold_symbols)):
                        try:
                            day_str = str(symbol[1]['day'].date())
                        except:
                            day_str = str(symbol[1]['day'])
                        day = datetime.strptime(day_str,'%Y-%m-%d')
                        data_daily = yf.download(symbol[0],start = day_str, end= (day +timedelta(days=4)).strftime('%Y-%m-%d'),interval='1d',progress=False)
                        if(symbol[1]['today']):
                            buy_price = data_daily['Open'][0]
                        else:
                            buy_price = data_daily['Open'][1]
                        self.place_buy_order(symbol[0],data_daily,buy_price)
        self.close_out()
       

    def buy_rate(self,symbol_data_month,symbol_data_weekly,data_day,symbol,week):
        rank = 0
        enter = False
        buy_ret = {'day':week,'rank':rank,'today': True}
        seq_month, seq_weekly = get_sequence_month_week(symbol,symbol_data_month,symbol_data_weekly,week)
        seq_daily = SequenceMethod(data_day,'day',week + timedelta(days=6))
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
        data_day['SMA13'] = ta.SMA(data_day['Close'],timeperiod=13)
        data_day['SMA5'] = ta.SMA(data_day['SMA13'], timeperiod=5)
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
        
        # if(check_seq_by_date_daily(seq_daily.get_seq_df(),week) == 1):
        #     rank += 1
        if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),week) == 1):
            rank += 1
        else :
            buy_ret['rank'] = rank
            return buy_ret

        for day, row in data_daily.iterrows():
            if(week == (day - timedelta(days=day.weekday()))):
                if(row['Close'] > data_day.loc[str(day),'SMA13'] and check_seq_by_date_daily2(seq_daily.get_seq_df(),day) == 1):
                    enter = True
                    rank += BUY_RANK
                    buy_ret['day'] = day
                    buy_ret['today'] = False
                    
        if(check_seq_by_date_monthly(seq_month.get_seq_df(),week) == 1):
            rank += 2
        # try:
        #     if(data_day.loc[str(week),'SMA13'] < data_day.loc[str(week),'SMA5'] and data_day.loc[str(week - timedelta(days=3)),'SMA13'] < data_day.loc[str(week - timedelta(days=3)),'SMA5'] and data_day.loc[str(week - timedelta(days=5)),'SMA13'] < data_day.loc[str(week - timedelta(days=5)),'SMA5']):
        #         rank += 1
        # except:
        #     rank += 0
        try:
            if(data_day.loc[str(week - timedelta(days=3)),'SMA13'] < data_day.loc[str(week - timedelta(days=3)),'SMA5'] and data_day.loc[str(week - timedelta(days=5)),'SMA13'] < data_day.loc[str(week - timedelta(days=5)),'SMA5']):
                rank += 1
        except:
            rank += 0
        # try:
        #     if(first_weekly_date <= week and data_weekly.loc[str(week),'SMA13'] > data_weekly.loc[str(week),'SMA5']):
        #         rank += 1
        # except:
        #     rank += 0
        try:
            if(first_monthly_date <= last_month and data_monthly.loc[str(last_month),'SMA13'] > data_monthly.loc[str(last_month),'SMA5']):
                rank += 1
        except:
            rank += 0
        if(is_moving_away_weekly(data_weekly,week,pre_week)):
            rank += 1
        if(is_moving_away_monthly(data_monthly,last_month,pre_month)):
            rank += 1
        if(move_return != None and move_return <= avg_weekly_move/2.5):
            rank += 1

        buy_ret['rank'] = rank
        if(not enter): buy_ret['day'] = week
        return buy_ret

    def sell_rate(self,symbol_data_month,symbol_data_weekly,data_day,symbol,week):
        rank = 0
        sell_ret = {'day':week,'rank':rank,'today':True}
        seq_month, seq_weekly = get_sequence_month_week(symbol,symbol_data_month,symbol_data_weekly,week)
        seq_daily = SequenceMethod(data_day,'day',week + timedelta(days=6))
        avg_weekly_move = seq_weekly.get_avg_up_return()
        try:
            data_daily = yf.download(symbol,start = week, end= (week +timedelta(days=5)),progress=False)
            daily_price = data_daily['Open'][0]
        except:
            daily_price = None
        if(daily_price != None): trade_yield = (daily_price - self.holdings[symbol]['Avg Price'])/self.holdings[symbol]['Avg Price']*100
        else: trade_yield = None
        data_weekly = symbol_data_weekly
        data_monthly = symbol_data_month
        data_day['SMA13'] = ta.SMA(data_day['Close'],timeperiod=13)
        data_day['SMA5'] = ta.SMA(data_day['SMA13'], timeperiod=5)
        data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
        data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
        data_monthly['SMA13'] = ta.SMA(data_monthly['Close'],timeperiod=13)
        data_monthly['SMA5'] = ta.SMA(data_monthly['SMA13'], timeperiod=5)
        data_monthly = data_monthly.dropna()
        data_weekly = data_weekly.dropna()
        first_monthly_date = data_monthly.index[0].date()
        first_weekly_date = data_weekly.index[0].date()
        month = week.replace(day=1)
        last_month = month - timedelta(days=1) 
        last_month = last_month.replace(day = 1)
        last_week = week - timedelta(days=week.weekday(), weeks=1)
        # pre_week = week - timedelta(days=7*4)
        # pre_month = week.replace(day =1)
        # for i in range(3):
        #     pre_month = pre_month - timedelta(days=1)
        #     pre_month = pre_month.replace(day = 1)
        
        if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),week) == -1):
            rank += 1
            self.holdings[symbol]['Red Weeks'] = self.holdings[symbol]['Red Weeks'] + 1
        else :
            self.holdings[symbol]['Red Weeks'] = 0    
        if(self.holdings[symbol]['Red Weeks'] >= 2): # WAs 2
            rank += 1
        if(check_seq_by_date_monthly(seq_month.get_seq_df(),week) == -1):
            rank += 2
        # try:
        #     if(first_weekly_date <= week and data_weekly.loc[str(last_week),'SMA13'] < data_weekly.loc[str(last_week),'SMA5']):
        #         rank += 1
        # except:
        #     rank += 0
        try:
            if(first_monthly_date <= last_month and data_monthly.loc[str(last_month),'SMA13'] < data_monthly.loc[str(last_month),'SMA5']):
                rank += 1
        except:
            rank += 0
        if(trade_yield != None and trade_yield >= avg_weekly_move*0.75): #Was 0.75
            rank += 1
        if(trade_yield != None and trade_yield >= avg_weekly_move):
            rank += 1
        if(trade_yield != None and trade_yield >= avg_weekly_move*1.25): #was 2
            rank += 1
        if(trade_yield != None and trade_yield >= avg_weekly_move*1.5): #was 3
            rank += 1

        sell_ret['rank'] = rank
        sell_ret['day'] = week
        if(rank >= SELL_RANK):
            return sell_ret

        for day, row in data_daily.iterrows():
            if(week == (day - timedelta(days=day.weekday()))):
                if(row['Close'] < data_day.loc[str(day),'SMA13'] and check_seq_by_date_daily2(seq_daily.get_seq_df(),day) == -1):
                    rank += SELL_RANK
                    sell_ret['rank'] = rank
                    sell_ret['day'] = day
                    sell_ret['today'] = False
                    return sell_ret
        return sell_ret

    def is_holding(self,symbol):
        for ticker in self.holdings.items():
            if(ticker[0] == symbol): return True
        return False


def get_buy_ratings(self,symbols,week):
    rating = {}
    for symbol in symbols:
        symbol_data_day = pd.DataFrame(yf.download(tickers=symbol, period='max',interval='1d',progress=False)).dropna()
        symbol_data_month = pd.DataFrame(yf.download(tickers=symbol, period='max',interval='1mo',progress=False)).dropna()
        symbol_data_weekly = pd.DataFrame(yf.download(tickers=symbol, period='max',interval='1wk',progress=False)).dropna()
        rating[symbol] = self.buy_rate(symbol_data_month,symbol_data_weekly,symbol_data_day,symbol,week)
    return rating

def get_sell_rating(self,week):
    rating = {}
    if(not self.holdings):
        return None
    for symbol in self.holdings.items():
        symbol_data_day = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1d',progress=False)).dropna()
        symbol_data_month = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1mo',progress=False)).dropna()
        symbol_data_weekly = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1wk',progress=False)).dropna()
        rating[symbol[0]] = self.sell_rate(symbol_data_month,symbol_data_weekly,symbol_data_day,symbol[0],week)
    return rating


def update_hold_yield(self,symbol):
    data_daily = yf.download(symbol,start = self.today, end= (self.today +timedelta(days=3)),progress=False)
    daily_price = data_daily['Open'][0]
    new_row = {}
    new_row['Hold Yield'] = (daily_price - self.hold_entry_price)/self.hold_entry_price*100
    self.trade_log = self.trade_log.append(new_row, ignore_index=True)
    self.trade_log.to_csv(results_path / f"seq_strategy.csv")

def is_moving_away_weekly(data_weekly,week,pre_week):
    try:
        if((data_weekly.loc[str(week),'SMA13'] - data_weekly.loc[str(week),'SMA5']) > (data_weekly.loc[str(pre_week),'SMA13'] - data_weekly.loc[str(pre_week),'SMA5'])):
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

def check_seq_by_date_daily(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] < date):
            previous_row = row
            first = False
        else: break
    if(first): return 0
    return int(previous_row['Sequence'])

def check_seq_by_date_daily2(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] <= date):
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

def run_strategies():
    # xlc.run_seq_strategy_trades(13, 5)
    pass
        
data_output = pd.DataFrame(columns=['Symbol','Period','Strategy Yield','Hold Yield','Trades','Win Rate'])
data_output_trades = pd.DataFrame(columns=['Date','Buy\Sell','Price','Trade Yield','Days Hold'])

if __name__ == '__main__':
    results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Strategy'
    if not results_path.exists():
        results_path.mkdir(parents=True)
    start_date = datetime.strptime('2017-01-03','%Y-%m-%d')
    end_date = datetime.strptime('2022-08-11','%Y-%m-%d')
    portfolio = Backtest(amount=1000000,start=start_date,end=end_date,ptc=0.005)
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

    