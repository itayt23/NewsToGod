from mybacktestingbase import *
from sequencing import SequenceMethod
from pathlib import Path
from datetime import date,datetime,timedelta
import yfinance as yf
import numpy as np
import json
import time

start_time = time.time()

#line 64 check maybe need to check more deeply
BUY_RANK = 6
SELL_RANK = 5
SELL_RANK_HARD = 9
TOTAL_SELL_RANK = 19
TOTAL_SELL_RANK_NO_SL = 10
TIME_OUT = 59
NO_STOPLOSS = 0
MINIMUN_SELL = 1
MINIMUN_MINUS_SELL = -2


class Backtest(MyBacktestBase):

    def run_seq_strategy(self):
        global symbols_daily_df,symbols_weekly_df,symbols_monthly_df,symbols
        symbols_sell_ratings = {}
        symbols_buy_ratings = {}
        trading_days = symbols_daily_df['XLK']
        trading_days = trading_days.index.to_list()
        strat_index = 278
        print(self.start.date())
        for i in range(len(trading_days)):
            trading_days[i] = trading_days[i].date()
            if(self.start.date() == trading_days[i]): strat_index = i
        trading_days = trading_days[strat_index:] #Start of 2019 was 286
        for day in trading_days:
            # time_passed = (time.time() - start_time)/60
            # if(time_passed >= TIME_OUT):
            #     break
            position_size = 1
            self.today = day
            sold_now = []
            symbols_sell_ratings = get_sell_ratings(self,day)
            if(symbols_sell_ratings != None):
                for symbol in symbols_sell_ratings.items():
                    position_size = 1
                    sold = False
                    selling_date = day
                    entry_date = self.holdings[symbol[0]]['Entry Date']
                    selling_price = symbols_daily_df[symbol[0]].loc[str(day),'Open']
                    if(type(entry_date) is list): days_hold = (selling_date - entry_date[0]).days
                    else: days_hold = (selling_date - entry_date).days
                    trade_return = (selling_price - self.holdings[symbol[0]]['Avg Price'])/self.holdings[symbol[0]]['Avg Price']*100
                    if(symbol[1]['rank'] >= SELL_RANK):
                        if(MINIMUN_MINUS_SELL > trade_return or trade_return > MINIMUN_SELL):
                            if(days_hold < 15):
                                if(symbol[1]['rank'] >= SELL_RANK_HARD or (symbol[1]['rank'] >= SELL_RANK and trade_return <= (-8))):
                                    sold_now.append(symbol[0])
                                    sold = True
                                    self.place_sell_order(symbol[0],selling_date,selling_price,symbol[1]['rules'],position_size)
                            elif(symbol[1]['rank'] >= SELL_RANK):
                                sold_now.append(symbol[0])
                                sold = True
                                self.place_sell_order(symbol[0],selling_date,selling_price,symbol[1]['rules'],position_size)
                    if(not sold and (MINIMUN_MINUS_SELL > trade_return or trade_return > MINIMUN_SELL)):
                        stoploss_rule = get_stoploss_rule(symbol[1]['rules'])
                        if(stoploss_rule == NO_STOPLOSS): continue
                        if('stoploss_rules' not in self.holdings[symbol[0]]):
                            self.holdings[symbol[0]]['stoploss_rules'] = []
                        if(stoploss_rule in self.holdings[symbol[0]]['stoploss_rules']): continue
                        self.holdings[symbol[0]]['stoploss_rules'].append(stoploss_rule)
                        position_size = sell_rule_to_position_size(stoploss_rule)
                        sold_now.append(symbol[0])
                        self.place_sell_order(symbol[0],selling_date,selling_price,symbol[1]['rules'],position_size)
            if(self.cash > self.leverage_amount): 
                symbols_buy_ratings = get_buy_ratings(self,symbols,day)
                symbols_buy_ratings = {key:value for key, value in sorted(symbols_buy_ratings.items(), key=lambda x: x[1]['rank'],reverse=True)}
                for symbol in symbols_buy_ratings.items():
                    if(symbol[1]['rank'] >= BUY_RANK and not self.is_holding_full_size(symbol[0]) and self.cash > self.leverage_amount and (symbol[0] not in sold_now)):
                        price = symbols_daily_df[symbol[0]].loc[str(day),'Open']
                        position_size = 1
                        if(self.is_holding(symbol[0])) : position_size = 1 - self.holdings[symbol[0]]['Position Size']
                        self.place_buy_order(symbol[0],day,price,symbol[1]['rules'],position_size)
        self.close_out(self.today)
       

    def buy_rate(self,symbol_data_month,symbol_data_weekly,data_day,symbol,day):
        rank = 0
        stop_check = False
        buy_rules = []
        buy_ret = {'rank':rank,'rules': buy_rules,'seq_month':False}
        seq_month  = SequenceMethod(symbol_data_month,'monthly',day)
        seq_weekly =  SequenceMethod(symbol_data_weekly,'weekly',day)
        seq_daily = SequenceMethod(data_day,'day',day)
        last_6_days = day - timedelta(days=15)
        last_6_days = data_day.truncate(before=last_6_days, after=day)
        if(last_6_days.shape[0] >=6 ): last_6_days = last_6_days.tail(last_6_days.shape[0] - (last_6_days.shape[0] - 6)) 
        last_day = last_6_days.tail(2)
        last_day = last_day.head(1)
        month = day.replace(day=1)
        pre_week = day - timedelta(days=7*4)
        last_month = month - timedelta(days=1) 
        last_month = last_month.replace(day = 1)
        pre_3_month = day.replace(day =1)
        try:
            last_seq_date = seq_daily.get_seq_df()['Date'].iloc[-1]
        except:
            buy_ret['rank'] = 0
            buy_ret['rules'] = buy_rules
            return buy_ret
        for i in range(3):
            pre_3_month = pre_3_month - timedelta(days=1)
            pre_3_month = pre_3_month.replace(day = 1)
        # last_seq_date = seq_daily.get_seq_df()['Date'].iloc[-1]
        ##################START BUY RULES#######################
        if(float(data_day.loc[str(last_day.index[-1]),'Close']) > float(data_day.loc[str(last_day.index[-1]),'SMA13']) and check_seq_by_date_daily(seq_daily.get_seq_df(),day) == 1
                and (last_day.index[-1].date() - last_seq_date).days == 0):
            rank += 5
            buy_rules.append('2')
        if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),day) == 1):
            rank += 1
            buy_rules.append('3')
        else :
            stop_check = True
        if(check_seq_by_date_monthly(seq_month.get_seq_df(),day) == 1):
            buy_ret['seq_month'] = True
            if(not stop_check):
                rank += 2
                buy_rules.append('4')
        if(stop_check):
            buy_ret['rank'] = rank
            buy_ret['rules'] = buy_rules
            return buy_ret
        try:
            if(data_day.loc[str(last_day.index[-1]),'SMA13'] > data_day.loc[str(last_day.index[-1]),'SMA5'] and data_day.loc[str(last_6_days.head(3).tail(1).index[-1]),'SMA13'] > data_day.loc[str(last_6_days.head(3).tail(1).index[-1]),'SMA5']):
                rank += 1
                buy_rules.append('5')
        except:
            rank += 0
        try:
            if(symbol_data_month.loc[str(last_month),'SMA13'] > symbol_data_month.loc[str(last_month),'SMA5']):
                rank += 1
                buy_rules.append('6')
        except:
            rank += 0
        if(is_moving_away_weekly(symbol_data_weekly,day,pre_week)):
            rank += 1
            buy_rules.append('7')
        if(is_moving_away_monthly(symbol_data_month,last_month,pre_3_month)):
            rank += 1
            buy_rules.append('8')
        buy_ret['rank'] = rank
        buy_ret['rules'] = buy_rules
        return buy_ret

    def sell_rate(self,symbol_data_month,symbol_data_weekly,data_day,symbol,day):
        global symbols_daily_df,symbols_weekly_df,symbols_monthly_df
        rank = 0
        sell_rules = []
        sell_ret = {'rank':rank,'rules': sell_rules}
        seq_month  = SequenceMethod(symbol_data_month,'monthly',day)
        seq_weekly =  SequenceMethod(symbol_data_weekly,'weekly',day)
        seq_daily = SequenceMethod(data_day,'day',day)
        daily_price = data_day.loc[str(day),'Open']
        if(daily_price != None): trade_yield = (daily_price - self.holdings[symbol]['Avg Price'])/self.holdings[symbol]['Avg Price']*100
        else: trade_yield = None
        last_day = day - timedelta(days=5)
        last_day = data_day.truncate(before=last_day, after=day)
        last_day = last_day.tail(2)
        last_day = last_day.head(1)
        month = day.replace(day=1)
        last_month = month - timedelta(days=1) 
        last_month = last_month.replace(day = 1)
        ################START OF RULES##################################
        if(float(last_day.loc[str(last_day.index[-1]),'Close']) < float(data_day.loc[str(last_day.index[-1]),'SMA5']) and check_seq_by_date_daily(seq_daily.get_seq_df(),day) == -1):
            rank += 5
            sell_rules.append("2")
        if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),day) == -1):
            rank += 1
            sell_rules.append("3")
            if(check_seq_by_date_weekly_previous(seq_weekly.get_seq_df()) == -1):
                rank += 1
                sell_rules.append("3a")
        if(check_seq_by_date_monthly(seq_month.get_seq_df(),day) == -1):
            rank += 2
            sell_rules.append('4')
        if(symbol_data_month.loc[str(last_month),'SMA13'] < symbol_data_month.loc[str(last_month),'SMA5']):
            rank += 1
            sell_rules.append('5')
        if(float(symbols_daily_df[symbol].loc[str(day),'ATRP'])*7 <= trade_yield):
            sell_rules.append('6')
        elif(float(symbols_daily_df[symbol].loc[str(day),'ATRP'])*5 <= trade_yield):
            sell_rules.append('7')
        elif(float(symbols_daily_df[symbol].loc[str(day),'ATRP'])*4 <= trade_yield):
            sell_rules.append('8')
        elif(float(symbols_daily_df[symbol].loc[str(day),'ATRP'])*3 <= trade_yield):
            sell_rules.append('9')
           
        sell_ret['rank'] = rank
        sell_ret['rules'] = sell_rules
        return sell_ret
            
    def is_holding(self,symbol):
        for ticker in self.holdings.items():
            if(ticker[0] == symbol): return True
        return False

    def is_holding_full_size(self,symbol):
        for ticker in self.holdings.items():
            if(ticker[0] == symbol and ticker[1]['Position Size'] == 1): return True
        return False

def get_buy_ratings(self,symbols,day):
    global symbols_daily_df,symbols_weekly_df,symbols_monthly_df
    rating = {}
    for symbol in symbols:
        symbol_data_day = symbols_daily_df[symbol]
        symbol_data_weekly = symbols_weekly_df[symbol]
        symbol_data_month = symbols_monthly_df[symbol]
        rating[symbol] = self.buy_rate(symbol_data_month,symbol_data_weekly,symbol_data_day,symbol,day)
    return rating

def get_sell_ratings(self,day):
    global symbols_daily_df,symbols_weekly_df,symbols_monthly_df
    rating = {}
    if(not self.holdings):
        return None
    for symbol in self.holdings.items():
        symbol_data_day = symbols_daily_df[symbol[0]]
        symbol_data_weekly = symbols_weekly_df[symbol[0]]
        symbol_data_month = symbols_monthly_df[symbol[0]]
        rating[symbol[0]] = self.sell_rate(symbol_data_month,symbol_data_weekly,symbol_data_day,symbol[0],day)
    return rating

def is_moving_away_weekly(data_weekly,today,pre_week):
    try:
        if(data_weekly.loc[str(today),'SMA13'] > data_weekly.loc[str(today),'SMA5'] and data_weekly.loc[str(pre_week),'SMA13'] > data_weekly.loc[str(pre_week),'SMA5']):
            if((data_weekly.loc[str(today),'SMA13'] - data_weekly.loc[str(today),'SMA5']) > (data_weekly.loc[str(pre_week),'SMA13'] - data_weekly.loc[str(pre_week),'SMA5'])):
                return True
    except:
        return False
    return False

def is_moving_away_monthly(data_monthly,last_month,pre_month):
    try:
        if(data_monthly.loc[str(last_month),'SMA13'] > data_monthly.loc[str(last_month),'SMA5'] and data_monthly.loc[str(pre_month),'SMA13'] > data_monthly.loc[str(pre_month),'SMA5']):
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

def get_sequence_month_week(symbol,symbol_data_month,symbol_data_weekly,day):
    data_monthly = symbol_data_month
    data_weekly = symbol_data_weekly
    symbol_sequence_monthly = SequenceMethod(data_monthly,'monthly',day)
    symbol_sequence_weekly = SequenceMethod(data_weekly,'weekly',day)
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

def check_seq_by_date_weekly_previous(seq):
   return int(seq.iloc[-2]['Sequence'])

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

def atr_calculate(data):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1).dropna()
    atr = true_range.rolling(14).sum()/14
    data['ATR'] = atr

def sell_rule_to_position_size(rule):
    if(rule == '6'): return 1
    if(rule == '7'): return 0.75
    if(rule == '8'): return 0.5
    if(rule == '9'): return 0.25
    return NO_STOPLOSS

def get_stoploss_rule(rules):
    if('6' in rules): return '6'
    if('7' in rules): return '7'
    if('8' in rules): return '8'
    if('9' in rules): return '9'
    return NO_STOPLOSS
    
symbols = ['XLK','XLV','XLE','XLC','XLRE','XLU','SPY','QQQ','DIA','NOBL','DVY','DXJ','GLD','SMH','TLT',
            'XBI','EEM','XHB','XRT','XLY','VGK','XOP','VGT','FDN','HACK','SKYY','KRE','XLF','XLB']
symbols_daily_df= {}
symbols_weekly_df= {}
symbols_monthly_df= {}
for symbol in symbols:
    symbols_daily_df[symbol] = (pd.DataFrame(yf.download(tickers=symbol, period='10y',interval='1d',progress=False)).dropna())
    symbols_weekly_df[symbol] = (pd.DataFrame(yf.download(tickers=symbol, period='10y',interval='1wk',progress=False)).dropna())
    symbols_monthly_df[symbol] = (pd.DataFrame(yf.download(tickers=symbol, period='10y',interval='1mo',progress=False)).dropna())

    symbols_daily_df[symbol]['SMA13'] = symbols_daily_df[symbol]['Close'].rolling(window=13).mean()
    symbols_daily_df[symbol]['SMA5'] = symbols_daily_df[symbol]['SMA13'].rolling(window=5).mean()
    symbols_weekly_df[symbol]['SMA13'] = symbols_weekly_df[symbol]['Close'].rolling(window=13).mean()
    symbols_weekly_df[symbol]['SMA5'] = symbols_weekly_df[symbol]['SMA13'].rolling(window=5).mean()
    symbols_monthly_df[symbol]['SMA13'] = symbols_monthly_df[symbol]['Close'].rolling(window=13).mean()
    symbols_monthly_df[symbol]['SMA5'] = symbols_monthly_df[symbol]['SMA13'].rolling(window=5).mean()
    # symbols_daily_df[symbol]["ATR"] = ta.ATR(symbols_daily_df[symbol]['High'], symbols_daily_df[symbol]['Low'], symbols_daily_df[symbol]['Close'], timeperiod=14)
    # symbols_weekly_df[symbol]["ATR"] = ta.ATR(symbols_weekly_df[symbol]['High'], symbols_weekly_df[symbol]['Low'], symbols_weekly_df[symbol]['Close'], timeperiod=14)
    # symbols_monthly_df[symbol]["ATR"] = ta.ATR(symbols_monthly_df[symbol]['High'], symbols_monthly_df[symbol]['Low'], symbols_monthly_df[symbol]['Close'], timeperiod=14)
    atr_calculate(symbols_daily_df[symbol])
    atr_calculate(symbols_weekly_df[symbol])
    atr_calculate(symbols_monthly_df[symbol])
    symbols_daily_df[symbol]['ATRP'] = (symbols_daily_df[symbol]['ATR']/symbols_daily_df[symbol]['Close'])*100
    symbols_weekly_df[symbol]['ATRP'] = (symbols_weekly_df[symbol]['ATR']/symbols_weekly_df[symbol]['Close'])*100
    symbols_monthly_df[symbol]['ATRP'] = (symbols_monthly_df[symbol]['ATR']/symbols_monthly_df[symbol]['Close'])*100
    symbols_monthly_df[symbol].dropna()
    symbols_weekly_df[symbol].dropna()

if __name__ == '__main__':
    try:
        symbols_daily_df,symbols_weekly_df,symbols_monthly_df
        results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Strategy'
        if not results_path.exists():
            results_path.mkdir(parents=True)
        start_date = datetime.strptime('2016-01-04','%Y-%m-%d')
        end_date = datetime.strptime('2022-11-02','%Y-%m-%d')
        portfolio = Backtest(start=start_date,end=end_date,amount=1000000,symbols_daily_df=symbols_daily_df,
                                symbols_weekly_df=symbols_weekly_df,symbols_monthly_df=symbols_monthly_df,ptc=0.005)
        portfolio.run_seq_strategy()
    except Exception as err:
        template = "An exception occured:\n{0} of type {1} occurred. Arguments:\n{2!r}"
        message = template.format(str(err),type(err).__name__, err.args)
        print(json.dumps({"message": message, "severity": "ERROR"}))
        exit(1)
            

    