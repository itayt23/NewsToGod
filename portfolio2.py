import yahoo_fin.stock_info as yf2
from sequencing import *
from myexceptions import *
import requests
import json
import traceback
import time
import tradestationapi as ts
import sys
import os
import numpy as np
# import gcsfs
from google.cloud import storage


ACCOUNT_ID = 11509188
STARTING_AMOUNT = 1000000
BUY_RANK = 6
SELL_RANK = 5
SELL_RANK_HARD = 9
MINIMUN_SELL = 1
MINIMUN_MINUS_SELL = -2
TRADE_SIZE = 0.25
LEVERAGE_SIZE = 0.01
FAILED_ORDER = -1
FAIL = -1
SUCCESS = 1
ERROR = -1
ERROR_ORDER = -1
NOT_EXIST = -1
NO_STOPLOSS = 0
MINIMUN_ENTER_POSITION_SIZE = 0.5
MINIMUN_SELL_POSITION_SIZE = 0.2
MAXIMUM_POSITION_SIZE = 0.75
ORDERS_HISTORY_FILE = 'orders_history.csv'
ORDERS_HISTORY_FILE = 'orders_history_backup.csv'
STORAGE_BUCKET_NAME = 'backtesting_results'
PROJECT_NAME = 'orbital-expanse-368511'




#TODO: need to initialite first empty csv backup if system is falling down! 
#TODO: need to look if this function is good - check_seq_by_date_daily_equal
#TODO: need to fix problem that uploading the same csv file name is not updating the file


class Portfolio:

    def __init__(self,trade_station):
        self.ts_session = trade_station
        self.cash = self.get_cash()
        self.starting_amount = STARTING_AMOUNT
        self.equity = self.get_equity()
        self.net_wealth = self.cash + self.equity
        self.holdings = self.get_holdings()
        self.orders_history_df = pd.DataFrame(columns=['Ticker','Position Left','Stoploss Rules','Dates'])
        self.orders_history_df = self.orders_history_df.set_index('Ticker')
        # self.orders_history_df.loc['AAPL'] = {'Position Left':20}
        self.upload_df_to_gcloud()
        self.trade_size_cash = TRADE_SIZE * self.net_wealth
        self.leverage_amount = LEVERAGE_SIZE * self.net_wealth
        self.queue_buying_money = 0
        self.queue_selling_money = 0
        self.orders = {}
        self.queue_orders = {}
        self.sold_symbols = []
        self.filled_orders = {}
        self.etfs_to_buy = ['XLK','XLV','XLE','XLC','XLRE','XLU','SPY','QQQ','DIA','NOBL','DVY','DXJ','GLD','SMH',
                    'TLT','XBI','EEM','XHB','XRT','XLY','VGK','XOP','VGT','FDN','HACK','SKYY','KRE','XLF','XLB']
    
    def get_start_amount(self):
        return self.starting_amount
    
    def update_ts_session(self,session):
        self.ts_session = session

    def execute_buy_order(self,symbol,symbol_price):
        position_size = 1
        if(self.is_holding(symbol) and symbol in self.orders_history_df.index):
            position_size = 1 - self.orders_history_df.loc[symbol,'Position Left']
            self.orders_history_df.loc[symbol,'Position Left'] = 1 
        size = int((self.trade_size_cash*position_size) / float(symbol_price))
        ts.place_order(self.ts_session,symbol,size,buy_sell="BUY")
        # self.buy(symbol, size)

    def execute_sell_order(self,symbol,size):
        self.sold_symbols.append(symbol)
        self.orders_history_df = self.orders_history_df.drop(symbol)
        ts.place_order(self.ts_session,symbol,size,buy_sell="SELL")
        # self.sell(symbol,size)

    def execute_stoploss(self,symbol,size,stoploss_rule,today,position_size = 1):
        all_sell_rules = []
        all_sell_dates = []
        self.sold_symbols.append(symbol)
        position_size = sell_rule_to_position_size(stoploss_rule) 
        position_left = 1 - position_size
        if(symbol not in self.orders_history_df.index):
            self.orders_history_df.loc[symbol] = {'Ticker': symbol,'Position Left': position_left}
        else:
            all_sell_rules = list(self.orders_history_df.loc[symbol,'Stoploss Rules'])
            all_sell_dates = list(self.orders_history_df.loc[symbol,'Dates'])
            self.orders_history_df.loc[symbol,'Position Left'] = self.orders_history_df.loc[symbol,'Position Left'] - position_size
        all_sell_rules.append(stoploss_rule)
        all_sell_dates.append(today)
        self.orders_history_df.at[symbol,'Stoploss Rules'] = all_sell_rules
        self.orders_history_df.at[symbol,'Dates'] = all_sell_dates
        if(self.orders_history_df.loc[symbol,'Position Left'] < MINIMUN_SELL_POSITION_SIZE ):
            self.orders_history_df = self.orders_history_df.drop(symbol) 
            position_size = 1
        quantity_sell = size*position_size
        ts.place_order(self.ts_session,symbol,quantity_sell,buy_sell="SELL")
        # self.sell(symbol,quantity_sell)
        
    def run_strategy(self):
        try:
            market_open = self.market_open() 
            today = datetime.now()
            self.sold_symbols = []
            symbols_sell_ratings = get_sell_rating(self) 
            if(symbols_sell_ratings != None):
                for symbol in symbols_sell_ratings.items():
                    sold = False
                    days_hold = get_days_hold(symbol[0],today,self.orders_history_df) 
                    trade_return = get_position_return(self,symbol[0])#todo: check if Unrealized pl is ture
                    size = self.holdings[symbol[0]]['Quantity']
                    if(symbol[1]['rank'] >= SELL_RANK):
                        if(MINIMUN_MINUS_SELL > trade_return or trade_return > MINIMUN_SELL):
                            if(days_hold < 15):
                                if(symbol[1]['rank'] >= SELL_RANK_HARD or (symbol[1]['rank'] >= SELL_RANK and trade_return <= (-8))):
                                    sold = True
                                    self.execute_sell_order(symbol[0],size,symbol[1]['rules'])
                            elif(symbol[1]['rank'] >= SELL_RANK):
                                sold = True
                                self.execute_sell_order(symbol[0],size,symbol[1]['rules'])
                    if(not sold and (MINIMUN_MINUS_SELL > trade_return or trade_return > MINIMUN_SELL)):
                        sold = True
                        stoploss_rule = get_stoploss_rule(symbol[1]['rules'])
                        if(stoploss_rule == NO_STOPLOSS): continue
                        if(used_rule(self,symbol[0],stoploss_rule)): continue
                        self.execute_stoploss(symbol[0],size,stoploss_rule,today)
                    if(sold):
                        self.update_orders()
                        self.update_portfolio()
                if(market_open and self.queue_orders): self.wait_for_confirm_sell_order() #TODO: need to fix sell symbol, close app- enter and still wanna tobuy problem
            
            if(self.cash - self.queue_buying_money + self.queue_selling_money >= self.trade_size_cash - self.leverage_amount):
                symbols_buy_ratings = get_buy_ratings(self) 
                symbols_buy_ratings = {key:value for key, value in sorted(symbols_buy_ratings.items(), key=lambda x: x[1]['rank'],reverse=True)}
                for symbol in symbols_buy_ratings.items():
                    if((symbol[1]['rank'] >= BUY_RANK) and (self.cash - self.queue_buying_money + self.queue_selling_money >= self.trade_size_cash - self.leverage_amount) and (symbol[0] not in self.sold_symbols)):
                        if(self.is_holding_full_size(symbol[0])): continue
                        symbol_price = get_symbol_price(self,symbol[0])
                        self.execute_buy_order(symbol[0],symbol_price)
                        self.wait_for_confirm_buy_order(symbol[0])
                        self.update_orders()
                        self.update_portfolio()
            self.upload_df_to_gcloud()
        except BucketError as e:
            raise e
        except ConnectionError as e:
            raise e
        except Exception:
            _, exc_value, exc_traceback = sys.exc_info()
            error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
            line_exception = exc_traceback.tb_lineno
            cause = None
            if(exc_value.args):
                cause = exc_value.args[0]
            raise PortfolioStrategyError(line_exception,"ERROR",cause,error_file)

    def wait_for_confirm_buy_order(self, symbol): 
        finish_buy = False
        counter = 0
        while(not finish_buy):
            symbol_order = self.get_order(symbol)
            if(symbol_order == NOT_EXIST): return
            if(symbol_order['Status'] == 'Filled'):
                finish_buy = True
            else:
                time.sleep(2)
                counter = counter + 1
            if(counter >= 60):
                print(json.dumps({'message': f'After {60*2/60} minutes Order still not confirmed, Closing Strategy\nPlease check order Status',"severity": "INFO"}))
                return
        print(json.dumps({"message": f'{symbol} Order confirmed' ,"severity": "INFO"}))
        return 

    def wait_for_confirm_sell_order(self): #TODO: need to check it 
        finish_sell_orders = False
        found = False
        while(not finish_sell_orders):
            self.update_orders()
            for order in self.queue_orders.items():
                if(order[1]['Buy or Sell'] == 'Sell'):
                    found = True
                    break
            if(not found): finish_sell_orders = True
        self.update_orders()
        self.update_portfolio()

    def upload_df_to_gcloud(self):
        try:
            client = storage.Client(project=PROJECT_NAME)
            bucket = client.get_bucket(STORAGE_BUCKET_NAME)
            bucket.blob('bla').upload_from_string(self.orders_history_df.to_csv(),'text/csv')
            print(json.dumps({"message": "Successfuly Uploaded Dataframe", "severity": "INFO"}))
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            file_name = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
            line_exception = exc_traceback.tb_lineno
            cause = None
            if(exc_value.args):
                cause = exc_value.args[0]
            raise BucketError(project_name=PROJECT_NAME,bucket=STORAGE_BUCKET_NAME,severity='ERROR',line=line_exception,error_file= file_name,cause = cause)

        
    def get_cash(self): #TODO: change it to ts
        try:
            url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/balances"
            headers = {"Authorization":f'Bearer {self.ts_session["access_token"]}'}
            account_details = requests.request("GET", url, headers=headers)
            account_details = json.loads(account_details.text)
            return float(account_details['Balances'][0]['CashBalance'])
        except:
            _, exc_value, exc_traceback = sys.exc_info()
            error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
            line_exception = exc_traceback.tb_lineno
            cause = None
            if(exc_value.args):
                cause = exc_value.args[0]
            raise ConnectionError(url,line_exception,"ERROR",cause,error_file)
        
        
    def market_open(self):
        market_status = yf2.get_market_status() 
        if(market_status ==  'OPEN' or market_status == 'REGULAR'):
            return True
        return False
        
    

    def get_equity(self):
        try:
            url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/balances"
            headers = {"Authorization":f'Bearer {self.ts_session["access_token"]}'}
            account_details = requests.request("GET", url, headers=headers)
            account_details = json.loads(account_details.text)
            return float(account_details['Balances'][0]['MarketValue'])
        except:
            _, exc_value, exc_traceback = sys.exc_info()
            error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
            line_exception = exc_traceback.tb_lineno
            cause = None
            if(exc_value.args):
                cause = exc_value.args[0]
            raise ConnectionError(url,line_exception,"ERROR",cause,error_file)


    def get_holdings(self):
        holdings = {}
        try:
            url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/positions"
            headers = {"Authorization":f'Bearer {self.ts_session["access_token"]}'}
            account_details = requests.request("GET", url, headers=headers)
            account_details = json.loads(account_details.text)
            for position in account_details['Positions']:
                position_id = position["PositionID"]
                quantity = position["Quantity"]
                long_short = position["LongShort"]
                average_price = position["AveragePrice"]
                trade_yield = position["UnrealizedProfitLossPercent"]
                total_cost = position["TotalCost"]
                market_value = position["MarketValue"]
                time_stamp = position["Timestamp"]
                time_stamp = time_stamp[:10]
                time_stamp = datetime.strptime(time_stamp,'%Y-%m-%d')
                holdings[position["Symbol"]] = {"PositionID":position_id,"Quantity":quantity,"LongShort":long_short,
                    "AveragePrice":average_price,"UnrealizedProfitLossPercent":trade_yield,"TotalCost":total_cost,"MarketValue":market_value,'Timestamp':time_stamp}
            return holdings
        except Exception:
            _, exc_value, exc_traceback = sys.exc_info()
            error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
            line_exception = exc_traceback.tb_lineno
            cause = None
            if(exc_value.args):
                cause = exc_value.args[0]
            raise ConnectionError(url,line_exception,"ERROR",cause,error_file)             

    def get_orders_file(self):
        try:
            client = storage.Client(project=PROJECT_NAME)
            bucket = client.get_bucket(STORAGE_BUCKET_NAME)
            blob = bucket.blob(ORDERS_HISTORY_FILE)
            if(blob.exists()):
                self.orders_history_df = pd.read_csv(f'gs://{STORAGE_BUCKET_NAME}/{ORDERS_HISTORY_FILE}', encoding='utf-8')
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
            line_exception = exc_traceback.tb_lineno
            cause = None
            if(exc_value.args):
                cause = exc_value.args[0]
            raise BucketError(project_name=PROJECT_NAME,bucket=STORAGE_BUCKET_NAME,file_name=ORDERS_HISTORY_FILE,severity='ERROR',line=line_exception,error_file= error_file,cause = cause)

    def get_orders(self):
        try:
            url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/orders"
            headers = {"Authorization":f'Bearer {self.ts_session["access_token"]}'}
            orders_details = requests.request("GET", url, headers=headers)
            orders_details = json.loads(orders_details.text)
            return orders_details
        except:
            _, exc_value, exc_traceback = sys.exc_info()
            error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
            line_exception = exc_traceback.tb_lineno
            cause = None
            if(exc_value.args):
                cause = exc_value.args[0]
            raise ConnectionError(url,line_exception,"ERROR",cause,error_file)

    def get_order(self,symbol):
        orders = self.get_orders()
        if(orders['Orders']):
            for order in orders:
                if(order['Legs'][0]['Symbol'] == symbol):
                    return order
        return NOT_EXIST #TODO: do i need tto rasie exception?

    def update_portfolio(self):
        self.cash = self.get_cash()
        self.equity = self.get_equity()
        self.net_wealth = self.cash + self.equity
        self.holdings = self.get_holdings()
        self.trade_size_cash = TRADE_SIZE * self.net_wealth
        self.leverage_amount = LEVERAGE_SIZE * self.net_wealth

    def update_orders(self):
        try:
            queue_buy_money = 0
            queue_sell_money = 0
            orders = self.get_orders()
            for order in orders['Orders']:
                symbol = order['Legs'][0]['Symbol']
                size = order['Legs'][0]['QuantityOrdered']
                open_time = order['OpenedDateTime']
                buy_or_sell =order['Legs'][0]['BuyOrSell']
                order_type = order['OrderType']
                order_status = order['Status']
                status_description = order['StatusDescription']
                order_price = order['PriceUsedForBuyingPower']
                if(status_description == 'Queued' or status_description == 'Received' or status_description == 'Sent'):
                    self.queue_orders[symbol] = {'Quantity': size, 'Price': order_price ,'Open Time': open_time, 'Order Type': order_type,
                            'Buy or Sell': buy_or_sell,'Order Status': order_status, 'Status Description': status_description}
                    self.orders[symbol] = {'Quantity': size, 'Price': order_price ,'Open Time': open_time, 'Order Type': order_type,
                            'Buy or Sell': buy_or_sell, 'Order Status': order_status, 'Status Description': status_description}

                    if(buy_or_sell == 'Buy'):
                        queue_buy_money = queue_buy_money + (int(size) * float(order_price))  

                    if(buy_or_sell == 'Sell'):
                        queue_sell_money = queue_sell_money + (int(size) * float(order_price))  
                elif(status_description == 'Filled'):
                    self.filled_orders[symbol] = {'Quantity': size, 'Filled Price': order['FilledPrice'] ,'Open Time': open_time, 'Order Type': order_type,
                            'Buy or Sell': buy_or_sell, 'Order Status': order_status, 'Status Description': status_description}
                    self.orders[symbol] = {'Quantity': size, 'Filled Price': order['FilledPrice'] ,'Open Time': open_time, 'Order Type': order_type,
                            'Buy or Sell': buy_or_sell, 'Order Status': order_status, 'Status Description': status_description}
                else:
                    self.orders[symbol] = {'Quantity': size, 'Price': order_price ,'Open Time': open_time, 'Order Type': order_type,
                            'Order Status': order_status, 'Status Description': status_description}
                self.queue_buying_money = queue_buy_money
                self.queue_selling_money = queue_sell_money
        except:
            _, exc_value, exc_traceback = sys.exc_info()
            error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
            line_exception = exc_traceback.tb_lineno
            cause = None
            if(exc_value.args):
                cause = exc_value.args[0]
            raise UpdatePortfolioError(line_exception,"ERROR",cause,error_file)

    def is_holding(self,symbol):
        for ticker in self.holdings.items():
            if(ticker[0] == symbol): return True
        for order in self.queue_orders.items():
            if(order[0] == symbol): return True
        return False

    def is_holding_full_size(self,symbol):
        if(self.is_holding(symbol)):
            if(symbol not in self.orders_history_df.index): return True
        return False

    def update_orders_df(self,ticker,dates,position_size=None,sell_rules=None):
        self.orders_history_df[ticker] =  {"Dates":dates,"Position Left":position_size,"Stoploss Rules": sell_rules}

def get_buy_ratings(self:Portfolio):
    try:
        rating = {}
        market_rank = 0
        for etf in self.etfs_to_buy:
            symbol_data_day = pd.DataFrame(yf.download(tickers=etf, period='5y',interval='1d',progress=False)).dropna()
            symbol_data_month = pd.DataFrame(yf.download(tickers=etf, period='5y',interval='1mo',progress=False)).dropna()
            symbol_data_weekly = pd.DataFrame(yf.download(tickers=etf, period='5y',interval='1wk',progress=False)).dropna()
            rating[etf] = buy_rate(self,symbol_data_month,symbol_data_weekly,symbol_data_day,etf,market_rank)
        return rating
    except:
        _, exc_value, exc_traceback = sys.exc_info()
        error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
        line_exception = exc_traceback.tb_lineno
        cause = None
        if(exc_value.args):
            cause = exc_value.args[0]
        raise YhaooDownloadDataError(etf,line_exception,"ERROR",cause,error_file)

def get_sell_rating(self:Portfolio):
    try:
        rating = {}
        market_rank = 0
        if(not self.holdings):
            return None
        for symbol in self.holdings.items():
            symbol_data_day = pd.DataFrame(yf.download(tickers=symbol[0], period='5y',interval='1d',progress=False)).dropna()
            symbol_data_month = pd.DataFrame(yf.download(tickers=symbol[0], period='5y',interval='1mo',progress=False)).dropna()
            symbol_data_weekly = pd.DataFrame(yf.download(tickers=symbol[0], period='5y',interval='1wk',progress=False)).dropna()
            rating[symbol[0]] = sell_rate(self,symbol_data_month,symbol_data_weekly,symbol_data_day,symbol[0],market_rank)
        return rating
    except:
        _, exc_value, exc_traceback = sys.exc_info()
        error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
        line_exception = exc_traceback.tb_lineno
        cause = None
        if(exc_value.args):
            cause = exc_value.args[0]
        raise YhaooDownloadDataError(symbol[0],line_exception,"ERROR",cause,error_file)


def buy_rate(self:Portfolio,data_monthly:pd.DataFrame,data_weekly:pd.DataFrame,data_day:pd.DataFrame,etf,market_rank):
    #TODO: last day line 397 need to check diffrence when market is open!
    rank = 0
    # rank += market_rank
    today = date.today()
    buy_rules = []
    buy_ret = {'rank':rank,'rules': buy_rules}
    seq_daily = SequenceMethod(data_day,'day',today)
    seq_weekly = SequenceMethod(data_weekly,'weekly',today)
    seq_month = SequenceMethod(data_monthly,'monthly',today)
    last_5_days = today - timedelta(days=12)
    last_5_days = data_day.truncate(before=last_5_days, after=today)
    if(last_5_days.shape[0] >=5 ): last_5_days = last_5_days.tail(last_5_days.shape[0] - (last_5_days.shape[0] - 5)) 
    if(self.market_open()):last_day = last_5_days.tail(2).head(1) #TODO: need tothink if this is what i want
    else: last_day = last_5_days.tail(1)
    last_seq_date = seq_daily.get_seq_df()['Date'].iloc[-1]
    data_day['SMA13'] = data_day['Close'].rolling(window=13).mean()
    data_day['SMA5'] = data_day['SMA13'].rolling(window=5).mean()
    data_weekly['SMA13'] = data_weekly['Close'].rolling(window=13).mean()
    data_weekly['SMA5'] = data_weekly['SMA13'].rolling(window=5).mean()
    data_monthly['SMA13'] = data_monthly['Close'].rolling(window=13).mean()
    data_monthly['SMA5'] = data_monthly['SMA13'].rolling(window=5).mean()
    data_day = data_day.dropna()
    data_weekly = data_weekly.dropna()
    data_monthly = data_monthly.dropna()
    month = today.replace(day=1)
    pre_week = today - timedelta(days=7*4)
    last_month = month - timedelta(days=1) 
    last_month = last_month.replace(day = 1)
    three_months_back = today.replace(day =1)
    for i in range(3):
        three_months_back = three_months_back - timedelta(days=1)
        three_months_back = three_months_back.replace(day = 1)

    if(float(last_day.loc[str(last_day.index[-1]),'Close']) > float(data_day.loc[str(last_day.index[-1]),'SMA13']) and check_seq_by_date_daily_equal(seq_daily.get_seq_df(),today) == 1
         and (last_day.index[-1].date() - last_seq_date).days == 0):
        rank += 5
        buy_rules.append('2')

    if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),today) == 1):
        rank += 1
        buy_rules.append('3')
    else :
        buy_ret['rank'] = rank
        buy_ret['rules'] = buy_rules
        return buy_ret
    if(check_seq_by_date_monthly(seq_month.get_seq_df(),today) == 1):
        rank += 2
        buy_rules.append('4')
    #TODO: nned to heck by backtesting what is the best match
    if(data_day.loc[str(last_day.index[-1]),'SMA13'] > data_day.loc[str(last_day.index[-1]),'SMA5'] and data_day.loc[str(last_5_days.head(2).tail(1).index[-1]),'SMA13'] > data_day.loc[str(last_5_days.head(2).tail(1).index[-1]),'SMA5']):
        rank += 1 
        buy_rules.append('5')
    if(data_monthly.loc[str(last_month),'SMA13'] > data_monthly.loc[str(last_month),'SMA5']):
        rank += 1
        buy_rules.append('6')
    if(is_moving_away_weekly(data_weekly,today,pre_week)):
        rank += 1
        buy_rules.append('7')
    if(is_moving_away_monthly(data_monthly,last_month,three_months_back)):
        rank += 1
        buy_rules.append('8')

    buy_ret['rank'] = rank
    buy_ret['rules'] = buy_rules
    return buy_ret


def sell_rate(self: Portfolio,data_monthly:pd.DataFrame,data_weekly:pd.DataFrame,data_day:pd.DataFrame,symbol,market_rank):
    rank = 0
    sell_rules = []
    # rank = rank + (market_rank*(-1))
    today = date.today()
    sell_ret = {'rank':rank,'rules': sell_rules}
    seq_daily = SequenceMethod(data_day,'day',today)
    seq_weekly = SequenceMethod(data_weekly,'weekly',today)
    seq_month = SequenceMethod(data_monthly,'monthly',today)
    last_5_days = today - timedelta(days=12)
    last_5_days = data_day.truncate(before=last_5_days, after=today)
    if(last_5_days.shape[0] >=5 ): last_5_days = last_5_days.tail(last_5_days.shape[0] - (last_5_days.shape[0] - 5)) 
    if(self.market_open()):last_day = last_5_days.tail(2).head(1)
    else: last_day = last_5_days.tail(1)
    trade_yield = float(self.holdings[symbol]['UnrealizedProfitLossPercent'])
    data_day['SMA13'] = data_day['Close'].rolling(window=13).mean()
    data_day['SMA5'] = data_day['SMA13'].rolling(window=5).mean()
    data_weekly['SMA13'] = data_weekly['Close'].rolling(window=13).mean()
    data_weekly['SMA5'] = data_weekly['SMA13'].rolling(window=5).mean()
    data_monthly['SMA13'] = data_monthly['Close'].rolling(window=13).mean()
    data_monthly['SMA5'] = data_monthly['SMA13'].rolling(window=5).mean()
    data_day = atr_calculate(data_day)
    data_weekly = atr_calculate(data_weekly)
    data_monthly = atr_calculate(data_monthly)
    data_day['ATRP'] = (data_day['ATR']/data_day['Close'])*100
    data_weekly['ATRP'] = (data_weekly['ATR']/data_weekly['Close'])*100
    data_monthly['ATRP'] = (data_monthly['ATR']/data_monthly['Close'])*100
    data_day = data_day.dropna()
    data_weekly = data_weekly.dropna()
    data_monthly = data_monthly.dropna()
    month = today.replace(day=1)
    last_month = month - timedelta(days=1) 
    last_month = last_month.replace(day = 1)
    if(float(last_day.loc[str(last_day.index[-1]),'Close']) < float(data_day.loc[str(last_day.index[-1]),'SMA13']) and check_seq_by_date_daily_equal(seq_daily.get_seq_df(),today) == -1):
        rank += 5
        sell_rules.append("2")
    
    if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),today) == -1):
        rank += 1
        sell_rules.append("3")
        if(check_seq_by_date_weekly_previous(seq_weekly.get_seq_df(),today) == -1):
            rank += 1
            sell_rules.append("3a")
    if(check_seq_by_date_monthly(seq_month.get_seq_df(),today) == -1):
        rank += 2
        sell_rules.append("4")
    if(data_monthly.loc[str(last_month),'SMA13'] < data_monthly.loc[str(last_month),'SMA5']):
        rank += 1
        sell_rules.append("5")
    if(float(data_day[symbol].loc[str(today),'ATRP'])*7 <= trade_yield):
        sell_rules.append('6')
    elif(float(data_day[symbol].loc[str(today),'ATRP'])*5 <= trade_yield):
        sell_rules.append('7')
    elif(float(data_day[symbol].loc[str(today),'ATRP'])*4 <= trade_yield):
        sell_rules.append('8')
    elif(float(data_day[symbol].loc[str(today),'ATRP'])*3 <= trade_yield):
        sell_rules.append('9')

    sell_ret['rank'] = rank
    sell_ret['rules'] = sell_rules
    return sell_ret


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

def get_days_hold(symbol,today,orders_history):
    try:
        dates_buy = list(orders_history.loc[symbol[0],'Dates'])
        days_hold = (today - dates_buy[0]).days
        return days_hold
    except:
        _, exc_value, exc_traceback = sys.exc_info()
        error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
        line_exception = exc_traceback.tb_lineno
        cause = None
        if(exc_value.args):
            cause = exc_value.args[0]
        raise DataFrameError(line_exception,cause,error_file)

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
    # return seq.iloc[-1]['Sequence'] #TODO: Should work instead of for loop
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] < date):
            previous_row = row
            first = False
        else: break
    if(first): return 0
    return int(previous_row['Sequence'])

def check_seq_by_date_weekly_previous(seq,date):
   return int(seq.iloc[-2]['Sequence'])

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

def check_seq_by_date_daily_equal(seq,date):
    previous_row = 0
    first = True
    for index,row in seq.iterrows():
        if(row["Date"] <= date):
            previous_row = row
            first = False
        else: break
    if(first): return 0
    return int(previous_row['Sequence'])


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

def print_order(status):
    try:
        print(f"Error Type: {status['Error']}\nError Message: {status['Message']}\nProgram was stopped")
        return ERROR_ORDER
    except:
        print(status['Orders'][0]['Message'])
        return SUCCESS

def get_symbol_price(self,symbol):
    try:
        url = f"https://api.tradestation.com/v3/marketdata/quotes/{symbol}"
        headers = {
            "content-type": "application/json",
            "Authorization": f'Bearer {self.ts_session["access_token"]}'
        }

        response = requests.request("GET", url, headers=headers)
        response =  json.loads(response.text)
        return float(response['Quotes'][0]['Last'])
    except:
        _, exc_value, exc_traceback = sys.exc_info()
        error_file = os.path.basename(exc_traceback.tb_frame.f_code.co_filename)
        line_exception = exc_traceback.tb_lineno
        cause = None
        if(exc_value.args):
            cause = exc_value.args[0]
        raise ConnectionError(url,line_exception,"ERROR",cause,error_file)

def get_last_price(self,symbol):
    try:
        url = f"https://api.tradestation.com/marketdata/stream/quotes/{symbol}"
        headers = {"Authorization":f'Bearer {self.ts_session["access_token"]}'}
        symbol_details = requests.request("GET", url, headers=headers)
        symbol_details = json.loads(symbol_details.text)
        return float(symbol_details['Last'])
    except Exception:
        print(f"CONNECTION problem with TradeStation, accured while tried to check account balances, Details: \n {traceback.format_exc()}")
        return None

def get_position_return(self: Portfolio,symbol):
    position_id = get_position_id(self,symbol)
    position = ts.get_position_by_id(self.ts_session,position_id)
    unrealized_return = position["UnrealizedProfitLossPercent"]
    return float(unrealized_return)

def get_position_id(self: Portfolio,symbol):
    for position in self.holdings.items():
        if(position[0] == symbol):
            return position[1]['PositionID']
    raise NotExist("Do not found symbol id in holdings",691,"portfolio.py")

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

def used_rule(self: Portfolio,symbol,stoploss_rule):
    # if(not pd.isna(past_sell_rules)): #TODO: do i really need it?
    if(symbol in self.orders_history_df.index): #?its mean first time selling this ticker
        past_sell_rules = self.orders_history_df.loc[symbol,"Stoploss Rules"]
        if(stoploss_rule in past_sell_rules): return True
    return False

def atr_calculate(data):
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1).dropna()
    atr = true_range.rolling(14).sum()/14
    data['ATR'] = atr
    return data

# columns=['Dates','Ticker','Position','Buy Rules','Stoploss Rules'])
    
# # self.symbols_basket =  ['IYZ','XLY','XHB', 'PEJ','XLP','XLC','PBJ','XLE','XES','ICLN','XLF','KIE','KCE','KRE','XLV','PPH','XLI','IGF',
#                 'XLK','FDN','XLU','FIW','FAN','XLRE','XLB','PYZ','XME','HAP','MXI','IGE','MOO','WOOD','COPX','FXZ','URA','LIT']
# self.etfs_xlc = ['XLC','FIVG','IYZ','VR']
# self.etfs_xly = ['XLY','XHB', 'PEJ', 'IBUY','BJK','BETZ''AWAY','SOCL','BFIT','KROP']
# self.etfs_xlp = ['XLP','FTXG','KXI','PBJ']
# self.etfs_xle = ['XLE','XES','CNRG','FTXN','SOLR','ICLN']
# self.etfs_xlf = ['XLF','KIE','KCE','KRE']
# self.etfs_xlv = ['XLV','XHE','XHS','GNOM','HTEC','PPH','AGNG','EDOC']
# self.etfs_xli = ['XLI','AIRR','IFRA','IGF','SIMS']
# self.etfs_xlk = ['XLK','HERO','FDN','IRBO','FINX','IHAK','SKYY','SNSR']
# self.etfs_xlu = ['XLU','RNRG','FIW','FAN']
# self.etfs_xlre = ['XLRE','KBWY','SRVR','VPN','GRNR'] #VPN, GRNR
# self.etfs_xlb = ['XLB','PYZ','XME','HAP','MXI','IGE','MOO','WOOD','COPX','FXZ','URA','LIT']


# today = datetime.now()
# orders_history_df = pd.DataFrame(columns=['Dates','Buy\Sell','Ticker','Position Left','Buy\Sell Price','Stoploss Rules'])
# orders_history_df = orders_history_df.set_index('Ticker')
# dates= []
# sell_rules = ['6','7','8']
# new_sell_rules = []
# rule = '9'
# dates.append(today)
# new_row= {"Dates":dates,"Position Left":220}
# orders_history_df.loc['AAPL'] = new_row
# new_row2= {"Dates":dates,"Position Left":0.75,"Stoploss Rules":sell_rules}
# orders_history_df.loc['TSLA'] = new_row2
# dates_buy = orders_history_df.loc["TSLA",'Dates']
# diff = (today-dates_buy[0]).days
# print(orders_history_df)
# position_size = 0.5
# orders_history_df.loc['TSLA','Position Left'] = orders_history_df.loc['TSLA','Position Left'] - position_size
# print(orders_history_df)
# position_size = orders_history_df.loc['TSLA','Position Left']
# print(orders_history_df)
# print(position_size)
# sell_rules = list(orders_history_df.loc['TSLA','Stoploss Rules'])
# sell_rules.append(rule)
# if('MSFT' not in orders_history_df):
#     orders_history_df.loc['MSFT'] = {}
# orders_history_df.at['MSFT','Stoploss Rules'] = sell_rules
# print(orders_history_df)
# print((orders_history_df.loc['TSLA','Stoploss Rules']))


# ck1 = orders_history_df.loc['TSLA','Stoploss Rules']
# if('MSA' in orders_history_df.index):
#     ck2 = orders_history_df.loc['MSA','Stoploss Rules']
# if(not pd.isna(ck1)):
#     print(ck1)
# print(ck2)
# print('BLA')


  # days_hold = (today - self.holdings[symbol[0]]['Timestamp']).days #TODO: need to check if timestamp is from first buying