import yahoo_fin.stock_info as yf2
from sequencing import *
import talib as ta
import requests
import json
import traceback
import time
import tkinter as tk
from tkinter import messagebox
import gcsfs
from google.cloud import storage
from google.cloud import logging


ACCOUNT_ID = 11509188
STARTING_AMOUNT = 1000000
BUY_RANK = 6
SELL_RANK = 5
SELL_RANK_HARD = 9
TRADE_SIZE = 0.25
LEVERAGE_SIZE = 0.01
SUCCESS = 1
FAILED_ORDER = -1
FAIL = 0
ERROR_ORDER = -1
NO_STOPLOSS = 0
ORDERS_HISTORY_FILE = 'orders_history.csv'
STORAGE_BUCKET_NAME = 'backtesting_results'
PROJECT_NAME = 'orbital-expanse-368511'



class LogHandler:
  def __init__(self):
    self.log_client = logging.Client()

  def error(self, message):
    log_name = "errors"
    logger = self.log_client.logger(log_name)
    logger.log_text(message, severity="ERROR")

  def warning(self, message):
    log_name = "warnings"
    logger = self.log_client.logger(log_name)
    logger.log_text(message, severity="WARNING")

  def info(self, message):
    log_name = "info"
    logger = self.log_client.logger(log_name)
    logger.log_text(message, severity="INFO")

########IMPLIMATION EXAMPLE##########
# logger = LogHandler()
# logger.error("This is an error message.")
# logger.warning("This is a warning message.")
# logger.info("This is an info message.")

class Portfolio:

    def __init__(self,trade_station,market_sentiment,sectors_sentiment):
        self.trade_station = trade_station
        self.cash = self.get_cash()
        self.starting_amount = STARTING_AMOUNT
        self.equity = self.get_equity()
        self.net_wealth = self.cash + self.equity
        self.holdings = self.get_holdings()
        self.orders_history = self.get_orders_history()
        self.trade_size_cash = TRADE_SIZE * self.net_wealth
        self.leverage_amount = LEVERAGE_SIZE * self.net_wealth
        self.queue_buying_money = 0
        self.queue_selling_money = 0
        self.orders = {}
        self.queue_orders = {}
        self.filled_orders = {}
        self.market_sentiment = market_sentiment
        self.sectors_sentiment = sectors_sentiment
        self.etfs_to_buy = ['XLK','XLV','XLE','XLC','XLRE','XLU','SPY','QQQ','DIA','NOBL','DVY','DXJ','GLD','SMH',
                    'TLT','XBI','EEM','XHB','XRT','XLY','VGK','XOP','VGT','FDN','HACK','SKYY','KRE','XLF','XLB']
        self.update_orders()
    
    def get_start_amount(self):
        return self.starting_amount
        
    def run_buy_and_sell_strategy(self,automate):
        message =  tk.Tk()
        message.geometry("250x250")
        market_open = self.market_open()
        answer = True
        today = datetime.now()
        sold_symbols = []
        symbols_sell_ratings = get_sell_rating(self)
        if(symbols_sell_ratings != None):
            for symbol in symbols_sell_ratings.items():
                if(symbol[1]['rank'] >= SELL_RANK):
                    size = self.holdings[symbol[0]]['Quantity']
                    days_hold = (today - self.holdings[symbol[0]]['Timestamp']).days #TODO: need to check if timestamp is from first buying
                    selling_price = get_symbol_price(symbol[0])
                    trade_return = (selling_price - self.holdings[symbol[0]]['AveragePrice'])/self.holdings[symbol[0]]['AveragePrice']*100
                    if(-1 > trade_return or trade_return > 1): #TODO: need to check by backtesting
                        if(days_hold < 15):
                            if(symbol[1]['rank'] >= SELL_RANK_HARD or (symbol[1]['rank'] >= SELL_RANK and trade_return <= (-8))):
                                sold_symbols.append(symbol[0])
                                sold = True
                                # self.place_sell_order(symbol[0],selling_date,selling_price,symbol[1]['rules'],position_size)
                        elif(symbol[1]['rank'] >= SELL_RANK):
                            sold_symbols.append(symbol[0])
                            sold = True
                            # self.place_sell_order(symbol[0],selling_date,selling_price,symbol[1]['rules'],position_size)
                    if(not sold):
                        stoploss_rule = get_stoploss_rule(symbol[1]['rules'])
                        if(stoploss_rule == NO_STOPLOSS): continue
                        if('stoploss_rules' not in self.holdings[symbol[0]]):
                            self.holdings[symbol[0]]['stoploss_rules'] = []
                        if(stoploss_rule in self.holdings[symbol[0]]['stoploss_rules']): continue
                        self.holdings[symbol[0]]['stoploss_rules'].append(stoploss_rule)
                        position_size = sell_rule_to_position_size(stoploss_rule)
                        sold_symbols.append(symbol[0])
                        # self.place_sell_order(symbol[0],selling_date,selling_price,symbol[1]['rules'],position_size)
                    if(not automate): answer = messagebox.askyesno('Order Confirmation',f"Selling {size} of {symbol[0]}\nAre You Confirm?")
                    if answer:
                        sold_symbols.append(symbol[0])
                        if(self.sell(symbol[0],size) != SUCCESS):
                            message.destroy()
                            return
                        self.update_orders()
                        self.update_portfolio()
            if(market_open and self.queue_orders): self.wait_for_confirm_sell_order() #TODO: need to fix sell symbol, close app- enter and still wanna tobuy problem
        
        if(self.cash - self.queue_buying_money + self.queue_selling_money >= self.trade_size_cash - self.leverage_amount):
            symbols_buy_ratings = get_buy_ratings(self)
            symbols_buy_ratings = {key:value for key, value in sorted(symbols_buy_ratings.items(), key=lambda x: x[1]['rank'],reverse=True)}
            for symbol in symbols_buy_ratings.items():
                if((symbol[1]['rank'] >= BUY_RANK) and (not self.is_holding(symbol[0])) and (self.cash - self.queue_buying_money + self.queue_selling_money >= self.trade_size_cash - self.leverage_amount) and (symbol[0] not in sold_symbols)):
                    size = int(self.trade_size_cash / float(symbol[1]['price']))
                    answer = messagebox.askyesno('Order Confirmation',f"Buying {size} of {symbol[0]}\nAre You Confirm?")
                    if answer:
                        if(self.buy(symbol[0], size) != SUCCESS):
                            message.destroy()
                            return
                        if(market_open):
                            if(self.wait_for_confirm_buy_order(symbol[0], size) != SUCCESS):
                                message.destroy()
                                return
                        self.update_orders()
                        self.update_portfolio()
        message.destroy()

    def wait_for_confirm_buy_order(self, symbol, size): #TODO: I can do it also with order info - Filled 
        finish_buy = False
        counter = 0
        while(not finish_buy and counter < 10):
            self.holdings = self.get_holdings()
            if(self.is_holding(symbol)):
                if(self.holdings[symbol]['Quantity'] == size):
                    finish_buy = True
            time.sleep(2)
            counter += 1
        if(counter == 10):
            print(f'{symbol}: Order still not confirmed, Closing Strategy\nPlease check order Status')
            return FAILED_ORDER
        print(f'{symbol} Order confirmed')
        return SUCCESS

    def wait_for_confirm_sell_order(self): 
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

    def wait_for_confirm_sell_order_old(self, symbol):
        finish_sell = False
        counter = 0
        while(not finish_sell and counter < 10):
            self.holdings = self.get_holdings()
            if(not self.is_holding(symbol)):
                    finish_sell = True
            time.sleep(2)
            counter += 1
        if(counter == 10):
            print(f'{symbol}: Order still not confirmed, Closing Strategy\nPlease check order Status')
            return FAILED_ORDER
        print(f'{symbol} Order confirmed')
        return SUCCESS
        
    def get_cash(self):
        try:
            url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/balances"
            headers = {"Authorization":f'Bearer {self.trade_station.TOKENS.access_token}'}
            account_details = requests.request("GET", url, headers=headers)
            account_details = json.loads(account_details.text)
            if(int(account_details['Balances'][0]['AccountID']) == ACCOUNT_ID):
                return float(account_details['Balances'][0]['CashBalance'])
            else: 
                print("PROBLEM WITH FINDING YOUR TRADE STATION ACCOUNT - PROBLEM ACCURED IN 'get_cash' function")
                return 0
        except Exception:
            print(f"CONNECTION problem with TradeStation, accured while tried to check account balances, Details: \n {traceback.format_exc()}")
            return 0
        
        
    def market_open(self):
        market_status = yf2.get_market_status() 
        if(market_status ==  'OPEN' or market_status == 'REGULAR'):
            return True
        return False
        
    

    def get_equity(self):
        try:
            url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/balances"
            headers = {"Authorization":f'Bearer {self.trade_station.TOKENS.access_token}'}
            account_details = requests.request("GET", url, headers=headers)
            account_details = json.loads(account_details.text)
            if(int(account_details['Balances'][0]['AccountID']) == ACCOUNT_ID):
                return float(account_details['Balances'][0]['MarketValue'])
            else: 
                print("PROBLEM WITH FINDING YOUR TRADE STATION ACCOUNT - PROBLEM ACCURED IN 'get_equity' function")
                return 0
        except Exception:
            print(f"CONNECTION problem with TradeStation, accured while tried to check account balances, Details: \n {traceback.format_exc()}")
            return 0

    def get_last_price(self,symbol):
        try:
            url = f"https://api.tradestation.com/marketdata/stream/quotes/{symbol}"
            headers = {"Authorization":f'Bearer {self.trade_station.TOKENS.access_token}'}
            symbol_details = requests.request("GET", url, headers=headers)
            symbol_details = json.loads(symbol_details.text)
            return float(symbol_details['Last'])
        except Exception:
            print(f"CONNECTION problem with TradeStation, accured while tried to check account balances, Details: \n {traceback.format_exc()}")
            return None

    def get_holdings(self):
        holdings = {}
        try:
            url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/positions"
            headers = {"Authorization":f'Bearer {self.trade_station.TOKENS.access_token}'}
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
            print(f"CONNECTION problem with TradeStation, accured while tried to check account balances, Details: \n {traceback.format_exc()}")
            return holdings             

    def get_orders_history():
        client = storage.Client(project=PROJECT_NAME)
        bucket = client.get_bucket(STORAGE_BUCKET_NAME)
        blob = bucket.blob(ORDERS_HISTORY_FILE)
        if(blob.exists()):
            return pd.read_csv(f'gs://{STORAGE_BUCKET_NAME}/{ORDERS_HISTORY_FILE}', encoding='utf-8')
        else:
            message = "Could Not Reading Orders History csv file, please check why "
            print(json.dumps({"message": message, "severity": "WARNING"}))
            # exit(1)#TODO: need to keep the while loop running! 0_0 
            orders_history_df = pd.DataFrame(columns=['Date','Buy\Sell','Ticker','Position','Buy\Sell Price','Buy Rules','Sell Rules'])
            bucket.blob(ORDERS_HISTORY_FILE).upload_from_string(orders_history_df,'text/csv')
            print(json.dumps({"message": "Uploaded Empty Dataframe file", "severity": "INFO"}))

    def get_orders(self):
        url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/orders"
        headers = {"Authorization":f'Bearer {self.trade_station.TOKENS.access_token}'}
        orders_details = requests.request("GET", url, headers=headers)
        orders_details = json.loads(orders_details.text)
        return orders_details

    def update_portfolio(self):
        self.cash = self.get_cash()
        self.equity = self.get_equity()
        self.net_wealth = self.cash + self.equity
        self.holdings = self.get_holdings()
        self.trade_size_cash = TRADE_SIZE * self.net_wealth
        self.leverage_amount = LEVERAGE_SIZE * self.net_wealth

    def update_orders(self):
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

    def is_holding(self,symbol):
        for ticker in self.holdings.items():
            if(ticker[0] == symbol): return True
        for order in self.queue_orders.items():
            if(order[0] == symbol): return True
        return False


    def buy(self,symbol,quantity,order_type='Market'):
        #order_type = "Limit" "StopMarket" "Market" "StopLimit"
        #"TimeInForce": {"Duration": "DAY"\ 'GTC'
        url = "https://api.tradestation.com/v3/orderexecution/orders"
        payload = {
            "AccountID": f"{ACCOUNT_ID}",
            "Symbol": f"{symbol}",
            "Quantity": f"{quantity}",
            "OrderType": f"{order_type}",
            "TradeAction": "BUY",
            "TimeInForce": {"Duration": "GTC"},#!need to check how to put just daily order
            "Route": "Intelligent"
        }
        headers = {
            "content-type": "application/json",
            "Authorization": f'Bearer {self.trade_station.TOKENS.access_token}'
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        response =  json.loads(response.text)

        try:
            print(f"Error Type: {response['Error']}\nError Message: {response['Message']}\nProgram was stopped")
            return ERROR_ORDER
        except:
            print(response['Orders'][0]['Message'])
            return SUCCESS

    def sell(self,symbol,quantity,order_type='Market'):
        #order_type = "Limit" "StopMarket" "Market" "StopLimit"
        url = "https://api.tradestation.com/v3/orderexecution/orders"
        payload = {
            "AccountID": f"{ACCOUNT_ID}",
            "Symbol": f"{symbol}",
            "Quantity": f"{quantity}",
            "OrderType": f"{order_type}",
            "TradeAction": "SELL",
            "TimeInForce": {"Duration": "GTC"}, #!need to check how to put just daily order
            "Route": "Intelligent"
        }
        headers = {
            "content-type": "application/json",
            "Authorization": f'Bearer {self.trade_station.TOKENS.access_token}'
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        response =  json.loads(response.text)

        try:
            print(f"Error Type: {response['Error']}\nError Message: {response['Message']}\nProgram was stopped")
            return ERROR_ORDER
        except:
            print(response['Orders'][0]['Message'])
            return SUCCESS

def get_buy_ratings(self):
    rating = {}
    market_rank = 0
    if(self.market_sentiment != None): market_rank = self.market_sentiment.get_sentiment_score()
    for etf in self.etfs_to_buy:
        symbol_data_day = pd.DataFrame(yf.download(tickers=etf, period='max',interval='1d',progress=False)).dropna()
        symbol_data_month = pd.DataFrame(yf.download(tickers=etf, period='max',interval='1mo',progress=False)).dropna()
        symbol_data_weekly = pd.DataFrame(yf.download(tickers=etf, period='max',interval='1wk',progress=False)).dropna()
        rating[etf] = buy_rate(self,symbol_data_month,symbol_data_weekly,symbol_data_day,etf,market_rank)
    return rating

def get_sell_rating(self):
    rating = {}
    market_rank = 0
    if(self.market_sentiment != None): market_rank = self.market_sentiment.get_sentiment_score()
    if(not self.holdings):
        return None
    for symbol in self.holdings.items():
        symbol_data_day = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1d',progress=False)).dropna()
        symbol_data_month = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1mo',progress=False)).dropna()
        symbol_data_weekly = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1wk',progress=False)).dropna()
        rating[symbol[0]] = sell_rate(self,symbol_data_month,symbol_data_weekly,symbol_data_day,symbol[0],market_rank)
    return rating


def buy_rate(self,data_monthly,data_weekly,data_day,etf,market_rank):
    #TODO: last day line 397 need to check diffrence when market is open!
    rank = 0
    # rank += market_rank
    today = date.today()
    buy_rules = []
    buy_ret = {'rank':rank,'rules': buy_rules,'price': 0}
    seq_daily = SequenceMethod(data_day,'day',today)
    seq_weekly = SequenceMethod(data_weekly,'weekly',today)
    seq_month = SequenceMethod(data_monthly,'monthly',today)
    avg_weekly_move = seq_weekly.get_avg_up_return()
    start_move_price = check_seq_price_by_date_weekly(seq_weekly.get_seq_df(),today)
    last_5_days = today - timedelta(days=12)
    last_5_days = data_day.truncate(before=last_5_days, after=today)
    if(last_5_days.shape[0] >=5 ): last_5_days = last_5_days.tail(last_5_days.shape[0] - (last_5_days.shape[0] - 5)) 
    print(last_5_days)
    if(self.market_open()):last_day = last_5_days.tail(2).head(1) #TODO: need tothink if this is what i want
    else: last_day = last_5_days.tail(1)
    print(last_day)
    last_seq_date = seq_daily.get_seq_df()['Date'].iloc[-1]
    daily_price =  get_symbol_price(self,etf)
    if(daily_price != None and start_move_price != None): move_return = (daily_price - start_move_price)/start_move_price*100
    else: move_return = None
    data_day['SMA13'] = ta.SMA(data_day['Close'],timeperiod=13)
    data_day['SMA5'] = ta.SMA(data_day['SMA13'], timeperiod=5)
    data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
    data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
    data_monthly['SMA13'] = ta.SMA(data_monthly['Close'],timeperiod=13)
    data_monthly['SMA5'] = ta.SMA(data_monthly['SMA13'], timeperiod=5)
    data_day = data_day.dropna()
    data_weekly = data_weekly.dropna()
    data_monthly = data_monthly.dropna()
    month = today.replace(day=1)
    pre_week = today - timedelta(days=7*4)
    last_month = month - timedelta(days=1) 
    last_month = last_month.replace(day = 1)
    pre_month = today.replace(day =1)
    for i in range(3):
        pre_month = pre_month - timedelta(days=1)
        pre_month = pre_month.replace(day = 1)

    if(float(last_day.loc[str(last_day.index[-1]),'Close']) > float(data_day.loc[str(last_day.index[-1]),'SMA13']) and check_seq_by_date_daily_equal(seq_daily.get_seq_df(),today) == 1
         and (last_day.index[-1].date() - last_seq_date).days == 0):
        rank += 5
        buy_rules.append('2')

    if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),today) == 1):
        rank += 1
        buy_rules.append('3')
    else :
        buy_ret['rank'] = rank
        buy_ret['price'] = daily_price
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
    if(is_moving_away_monthly(data_monthly,last_month,pre_month)):
        rank += 1
        buy_rules.append('8')
    # if(move_return != None and move_return <= avg_weekly_move/2): #was 2.5
    #     rank += 1
    #     buy_rules.append('9')

    buy_ret['rank'] = rank
    buy_ret['price'] = daily_price
    buy_ret['rules'] = buy_rules
    return buy_ret


def sell_rate(self,data_monthly,data_weekly,data_day,symbol,market_rank):
    rank = 0
    sell_rules = []
    # rank = rank + (market_rank*(-1))
    today = date.today()
    sell_ret = {'rank':rank,'rules': sell_rules}
    seq_daily = SequenceMethod(data_day,'day',today)
    seq_weekly = SequenceMethod(data_weekly,'weekly',today)
    seq_month = SequenceMethod(data_monthly,'monthly',today)
    avg_weekly_move = seq_weekly.get_avg_up_return()
    last_5_days = today - timedelta(days=12)
    last_5_days = data_day.truncate(before=last_5_days, after=today)
    if(last_5_days.shape[0] >=5 ): last_5_days = last_5_days.tail(last_5_days.shape[0] - (last_5_days.shape[0] - 5)) 
    print(last_day)
    if(self.market_open()):last_day = last_5_days.tail(2).head(1)
    else: last_day = last_5_days.tail(1)
    print(last_day)
    daily_price =  get_symbol_price(self,symbol)
    trade_yield = float(self.holdings[symbol]['UnrealizedProfitLossPercent'])
    data_day['SMA13'] = ta.SMA(data_day['Close'],timeperiod=13)
    data_day['SMA5'] = ta.SMA(data_day['SMA13'], timeperiod=5)
    data_weekly['SMA13'] = ta.SMA(data_weekly['Close'],timeperiod=13)
    data_weekly['SMA5'] = ta.SMA(data_weekly['SMA13'], timeperiod=5)
    data_monthly['SMA13'] = ta.SMA(data_monthly['Close'],timeperiod=13)
    data_monthly['SMA5'] = ta.SMA(data_monthly['SMA13'], timeperiod=5)
    data_day["ATR"] = ta.ATR(data_day['High'], data_day['Low'], data_day['Close'], timeperiod=14)
    data_weekly["ATR"] = ta.ATR(data_weekly['High'], data_weekly['Low'], data_weekly['Close'], timeperiod=14)
    data_monthly["ATR"] = ta.ATR(data_monthly['High'], data_monthly['Low'], data_monthly['Close'], timeperiod=14)
    data_day['ATRP'] = (data_day['ATR']/data_day['Close'])*100
    data_weekly['ATRP'] = (data_weekly['ATR']/data_weekly['Close'])*100
    data_monthly['ATRP'] = (data_monthly['ATR']/data_monthly['Close'])*100
    data_day = data_day.dropna()
    data_weekly = data_weekly.dropna()
    data_monthly = data_monthly.dropna()
    first_monthly_date = data_monthly.index[0].date()
    first_weekly_date = data_weekly.index[0].date()
    month = today.replace(day=1)
    last_month = month - timedelta(days=1) 
    last_month = last_month.replace(day = 1)
    last_week = today - timedelta(days=today.weekday(), weeks=1)
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
        # rank += SELL_RANK_HARD
        sell_rules.append('6')
    elif(float(data_day[symbol].loc[str(today),'ATRP'])*5 <= trade_yield):
        # rank += SELL_RANK_HARD
        sell_rules.append('7')
    elif(float(data_day[symbol].loc[str(today),'ATRP'])*4 <= trade_yield):
        # rank += SELL_RANK_HARD
        sell_rules.append('8')
    elif(float(data_day[symbol].loc[str(today),'ATRP'])*3 <= trade_yield):
        # rank += SELL_RANK_HARD
        sell_rules.append('9')

    sell_ret['rank'] = rank
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
    url = f"https://api.tradestation.com/v3/marketdata/quotes/{symbol}"
    headers = {
        "content-type": "application/json",
        "Authorization": f'Bearer {self.trade_station.TOKENS.access_token}'
    }

    response = requests.request("GET", url, headers=headers)
    response =  json.loads(response.text)
    return float(response['Quotes'][0]['Last'])


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
