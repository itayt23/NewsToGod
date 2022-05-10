
import yfinance as yf
import talib as ta
import numpy as np
import pandas as pd
import requests
from sentimentprocessor import SentimentProcessor
from ta.trend import *
from ta.momentum import *
from ta.others import *
from ta.utils import *
from ta.volatility import *
from ta.volume import *
from datetime import date,datetime,timedelta
import pymannkendall as mk
from pathlib import Path
from dotenv import load_dotenv
import os


#write tipranks score
#wrtie final score formula

class MarketSentiment:
    def __init__(self,news_number):
        indices = ['spy','qqq','dia']
        self.market_df = pd.DataFrame(index=['SPX','NDX','DJI'],columns=['News Sentiment','Article Sentiment','Technical Score daily',
            'Technical Score weekly','Technical Score monthly','Final Score'])
        self.technical_df = pd.DataFrame(index=['daily','weekly','monthly'],columns=['SMA10','EMA10','SMA20','EMA20','SMA30','EMA30',
            'SMA50','EMA50','SMA100','EMA100','SMA200','EMA200','RSI','STOCH','CCI','ADX','AWS','MOM','MACD','STOCHRSI','WILLIAM','ULTIMATE'])
        self.all_technical_df = pd.DataFrame()
        self.total_scores = 0
        total_properties = 70 # need to change it...
        load_dotenv("api.env")
        self.news_sentiment = market_news_sentiment(news_number)
        update_total_score(self,self.news_sentiment)
        for market in indices:
            market_index = convert_indicies(market)
            market_1d, market_1wk, market_1mo, market_price = download_symbol_data(market)
            market_1d, market_1wk, market_1mo = clean_df_nans(market_1d, market_1wk, market_1mo)
            technical_score(self,market_1d, market_1wk, market_1mo, market_price,market_index)
            # sa_score(self,market,market_index)
            # tip_score(self,market_index)
            final_score(self,market_index,total_properties)
            self.all_technical_df = self.all_technical_df.append(self.technical_df)
            self.total_scores = 0
        self.market_df.loc["SPX",'News Sentiment'] = self.news_sentiment
        self.market_df.loc["NDX",'News Sentiment'] = self.news_sentiment
        self.market_df.loc["DJI",'News Sentiment'] = self.news_sentiment
        build_df(self)
        

    def get_news_sentiment(self):
        return self.news_sentiment
    def get_technical_df(self):
        return  self.technical_df
    def get_market_df(self):
        return  self.market_df

def final_score(self,market_index,total_properties):
    score =  self.total_scores/total_properties
    self.market_df.loc[market_index,'Final Score'] = score_to_sentiment(score)

def convert_indicies(market):
    if(market == 'spy'): return 'SPX'
    if(market == 'qqq'): return 'NDX'
    if(market == 'dia'): return 'DJI'

def download_symbol_data(market):
    try:
        market_1d = yf.download(market,period='1y',interval='1d')
        market_price = market_1d['Close'].iloc[-1]
        market_1d = pd.DataFrame(market_1d)
        market_1wk = yf.download(market,period='5y',interval='1wk')
        market_1wk = pd.DataFrame(market_1wk)
        market_1mo = yf.download(market,period='max',interval='1mo')
        market_1mo = pd.DataFrame(market_1mo)
    except:
        print(f"Problem with download data, symbol is {market}")
        exit(7)
    return market_1d, market_1wk, market_1mo, market_price

def market_news_sentiment(news_number):
    news_processor = SentimentProcessor(news_number)
    news_processor.run_market_news_processor()
    return news_processor.get_market_news_sentiment()

def technical_score(self,market_1d, market_1wk, market_1mo, market_price,market):
    last_data_wk = -2
    last_data_mo = -2
    if is_date_round_wk(market_1wk) : last_data_wk = -1
    if is_date_round_mo(market_1mo) : last_data_mo = -1
    moving_averages_extract_data(market_1d, market_1wk, market_1mo)
    oscillators_extract_data(market_1d, market_1wk, market_1mo)
    ma_score(self,market_1d, market_1wk, market_1mo, market_price,last_data_wk,last_data_mo,market)
    oscillators_score(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo,market)
    technical_score_adaptation(self,market)

def ma_score(self,market_1d, market_1wk, market_1mo, market_price,last_data_wk,last_data_mo,market):
    for index, val in self.technical_df.iteritems():
       if(index == "RSI"): break
       if(market_1d[index].iloc[-1] > market_price):
           self.technical_df.at["daily",index] = -1 
       elif(market_1d[index].iloc[-1] < market_price):
           self.technical_df.at["daily",index] = 1
       else: self.technical_df.at["daily",index] = 0
       if(market_1wk[index].iloc[last_data_wk] > market_price):
           self.technical_df.at["weekly",index] = -1 
       elif(market_1wk[index].iloc[last_data_wk] < market_price):
           self.technical_df.at["weekly",index] = 1
       else: self.technical_df.at["weekly",index] = 0
       if(market_1mo[index].iloc[last_data_mo] > market_price):
           self.technical_df.at["monthly",index] = -1 
       elif(market_1mo[index].iloc[last_data_mo] < market_price):
           self.technical_df.at["monthly",index] = 1
       else: self.technical_df.at["monthly",index] = 0

def oscillators_score(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo,market):
    rsi_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo)
    stochastic_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo)
    cci_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo)
    adx_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo)
    aws_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo)
    mom_sentiment(self,market_1d, market_1wk, market_1mo)
    macd_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo)
    stochrsi_sentiment(self,market_1d, market_1wk, market_1mo)
    williams_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo)
    ultimate_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo)

def rsi_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo):
    if(market_1d["RSI"].iloc[-1] > 70 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1d') < 0):
        self.technical_df.at["daily","RSI"] = -1 
    elif(market_1d["RSI"].iloc[-1] < 30 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1d') > 0):
        self.technical_df.at["daily","RSI"] = 1
    else: self.technical_df.at["daily","RSI"] = 0
    if(market_1wk["RSI"].iloc[last_data_wk] > 70 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1wk') < 0):
        self.technical_df.at["weekly","RSI"] = -1 
    elif(market_1wk["RSI"].iloc[last_data_wk] < 30 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1wk') > 0):
        self.technical_df.at["weekly","RSI"] = 1
    else: self.technical_df.at["weekly","RSI"] = 0
    if(market_1mo["RSI"].iloc[last_data_mo] > 70 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1mo') < 0):
        self.technical_df.at["monthly","RSI"] = -1 
    elif(market_1mo["RSI"].iloc[last_data_mo] < 30 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1mo') > 0):
        self.technical_df.at["monthly","RSI"] = 1
    else: self.technical_df.at["monthly","RSI"] = 0

def stochastic_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo):
    if(market_1d["STOCH_S"].iloc[-1] > 80 and market_1d["STOCH_S"].iloc[-1] <= market_1d["STOCH_M"].iloc[-1]):
        self.technical_df.at["daily","STOCH"] = -1 
    elif(market_1d["STOCH_S"].iloc[-1] < 20 and market_1d["STOCH_S"].iloc[-1] >= market_1d["STOCH_M"].iloc[-1]):
        self.technical_df.at["daily","STOCH"] = 1
    else: self.technical_df.at["daily","STOCH"] = 0
    if(market_1wk["STOCH_S"].iloc[last_data_wk] > 80 and market_1wk["STOCH_S"].iloc[last_data_wk] <= market_1wk["STOCH_M"].iloc[last_data_wk]):
        self.technical_df.at["weekly","STOCH"] = -1 
    elif(market_1wk["STOCH_S"].iloc[last_data_wk] < 20 and market_1wk["STOCH_S"].iloc[last_data_wk] >= market_1wk["STOCH_M"].iloc[last_data_wk]):
        self.technical_df.at["weekly","STOCH"] = 1
    else: self.technical_df.at["weekly","STOCH"] = 0
    if(market_1mo["STOCH_S"].iloc[last_data_mo]  > 80 and market_1mo["STOCH_S"].iloc[last_data_mo] <= market_1mo["STOCH_M"].iloc[last_data_mo]):
        self.technical_df.at["monthly","STOCH"] = -1 
    elif(market_1mo["STOCH_S"].iloc[last_data_mo] < 20 and market_1mo["STOCH_S"].iloc[last_data_mo] >= market_1mo["STOCH_M"].iloc[last_data_mo]):
        self.technical_df.at["monthly","STOCH"] = 1
    else: self.technical_df.at["monthly","STOCH"] = 0

def cci_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo):
    if(market_1d["CCI"].iloc[-1] > 100 and market_1d["CCI"].iloc[-1] < market_1d["CCI"].iloc[-2]):
        self.technical_df.at["daily","CCI"] = -1 
    elif(market_1d["CCI"].iloc[-1] < -100 and market_1d["CCI"].iloc[-1] > market_1d["CCI"].iloc[-2]):
        self.technical_df.at["daily","CCI"] = 1
    else: self.technical_df.at["daily","CCI"] = 0
    if(market_1wk["CCI"].iloc[last_data_wk] > 100 and market_1wk["CCI"].iloc[last_data_wk] < market_1wk["CCI"].iloc[last_data_wk-1]):
        self.technical_df.at["weekly","CCI"] = -1 
    elif(market_1wk["CCI"].iloc[last_data_wk] < -100 and market_1wk["CCI"].iloc[last_data_wk] > market_1wk["CCI"].iloc[last_data_wk-1]):
        self.technical_df.at["weekly","CCI"] = 1
    else: self.technical_df.at["weekly","CCI"] = 0
    if(market_1mo["CCI"].iloc[last_data_mo] > 100 and market_1mo["CCI"].iloc[last_data_mo] < market_1mo["CCI"].iloc[last_data_mo-1]):
        self.technical_df.at["monthly","CCI"] = -1 
    elif(market_1mo["CCI"].iloc[last_data_mo] < -100 and market_1mo["CCI"].iloc[last_data_mo] > market_1mo["CCI"].iloc[last_data_mo-1]):
        self.technical_df.at["monthly","CCI"] = 1
    else: self.technical_df.at["monthly","CCI"] = 0

def adx_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo):
    if(market_1d["ADX"].iloc[-1] > 20 and market_1d["ADX_D+"].iloc[-1] < market_1d["ADX_D-"].iloc[-1]):
        self.technical_df.at["daily","ADX"] = -1 
    elif(market_1d["ADX"].iloc[-1] > 20 and market_1d["ADX_D+"].iloc[-1] > market_1d["ADX_D-"].iloc[-1]):
        self.technical_df.at["daily","ADX"] = 1
    else: self.technical_df.at["daily","ADX"] = 0
    if(market_1wk["ADX"].iloc[last_data_wk] > 20 and market_1wk["ADX_D+"].iloc[last_data_wk] < market_1wk["ADX_D-"].iloc[last_data_wk]):
        self.technical_df.at["weekly","ADX"] = -1 
    elif(market_1wk["ADX"].iloc[last_data_wk] > 20 and market_1wk["ADX_D+"].iloc[last_data_wk] > market_1wk["ADX_D-"].iloc[last_data_wk]):
        self.technical_df.at["weekly","ADX"] = 1
    else: self.technical_df.at["weekly","ADX"] = 0
    if(market_1mo["ADX"].iloc[last_data_mo] > 20 and market_1mo["ADX_D+"].iloc[last_data_mo] < market_1mo["ADX_D-"].iloc[last_data_mo]):
        self.technical_df.at["monthly","ADX"] = -1 
    elif(market_1mo["ADX"].iloc[last_data_mo] > 20 and market_1mo["ADX_D+"].iloc[last_data_mo] > market_1mo["ADX_D-"].iloc[last_data_mo]):
        self.technical_df.at["monthly","ADX"] = 1
    else: self.technical_df.at["monthly","ADX"] = 0

def aws_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo):
    if(market_1d["AWS"].iloc[-1] < 0):
        self.technical_df.at["daily","AWS"] = -1 
    elif(market_1d["AWS"].iloc[-1] > 0):
        self.technical_df.at["daily","AWS"] = 1
    else: self.technical_df.at["daily","AWS"] = 0
    if(market_1wk["AWS"].iloc[last_data_wk] < 0):
        self.technical_df.at["weekly","AWS"] = -1 
    elif(market_1wk["AWS"].iloc[last_data_wk] > 0):
        self.technical_df.at["weekly","AWS"] = 1
    else: self.technical_df.at["weekly","AWS"] = 0
    if(market_1mo["AWS"].iloc[last_data_mo] < 0):
        self.technical_df.at["monthly","AWS"] = -1 
    elif(market_1mo["AWS"].iloc[last_data_mo] > 0):
        self.technical_df.at["monthly","AWS"] = 1
    else: self.technical_df.at["monthly","AWS"] = 0

def mom_sentiment(self,market_1d, market_1wk, market_1mo):
    if(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1d') < 0):
        self.technical_df.at["daily","MOM"] = -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1d') > 0):
        self.technical_df.at["daily","MOM"] = 1
    else: self.technical_df.at["daily","MOM"] = 0
    if(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1wk') < 0):
        self.technical_df.at["weekly","MOM"] = -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1wk') > 0):
        self.technical_df.at["weekly","MOM"] = 1
    else: self.technical_df.at["weekly","MOM"] = 0
    if(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1mo') < 0):
        self.technical_df.at["monthly","MOM"] = -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1mo') > 0):
        self.technical_df.at["monthly","MOM"] = 1
    else: self.technical_df.at["monthly","MOM"] = 0

def macd_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo):
    if(market_1d["MACD"].iloc[-1] < market_1d["MACD_S"].iloc[-1]):
        self.technical_df.at["daily","MACD"] = -1 
    elif(market_1d["MACD"].iloc[-1] > market_1d["MACD_S"].iloc[-1]):
        self.technical_df.at["daily","MACD"] = 1
    else: self.technical_df.at["daily","MACD"] = 0
    if(market_1wk["MACD"].iloc[last_data_wk] < market_1wk["MACD_S"].iloc[last_data_wk]):
        self.technical_df.at["weekly","MACD"] = -1 
    elif(market_1wk["MACD"].iloc[last_data_wk] > market_1wk["MACD_S"].iloc[last_data_wk]):
        self.technical_df.at["weekly","MACD"] = 1
    else: self.technical_df.at["weekly","MACD"] = 0
    if(market_1mo["MACD"].iloc[last_data_mo] < market_1mo["MACD_S"].iloc[last_data_mo]):
        self.technical_df.at["monthly","MACD"] = -1 
    elif(market_1mo["MACD"].iloc[last_data_mo] > market_1mo["MACD_S"].iloc[last_data_mo]):
        self.technical_df.at["monthly","MACD"] = 1
    else: self.technical_df.at["monthly","MACD"] = 0

def stochrsi_sentiment(self,market_1d, market_1wk, market_1mo):
    if(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1d') > 0 and market_1d["STOCHRSI_K"].iloc[-1] > 80 and market_1d["STOCHRSI_D"].iloc[-1] > 80
        and market_1d["STOCHRSI_K"].iloc[-1] < market_1d["STOCHRSI_D"].iloc[-1]):
        self.technical_df.at["daily","STOCHRSI"] = -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1d') < 0 and market_1d["STOCHRSI_K"].iloc[-1] < 20 and market_1d["STOCHRSI_D"].iloc[-1] < 20
        and market_1d["STOCHRSI_K"].iloc[-1] > market_1d["STOCHRSI_D"].iloc[-1]):
        self.technical_df.at["daily","STOCHRSI"] = 1
    else: self.technical_df.at["daily","STOCHRSI"] = 0
    if(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1wk') > 0 and market_1wk["STOCHRSI_K"].iloc[-1] > 80 and market_1wk["STOCHRSI_D"].iloc[-1] > 80
        and market_1wk["STOCHRSI_K"].iloc[-1] < market_1wk["STOCHRSI_D"].iloc[-1]):
        self.technical_df.at["weekly","STOCHRSI"] = -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1wk') < 0 and market_1wk["STOCHRSI_K"].iloc[-1] < 20 and market_1wk["STOCHRSI_D"].iloc[-1] < 20
        and market_1wk["STOCHRSI_K"].iloc[-1] > market_1wk["STOCHRSI_D"].iloc[-1]):
        self.technical_df.at["weekly","STOCHRSI"] = 1
    else: self.technical_df.at["weekly","STOCHRSI"] = 0
    if(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1mo') > 0 and market_1mo["STOCHRSI_K"].iloc[-1] > 80 and market_1mo["STOCHRSI_D"].iloc[-1] > 80
        and market_1mo["STOCHRSI_K"].iloc[-1] < market_1mo["STOCHRSI_D"].iloc[-1]):
        self.technical_df.at["monthly","STOCHRSI"] = -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1mo') < 0 and market_1mo["STOCHRSI_K"].iloc[-1] < 20 and market_1mo["STOCHRSI_D"].iloc[-1] < 20
        and market_1mo["STOCHRSI_K"].iloc[-1] > market_1mo["STOCHRSI_D"].iloc[-1]):
        self.technical_df.at["monthly","STOCHRSI"] = 1
    else: self.technical_df.at["monthly","STOCHRSI"] = 0

def williams_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo):
    if(market_1d["WILLIAM"].iloc[-1] > -20 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1d') < 0):
        self.technical_df.at["daily","WILLIAM"] = -1 
    elif(market_1d["WILLIAM"].iloc[-1] < -80 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1d') > 0):
        self.technical_df.at["daily","WILLIAM"] = 1
    else: self.technical_df.at["daily","WILLIAM"] = 0
    if(market_1wk["WILLIAM"].iloc[last_data_wk] > -20 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1wk') < 0):
        self.technical_df.at["weekly","WILLIAM"] = -1 
    elif(market_1wk["WILLIAM"].iloc[last_data_wk] < -80 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1wk') > 0):
        self.technical_df.at["weekly","WILLIAM"] = 1
    else: self.technical_df.at["weekly","WILLIAM"] = 0
    if(market_1mo["WILLIAM"].iloc[last_data_mo] > -20 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1mo') < 0):
        self.technical_df.at["monthly","WILLIAM"] = -1 
    elif(market_1mo["WILLIAM"].iloc[last_data_mo] < -80 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1mo') > 0):
        self.technical_df.at["monthly","WILLIAM"] = 1
    else: self.technical_df.at["monthly","WILLIAM"] = 0

def ultimate_sentiment(self,market_1d, market_1wk, market_1mo,last_data_wk,last_data_mo):
    if(market_1d["ULTIMATE"].iloc[-1] < 30):
        self.technical_df.at["daily","ULTIMATE"] = -1 
    elif(market_1d["ULTIMATE"].iloc[-1] > 70):
        self.technical_df.at["daily","ULTIMATE"] = 1
    else: self.technical_df.at["daily","ULTIMATE"] = 0
    if(market_1wk["ULTIMATE"].iloc[last_data_wk] < 30):
        self.technical_df.at["weekly","ULTIMATE"] = -1 
    elif(market_1wk["ULTIMATE"].iloc[last_data_wk] > 70):
        self.technical_df.at["weekly","ULTIMATE"] = 1
    else: self.technical_df.at["weekly","ULTIMATE"] = 0
    if(market_1mo["ULTIMATE"].iloc[last_data_mo] < 30):
        self.technical_df.at["monthly","ULTIMATE"] = -1 
    elif(market_1mo["ULTIMATE"].iloc[last_data_mo] > 70):
        self.technical_df.at["monthly","ULTIMATE"] = 1
    else: self.technical_df.at["monthly","ULTIMATE"] = 0

def build_df(self):
    results_path_market = Path.cwd() / 'results' / 'csv_files' / 'Market Sentiment'
    results_path_technical = Path.cwd() / 'results' / 'csv_files' / 'Technical Sentiment'
    date = datetime.now().strftime("%Y_%m_%d-%I_%M_%S")
    if not results_path_market.exists():
        results_path_market.mkdir(parents=True)
    if not results_path_technical.exists():
        results_path_technical.mkdir(parents=True)
    self.market_df.to_csv(results_path_market / f"market_sentiment_{date}.csv")
    self.all_technical_df.to_csv(results_path_technical / f"technical_sentiment_{date}.csv")

def clean_df_nans(market_1d, market_1wk, market_1mo):
    for row in market_1wk.index:
        if(str(market_1wk['Close'][row]) == 'nan' ):
           market_1wk = market_1wk.drop(axis=0,index=[row])
    for row in market_1d.index:
        if(str(market_1d['Close'][row]) == 'nan' ):
           market_1d = market_1d.drop(axis=0,index=[row])
    for row in market_1mo.index:
        if(str(market_1mo['Close'][row]) == 'nan' ):
           market_1mo = market_1mo.drop(axis=0,index=[row])
    return  market_1d, market_1wk, market_1mo

def is_date_round_mo(df):
    date = str(df.index[-1]).split("-")
    date = date[2].split(" ")
    date = date[0]
    if(date == '01'):
        return True
    return False

def is_date_round_wk(df):
    today_date = date.today()
    date_wk = str(df.index[-2]).split(" ")
    date_wk = date_wk[0]
    date_wk = datetime.strptime(date_wk, "%Y-%m-%d").date()
    if((date_wk + timedelta(days=7)) == today_date):
        return True
    return False

def moving_averages_extract_data(market_1d, market_1wk, market_1mo):

    market_1d['SMA10'] = ta.SMA(market_1d['Close'], timeperiod=10)
    market_1d['EMA10'] = ta.EMA(market_1d['Close'], timeperiod=10)
    market_1wk['SMA10'] = ta.SMA(market_1wk['Close'], timeperiod=10)
    market_1wk['EMA10'] = ta.EMA(market_1wk['Close'], timeperiod=10)
    market_1mo['SMA10'] = ta.SMA(market_1mo['Close'], timeperiod=10)
    market_1mo['EMA10'] = ta.EMA(market_1mo['Close'], timeperiod=10)

    market_1d['SMA20'] = ta.SMA(market_1d['Close'], timeperiod=20)
    market_1d['EMA20'] = ta.EMA(market_1d['Close'], timeperiod=20)
    market_1wk['SMA20'] = ta.SMA(market_1wk['Close'], timeperiod=20)
    market_1wk['EMA20'] = ta.EMA(market_1wk['Close'], timeperiod=20)
    market_1mo['SMA20'] = ta.SMA(market_1mo['Close'], timeperiod=20)
    market_1mo['EMA20'] = ta.EMA(market_1mo['Close'], timeperiod=20)

    market_1d['SMA30'] = ta.SMA(market_1d['Close'], timeperiod=30)
    market_1d['EMA30'] = ta.EMA(market_1d['Close'], timeperiod=30)
    market_1wk['SMA30'] = ta.SMA(market_1wk['Close'], timeperiod=30)
    market_1wk['EMA30'] = ta.EMA(market_1wk['Close'], timeperiod=30)
    market_1mo['SMA30'] = ta.SMA(market_1mo['Close'], timeperiod=30)
    market_1mo['EMA30'] = ta.EMA(market_1mo['Close'], timeperiod=30)
    
    market_1d['SMA50'] = ta.SMA(market_1d['Close'], timeperiod=50)
    market_1d['EMA50'] = ta.EMA(market_1d['Close'], timeperiod=50)
    market_1wk['SMA50'] = ta.SMA(market_1wk['Close'], timeperiod=50)
    market_1wk['EMA50'] = ta.EMA(market_1wk['Close'], timeperiod=50)
    market_1mo['SMA50'] = ta.SMA(market_1mo['Close'], timeperiod=50)
    market_1mo['EMA50'] = ta.EMA(market_1mo['Close'], timeperiod=50)

    market_1d['SMA100'] = ta.SMA(market_1d['Close'], timeperiod=100)
    market_1d['EMA100'] = ta.EMA(market_1d['Close'], timeperiod=100)
    market_1wk['SMA100'] = ta.SMA(market_1wk['Close'], timeperiod=100)
    market_1wk['EMA100'] = ta.EMA(market_1wk['Close'], timeperiod=100)
    market_1mo['SMA100'] = ta.SMA(market_1mo['Close'], timeperiod=100)
    market_1mo['EMA100'] = ta.EMA(market_1mo['Close'], timeperiod=100)

    market_1d['SMA200'] = ta.SMA(market_1d['Close'], timeperiod=200)
    market_1d['EMA200'] = ta.EMA(market_1d['Close'], timeperiod=200)
    market_1wk['SMA200'] = ta.SMA(market_1wk['Close'], timeperiod=200)
    market_1wk['EMA200'] = ta.EMA(market_1wk['Close'], timeperiod=200)
    market_1mo['SMA200'] = ta.SMA(market_1mo['Close'], timeperiod=200)
    market_1mo['EMA200'] = ta.EMA(market_1mo['Close'], timeperiod=200)

def oscillators_extract_data(market_1d, market_1wk, market_1mo):
    market_1d['RSI'] = RSIIndicator(market_1d['Close']).rsi()
    market_1wk['RSI'] = RSIIndicator(market_1wk['Close']).rsi()
    market_1mo['RSI'] = RSIIndicator(market_1mo['Close']).rsi()

    market_1d['STOCH_S'] = StochasticOscillator(market_1d['High'],market_1d['Low'],market_1d['Close'], window=14,smooth_window=3).stoch_signal()
    market_1wk['STOCH_S'] = StochasticOscillator(market_1wk['High'],market_1wk['Low'],market_1wk['Close']).stoch_signal()
    market_1mo['STOCH_S'] = StochasticOscillator(market_1mo['High'],market_1mo['Low'],market_1mo['Close']).stoch_signal()

    market_1d['STOCH_M'] = SMAIndicator(market_1d['STOCH_S'],window=3).sma_indicator()
    market_1wk['STOCH_M'] = SMAIndicator(market_1wk['STOCH_S'],window=3).sma_indicator()
    market_1mo['STOCH_M'] = SMAIndicator(market_1mo['STOCH_S'],window=3).sma_indicator()

    market_1d['CCI'] = CCIIndicator(market_1d['High'],market_1d['Low'],market_1d['Close']).cci()
    market_1wk['CCI'] = CCIIndicator(market_1wk['High'],market_1wk['Low'],market_1wk['Close']).cci()
    market_1mo['CCI'] = CCIIndicator(market_1mo['High'],market_1mo['Low'],market_1mo['Close']).cci()
    
    market_1d['ADX'] = ADXIndicator(market_1d['High'],market_1d['Low'],market_1d['Close']).adx()
    market_1wk['ADX'] = ADXIndicator(market_1wk['High'],market_1wk['Low'],market_1wk['Close']).adx()
    market_1mo['ADX'] = ADXIndicator(market_1mo['High'],market_1mo['Low'],market_1mo['Close']).adx()

    market_1d['ADX_D+'] = ADXIndicator(market_1d['High'],market_1d['Low'],market_1d['Close']).adx_pos()
    market_1wk['ADX_D+'] = ADXIndicator(market_1wk['High'],market_1wk['Low'],market_1wk['Close']).adx_pos()
    market_1mo['ADX_D+'] = ADXIndicator(market_1mo['High'],market_1mo['Low'],market_1mo['Close']).adx_pos()

    market_1d['ADX_D-'] = ADXIndicator(market_1d['High'],market_1d['Low'],market_1d['Close']).adx_neg()
    market_1wk['ADX_D-'] = ADXIndicator(market_1wk['High'],market_1wk['Low'],market_1wk['Close']).adx_neg()
    market_1mo['ADX_D-'] = ADXIndicator(market_1mo['High'],market_1mo['Low'],market_1mo['Close']).adx_neg()

    market_1d['AWS'] = AwesomeOscillatorIndicator(market_1d['High'],market_1d['Low']).awesome_oscillator()
    market_1wk['AWS'] = AwesomeOscillatorIndicator(market_1wk['High'],market_1wk['Low']).awesome_oscillator()
    market_1mo['AWS'] = AwesomeOscillatorIndicator(market_1mo['High'],market_1mo['Low']).awesome_oscillator()

    market_1d['MOM'] = ta.MOM(market_1d['Close'], timeperiod=10)
    market_1wk['MOM'] = ta.MOM(market_1wk['Close'], timeperiod=10)
    market_1mo['MOM'] = ta.MOM(market_1mo['Close'], timeperiod=10)

    market_1d['MACD'] = MACD(market_1d['Close']).macd()
    market_1wk['MACD'] = MACD(market_1wk['Close']).macd()
    market_1mo['MACD'] = MACD(market_1mo['Close']).macd()

    market_1d['MACD_S'] = MACD(market_1d['Close']).macd_signal()
    market_1wk['MACD_S'] = MACD(market_1wk['Close']).macd_signal()
    market_1mo['MACD_S'] = MACD(market_1mo['Close']).macd_signal()
    
    market_1d['STOCHRSI_K'] = StochRSIIndicator(market_1d['Close']).stochrsi_k()*100
    market_1wk['STOCHRSI_K'] = StochRSIIndicator(market_1wk['Close']).stochrsi_k()*100
    market_1mo['STOCHRSI_K'] = StochRSIIndicator(market_1mo['Close']).stochrsi_k()*100

    market_1d['STOCHRSI_D'] = StochRSIIndicator(market_1d['Close']).stochrsi_d()*100
    market_1wk['STOCHRSI_D'] = StochRSIIndicator(market_1wk['Close']).stochrsi_d()*100
    market_1mo['STOCHRSI_D'] = StochRSIIndicator(market_1mo['Close']).stochrsi_d()*100

    market_1d['WILLIAM'] = WilliamsRIndicator(market_1d['High'],market_1d['Low'],market_1d['Close']).williams_r()
    market_1wk['WILLIAM'] = WilliamsRIndicator(market_1wk['High'],market_1wk['Low'],market_1wk['Close']).williams_r()
    market_1mo['WILLIAM'] = WilliamsRIndicator(market_1mo['High'],market_1mo['Low'],market_1mo['Close']).williams_r()
    
    market_1d['ULTIMATE'] = UltimateOscillator(market_1d['High'],market_1d['Low'],market_1d['Close']).ultimate_oscillator()
    market_1wk['ULTIMATE'] = UltimateOscillator(market_1wk['High'],market_1wk['Low'],market_1wk['Close']).ultimate_oscillator()
    market_1mo['ULTIMATE'] = UltimateOscillator(market_1mo['High'],market_1mo['Low'],market_1mo['Close']).ultimate_oscillator()

def sa_score(self, market, market_index):
    try:
       url = "https://seeking-alpha.p.rapidapi.com/symbols/get-ratings"
       querystring = {"symbol":market}
       headers = {'x-rapidapi-host': "seeking-alpha.p.rapidapi.com",
               'x-rapidapi-key': os.getenv('sa_api_key')}
       response = requests.request("GET", url, headers=headers, params=querystring)
       ranking = response.json()
    except Exception as e:
        print("Problem with SeekingAlpha WebSite: "+str(e))
    try:
        sa_quant_rating = ranking['data'][0]['attributes']['ratings']['quantRating']
    except:
        sa_quant_rating = 3
    try:
        sa_authors_rating = ranking['data'][0]['attributes']['ratings']['authorsRatingPro']
    except:
        sa_authors_rating = 3
    sa_quant_rating = sa_score_to_sentiment(sa_quant_rating)
    sa_authors_rating = sa_score_to_sentiment(sa_authors_rating)
    update_total_score(self, sa_quant_rating)
    update_total_score(self, sa_authors_rating)
    self.market_df.loc[market_index,"SA quant"] = sa_quant_rating
    self.market_df.loc[market_index,"SA authors"] =  sa_authors_rating

def tip_score(self, market_index):
    if(market_index == "SPX") : symbol = 'spx'
    elif(market_index == "NDX") : symbol = 'nasdaq-100'
    elif(market_index == "DJI") : symbol = 'dow-jones'
    try:
       url = f"https://tr-frontend-cdn.azureedge.net/research/prod/index/{symbol}/payload.json"
       response = requests.request("GET", url)
       ranking = response.json()
    except Exception as e:
        print("Problem with TipRanks WebSite: "+str(e))
    try:
        smart_score = ranking['Indices']['data']['overview']['smartScore']
    except:
        smart_score = 5
    smart_score = tip_score_to_sentiment(smart_score)
    update_total_score(self,smart_score)
    self.market_df.loc[market_index,"TipRanks score"] = smart_score


def update_total_score(self, sentiment):
    if(sentiment == "Strong Sell" or sentiment == "Sell" or sentiment == 'Negative'): self.total_scores += (-1)
    if(sentiment == "Strong Buy" or sentiment == "Buy" or sentiment == 'Positive'): self.total_scores += 1

def tip_score_to_sentiment(score):
    score = round(score)
    if(score == 1): return ("Strong Sell")
    elif( 2 <= score <= 3): return ("Sell")
    elif(4 <= score <= 7): return ("Netural")
    elif(8 <= score <= 9): return ("Buy")
    elif(score == 10): return ("Strong Buy")

def sa_score_to_sentiment(score):
    if(1<= score <= 1.5): return ("Strong Sell")
    elif( 1.5 < score <= 2.5): return ("Sell")
    elif(2.5 < score <= 3.5): return ("Netural")
    elif(3.5 < score <= 4.5): return ("Buy")
    elif(4.5 < score <=5): return ("Strong Buy")

def sa_consecutive(ranking):
    consecutive_quant = 'Netural'
    consecutive_authors = 'Netural'
    quant_rating_0m = ranking['data'][0]['attributes']['ratings']['quantRating']
    quant_rating_3m = ranking['data'][1]['attributes']['ratings']['quantRating']
    quant_rating_6m = ranking['data'][2]['attributes']['ratings']['quantRating']
    sa_authors_rating_0m = ranking['data'][0]['attributes']['ratings']['authorsRatingPro']
    sa_authors_rating_3m = ranking['data'][1]['attributes']['ratings']['authorsRatingPro']
    sa_authors_rating_6m = ranking['data'][2]['attributes']['ratings']['authorsRatingPro']
    if(quant_rating_6m < quant_rating_3m < quant_rating_0m):
        consecutive_quant = 'Positive'
    elif(quant_rating_6m > quant_rating_3m > quant_rating_0m):
        consecutive_quant = 'Negative'
    elif(quant_rating_6m > quant_rating_3m and quant_rating_3m < quant_rating_0m):
        consecutive_quant ='Change Up'
    elif(quant_rating_6m < quant_rating_3m and quant_rating_3m > quant_rating_0m):
        consecutive_quant ='Change down'
    if(sa_authors_rating_6m < sa_authors_rating_3m < sa_authors_rating_0m):
        consecutive_authors = 'Positive'
    elif(sa_authors_rating_6m > sa_authors_rating_3m > sa_authors_rating_0m):
        consecutive_authors = 'Negative'
    elif(sa_authors_rating_6m > sa_authors_rating_3m and sa_authors_rating_3m < sa_authors_rating_0m):
        consecutive_authors ='Change Up'
    elif(sa_authors_rating_6m < sa_authors_rating_3m and sa_authors_rating_3m > sa_authors_rating_0m):
        consecutive_authors ='Change down'
    return consecutive_quant, consecutive_authors

def trend_estimate(market_1d, market_1wk, market_1mo,oscillator, interval):
    index = [1,2,3,4,5,6,7]
    if interval == '1d':
        data = market_1d[oscillator].to_numpy()
        data = data[-7:]
    elif interval == '1wk':
        data = market_1wk[oscillator].to_numpy()
        if(is_date_round_wk(market_1wk)): data = data[-7:]
        else : data = data[-8:-1]
    elif interval == '1mo':
        data = market_1mo[oscillator].to_numpy()
        if(is_date_round_mo(market_1wk)): data = data[-7:]
        else : data = data[-8:-1]

    result = np.polyfit(index,list(data), 1)
    slope = result[-2]
    result_mk = mk.original_test(data)
    if(result_mk.slope < 0.1 and result_mk.slope > -0.1): return 0
    return slope

def technical_score_adaptation(self,market):
    sma_flag = True
    sma_number = 12
    oscillator_number = 10
    sma_sum_daily = 0
    sma_sum_weekly = 0 
    sma_sum_monthly = 0
    oscillator_sum_daily = 0 
    oscillator_sum_weekly = 0
    oscillator_sum_monthly = 0
    for index, val in self.technical_df.iteritems():
        if(index == "RSI"): sma_flag = False
        if(sma_flag):
            sma_sum_daily += val["daily"]
            sma_sum_weekly += val["weekly"]
            sma_sum_monthly += val["monthly"]
        else:
            oscillator_sum_daily += val["daily"]
            oscillator_sum_weekly += val["weekly"]
            oscillator_sum_monthly += val["monthly"]
    
    self.market_df.loc[market, 'Technical Score daily'] = score_to_sentiment((sma_sum_daily + oscillator_sum_daily)/(sma_number+oscillator_number)) 
    self.market_df.loc[market, 'Technical Score weekly'] = score_to_sentiment((sma_sum_weekly + oscillator_sum_daily)/(sma_number+oscillator_number))
    self.market_df.loc[market, 'Technical Score monthly'] = score_to_sentiment((sma_sum_monthly + oscillator_sum_monthly)/(sma_number+oscillator_number))
    self.total_scores += sma_sum_daily + oscillator_sum_daily + sma_sum_weekly + oscillator_sum_daily + sma_sum_monthly + oscillator_sum_monthly

def score_to_sentiment(score):
    if(-1 <= score < -0.5): return ("Strong Sell")
    elif( -0.5 <= score < -0.1): return ("Sell")
    elif(-0.1 <= score <= 0.1): return ("Netural")
    elif(0.1 < score <= 0.5): return ("Buy")
    elif(0.5 < score <=1): return ("Strong Buy")
    

def color_map(val):
    if val == "Strong Buy" or val == 'Buy' or val == 'Positive':
        color = 'green'
    elif val == "Strong Sell" or val =="Sell" or val=="Negative":
        color = 'black'
    else:
        color = 'gray'
    return 'color: %s' % color

