import yahoo_fin.stock_info as yf2
from sequencing import *
import talib as ta
import requests
import json
import traceback
from functools import reduce
import time
import tkinter as tk
from tkinter import messagebox
import marketopen

# TODO: change buy and sell rank
#TODO NEED TO CHECK SELL STARTEGY
#TODO NEED TO write code for close market!
#TODO NEED TO check if market open really working

ACCOUNT_ID = 11509188
BUY_RANK = 5
SELL_RANK = 5
TRADE_SIZE = 0.25
LEVERAGE_SIZE = 0.02
SUCCESS = 1
FAILED_ORDER = -1
FAIL = 0
ERROR_ORDER = -1

class Portfolio:

    def __init__(self,trade_station,market_sentiment,sectors_sentiment):
        self.trade_station = trade_station
        self.cash = self.get_cash()
        self.equity = self.get_equity()
        self.net_wealth = self.cash + self.equity
        self.holdings = self.get_holdings()
        self.trade_size_cash = TRADE_SIZE * self.net_wealth
        self.leverage_amount = LEVERAGE_SIZE * self.net_wealth
        self.queue_buying_money = 0
        self.queue_selling_money = 0
        self.orders = {}
        self.queue_orders = {}
        self.filled_orders = {}
        self.market_sentiment = market_sentiment
        self.sectors_sentiment = sectors_sentiment
        self.etfs = {'XLC':['XLC','FIVG','IYZ','VR'],'XLY':['XLY','XHB', 'PEJ', 'IBUY','BJK','BETZ''AWAY','SOCL','BFIT','KROP'],'XLP':['XLP','FTXG','KXI','PBJ'],
                    'XLE':['XLE','FTXN','ICLN'],'XLF':['XLF','KIE','KCE','KRE'],'XLV':['XLV','XHE','XHS','GNOM','HTEC','PPH','AGNG','EDOC'],
                    'XLI':['XLI','AIRR','IFRA','IGF','SIMS'],'XLK':['XLK','HERO','FDN','IRBO','FINX','IHAK','SKYY','SNSR'],'XLU':['XLU','FIW','FAN'],
                    'XLRE':['XLRE','KBWY','SRVR','VPN','GRNR'],'XLB':['XLB','PYZ','XME','HAP','MXI','IGE','MOO','WOOD','COPX','FXZ','URA','LIT']}
        self.etfs_to_buy = get_best_etfs(self)
        self.update_orders()
       
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
            "AccountID": ACCOUNT_ID,
            "Symbol": symbol,
            "Quantity": quantity,
            "OrderType": order_type,
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

        return response

    def run_buy_and_sell_strategy(self,automate):
        message =  tk.Tk()
        message.geometry("250x250")
        # message.focus_force() #TODO: try it to see if its make focus!
        market_open = self.market_open()
        answer = True
        sold_symbols = []
        symbols_sell_ratings = get_sell_rating(self)
        if(symbols_sell_ratings != None):
            for symbol in symbols_sell_ratings.items():
                if(symbol[1]['rank'] >= SELL_RANK):
                    size = self.holdings[symbol[0]]['Quantity']
                    if(not automate): answer = messagebox.askyesno('Order Confirmation',f"Selling {size} of {symbol[0]}\nAre You Confirm?")
                    if answer:
                        sold_symbols.append(symbol[0])
                        self.sell(symbol[0],size)
                        self.update_orders()
                        self.update_portfolio()
            if(market_open): self.wait_for_confirm_sell_order()

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
                if(position['AccountID'] != ACCOUNT_ID):
                    continue
                position_id = position["PositionID"]
                quantity = position["Quantity"]
                long_short = position["LongShort"]
                average_price = position["AveragePrice"]
                trade_yield = position["UnrealizedProfitLossPercent"]
                total_cost = position["TotalCost"]
                market_value = position["MarketValue"]
                holdings[position["Symbol"]] = {"PositionID":position_id,"Quantity":quantity,"LongShort":long_short,
                    "AveragePrice":average_price,"UnrealizedProfitLossPercent":trade_yield,"TotalCost":total_cost,"MarketValue":market_value}
            return holdings
        except Exception:
            print(f"CONNECTION problem with TradeStation, accured while tried to check account balances, Details: \n {traceback.format_exc()}")
            return holdings             


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
                self.queue_orders[symbol] = {'Quantity': size, 'Filled Price': order['FilledPrice'] ,'Open Time': open_time, 'Order Type': order_type,
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

def get_best_etfs(self):
    sectors_dict = {}
    sectors_to_buy = []
    counter = 0
    sectors_dict['XLB'] = self.sectors_sentiment.get_materials_sentiment()
    sectors_dict['XLC'] = self.sectors_sentiment.get_communication_sentimennt()
    sectors_dict['XLY'] = self.sectors_sentiment.get_consumer_discretionary_sentiment()
    sectors_dict['XLP'] = self.sectors_sentiment.get_consumer_staples_sentiment()
    sectors_dict['XLE'] = self.sectors_sentiment.get_energy_sentiment()
    sectors_dict['XLV'] = self.sectors_sentiment.get_healthcare_sentiment()
    sectors_dict['XLF'] = self.sectors_sentiment.get_finance_sentiment()
    sectors_dict['XLI'] = self.sectors_sentiment.get_industrial_sentiment()
    sectors_dict['XLK'] = self.sectors_sentiment.get_technology_sentiment()
    sectors_dict['XLU'] = self.sectors_sentiment.get_utilities_sentiment()
    sectors_dict['XLRE'] = self.sectors_sentiment.get_real_estate_sentiment()

    sectors_dict = {key:value for key, value in sorted(sectors_dict.items(), key=lambda x: x[1],reverse=True)}
    
    for key,value in sectors_dict.items():
        if(counter == 2):
            break
        if(value >= 0):
            counter += 1
            sectors_to_buy.append(self.etfs[key])

    sectors_to_buy = reduce(lambda x,y: x+y, sectors_to_buy)
    return sectors_to_buy



def get_buy_ratings(self):
    rating = {}
    market_rank = self.market_sentiment.get_sentiment_score()
    for etf in self.etfs_to_buy:
        symbol_data_day = pd.DataFrame(yf.download(tickers=etf, period='max',interval='1d',progress=False)).dropna()
        symbol_data_month = pd.DataFrame(yf.download(tickers=etf, period='max',interval='1mo',progress=False)).dropna()
        symbol_data_weekly = pd.DataFrame(yf.download(tickers=etf, period='max',interval='1wk',progress=False)).dropna()
        rating[etf] = buy_rate(symbol_data_month,symbol_data_weekly,symbol_data_day,etf,market_rank)
    return rating

def get_sell_rating(self):
    rating = {}
    if(not self.holdings):
        return None
    for symbol in self.holdings.items():
        symbol_data_day = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1d',progress=False)).dropna()
        symbol_data_month = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1mo',progress=False)).dropna()
        symbol_data_weekly = pd.DataFrame(yf.download(tickers=symbol[0], period='max',interval='1wk',progress=False)).dropna()
        rating[symbol[0]] = sell_rate(symbol_data_month,symbol_data_weekly,symbol_data_day,symbol[0])
    return rating


def buy_rate(data_monthly,data_weekly,data_day,etf,market_rank):
    rank = 0
    rank += market_rank
    today = date.today()
    buy_ret = {'rank':rank,'price': 0}
    seq_daily = SequenceMethod(data_day,'day',today)
    seq_weekly = SequenceMethod(data_weekly,'weekly',today)
    seq_month = SequenceMethod(data_monthly,'monthly',today)
    avg_weekly_move = seq_weekly.get_avg_up_return()
    start_move_price = check_seq_price_by_date_weekly(seq_weekly.get_seq_df(),today)
    try:
        data_daily = yf.download(etf,start = (today - timedelta(days=5)), end= today,progress=False) 
        daily_price = data_daily['Close'][-1]
    except:
        daily_price = None
    if(daily_price != None and start_move_price != None): move_return = (daily_price - start_move_price)/start_move_price*100
    else: move_return = None
    last_day = data_daily.tail(1)
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
    month = today.replace(day=1)
    pre_week = today - timedelta(days=7*4)
    last_month = month - timedelta(days=1) 
    last_month = last_month.replace(day = 1)
    pre_month = today.replace(day =1)
    for i in range(3):
        pre_month = pre_month - timedelta(days=1)
        pre_month = pre_month.replace(day = 1)

    if(float(last_day.loc[str(last_day.index[-1]),'Close']) > float(data_day.loc[str(last_day.index[-1]),'SMA13']) and check_seq_by_date_daily_equal(seq_daily.get_seq_df(),today) == 1):
        rank += BUY_RANK

    if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),today) == 1):
        rank += 1
    else :
        buy_ret['rank'] = rank
        buy_ret['price'] = daily_price
        return buy_ret
    if(check_seq_by_date_monthly(seq_month.get_seq_df(),today) == 1):
        rank += 2
    try:
        if(data_day.loc[str(today - timedelta(days=3)),'SMA13'] > data_day.loc[str(today - timedelta(days=3)),'SMA5'] and data_day.loc[str(today - timedelta(days=5)),'SMA13'] > data_day.loc[str(today - timedelta(days=5)),'SMA5']):
            rank += 1
    except:
        rank += 0
    try:
        if(first_monthly_date <= last_month and data_monthly.loc[str(last_month),'SMA13'] > data_monthly.loc[str(last_month),'SMA5']):
            rank += 1
    except:
        rank += 0
    if(is_moving_away_weekly(data_weekly,today,pre_week)):
        rank += 1
    if(is_moving_away_monthly(data_monthly,last_month,pre_month)):
        rank += 1
    if(move_return != None and move_return <= avg_weekly_move/2): #was 2.5
        rank += 1

    buy_ret['rank'] = rank
    buy_ret['price'] = daily_price
    return buy_ret



def sell_rate(self,symbol_data_month,symbol_data_weekly,data_day,symbol):
    rank = 0
    today = date.today()
    sell_ret = {'rank':rank}
    seq_daily = SequenceMethod(data_day,'day',today)
    seq_weekly = SequenceMethod(data_weekly,'weekly',today)
    seq_month = SequenceMethod(data_monthly,'monthly',today)
    avg_weekly_move = seq_weekly.get_avg_up_return()
    try:
        data_daily = yf.download(symbol,start = (today - timedelta(days=5)), end= today,progress=False) 
        daily_price = data_daily['Close'][-1]
    except:
        daily_price = None
    if(daily_price != None): trade_yield = (daily_price - self.holdings[symbol]['Avg Price'])/self.holdings[symbol]['Avg Price']*100
    else: trade_yield = None
    last_day = data_daily.tail(1)
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
    month = today.replace(day=1)
    last_month = month - timedelta(days=1) 
    last_month = last_month.replace(day = 1)
    last_week = today - timedelta(days=today.weekday(), weeks=1)
    if(float(last_day.loc[str(last_day.index[-1]),'Close']) < float(data_day.loc[str(last_day.index[-1]),'SMA13']) and check_seq_by_date_daily_equal(seq_daily.get_seq_df(),today) == -1):
        rank += SELL_RANK
    
    if(check_seq_by_date_weekly(seq_weekly.get_seq_df(),today) == -1):
        rank += 1
        self.holdings[symbol]['Red Weeks'] = self.holdings[symbol]['Red Weeks'] + 1
    else :
        self.holdings[symbol]['Red Weeks'] = 0    
    if(self.holdings[symbol]['Red Weeks'] >= 2): # WAs 2
        rank += 1
    if(check_seq_by_date_monthly(seq_month.get_seq_df(),today) == -1):
        rank += 2
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
    return sell_ret



def is_moving_away_weekly(data_weekly,today,pre_week):
    try:
        if((data_weekly.loc[str(today),'SMA13'] - data_weekly.loc[str(today),'SMA5']) > (data_weekly.loc[str(pre_week),'SMA13'] - data_weekly.loc[str(pre_week),'SMA5'])):
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
