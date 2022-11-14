from mybacktestingbase import *
from sequencing import SequenceMethod
from pathlib import Path
from datetime import date,datetime,timedelta
import yfinance as yf
import numpy as np
# import yfinance.shared as shared



#Add counter of consective red weeks for sell rate
#ADd 0.75 from weekly move +1
#dont buy week after week
# add IUSV ETF? and xlu
#stochastin low rank + 1 in buy rate?

BUY_RANK = 6
SELL_RANK = 5
SELL_RANK_HARD = 8


###BEST 3 ETFS####
# - XLK - 87.37
#XLV - 46.54
#XLE - 45.94
###WORST 3 ETFS###
#XLC - 1
#XLRE - 6 
#XLU - 21.02
#ALL AVG IS: 34.645
class Backtest(MyBacktestBase):

    def run_seq_strategy(self):
        global symbols_daily_df,symbols_weekly_df,symbols_monthly_df
        symbols = ['XLK','XLV','XLE','XLC','XLRE','XLU']
        symbols_sell_ratings = {}
        symbols_buy_ratings = {}
        trading_days = symbols_daily_df['XLK']
        trading_days = trading_days.index.to_list()
        for i in range(len(trading_days)):
            trading_days[i] = trading_days[i].date()
        trading_days = trading_days[286:] #Start of 2019 was 286
        for day in trading_days:
            self.today = day
            sold_now = []
            print(day)
            symbols_sell_ratings = get_sell_ratings(self,day)
            if(symbols_sell_ratings != None):
                # symbols_sell_ratings = {key:value for key, value in sorted(symbols_sell_ratings.items(), key=lambda x: x[1],reverse=True)}
                for symbol in symbols_sell_ratings.items():
                    if(symbol[1]['rank'] < SELL_RANK): continue
                    selling_date = day
                    days_hold = (selling_date - self.holdings[symbol[0]]['Entry Date']).days
                    selling_price = symbols_daily_df[symbol[0]].loc[str(day),'Open']
                    trade_return = (selling_price - self.holdings[symbol[0]]['Avg Price'])/self.holdings[symbol[0]]['Avg Price']*100
                    if(days_hold < 14):
                        if(symbol[1]['rank'] >= SELL_RANK_HARD or (symbol[1]['rank'] >= SELL_RANK and trade_return <= (-10))):
                            sold_now.append(symbol[0])
                            self.place_sell_order(symbol[0],selling_date,selling_price,symbol[1]['rules'])
                    elif(symbol[1]['rank'] >= SELL_RANK):
                        sold_now.append(symbol[0])
                        self.place_sell_order(symbol[0],selling_date,selling_price,symbol[1]['rules'])
            if(self.cash > self.leverage_amount): 
                symbols_buy_ratings = get_buy_ratings(self,symbols,day)
                symbols_buy_ratings = {key:value for key, value in sorted(symbols_buy_ratings.items(), key=lambda x: x[1]['rank'],reverse=True)}
                for symbol in symbols_buy_ratings.items():
                    if(symbol[1]['rank'] >= BUY_RANK and not self.is_holding(symbol[0]) and self.cash > self.leverage_amount and (symbol[0] not in sold_now)):
                        price = symbols_daily_df[symbol[0]].loc[str(day),'Open']
                        self.place_buy_order(symbol[0],day,price,symbol[1]['rules'])
        self.close_out(self.today)
       

    def buy_rate(self,symbol_data_month,symbol_data_weekly,data_day,symbol,day):
        rank = 0
        buy_rules = []
        buy_ret = {'rank':rank,'rules': buy_rules}
        seq_month  = SequenceMethod(symbol_data_month,'monthly',day)
        seq_weekly =  SequenceMethod(symbol_data_weekly,'weekly',day)
        seq_daily = SequenceMethod(data_day,'day',day)
        avg_weekly_move = seq_weekly.get_avg_up_return()
        last_day = day - timedelta(days=5)
        last_day = data_day.truncate(before=last_day, after=day)
        last_day = last_day.tail(2)
        last_day = last_day.head(1)
        start_move_price = check_seq_price_by_date_weekly(seq_weekly.get_seq_df(),day)
        daily_price = data_day.loc[str(day),'Open']
        if(daily_price != None and start_move_price != None): move_return = (daily_price - start_move_price)/start_move_price*100
        else: move_return = None
        first_monthly_date = symbol_data_month.index[0].date()
        first_weekly_date = symbol_data_weekly.index[0].date()
        month = day.replace(day=1)
        pre_week = day - timedelta(days=7*4)
        last_month = month - timedelta(days=1) 
        last_month = last_month.replace(day = 1)
        pre_3_month = day.replace(day =1)
        for i in range(3):
            pre_3_month = pre_3_month - timedelta(days=1)
            pre_3_month = pre_3_month.replace(day = 1)
        last_seq_date = seq_daily.get_seq_df()['Date'].iloc[-1]
        # print(f'last day is: {str(last_day.index[-1])}')
        # print(f'diff is: {(last_day.index[-1].date() - last_seq_date).days}')
        # print(f"close price {last_day.loc[str(last_day.index[-1]),'Close']}")
        # print(f"SMA13 price {data_day.loc[str(last_day.index[-1]),'SMA13']}")
        ##################START BUY RULES#######################
        if(float(data_day.loc[str(last_day.index[-1]),'Close']) > float(data_day.loc[str(last_day.index[-1]),'SMA13']) and check_seq_by_date_daily(seq_daily.get_seq_df(),day) == 1
                and (last_day.index[-1].date() - last_seq_date).days == 0):
            rank += 5
            buy_rules.append('2')
        if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),day) == 1):
            rank += 1
            buy_rules.append('3')
        else :
            buy_ret['rank'] = rank
            buy_ret['rules'] = buy_rules
            return buy_ret
        if(check_seq_by_date_monthly(seq_month.get_seq_df(),day) == 1):
            rank += 2
            buy_rules.append('4')
        try:
            if(data_day.loc[str(day),'SMA13'] > data_day.loc[str(day),'SMA5'] and data_day.loc[str(day+ timedelta(days=1)),'SMA13'] > data_day.loc[str(day+ timedelta(days=1)),'SMA5']):
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
        # if(move_return != None and move_return <= avg_weekly_move/2): #was 2.5
        #     rank += 1
        #     buy_rules.append('9')
        buy_ret['rank'] = rank
        buy_ret['rules'] = buy_rules
        return buy_ret

    def sell_rate(self,symbol_data_month,symbol_data_weekly,data_day,symbol,day): #TODO:fix comments
        global symbols_daily_df,symbols_weekly_df,symbols_monthly_df
        rank = 0
        sell_rules = []
        sell_ret = {'rank':rank,'rules': sell_rules}
        # seq_month, seq_weekly = get_sequence_month_week(symbol,symbol_data_month,symbol_data_weekly,day)
        seq_month  = SequenceMethod(symbol_data_month,'monthly',day)
        seq_weekly =  SequenceMethod(symbol_data_weekly,'weekly',day)
        seq_daily = SequenceMethod(data_day,'day',day)
        avg_weekly_move = seq_weekly.get_avg_up_return()
        daily_price = data_day.loc[str(day),'Open']#! was'Cloes need to check it
        if(daily_price != None): trade_yield = (daily_price - self.holdings[symbol]['Avg Price'])/self.holdings[symbol]['Avg Price']*100
        else: trade_yield = None
        last_day = day - timedelta(days=5)
        last_day = data_day.truncate(before=last_day, after=day)
        last_day = last_day.tail(2)
        last_day = last_day.head(1)
        first_monthly_date = symbol_data_month.index[0].date()
        first_weekly_date = symbol_data_weekly.index[0].date()
        month = day.replace(day=1)
        pre_week = day - timedelta(days=7*4)
        last_month = month - timedelta(days=1) 
        last_month = last_month.replace(day = 1)
        pre_month = day.replace(day =1)
        for i in range(3):
            pre_month = pre_month - timedelta(days=1)
            pre_month = pre_month.replace(day = 1) #!Check if its ok
        ################START OF RULES##################################
        if(float(last_day.loc[str(last_day.index[-1]),'Close']) < float(data_day.loc[str(last_day.index[-1]),'SMA13']) and check_seq_by_date_daily(seq_daily.get_seq_df(),day) == -1):
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
        try:
            if(symbol_data_month.loc[str(last_month),'SMA13'] < symbol_data_month.loc[str(last_month),'SMA5']):#!check what is last month
                rank += 1
                sell_rules.append('5')
        except:
            rank += 0
        if(trade_yield >= avg_weekly_move*0.75):
            rank += 1
            sell_rules.append('6')
        if(trade_yield >= avg_weekly_move):
            rank += 1
            sell_rules.append('7')
        if(trade_yield >= avg_weekly_move*1.25): #was 2
            rank += 1
            sell_rules.append('8')
        if(trade_yield >= avg_weekly_move*1.5): #was 3
            rank += 1
            sell_rules.append('9')
        sell_ret['rank'] = rank
        sell_ret['rules'] = sell_rules
        return sell_ret
            
    def is_holding(self,symbol):
        for ticker in self.holdings.items():
            if(ticker[0] == symbol): return True
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
        if(data_weekly.loc[str(today),'SMA13'] > data_weekly.loc[str(today),'SMA5']):
            if((data_weekly.loc[str(today),'SMA13'] - data_weekly.loc[str(today),'SMA5']) > (data_weekly.loc[str(pre_week),'SMA13'] - data_weekly.loc[str(pre_week),'SMA5'])):
                return True
    except:
        return False
    return False

def is_moving_away_monthly(data_monthly,last_month,pre_month):
    try:
        if(data_monthly.loc[str(last_month),'SMA13'] > data_monthly.loc[str(last_month),'SMA5']):
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
def get_daily_data(symbol):
    match symbol:
        case 'XLK':
            return "Dsa"
        case 'XLV':
            return "Not found"
        case 'XLE':
            return "I'm a teapot"
        case 'XLC':
            return "I'm a teapot"
        case 'XLRE':
            return "I'm a teapot"
        case 'XLU':
            return "I'm a teapot"
        case _:
            return "Something's wrong with the internet"

def atr_calculate(data):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1).dropna()
    atr = true_range.rolling(14).sum()/14
    # print(type(atr))
    data['ATR'] = atr
    
# def get_weekly_data(symbol):
# def get_monthly_data(symbol):
# data_output = pd.DataFrame(columns=['Symbol','Period','Strategy Yield','Hold Yield','Trades','Win Rate'])
# data_output_trades = pd.DataFrame(columns=['Date','Buy\Sell','Price','Trade Yield','Days Hold'])

symbols = ['XLK','XLV','XLE','XLC','XLRE','XLU']
symbols_daily_df= {}
symbols_weekly_df= {}
symbols_monthly_df= {}
for symbol in symbols:
    symbols_daily_df[symbol] = (pd.DataFrame(yf.download(tickers=symbol, period='5y',interval='1d',progress=False)).dropna())
    symbols_weekly_df[symbol] = (pd.DataFrame(yf.download(tickers=symbol, period='5y',interval='1wk',progress=False)).dropna())
    symbols_monthly_df[symbol] = (pd.DataFrame(yf.download(tickers=symbol, period='5y',interval='1mo',progress=False)).dropna())

    symbols_daily_df[symbol]['SMA13'] = symbols_daily_df[symbol]['Close'].rolling(window=13).mean()
    symbols_daily_df[symbol]['SMA5'] = symbols_daily_df[symbol]['SMA13'].rolling(window=5).mean()
    symbols_weekly_df[symbol]['SMA13'] = symbols_weekly_df[symbol]['Close'].rolling(window=13).mean()
    symbols_weekly_df[symbol]['SMA5'] = symbols_weekly_df[symbol]['SMA13'].rolling(window=5).mean()
    symbols_monthly_df[symbol]['SMA13'] = symbols_monthly_df[symbol]['Close'].rolling(window=13).mean()
    symbols_monthly_df[symbol]['SMA5'] = symbols_monthly_df[symbol]['SMA13'].rolling(window=5).mean()
    atr_calculate(symbols_daily_df[symbol])
    atr_calculate(symbols_weekly_df[symbol])
    atr_calculate(symbols_monthly_df[symbol])

    symbols_monthly_df[symbol].dropna()
    symbols_weekly_df[symbol].dropna()

if __name__ == '__main__':
    results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Strategy'
    if not results_path.exists():
        results_path.mkdir(parents=True)
    start_date = datetime.strptime('2019-01-01','%Y-%m-%d')
    end_date = datetime.strptime('2022-11-02','%Y-%m-%d')
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

    