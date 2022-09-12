from concurrent.futures import ThreadPoolExecutor
from timeit import timeit
from tracemalloc import start
from typing import Counter
from numpy import sinc
import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import time
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from pathlib import Path
import pandas as pd
import yfinance as yf
import talib as ta
from ta.trend import *
from ta.momentum import *
from ta.others import *
from ta.utils import *
from ta.volatility import *
from ta.volume import *
import pymannkendall as mk
import traceback
import glob


# market_1d.to_csv("market_1d.csv")
# market_1wk.to_csv("market_1wk.csv")
# market_1mo.to_csv("market_1mo.csv")

# need to check if im taking monthhlylast closing price if its make sense.
#add try and except in every place you need 
# add finish print line after finish reading article or news

load_dotenv("api.env")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
# url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
headers = {
 "X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com",
 "X-RapidAPI-Key": os.getenv('sa_api_key')
}

global total_scores, total_properties, daily_scores, daily_properties, weekly_scores, weekly_properties, monthly_scores, monthly_properties
global cut, index, articles_score, articles_properties, news_score, news_properties
start_run_time = time.time()
cut = 0
articles_properties = 0
articles_score = 0
news_score = 0
news_properties = 0
index = 0
total_scores = 0
total_properties = 0
daily_scores = 0
daily_properties = 0
weekly_scores = 0
weekly_properties = 0
monthly_scores = 0
monthly_properties = 0

class BackTestingCorona:   
    def __init__(self):
        global total_scores, total_properties, daily_scores, daily_properties, weekly_scores, weekly_properties, monthly_scores, monthly_properties
        global index
        results_path = Path.cwd() / 'Results' / 'BackTesting' 
        if not results_path.exists():
            results_path.mkdir(parents=True)
        self.market_df = pd.DataFrame(columns=['News Sentiment','Article Sentiment','Technical Score daily',
            'Technical Score weekly','Technical Score monthly','Final Score','Date'])
        market_1d = pd.read_csv("market_1d_short.csv")
        market_1wk = pd.read_csv("market_1wk_short.csv")
        market_1mo = pd.read_csv("market_1mo_short.csv")
        self.technical_weight = 0.03
        self.monthly_weight = 0.17
        self.news_weight = 0.3
        self.articles_weight = 0.5
        run_back_testing(self,market_1d, market_1wk, market_1mo,results_path)
        self.market_df.to_csv(results_path / f"final_sentiment_spy_corona_weights.csv")
        print(f'TOTAL RUN TIME WAS: {round((time.time() - start_run_time)/60, 2)}')

def convert_indicies(market):
    if(market == 'spy'): return 'SPX'
    if(market == 'qqq'): return 'NDX'
    if(market == 'dia'): return 'DJI'


def download_symbol_data(market):
    try:
        market_1d = yf.download(market,period='5y',interval='1d')
        market_1d = pd.DataFrame(market_1d)
        market_1d.reset_index(inplace=True)
        market_1wk = yf.download(market,period='10y',interval='1wk')
        market_1wk = pd.DataFrame(market_1wk)
        market_1wk.reset_index(inplace=True)
        market_1mo = yf.download(market,period='max',interval='1mo')
        market_1mo = pd.DataFrame(market_1mo)
        market_1mo.reset_index(inplace=True)
    except Exception as e:
        print(f"Problem with download data, symbol is {market}, Details: \n {traceback.format_exc()}")
        exit(7)
    return market_1d, market_1wk, market_1mo


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

def add_technical_data(market_1d, market_1wk, market_1mo):
    moving_averages_extract_data(market_1d, market_1wk, market_1mo)
    oscillators_extract_data(market_1d, market_1wk, market_1mo)
    round_date_wk(market_1wk)
    round_date_mo(market_1mo)

def run_back_testing(self,market_1d, market_1wk, market_1mo,results_path):
    global total_scores, total_properties, daily_scores, daily_properties, weekly_scores, weekly_properties, monthly_scores, monthly_properties
    global cut, index, articles_score, articles_properties, news_score, news_properties
    iterator = 0
    hit = 0
    try:
        path_articels = Path.cwd() / 'Results' / 'BackTesting' / 'Corona' / 'Articles Sentiment'    
        path_news = Path.cwd() / 'Results' / 'BackTesting' / 'Corona' / 'News Sentiment'    
        news_files = glob.glob(str(path_news) + "\*.csv")
        articles_files = glob.glob(str(path_articels) + "\*.csv")
        articles_files.reverse()
        start_date = datetime.strptime(market_1d.loc[market_1d.index[-1]]["Date"],"%d/%m/%Y").date()
        stop_date = datetime.strptime(market_1wk.loc[market_1wk.index[-1]]["Date"],"%d/%m/%Y").date() - timedelta(days=3)
        current_date = datetime.strptime(market_1wk.loc[market_1wk.index[-1]]["Date"],"%d/%m/%Y").date()
        month =  datetime.strptime(market_1mo.loc[market_1mo.index[-1]]["Date"],"%d/%m/%Y").date().month
        end_date = datetime.strptime("2020-01-03", "%Y-%m-%d").date()
    except Exception as e:
        print(f"Problem was acuured during getting last date, Details: \n {traceback.format_exc()}")
    while (current_date > end_date):
        self.technical_weight = 0.03
        self.monthly_weight = 0.15
        self.news_weight = 0.32
        self.articles_weight = 0.5
        ma_score_daily(market_1d,market_1wk)
        oscillators_score_daily(market_1d, market_1wk, market_1mo)
        ma_score_weekly(market_1wk)
        oscillators_score_weekly(market_1d, market_1wk, market_1mo)
        if(current_date.month == month or month == 7):
            monthly_scores = 0
            monthly_properties = 0
            ma_score_monthly(market_1mo)
            oscillators_score_monthly(market_1d, market_1wk, market_1mo)
            market_1mo.drop(market_1mo.tail(1).index,inplace = True)
            month =  datetime.strptime(market_1mo.loc[market_1mo.index[-1]]["Date"],"%d/%m/%Y").date().month
        
        news_df = pd.read_csv(news_files[iterator])
        articles_df = pd.read_csv(articles_files[iterator])

        news_score = news_df['Sentiment'].sum()
        news_properties = news_df.shape[0]

        articles_score = articles_df['Sentiment'].sum()
        articles_properties = articles_df.shape[0]


        # total_scores = (daily_scores + weekly_scores + monthly_scores*4)*technical_weight + articles_score*articles_weight + news_score*news_weight
        # total_properties = (daily_properties + weekly_properties + monthly_properties*4)*technical_weight + articles_properties*articles_weight + news_properties*news_weight

        if(score_to_sentiment(articles_score/articles_properties) == "Netural"):
            self.technical_weight = 0.07
            self.monthly_weight = 0.76
            self.news_weight = 0.13
            self.articles_weight = 0.04
        
        total_scores = (daily_scores + weekly_scores)*self.technical_weight + monthly_scores*self.monthly_weight + articles_score*self.articles_weight + news_score*self.news_weight
        total_properties = (daily_properties + weekly_properties)*self.technical_weight + monthly_properties*self.monthly_weight+ articles_properties*self.articles_weight + news_properties*self.news_weight

        if(index != 0):
            sentiment = score_to_sentiment(total_scores/total_properties)
            current_price = float(market_1wk.loc[market_1wk.index[-1]]["Close"])
            if(sentiment == 'Sell' or sentiment == "Strong Sell"):
                if(current_price >= target_price): hit = 1
                else: hit = -1
            elif(sentiment == 'Buy' or sentiment == "Strong Buy"):
                if(current_price <= target_price): hit = 1
                else: hit = -1
            else: hit = 0


        self.market_df.loc[index, 'News Sentiment'] = score_to_sentiment(news_score/news_properties)
        self.market_df.loc[index, 'Article Sentiment'] = score_to_sentiment(articles_score/articles_properties)
        self.market_df.loc[index, 'Technical Score daily'] = score_to_sentiment(daily_scores/daily_properties)
        self.market_df.loc[index, 'Technical Score weekly'] = score_to_sentiment(weekly_scores/weekly_properties)
        self.market_df.loc[index, 'Technical Score monthly'] = score_to_sentiment(monthly_scores/monthly_properties)
        self.market_df.loc[index, 'Final Score'] = score_to_sentiment(total_scores/total_properties)
        self.market_df.loc[index, 'Date'] = current_date
        self.market_df.loc[index, 'HIT'] = hit

        target_price = float(market_1wk.loc[market_1wk.index[-1]]["Close"])
        market_1d.drop(market_1d.tail(cut).index,inplace = True)
        market_1wk.drop(market_1wk.tail(1).index,inplace = True)
        current_date =  datetime.strptime(market_1wk.loc[market_1wk.index[-1]]["Date"],"%d/%m/%Y").date()
        start_date =  datetime.strptime(market_1d.loc[market_1d.index[-1]]["Date"],"%d/%m/%Y").date()
        stop_date =  datetime.strptime(market_1wk.loc[market_1wk.index[-1]]["Date"],"%d/%m/%Y").date() - timedelta(days=3)
        total_scores = 0
        total_properties = 0
        daily_scores = 0
        daily_properties = 0
        weekly_scores = 0
        weekly_properties = 0
        articles_score = 0
        articles_properties = 0
        news_score = 0
        news_properties = 0
        cut = 0
        index += 1
    self.market_df.to_csv(results_path / f"final_sentiment_spy_corona_weights.csv")
    

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


def ma_score_daily(market_1d,market_1wk):
    global daily_scores, daily_properties, cut
    try:
        temp_df = pd.DataFrame()
        it_date =  datetime.strptime(market_1d.loc[market_1d.index[-1]]["Date"],"%d/%m/%Y").date()
        start_week_date =  datetime.strptime(market_1wk.loc[market_1wk.index[-1]]["Date"],"%d/%m/%Y").date()
        start_next_week_date = start_week_date + timedelta(days=7)
        moving_averages = ['SMA10','EMA10','SMA20','EMA20','SMA30','EMA30','SMA50','EMA50','SMA100','EMA100','SMA200','EMA200']
        temp_df = market_1d.copy(deep=True)
        while(start_next_week_date > it_date >= start_week_date):
            for ma in moving_averages:
                daily_properties +=1
                if(temp_df[ma].iloc[-1] > temp_df['Close'].iloc[-1]):
                   daily_scores += -1 
                elif(temp_df[ma].iloc[-1] < temp_df['Close'].iloc[-1]):
                    daily_scores += 1
            temp_df.drop(temp_df.tail(1).index,inplace = True)
            cut += 1
            it_date =  datetime.strptime(temp_df.loc[temp_df.index[-1]]["Date"],"%d/%m/%Y").date()
    except Exception:
        print(f"Problem was accured during scoring MA daily, Details: \n {traceback.format_exc()}")
        daily_properties = 0
        daily_scores = 0

def ma_score_weekly(market_1wk):
    global weekly_scores, weekly_properties
    try:
        moving_averages = ['SMA10','EMA10','SMA20','EMA20','SMA30','EMA30','SMA50','EMA50','SMA100','EMA100','SMA200','EMA200']
        for ma in moving_averages:
            weekly_properties +=1
            if(market_1wk[ma].iloc[-1] > market_1wk['Close'].iloc[-1]):
               weekly_scores += -1 
            elif(market_1wk[ma].iloc[-1] < market_1wk['Close'].iloc[-1]):
                weekly_scores += 1
    except Exception:
        print(f"Problem was accured during scoring MA weekly, Details: \n {traceback.format_exc()}")
        weekly_properties = 0
        weekly_scores = 0


def ma_score_monthly(market_1mo):
    global monthly_scores, monthly_properties
    try:
        moving_averages = ['SMA10','EMA10','SMA20','EMA20','SMA30','EMA30','SMA50','EMA50','SMA100','EMA100','SMA200','EMA200']
        for ma in moving_averages:
            monthly_properties +=1
            if(market_1mo[ma].iloc[-1] > market_1mo['Close'].iloc[-1]):
                monthly_scores += -1 
            elif(market_1mo[ma].iloc[-1] < market_1mo['Close'].iloc[-1]):
                monthly_scores += 1
    except Exception:
        print(f"Problem was accured during scoring MA monthly, Details: \n {traceback.format_exc()}")


def oscillators_score_daily(market_1d, market_1wk, market_1mo):
    global daily_properties
    try:
        it_date =  datetime.strptime(market_1d.loc[market_1d.index[-1]]["Date"],"%d/%m/%Y").date()
        start_week_date =  datetime.strptime(market_1wk.loc[market_1wk.index[-1]]["Date"],"%d/%m/%Y").date()
        start_next_week_date = start_week_date + timedelta(days=7)
        temp_df = market_1d.copy(deep=True)
        while(start_next_week_date > it_date >= start_week_date):
            rsi_sentiment_daily(temp_df, market_1wk, market_1mo)
            stochastic_sentiment_daily(temp_df)
            cci_sentiment_daily(temp_df)
            adx_sentiment_daily(temp_df)
            aws_sentiment_daily(temp_df)
            mom_sentiment_daily(temp_df,market_1wk, market_1mo)
            macd_sentiment_daily(temp_df)
            stochrsi_sentiment_daily(temp_df,market_1wk, market_1mo)
            williams_sentiment_daily(temp_df,market_1wk, market_1mo)
            ultimate_sentiment_daily(temp_df)
            daily_properties += 10
            temp_df.drop(temp_df.tail(1).index,inplace = True)
            it_date =  datetime.strptime(temp_df.loc[temp_df.index[-1]]["Date"],"%d/%m/%Y").date()
    except Exception:
        print(f"Problem was accured during scoring OSCILATORS daily, Details: \n {traceback.format_exc()}")


def oscillators_score_weekly(market_1d, market_1wk, market_1mo):
    global weekly_properties
    rsi_sentiment_weekly(market_1d, market_1wk, market_1mo)
    stochastic_sentiment_weekly(market_1wk)
    cci_sentiment_weekly(market_1wk)
    adx_sentiment_weekly(market_1wk)
    aws_sentiment_weekly(market_1wk)
    mom_sentiment_weekly(market_1d,market_1wk, market_1mo)
    macd_sentiment_weekly(market_1wk)
    stochrsi_sentiment_weekly(market_1d,market_1wk, market_1mo)
    williams_sentiment_weekly(market_1d,market_1wk, market_1mo)
    ultimate_sentiment_weekly(market_1wk)
    weekly_properties += 10


def oscillators_score_monthly(market_1d, market_1wk, market_1mo):
    global monthly_properties
    rsi_sentiment_monthly(market_1d, market_1wk, market_1mo)
    stochastic_sentiment_monthly(market_1mo)
    cci_sentiment_monthly(market_1mo)
    adx_sentiment_monthly(market_1mo)
    aws_sentiment_monthly(market_1mo)
    mom_sentiment_monthly(market_1d,market_1wk, market_1mo)
    macd_sentiment_monthly(market_1mo)
    stochrsi_sentiment_monthly(market_1d,market_1wk, market_1mo)
    williams_sentiment_monthly(market_1d,market_1wk, market_1mo)
    ultimate_sentiment_monthly(market_1mo)
    monthly_properties += 10

def rsi_sentiment_daily(market_1d, market_1wk, market_1mo):
    global daily_scores
    if(market_1d["RSI"].iloc[-1] > 70 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1d') < 0):
        daily_scores += -1 
    elif(market_1d["RSI"].iloc[-1] < 30 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1d') > 0):
       daily_scores += 1

def rsi_sentiment_weekly(market_1d, market_1wk, market_1mo):
    global weekly_scores
    if(market_1wk["RSI"].iloc[-1] > 70 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1wk') < 0):
        weekly_scores += -1 
    elif(market_1wk["RSI"].iloc[-1] < 30 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1wk') > 0):
       weekly_scores += 1


def rsi_sentiment_monthly(market_1d, market_1wk, market_1mo):
    global monthly_scores
    if(market_1mo["RSI"].iloc[-1] > 70 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1mo') < 0):
        monthly_scores += -1 
    elif(market_1mo["RSI"].iloc[-1] < 30 and trend_estimate(market_1d, market_1wk, market_1mo,"RSI",'1mo') > 0):
        monthly_scores += 1


def stochastic_sentiment_daily(market_1d):
    global daily_scores
    if(market_1d["STOCH_S"].iloc[-1] > 80 and market_1d["STOCH_S"].iloc[-1] <= market_1d["STOCH_M"].iloc[-1]):
        daily_scores += -1 
    elif(market_1d["STOCH_S"].iloc[-1] < 20 and market_1d["STOCH_S"].iloc[-1] >= market_1d["STOCH_M"].iloc[-1]):
        daily_scores += 1


def stochastic_sentiment_weekly(market_1wk):
    global weekly_scores
    if(market_1wk["STOCH_S"].iloc[-1] > 80 and market_1wk["STOCH_S"].iloc[-1] <= market_1wk["STOCH_M"].iloc[-1]):
        weekly_scores += -1 
    elif(market_1wk["STOCH_S"].iloc[-1] < 20 and market_1wk["STOCH_S"].iloc[-1] >= market_1wk["STOCH_M"].iloc[-1]):
        weekly_scores += 1

def stochastic_sentiment_monthly(market_1mo):
    global monthly_scores
    if(market_1mo["STOCH_S"].iloc[-1] > 80 and market_1mo["STOCH_S"].iloc[-1] <= market_1mo["STOCH_M"].iloc[-1]):
        monthly_scores += -1 
    elif(market_1mo["STOCH_S"].iloc[-1] < 20 and market_1mo["STOCH_S"].iloc[-1] >= market_1mo["STOCH_M"].iloc[-1]):
        monthly_scores += 1

def cci_sentiment_daily(market_1d):
    global daily_scores
    if(market_1d["CCI"].iloc[-1] > 100 and market_1d["CCI"].iloc[-1] < market_1d["CCI"].iloc[-2]):
        daily_scores += -1 
    elif(market_1d["CCI"].iloc[-1] < -100 and market_1d["CCI"].iloc[-1] > market_1d["CCI"].iloc[-2]):
        daily_scores += 1

def cci_sentiment_weekly(market_1wk):
    global weekly_scores
    if(market_1wk["CCI"].iloc[-1] > 100 and market_1wk["CCI"].iloc[-1] < market_1wk["CCI"].iloc[-2]):
        weekly_scores += -1 
    elif(market_1wk["CCI"].iloc[-1] < -100 and market_1wk["CCI"].iloc[-1] > market_1wk["CCI"].iloc[-2]):
        weekly_scores += 1

def cci_sentiment_monthly(market_1mo):
    global monthly_scores
    if(market_1mo["CCI"].iloc[-1] > 100 and market_1mo["CCI"].iloc[-1] < market_1mo["CCI"].iloc[-2]):
        monthly_scores += -1 
    elif(market_1mo["CCI"].iloc[-1] < -100 and market_1mo["CCI"].iloc[-1] > market_1mo["CCI"].iloc[-2]):
        monthly_scores += 1

def adx_sentiment_daily(market_1d):
    global daily_scores
    if(market_1d["ADX"].iloc[-1] > 20 and market_1d["ADX_D+"].iloc[-1] < market_1d["ADX_D-"].iloc[-1]):
        daily_scores += -1 
    elif(market_1d["ADX"].iloc[-1] > 20 and market_1d["ADX_D+"].iloc[-1] > market_1d["ADX_D-"].iloc[-1]):
        daily_scores += 1

def adx_sentiment_weekly(market_1wk):
    global weekly_scores
    if(market_1wk["ADX"].iloc[-1] > 20 and market_1wk["ADX_D+"].iloc[-1] < market_1wk["ADX_D-"].iloc[-1]):
        weekly_scores += -1 
    elif(market_1wk["ADX"].iloc[-1] > 20 and market_1wk["ADX_D+"].iloc[-1] > market_1wk["ADX_D-"].iloc[-1]):
        weekly_scores += 1


def adx_sentiment_monthly(market_1mo):
    global monthly_scores
    if(market_1mo["ADX"].iloc[-1] > 20 and market_1mo["ADX_D+"].iloc[-1] < market_1mo["ADX_D-"].iloc[-1]):
        monthly_scores += -1 
    elif(market_1mo["ADX"].iloc[-1] > 20 and market_1mo["ADX_D+"].iloc[-1] > market_1mo["ADX_D-"].iloc[-1]):
        monthly_scores += 1

def aws_sentiment_daily(market_1d):
    global daily_scores
    if(market_1d["AWS"].iloc[-1] < 0):
       daily_scores += -1 
    elif(market_1d["AWS"].iloc[-1] > 0):
        daily_scores += 1

def aws_sentiment_weekly(market_1wk):
    global weekly_scores
    if(market_1wk["AWS"].iloc[-1] < 0):
       weekly_scores += -1 
    elif(market_1wk["AWS"].iloc[-1] > 0):
        weekly_scores += 1


def aws_sentiment_monthly(market_1mo):
    global monthly_scores
    if(market_1mo["AWS"].iloc[-1] < 0):
       monthly_scores += -1 
    elif(market_1mo["AWS"].iloc[-1] > 0):
        monthly_scores += 1

def mom_sentiment_daily(market_1d, market_1wk, market_1mo):
    global daily_scores
    if(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1d') < 0):
        daily_scores += -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1d') > 0):
        daily_scores += 1


def mom_sentiment_weekly(market_1d, market_1wk, market_1mo):
    global weekly_scores
    if(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1wk') < 0):
        weekly_scores += -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1wk') > 0):
        weekly_scores += 1

def mom_sentiment_monthly(market_1d, market_1wk, market_1mo):
    global monthly_scores
    if(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1mo') < 0):
        monthly_scores += -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"MOM",'1mo') > 0):
        monthly_scores += 1

def macd_sentiment_daily(market_1d):
    global daily_scores
    if(market_1d["MACD"].iloc[-1] < market_1d["MACD_S"].iloc[-1]):
        daily_scores += -1 
    elif(market_1d["MACD"].iloc[-1] > market_1d["MACD_S"].iloc[-1]):
        daily_scores += 1

def macd_sentiment_weekly(market_1wk):
    global weekly_scores
    if(market_1wk["MACD"].iloc[-1] < market_1wk["MACD_S"].iloc[-1]):
        weekly_scores += -1 
    elif(market_1wk["MACD"].iloc[-1] > market_1wk["MACD_S"].iloc[-1]):
        weekly_scores += 1

def macd_sentiment_monthly(market_1mo):
    global monthly_scores
    if(market_1mo["MACD"].iloc[-1] < market_1mo["MACD_S"].iloc[-1]):
        monthly_scores += -1 
    elif(market_1mo["MACD"].iloc[-1] > market_1mo["MACD_S"].iloc[-1]):
        monthly_scores += 1

def stochrsi_sentiment_daily(market_1d, market_1wk, market_1mo):
    global daily_scores
    if(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1d') > 0 and market_1d["STOCHRSI_K"].iloc[-1] > 80 and market_1d["STOCHRSI_D"].iloc[-1] > 80
        and market_1d["STOCHRSI_K"].iloc[-1] < market_1d["STOCHRSI_D"].iloc[-1]):
        daily_scores += -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1d') < 0 and market_1d["STOCHRSI_K"].iloc[-1] < 20 and market_1d["STOCHRSI_D"].iloc[-1] < 20
        and market_1d["STOCHRSI_K"].iloc[-1] > market_1d["STOCHRSI_D"].iloc[-1]):
        daily_scores += 1

def stochrsi_sentiment_weekly(market_1d, market_1wk, market_1mo):
    global weekly_scores
    if(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1wk') > 0 and market_1wk["STOCHRSI_K"].iloc[-1] > 80 and market_1wk["STOCHRSI_D"].iloc[-1] > 80
        and market_1wk["STOCHRSI_K"].iloc[-1] < market_1wk["STOCHRSI_D"].iloc[-1]):
        weekly_scores += -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1wk') < 0 and market_1wk["STOCHRSI_K"].iloc[-1] < 20 and market_1wk["STOCHRSI_D"].iloc[-1] < 20
        and market_1wk["STOCHRSI_K"].iloc[-1] > market_1wk["STOCHRSI_D"].iloc[-1]):
        weekly_scores += 1

def stochrsi_sentiment_monthly(market_1d, market_1wk, market_1mo):
    global monthly_scores
    if(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1mo') > 0 and market_1mo["STOCHRSI_K"].iloc[-1] > 80 and market_1mo["STOCHRSI_D"].iloc[-1] > 80
        and market_1mo["STOCHRSI_K"].iloc[-1] < market_1mo["STOCHRSI_D"].iloc[-1]):
        monthly_scores += -1 
    elif(trend_estimate(market_1d, market_1wk, market_1mo,"STOCHRSI_K",'1mo') < 0 and market_1mo["STOCHRSI_K"].iloc[-1] < 20 and market_1mo["STOCHRSI_D"].iloc[-1] < 20
        and market_1mo["STOCHRSI_K"].iloc[-1] > market_1mo["STOCHRSI_D"].iloc[-1]):
        monthly_scores += 1

def williams_sentiment_daily(market_1d, market_1wk, market_1mo):
    global daily_scores
    if(market_1d["WILLIAM"].iloc[-1] > -20 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1d') < 0):
        daily_scores += -1 
    elif(market_1d["WILLIAM"].iloc[-1] < -80 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1d') > 0):
        daily_scores += 1

def williams_sentiment_weekly(market_1d, market_1wk, market_1mo):
    global weekly_scores
    if(market_1wk["WILLIAM"].iloc[-1] > -20 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1wk') < 0):
        weekly_scores += -1 
    elif(market_1wk["WILLIAM"].iloc[-1] < -80 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1wk') > 0):
        weekly_scores += 1

def williams_sentiment_monthly(market_1d, market_1wk, market_1mo):
    global monthly_scores
    if(market_1mo["WILLIAM"].iloc[-1] > -20 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1mo') < 0):
        monthly_scores += -1 
    elif(market_1mo["WILLIAM"].iloc[-1] < -80 and trend_estimate(market_1d, market_1wk, market_1mo,"WILLIAM",'1mo') > 0):
        monthly_scores += 1

def ultimate_sentiment_daily(market_1d):
    global daily_scores
    if(market_1d["ULTIMATE"].iloc[-1] < 30):
        daily_scores += -1 
    elif(market_1d["ULTIMATE"].iloc[-1] > 70):
        daily_scores += 1


def ultimate_sentiment_weekly(market_1wk):
    global weekly_scores
    if(market_1wk["ULTIMATE"].iloc[-1] < 30):
        weekly_scores += -1 
    elif(market_1wk["ULTIMATE"].iloc[-1] > 70):
        weekly_scores += 1

def ultimate_sentiment_monthly(market_1mo):
    global monthly_scores
    if(market_1mo["ULTIMATE"].iloc[-1] < 30):
        monthly_scores += -1 
    elif(market_1mo["ULTIMATE"].iloc[-1] > 70):
        monthly_scores += 1

def trend_estimate(market_1d, market_1wk, market_1mo,oscillator, interval):
    index = [1,2,3,4,5,6,7]
    if interval == '1d':
        data = market_1d[oscillator].to_numpy()
        data = data[-7:]
    elif interval == '1wk':
        data = market_1wk[oscillator].to_numpy()
        if(round_date_wk(market_1wk)): data = data[-7:]
        else : data = data[-8:-1]
    elif interval == '1mo':
        data = market_1mo[oscillator].to_numpy()
        if(round_date_mo(market_1mo)): data = data[-7:]
        else : data = data[-8:-1]
    try:
        result = np.polyfit(index,list(data), 1)
        slope = result[-2]
        result_mk = mk.original_test(data)
        if(result_mk.slope < 0.1 and result_mk.slope > -0.1): return 0
    except Exception as e:
        print(f"problem was accured while calculating slope, details: {e}")
        return 0
    return slope


def round_date_mo(df):
    last_date_mo =  datetime.strptime(df.loc[df.index[-1]]["Date"],"%d/%m/%Y").date()
    second_date_mo =  datetime.strptime(df.loc[df.index[-2]]["Date"],"%d/%m/%Y").date()
    if((second_date_mo + relativedelta(months=1)) == last_date_mo):
        return
    df.drop(df.tail(1).index,inplace = True)
    return 

def round_date_wk(df):
    last_date_wk =  datetime.strptime(df.loc[df.index[-1]]["Date"],"%d/%m/%Y").date()
    second_date_wk =  datetime.strptime(df.loc[df.index[-2]]["Date"],"%d/%m/%Y").date()
    if((second_date_wk + timedelta(days=7)) == last_date_wk):
        return
    df.drop(df.tail(1).index,inplace = True)
    return 


def clean_content(content):
    bad = False
    final = ""
    for char in content:
        if(char == "<"):
            bad = True
        if(char == ">"):
            bad = False
        if(not bad):
            final = final + char
    return final.replace(">","")


def sentiment_score(headline):
    tokens = tokenizer(headline,padding = True, truncation = True,  return_tensors='pt')
    result = model(**tokens)
    result = torch.nn.functional.softmax(result.logits, dim=-1)
    return score_num(int(torch.argmax(result))+1)


def score_num(score):
    if(score == 1):
        return 1
    if(score == 2):
        return -1
    if(score == 3):
        return 0
    return 0



def moving_averages_extract_data(market_1d, market_1wk, market_1mo):
    try:
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
    except Exception:
        print(f"Problem was accured during extract MA data, Details: \n {traceback.format_exc()}")

def oscillators_extract_data(market_1d, market_1wk, market_1mo):
    try:
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
    except Exception:
        print(f"Problem was accured during extract OSCILLATORS data, Details: \n {traceback.format_exc()}")


def articles_week_analyzer(articles, date):
    global articles_score
    counter = 1
    sum = 0
    market_articles_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
    results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Articles Sentiment'
    if not results_path.exists():
        results_path.mkdir(parents=True)
    new_row ={}
    for article in articles.values():
        try:
            article_url = article['data']['links']['canonical']
            article = article['data']['attributes']
            article_title = article['title']
            article_date = article['publishOn']
            article_content = article['content']
            article_content = clean_content(article_content)
            article_content_score = sentiment_score(article_content)
            article_summary = article['summary']
            for article_no in article_summary:
                sum += (sentiment_score(article_no))
            if(sum > 0 ): article_summary_score = 1
            elif(sum == 0): article_summary_score = 0
            elif(sum < 0): article_summary_score = -1
            if((article_summary_score + article_content_score) > 0) : final_score = 1
            elif((article_summary_score + article_content_score) < 0) : final_score = -1
            else: final_score = 0
            articles_score += final_score
            new_row['HeadLine'] = article_title
            new_row['Sentiment'] = final_score
            new_row['Date'] = article_date
            new_row["URL"] = article_url
            market_articles_sentiment_df = market_articles_sentiment_df.append(new_row, ignore_index=True)
            print(f'Finish analyse {counter} articles at week {date} | TOTAL RUNTIME: {round((time.time() - start_run_time)/60, 2)} minutes')
        except Exception as e:
            print(f'Problem accured in article No.{counter}, Error details: {e}')

        new_row.clear()
        counter += 1
        sum = 0
    market_articles_sentiment_df.to_csv(results_path / f"articles_sentiment_week_{date}.csv")

def get_all_articles(id):
    url = "https://seeking-alpha.p.rapidapi.com/articles/get-details"
    querystring = {"id": id}
    try:
        article = requests.request("GET", url, headers=headers, params=querystring)
        article = json.loads(article.text)
    except Exception as e:
        print(f'Problem at one of the articles ENCODING PROBLEM: {e}')
    return article

def run_articles_news_processor(start_date, stop_date):
    articles = {}
    articles_id = articles_sentiment(start_date, stop_date)
    count = 0
    with ThreadPoolExecutor(max_workers=6) as executor:
        all_articles = executor.map(get_all_articles, articles_id)
        executor.shutdown(wait=True)
    for article in all_articles:
        articles[count] = article
        count += 1
    articles_week_analyzer(articles,start_date)


def articles_sentiment(start_date, stop_date):
    global articles_properties
    start_date += timedelta(days=1)
    start_date = datetime.strptime(f'{start_date} 06:59:59', '%Y-%m-%d %H:%M:%S')
    # start_date -= timedelta(days=2)
    # stop_date = finish_date - timedelta(days=3)
    since_timestamp = int(start_date.timestamp())
    until_timestamp = time.mktime(time.strptime('2022-10-12 06:59:59', '%Y-%m-%d %H:%M:%S')) + 0.999
    articles = []
    stop = False
    url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
    for page in range(0,7):
        if(stop): break
        querystring = {"until":since_timestamp,"since":until_timestamp,"size":"40","number":page,"category":"market-outlook"}
        try:
            articels_list = requests.request("GET", url, headers=headers, params=querystring)
            articels_list = json.loads(articels_list.text)
            articels_list = articels_list['data']
            for article in articels_list:
                date = article['attributes']['publishOn']
                date = date.replace('T'," ")
                date =  date[:-6]
                date_t = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                if(stop_date >= date_t.date()) : stop = True
                elif(stop == False):
                    articles.append(article['id'])
                    articles_properties += 1
        except Exception as e:
            print(f'EXCEPTION was accured during network connection trying get articles, DETAILS: {e}')
    return articles

def run_market_news_processor(start_date, stop_date):
    market_news_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
    date = datetime.now().strftime("%d.%m.%Y-%I.%M")
    results_path = Path.cwd() / 'Results' / 'BackTesting' /'News Sentiment'
    if not results_path.exists():
        results_path.mkdir(parents=True)
    news_data = get_news_dict(start_date, stop_date)
    market_news_sentiment_df = news_extractor(news_data, start_date)
    try:       
        market_news_sentiment_df.to_csv(results_path / f"market_news_sentiment_{date}.csv")
    except Exception:
        print(f"Problem was accured while tried to save csv file, Details: \n {traceback.format_exc()}")

def news_extractor(news_data, date):
    global news_score
    market_news_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
    stocks_news_dict = {}
    new_row = {}
    counter = 1
    for key, new in news_data.items():
        try:
            title = new['attributes']['title']
            date_time = new['attributes']['publishOn']
            content = new['attributes']['content']
            url = new['links']['canonical']
            url = str(url).replace('"',"")
            content = clean_content(content)
            score = sentiment_score(content)
            news_score += score
            new_row['HeadLine'] = title
            new_row['Sentiment'] = score
            new_row['Date'] = date_time
            new_row["URL"] = url
            market_news_sentiment_df = market_news_sentiment_df.append(new_row, ignore_index=True)
            stocks_news_dict.clear()
            new_row.clear()
            print(f'Finish analyse {counter} news at week {date} | TOTAL RUN TIME: {round((time.time() - start_run_time)/60, 2)} minutes')
            counter += 1
        except Exception as e:
            print(f"f'Problem accured in NEW No.{counter}, Error details: {e}")
            stocks_news_dict.clear()
            new_row.clear()
            counter += 1
    return market_news_sentiment_df


def get_news_dict(start_date, stop_date):    
    global news_properties
    news = {}
    stop = False
    start_date += timedelta(days=1)
    start_date = datetime.strptime(f'{start_date} 06:59:59', '%Y-%m-%d %H:%M:%S')
    since_timestamp = int(start_date.timestamp())
    until_timestamp = time.mktime(time.strptime('2022-10-12 06:59:59', '%Y-%m-%d %H:%M:%S')) + 0.999
    url = "https://seeking-alpha.p.rapidapi.com/news/v2/list"
    for page in range(0,7):
        if(stop): break
        querystring = {"until":since_timestamp,"since":until_timestamp,"size":"40","number":page,"category":"market-news::us-economy"}
        try:
            news_data = requests.request("GET", url, headers=headers, params=querystring)
            news_data = json.loads(news_data.text)
            news_data = news_data['data']
            for new in news_data:
                date = new['attributes']['publishOn']
                date = date.replace('T'," ")
                date =  date[:-6]
                date_t = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                if(stop_date >= date_t.date()) : stop = True
                elif(stop == False):
                    news[date] = new
                    news_properties += 1
        except Exception as e:
            print(f'EXCEPTION was accured during network connection trying get News, DETAILS: {e}')
    return news



def concat_stocks(stocks_news_dict):
    stocks = ""
    for key,value in stocks_news_dict.items():
        if(stocks == ""):
            stocks = value
        else:
            stocks = stocks +", "+ value
    return stocks


def articles_2021():
    articles_sentiment = pd.DataFrame(columns=['Date','Articles Analayzed','Sum Score','Avg'])
    new_row = {}
    path_articels = Path.cwd() / 'Results' / 'BackTesting' / 'Articles 2021' 
    articles_files = glob.glob(str(path_articels) + "\*.csv")
    for article in range(len(articles_files)):
        article_df = pd.read_csv(articles_files[article])
        article_sum_score = article_df['Sentiment'].sum()
        article_size = article_df.shape[0]
        article_date = article_df.loc[0,'Date'][:10]
        new_row['Date'] = article_date
        new_row['Articles Analayzed'] = article_size
        new_row['Sum Score'] = article_sum_score
        new_row['Avg'] = article_sum_score/article_size
        # new_row['Sentiment'] = score_to_sentiment(article_sum_score/article_size)
        articles_sentiment = articles_sentiment.append(new_row, ignore_index=True)
    articles_sentiment.to_csv(path_articels / f"articles_sentiment_2021_TOTAL.csv")

# BackTestingCorona()

articles_2021()

