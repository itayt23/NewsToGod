from concurrent.futures import ThreadPoolExecutor
from timeit import timeit
from tracemalloc import start
from typing import Counter
from numpy import sinc
from pyrsistent import s
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
import subprocess


# sector_1d.to_csv("sector_1d.csv")
# sector_1wk.to_csv("sector_1wk.csv")
# sector_1mo.to_csv("sector_1mo.csv")

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
global cut, articles_score, articles_properties, news_score, news_properties, zacks_score, zacks_properties
# start_run_time = time.time()
zacks_score = 0 
zacks_properties = 1
cut = 0
articles_properties = 1 # TODO: need to change it after dealing with articles
articles_score = 0
news_score = {}
news_properties = {} #TODO: was 1 
total_scores = 0
total_properties = 0
daily_scores = 0
daily_properties = 0
weekly_scores = 0
weekly_properties = 0
monthly_scores = 0
monthly_properties = 0

        # sector_1d.to_csv("sector_1d.csv")
        # sector_1wk.to_csv("sector_1wk.csv")
        # sector_1mo.to_csv("sector_1mo.csv")
class SectorsSentiment:   
    def __init__(self):
        global total_scores, total_properties, daily_scores, daily_properties, weekly_scores, weekly_properties, monthly_scores, monthly_properties, tech_temp
        start_run_time = time.time()
        results_path = Path.cwd() / 'Results' / 'csv_files' / 'Sectors'  
        if not results_path.exists():
            results_path.mkdir(parents=True)
        self.sector_df = pd.DataFrame(index=['XLB','XLC','XLY','XLP','XLE','XLF','XLV','XLI','XLK','XLU','XLRE'],
            columns=['News Sentiment','Article Sentiment','Zacks Rank','Technical Score daily','Technical Score weekly',
                'Technical Score monthly','Final Score','Date'])
        self.technical_df = pd.DataFrame(index=['daily','weekly','monthly'],columns=['SMA10','EMA10','SMA20','EMA20','SMA30','EMA30',
            'SMA50','EMA50','SMA100','EMA100','SMA200','EMA200','RSI','STOCH','CCI','ADX','AWS','MOM','MACD','STOCHRSI','WILLIAM','ULTIMATE'])
        sectors = ['XLB','XLC','XLY','XLP','XLE','XLF','XLV','XLI','XLK','XLU','XLRE']
        self.sentiment = 0
        self.materials_sentiment = 0
        self.communication_sentimennt = 0
        self.energy_sentiment = 0
        self.finance_sentiment = 0
        self.consumer_discretionary_sentiment = 0 
        self.consumer_staples_sentiment = 0 
        self.healthcare_sentiment = 0
        self.industrial_sentiment = 0
        self.technology_sentiment = 0
        self.utilities_sentiment = 0
        self.real_estate_sentiment = 0
        for sector in sectors:
            news_score[sector] = 0
            news_properties[sector] = 1
            sector_1d, sector_1wk, sector_1mo = download_symbol_data(sector)
            sector_1d, sector_1wk, sector_1mo = clean_df_nans(sector_1d, sector_1wk, sector_1mo)
            add_technical_data(sector_1d, sector_1wk, sector_1mo)
            run(self,sector_1d, sector_1wk, sector_1mo, sector,start_run_time)
            print(f'FINISH ANALYSE {sector} | TOTAL RUN TIME: {round((time.time() - start_run_time)/60, 2)} minutes')
        self.sector_df.to_csv(results_path / f"Sectors final sentiment {date.today()}.csv")
        print(f'TOTAL RUN TIME WAS: {round((time.time() - start_run_time)/60, 2)} minutes')
      
    def get_sentiment_number(self):
        return self.sentiment

    def get_sentiment(self):
        return score_to_sentiment(self.sentiment) 
    
    def print_all_sentiment(self): #BETWEEN -1 AND 1 
        print(f'XLB: {self.materials_sentiment}')
        print(f'XLC: {self.communication_sentimennt}')
        print(f'XLY: {self.consumer_discretionary_sentiment}')
        print(f'XLP: {self.consumer_staples_sentiment}')
        print(f'XLE: {self.energy_sentiment}')
        print(f'XLF: {self.finance_sentiment}')
        print(f'XLV: {self.healthcare_sentiment}')
        print(f'XLI: {self.industrial_sentiment}')
        print(f'XLK: {self.technology_sentiment}')
        print(f'XLU: {self.utilities_sentiment}')
        print(f'XLRE: {self.real_estate_sentiment}')
def download_symbol_data(sector):
    try:
        sector_1d = yf.download(sector,period='5y',interval='1d')
        sector_1d = pd.DataFrame(sector_1d)
        sector_1d.reset_index(inplace=True)
        sector_1wk = yf.download(sector,period='10y',interval='1wk')
        sector_1wk = pd.DataFrame(sector_1wk)
        sector_1wk.reset_index(inplace=True)
        sector_1mo = yf.download(sector,period='max',interval='1mo')
        sector_1mo = pd.DataFrame(sector_1mo)
        sector_1mo.reset_index(inplace=True)
    except Exception as e:
        print(f"Problem with download data, symbol is {sector}, Details: \n {traceback.format_exc()}")
        exit(7)
    return sector_1d, sector_1wk, sector_1mo


def clean_df_nans(sector_1d, sector_1wk, sector_1mo):
    for row in sector_1wk.index:
        if(str(sector_1wk['Close'][row]) == 'nan' ):
           sector_1wk = sector_1wk.drop(axis=0,index=[row])
    for row in sector_1d.index:
        if(str(sector_1d['Close'][row]) == 'nan' ):
           sector_1d = sector_1d.drop(axis=0,index=[row])
    for row in sector_1mo.index:
        if(str(sector_1mo['Close'][row]) == 'nan' ):
           sector_1mo = sector_1mo.drop(axis=0,index=[row])
    return  sector_1d, sector_1wk, sector_1mo

def add_technical_data(sector_1d, sector_1wk, sector_1mo):
    moving_averages_extract_data(sector_1d, sector_1wk, sector_1mo)
    oscillators_extract_data(sector_1d, sector_1wk, sector_1mo)
    round_date_wk(sector_1wk)
    round_date_mo(sector_1mo)
    # start_date = sector_1wk.loc[sector_1wk.index[-1]]["Date"].date() #datetime.date
    # date_1d = sector_1d.loc[sector_1d.index[-1]]["Date"].date() 
    # while(start_date != date_1d):
    #     sector_1d.drop(sector_1d.tail(1).index,inplace = True)
    #     date_1d = sector_1d.loc[sector_1d.index[-1]]["Date"].date() 

def run(self,sector_1d, sector_1wk, sector_1mo,sector,start_run_time):
    global total_scores, total_properties, daily_scores, daily_properties, weekly_scores, weekly_properties, monthly_scores, monthly_properties
    global cut, index, articles_score, articles_properties, news_score, news_properties,zacks_score,zacks_properties
    try:
        start_date_news = today = date.today()
        start_week = today - timedelta(days=today.weekday())
        start_date = sector_1d.loc[sector_1d.index[-1]]["Date"].date()
        stop_date = sector_1wk.loc[sector_1wk.index[-1]]["Date"].date() - timedelta(days=3)
        current_date = sector_1wk.loc[sector_1wk.index[-1]]["Date"].date() # !i think i dont need this
        month = sector_1mo.loc[sector_1mo.index[-1]]["Date"].date().month
        end_date = datetime.strptime("2021-01-01", "%Y-%m-%d").date()
    except Exception as e:
        print(f"Problem was acuured during getting last date, Details: \n {traceback.format_exc()}")
    ma_score_daily(sector_1d,sector_1wk)
    oscillators_score_daily(sector_1d, sector_1wk, sector_1mo)
    ma_score_weekly(sector_1wk)
    oscillators_score_weekly(sector_1d, sector_1wk, sector_1mo)
    if(current_date.month == month or start_date.month == month):
        monthly_scores = 0
        monthly_properties = 0
        ma_score_monthly(sector_1mo)
        oscillators_score_monthly(sector_1d, sector_1wk, sector_1mo)
        sector_1mo.drop(sector_1mo.tail(1).index,inplace = True)
        month = sector_1mo.loc[sector_1mo.index[-1]]["Date"].date().month
    zacks_score = run_zacks_rank(sector)
    run_sectors_news_processor(start_date_news, stop_date, sector,start_run_time)
    
    # run_sectors_news_processor(start_date_news, stop_date,sector)
    # run_articles_news_processor(start_date_news, stop_date)
    total_scores = daily_scores + weekly_scores + monthly_scores + articles_score + news_score[sector] + zacks_score
    total_properties = daily_properties + weekly_properties + monthly_properties + articles_properties + news_properties[sector] + zacks_properties
    self.sector_df.loc[sector, 'News Sentiment'] = score_to_sentiment(news_score[sector]/news_properties[sector])
    self.sector_df.loc[sector, 'Article Sentiment'] = score_to_sentiment(articles_score/articles_properties)
    self.sector_df.loc[sector, 'Zacks Rank'] = zacks_to_sentiment(zacks_score)
    self.sector_df.loc[sector, 'Technical Score daily'] = score_to_sentiment(daily_scores/daily_properties)
    self.sector_df.loc[sector, 'Technical Score weekly'] = score_to_sentiment(weekly_scores/weekly_properties)
    self.sector_df.loc[sector, 'Technical Score monthly'] = score_to_sentiment(monthly_scores/monthly_properties)
    self.sector_df.loc[sector, 'Final Score'] = score_to_sentiment(total_scores/total_properties)
    self.sector_df.loc[sector, 'Date'] = current_date
    update_sentiment(self, sector)
    sector_1d.drop(sector_1d.tail(cut).index,inplace = True)
    sector_1wk.drop(sector_1wk.tail(1).index,inplace = True)
    current_date = sector_1wk.loc[sector_1wk.index[-1]]["Date"].date()
    start_date = sector_1d.loc[sector_1d.index[-1]]["Date"].date()
    stop_date = sector_1wk.loc[sector_1wk.index[-1]]["Date"].date() - timedelta(days=3)
    total_scores = 0
    total_properties = 0
    daily_scores = 0
    daily_properties = 0
    weekly_scores = 0
    weekly_properties = 0
    articles_score = 0
    articles_properties = 1
    zacks_score = 0
    cut = 0
    # self.sector_df.to_csv(results_path / f"final_sentiment_spy.csv")
    
def run_zacks_rank(sector):
    global zacks_score
    try:
        data = subprocess.Popen("zacks-api "+sector, shell=True, stdout=subprocess.PIPE).stdout.read()
        data = str(data, 'utf-8')
        data = data.strip("\r\n")
        data = data.split(',')
        for line in data:
            if 'zacksRank' in line and line != 'zacksRankText':
                rating = line
        rating = rating.split(":")
        rating = rating[1]
        rating = rating.strip(" ").replace('"',"")
        rating = int(rating)
        zacks_score = zacks_to_score(rating)
        return rating
    except Exception as e:
        print('Problem with Zacks website: '+str(e))
        return 0
def update_sentiment(self,sector):
    global total_scores,total_properties
    if(sector == 'XLB'):  self.materials_sentiment = total_scores/total_properties
    elif(sector == 'XLC'): self.communication_sentimennt = total_scores/total_properties
    elif(sector == 'XLY'): self.consumer_discretionary_sentiment = total_scores/total_properties
    elif(sector == 'XLP'): self.consumer_staples_sentiment = total_scores/total_properties
    elif(sector == 'XLE'): self.energy_sentiment = total_scores/total_properties
    elif(sector == 'XLF'): self.finance_sentiment = total_scores/total_properties
    elif(sector == 'XLV'): self.healthcare_sentiment = total_scores/total_properties
    elif(sector == 'XLI'): self.industrial_sentiment = total_scores/total_properties
    elif(sector == 'XLK'): self.technology_sentiment = total_scores/total_properties
    elif(sector == 'XLU'): self.utilities_sentiment = total_scores/total_properties
    elif(sector == 'XLRE'): self.real_estate_sentiment = total_scores/total_properties

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
    
    self.sector_df.loc[market, 'Technical Score daily'] = score_to_sentiment((sma_sum_daily + oscillator_sum_daily)/(sma_number+oscillator_number)) 
    self.sector_df.loc[market, 'Technical Score weekly'] = score_to_sentiment((sma_sum_weekly + oscillator_sum_daily)/(sma_number+oscillator_number))
    self.sector_df.loc[market, 'Technical Score monthly'] = score_to_sentiment((sma_sum_monthly + oscillator_sum_monthly)/(sma_number+oscillator_number))
    self.total_scores += sma_sum_daily + oscillator_sum_daily + sma_sum_weekly + oscillator_sum_daily + sma_sum_monthly + oscillator_sum_monthly

def score_to_sentiment(score):
    if(-1 <= score < -0.5): return ("Strong Sell")
    elif( -0.5 <= score < -0.1): return ("Sell")
    elif(-0.1 <= score <= 0.1): return ("Netural")
    elif(0.1 < score <= 0.5): return ("Buy")
    elif(0.5 < score <=1): return ("Strong Buy")

def zacks_to_sentiment(score):
    if(score == 1): return ("Strong Sell")
    elif(score == 2): return ("Sell")
    elif(score == 3): return ("Netural")
    elif(score == 4): return ("Buy")
    elif(score == 5): return ("Strong Buy")


def ma_score_daily(sector_1d,sector_1wk):
    global daily_scores, daily_properties, cut
    try:
        temp_df = pd.DataFrame()
        it_date = sector_1d.loc[sector_1d.index[-1]]["Date"].date()
        stop_date = sector_1wk.loc[sector_1wk.index[-1]]["Date"].date() 
        #start_next_week_date = stop_date + timedelta(days=7) #! need to check why i needs this?
        moving_averages = ['SMA10','EMA10','SMA20','EMA20','SMA30','EMA30','SMA50','EMA50','SMA100','EMA100','SMA200','EMA200']
        temp_df = sector_1d.copy(deep=True)
        while(it_date >= stop_date):
            for ma in moving_averages:
                daily_properties +=1
                if(temp_df[ma].iloc[-1] > temp_df['Close'].iloc[-1]):
                   daily_scores += -1 
                elif(temp_df[ma].iloc[-1] < temp_df['Close'].iloc[-1]):
                    daily_scores += 1
            temp_df.drop(temp_df.tail(1).index,inplace = True)
            cut += 1
            it_date = temp_df.loc[temp_df.index[-1]]["Date"].date()
    except Exception:
        print(f"Problem was accured during scoring MA daily, Details: \n {traceback.format_exc()}")
        daily_properties = 0
        daily_scores = 0

def ma_score_weekly(sector_1wk): #! here i can add some more days into the week...currently im taking just week before
    global weekly_scores, weekly_properties
    try:
        moving_averages = ['SMA10','EMA10','SMA20','EMA20','SMA30','EMA30','SMA50','EMA50','SMA100','EMA100','SMA200','EMA200']
        for ma in moving_averages:
            weekly_properties +=1
            if(sector_1wk[ma].iloc[-1] > sector_1wk['Close'].iloc[-1]):
               weekly_scores += -1 
            elif(sector_1wk[ma].iloc[-1] < sector_1wk['Close'].iloc[-1]):
                weekly_scores += 1
    except Exception:
        print(f"Problem was accured during scoring MA weekly, Details: \n {traceback.format_exc()}")
        weekly_properties = 0
        weekly_scores = 0


def ma_score_monthly(sector_1mo):
    global monthly_scores, monthly_properties
    try:
        moving_averages = ['SMA10','EMA10','SMA20','EMA20','SMA30','EMA30','SMA50','EMA50','SMA100','EMA100','SMA200','EMA200']
        for ma in moving_averages:
            monthly_properties +=1
            if(sector_1mo[ma].iloc[-1] > sector_1mo['Close'].iloc[-1]):
                monthly_scores += -1 
            elif(sector_1mo[ma].iloc[-1] < sector_1mo['Close'].iloc[-1]):
                monthly_scores += 1
    except Exception:
        print(f"Problem was accured during scoring MA monthly, Details: \n {traceback.format_exc()}")


def oscillators_score_daily(sector_1d, sector_1wk, sector_1mo):
    global daily_properties
    try:
        it_date = sector_1d.loc[sector_1d.index[-1]]["Date"].date()
        stop_date = sector_1wk.loc[sector_1wk.index[-1]]["Date"].date()
        # start_next_week_date = start_week_date + timedelta(days=7)
        temp_df = sector_1d.copy(deep=True)
        while(it_date >= stop_date):
            rsi_sentiment_daily(temp_df, sector_1wk, sector_1mo)
            stochastic_sentiment_daily(temp_df)
            cci_sentiment_daily(temp_df)
            adx_sentiment_daily(temp_df)
            aws_sentiment_daily(temp_df)
            mom_sentiment_daily(temp_df,sector_1wk, sector_1mo)
            macd_sentiment_daily(temp_df)
            stochrsi_sentiment_daily(temp_df,sector_1wk, sector_1mo)
            williams_sentiment_daily(temp_df,sector_1wk, sector_1mo)
            ultimate_sentiment_daily(temp_df)
            daily_properties += 10
            temp_df.drop(temp_df.tail(1).index,inplace = True)
            it_date = temp_df.loc[temp_df.index[-1]]["Date"].date()
    except Exception:
        print(f"Problem was accured during scoring OSCILATORS daily, Details: \n {traceback.format_exc()}")


def oscillators_score_weekly(sector_1d, sector_1wk, sector_1mo):
    global weekly_properties
    rsi_sentiment_weekly(sector_1d, sector_1wk, sector_1mo)
    stochastic_sentiment_weekly(sector_1wk)
    cci_sentiment_weekly(sector_1wk)
    adx_sentiment_weekly(sector_1wk)
    aws_sentiment_weekly(sector_1wk)
    mom_sentiment_weekly(sector_1d,sector_1wk, sector_1mo)
    macd_sentiment_weekly(sector_1wk)
    stochrsi_sentiment_weekly(sector_1d,sector_1wk, sector_1mo)
    williams_sentiment_weekly(sector_1d,sector_1wk, sector_1mo)
    ultimate_sentiment_weekly(sector_1wk)
    weekly_properties += 10


def oscillators_score_monthly(sector_1d, sector_1wk, sector_1mo):
    global monthly_properties
    rsi_sentiment_monthly(sector_1d, sector_1wk, sector_1mo)
    stochastic_sentiment_monthly(sector_1mo)
    cci_sentiment_monthly(sector_1mo)
    adx_sentiment_monthly(sector_1mo)
    aws_sentiment_monthly(sector_1mo)
    mom_sentiment_monthly(sector_1d,sector_1wk, sector_1mo)
    macd_sentiment_monthly(sector_1mo)
    stochrsi_sentiment_monthly(sector_1d,sector_1wk, sector_1mo)
    williams_sentiment_monthly(sector_1d,sector_1wk, sector_1mo)
    ultimate_sentiment_monthly(sector_1mo)
    monthly_properties += 10

def rsi_sentiment_daily(sector_1d, sector_1wk, sector_1mo):
    global daily_scores
    if(sector_1d["RSI"].iloc[-1] > 70 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"RSI",'1d') < 0):
        daily_scores += -1 
    elif(sector_1d["RSI"].iloc[-1] < 30 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"RSI",'1d') > 0):
       daily_scores += 1

def rsi_sentiment_weekly(sector_1d, sector_1wk, sector_1mo):
    global weekly_scores
    if(sector_1wk["RSI"].iloc[-1] > 70 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"RSI",'1wk') < 0):
        weekly_scores += -1 
    elif(sector_1wk["RSI"].iloc[-1] < 30 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"RSI",'1wk') > 0):
       weekly_scores += 1


def rsi_sentiment_monthly(sector_1d, sector_1wk, sector_1mo):
    global monthly_scores
    if(sector_1mo["RSI"].iloc[-1] > 70 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"RSI",'1mo') < 0):
        monthly_scores += -1 
    elif(sector_1mo["RSI"].iloc[-1] < 30 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"RSI",'1mo') > 0):
        monthly_scores += 1


def stochastic_sentiment_daily(sector_1d):
    global daily_scores
    if(sector_1d["STOCH_S"].iloc[-1] > 80 and sector_1d["STOCH_S"].iloc[-1] <= sector_1d["STOCH_M"].iloc[-1]):
        daily_scores += -1 
    elif(sector_1d["STOCH_S"].iloc[-1] < 20 and sector_1d["STOCH_S"].iloc[-1] >= sector_1d["STOCH_M"].iloc[-1]):
        daily_scores += 1


def stochastic_sentiment_weekly(sector_1wk):
    global weekly_scores
    if(sector_1wk["STOCH_S"].iloc[-1] > 80 and sector_1wk["STOCH_S"].iloc[-1] <= sector_1wk["STOCH_M"].iloc[-1]):
        weekly_scores += -1 
    elif(sector_1wk["STOCH_S"].iloc[-1] < 20 and sector_1wk["STOCH_S"].iloc[-1] >= sector_1wk["STOCH_M"].iloc[-1]):
        weekly_scores += 1

def stochastic_sentiment_monthly(sector_1mo):
    global monthly_scores
    if(sector_1mo["STOCH_S"].iloc[-1] > 80 and sector_1mo["STOCH_S"].iloc[-1] <= sector_1mo["STOCH_M"].iloc[-1]):
        monthly_scores += -1 
    elif(sector_1mo["STOCH_S"].iloc[-1] < 20 and sector_1mo["STOCH_S"].iloc[-1] >= sector_1mo["STOCH_M"].iloc[-1]):
        monthly_scores += 1

def cci_sentiment_daily(sector_1d):
    global daily_scores
    if(sector_1d["CCI"].iloc[-1] > 100 and sector_1d["CCI"].iloc[-1] < sector_1d["CCI"].iloc[-2]):
        daily_scores += -1 
    elif(sector_1d["CCI"].iloc[-1] < -100 and sector_1d["CCI"].iloc[-1] > sector_1d["CCI"].iloc[-2]):
        daily_scores += 1

def cci_sentiment_weekly(sector_1wk):
    global weekly_scores
    if(sector_1wk["CCI"].iloc[-1] > 100 and sector_1wk["CCI"].iloc[-1] < sector_1wk["CCI"].iloc[-2]):
        weekly_scores += -1 
    elif(sector_1wk["CCI"].iloc[-1] < -100 and sector_1wk["CCI"].iloc[-1] > sector_1wk["CCI"].iloc[-2]):
        weekly_scores += 1

def cci_sentiment_monthly(sector_1mo):
    global monthly_scores
    if(sector_1mo["CCI"].iloc[-1] > 100 and sector_1mo["CCI"].iloc[-1] < sector_1mo["CCI"].iloc[-2]):
        monthly_scores += -1 
    elif(sector_1mo["CCI"].iloc[-1] < -100 and sector_1mo["CCI"].iloc[-1] > sector_1mo["CCI"].iloc[-2]):
        monthly_scores += 1

def adx_sentiment_daily(sector_1d):
    global daily_scores
    if(sector_1d["ADX"].iloc[-1] > 20 and sector_1d["ADX_D+"].iloc[-1] < sector_1d["ADX_D-"].iloc[-1]):
        daily_scores += -1 
    elif(sector_1d["ADX"].iloc[-1] > 20 and sector_1d["ADX_D+"].iloc[-1] > sector_1d["ADX_D-"].iloc[-1]):
        daily_scores += 1

def adx_sentiment_weekly(sector_1wk):
    global weekly_scores
    if(sector_1wk["ADX"].iloc[-1] > 20 and sector_1wk["ADX_D+"].iloc[-1] < sector_1wk["ADX_D-"].iloc[-1]):
        weekly_scores += -1 
    elif(sector_1wk["ADX"].iloc[-1] > 20 and sector_1wk["ADX_D+"].iloc[-1] > sector_1wk["ADX_D-"].iloc[-1]):
        weekly_scores += 1


def adx_sentiment_monthly(sector_1mo):
    global monthly_scores
    if(sector_1mo["ADX"].iloc[-1] > 20 and sector_1mo["ADX_D+"].iloc[-1] < sector_1mo["ADX_D-"].iloc[-1]):
        monthly_scores += -1 
    elif(sector_1mo["ADX"].iloc[-1] > 20 and sector_1mo["ADX_D+"].iloc[-1] > sector_1mo["ADX_D-"].iloc[-1]):
        monthly_scores += 1

def aws_sentiment_daily(sector_1d):
    global daily_scores
    if(sector_1d["AWS"].iloc[-1] < 0):
       daily_scores += -1 
    elif(sector_1d["AWS"].iloc[-1] > 0):
        daily_scores += 1

def aws_sentiment_weekly(sector_1wk):
    global weekly_scores
    if(sector_1wk["AWS"].iloc[-1] < 0):
       weekly_scores += -1 
    elif(sector_1wk["AWS"].iloc[-1] > 0):
        weekly_scores += 1


def aws_sentiment_monthly(sector_1mo):
    global monthly_scores
    if(sector_1mo["AWS"].iloc[-1] < 0):
       monthly_scores += -1 
    elif(sector_1mo["AWS"].iloc[-1] > 0):
        monthly_scores += 1

def mom_sentiment_daily(sector_1d, sector_1wk, sector_1mo):
    global daily_scores
    if(trend_estimate(sector_1d, sector_1wk, sector_1mo,"MOM",'1d') < 0):
        daily_scores += -1 
    elif(trend_estimate(sector_1d, sector_1wk, sector_1mo,"MOM",'1d') > 0):
        daily_scores += 1


def mom_sentiment_weekly(sector_1d, sector_1wk, sector_1mo):
    global weekly_scores
    if(trend_estimate(sector_1d, sector_1wk, sector_1mo,"MOM",'1wk') < 0):
        weekly_scores += -1 
    elif(trend_estimate(sector_1d, sector_1wk, sector_1mo,"MOM",'1wk') > 0):
        weekly_scores += 1

def mom_sentiment_monthly(sector_1d, sector_1wk, sector_1mo):
    global monthly_scores
    if(trend_estimate(sector_1d, sector_1wk, sector_1mo,"MOM",'1mo') < 0):
        monthly_scores += -1 
    elif(trend_estimate(sector_1d, sector_1wk, sector_1mo,"MOM",'1mo') > 0):
        monthly_scores += 1

def macd_sentiment_daily(sector_1d):
    global daily_scores
    if(sector_1d["MACD"].iloc[-1] < sector_1d["MACD_S"].iloc[-1]):
        daily_scores += -1 
    elif(sector_1d["MACD"].iloc[-1] > sector_1d["MACD_S"].iloc[-1]):
        daily_scores += 1

def macd_sentiment_weekly(sector_1wk):
    global weekly_scores
    if(sector_1wk["MACD"].iloc[-1] < sector_1wk["MACD_S"].iloc[-1]):
        weekly_scores += -1 
    elif(sector_1wk["MACD"].iloc[-1] > sector_1wk["MACD_S"].iloc[-1]):
        weekly_scores += 1

def macd_sentiment_monthly(sector_1mo):
    global monthly_scores
    if(sector_1mo["MACD"].iloc[-1] < sector_1mo["MACD_S"].iloc[-1]):
        monthly_scores += -1 
    elif(sector_1mo["MACD"].iloc[-1] > sector_1mo["MACD_S"].iloc[-1]):
        monthly_scores += 1

def stochrsi_sentiment_daily(sector_1d, sector_1wk, sector_1mo):
    global daily_scores
    if(trend_estimate(sector_1d, sector_1wk, sector_1mo,"STOCHRSI_K",'1d') > 0 and sector_1d["STOCHRSI_K"].iloc[-1] > 80 and sector_1d["STOCHRSI_D"].iloc[-1] > 80
        and sector_1d["STOCHRSI_K"].iloc[-1] < sector_1d["STOCHRSI_D"].iloc[-1]):
        daily_scores += -1 
    elif(trend_estimate(sector_1d, sector_1wk, sector_1mo,"STOCHRSI_K",'1d') < 0 and sector_1d["STOCHRSI_K"].iloc[-1] < 20 and sector_1d["STOCHRSI_D"].iloc[-1] < 20
        and sector_1d["STOCHRSI_K"].iloc[-1] > sector_1d["STOCHRSI_D"].iloc[-1]):
        daily_scores += 1

def stochrsi_sentiment_weekly(sector_1d, sector_1wk, sector_1mo):
    global weekly_scores
    if(trend_estimate(sector_1d, sector_1wk, sector_1mo,"STOCHRSI_K",'1wk') > 0 and sector_1wk["STOCHRSI_K"].iloc[-1] > 80 and sector_1wk["STOCHRSI_D"].iloc[-1] > 80
        and sector_1wk["STOCHRSI_K"].iloc[-1] < sector_1wk["STOCHRSI_D"].iloc[-1]):
        weekly_scores += -1 
    elif(trend_estimate(sector_1d, sector_1wk, sector_1mo,"STOCHRSI_K",'1wk') < 0 and sector_1wk["STOCHRSI_K"].iloc[-1] < 20 and sector_1wk["STOCHRSI_D"].iloc[-1] < 20
        and sector_1wk["STOCHRSI_K"].iloc[-1] > sector_1wk["STOCHRSI_D"].iloc[-1]):
        weekly_scores += 1

def stochrsi_sentiment_monthly(sector_1d, sector_1wk, sector_1mo):
    global monthly_scores
    if(trend_estimate(sector_1d, sector_1wk, sector_1mo,"STOCHRSI_K",'1mo') > 0 and sector_1mo["STOCHRSI_K"].iloc[-1] > 80 and sector_1mo["STOCHRSI_D"].iloc[-1] > 80
        and sector_1mo["STOCHRSI_K"].iloc[-1] < sector_1mo["STOCHRSI_D"].iloc[-1]):
        monthly_scores += -1 
    elif(trend_estimate(sector_1d, sector_1wk, sector_1mo,"STOCHRSI_K",'1mo') < 0 and sector_1mo["STOCHRSI_K"].iloc[-1] < 20 and sector_1mo["STOCHRSI_D"].iloc[-1] < 20
        and sector_1mo["STOCHRSI_K"].iloc[-1] > sector_1mo["STOCHRSI_D"].iloc[-1]):
        monthly_scores += 1

def williams_sentiment_daily(sector_1d, sector_1wk, sector_1mo):
    global daily_scores
    if(sector_1d["WILLIAM"].iloc[-1] > -20 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"WILLIAM",'1d') < 0):
        daily_scores += -1 
    elif(sector_1d["WILLIAM"].iloc[-1] < -80 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"WILLIAM",'1d') > 0):
        daily_scores += 1

def williams_sentiment_weekly(sector_1d, sector_1wk, sector_1mo):
    global weekly_scores
    if(sector_1wk["WILLIAM"].iloc[-1] > -20 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"WILLIAM",'1wk') < 0):
        weekly_scores += -1 
    elif(sector_1wk["WILLIAM"].iloc[-1] < -80 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"WILLIAM",'1wk') > 0):
        weekly_scores += 1

def williams_sentiment_monthly(sector_1d, sector_1wk, sector_1mo):
    global monthly_scores
    if(sector_1mo["WILLIAM"].iloc[-1] > -20 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"WILLIAM",'1mo') < 0):
        monthly_scores += -1 
    elif(sector_1mo["WILLIAM"].iloc[-1] < -80 and trend_estimate(sector_1d, sector_1wk, sector_1mo,"WILLIAM",'1mo') > 0):
        monthly_scores += 1

def ultimate_sentiment_daily(sector_1d):
    global daily_scores
    if(sector_1d["ULTIMATE"].iloc[-1] < 30):
        daily_scores += -1 
    elif(sector_1d["ULTIMATE"].iloc[-1] > 70):
        daily_scores += 1


def ultimate_sentiment_weekly(sector_1wk):
    global weekly_scores
    if(sector_1wk["ULTIMATE"].iloc[-1] < 30):
        weekly_scores += -1 
    elif(sector_1wk["ULTIMATE"].iloc[-1] > 70):
        weekly_scores += 1

def ultimate_sentiment_monthly(sector_1mo):
    global monthly_scores
    if(sector_1mo["ULTIMATE"].iloc[-1] < 30):
        monthly_scores += -1 
    elif(sector_1mo["ULTIMATE"].iloc[-1] > 70):
        monthly_scores += 1

def trend_estimate(sector_1d, sector_1wk, sector_1mo,oscillator, interval):
    index = [1,2,3,4,5,6,7]
    if interval == '1d':
        data = sector_1d[oscillator].to_numpy()
        data = data[-7:]
    elif interval == '1wk':
        data = sector_1wk[oscillator].to_numpy()
        if(round_date_wk(sector_1wk)): data = data[-7:]
        else : data = data[-8:-1]
    elif interval == '1mo':
        data = sector_1mo[oscillator].to_numpy()
        if(round_date_mo(sector_1mo)): data = data[-7:]
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
    last_date_mo = df.loc[df.index[-1]]["Date"].date()
    second_date_mo = df.loc[df.index[-2]]["Date"].date()
    if((second_date_mo + relativedelta(months=1)) == last_date_mo):
        return
    df.drop(df.tail(1).index,inplace = True)
    return 

def round_date_wk(df):
    last_date_wk = df.loc[df.index[-1]]["Date"].date()
    second_date_wk = df.loc[df.index[-2]]["Date"].date()
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



def moving_averages_extract_data(sector_1d, sector_1wk, sector_1mo):
    try:
        sector_1d['SMA10'] = ta.SMA(sector_1d['Close'], timeperiod=10)
        sector_1d['EMA10'] = ta.EMA(sector_1d['Close'], timeperiod=10)
        sector_1wk['SMA10'] = ta.SMA(sector_1wk['Close'], timeperiod=10)
        sector_1wk['EMA10'] = ta.EMA(sector_1wk['Close'], timeperiod=10)
        sector_1mo['SMA10'] = ta.SMA(sector_1mo['Close'], timeperiod=10)
        sector_1mo['EMA10'] = ta.EMA(sector_1mo['Close'], timeperiod=10)

        sector_1d['SMA20'] = ta.SMA(sector_1d['Close'], timeperiod=20)
        sector_1d['EMA20'] = ta.EMA(sector_1d['Close'], timeperiod=20)
        sector_1wk['SMA20'] = ta.SMA(sector_1wk['Close'], timeperiod=20)
        sector_1wk['EMA20'] = ta.EMA(sector_1wk['Close'], timeperiod=20)
        sector_1mo['SMA20'] = ta.SMA(sector_1mo['Close'], timeperiod=20)
        sector_1mo['EMA20'] = ta.EMA(sector_1mo['Close'], timeperiod=20)

        sector_1d['SMA30'] = ta.SMA(sector_1d['Close'], timeperiod=30)
        sector_1d['EMA30'] = ta.EMA(sector_1d['Close'], timeperiod=30)
        sector_1wk['SMA30'] = ta.SMA(sector_1wk['Close'], timeperiod=30)
        sector_1wk['EMA30'] = ta.EMA(sector_1wk['Close'], timeperiod=30)
        sector_1mo['SMA30'] = ta.SMA(sector_1mo['Close'], timeperiod=30)
        sector_1mo['EMA30'] = ta.EMA(sector_1mo['Close'], timeperiod=30)

        sector_1d['SMA50'] = ta.SMA(sector_1d['Close'], timeperiod=50)
        sector_1d['EMA50'] = ta.EMA(sector_1d['Close'], timeperiod=50)
        sector_1wk['SMA50'] = ta.SMA(sector_1wk['Close'], timeperiod=50)
        sector_1wk['EMA50'] = ta.EMA(sector_1wk['Close'], timeperiod=50)
        sector_1mo['SMA50'] = ta.SMA(sector_1mo['Close'], timeperiod=50)
        sector_1mo['EMA50'] = ta.EMA(sector_1mo['Close'], timeperiod=50)

        sector_1d['SMA100'] = ta.SMA(sector_1d['Close'], timeperiod=100)
        sector_1d['EMA100'] = ta.EMA(sector_1d['Close'], timeperiod=100)
        sector_1wk['SMA100'] = ta.SMA(sector_1wk['Close'], timeperiod=100)
        sector_1wk['EMA100'] = ta.EMA(sector_1wk['Close'], timeperiod=100)
        sector_1mo['SMA100'] = ta.SMA(sector_1mo['Close'], timeperiod=100)
        sector_1mo['EMA100'] = ta.EMA(sector_1mo['Close'], timeperiod=100)

        sector_1d['SMA200'] = ta.SMA(sector_1d['Close'], timeperiod=200)
        sector_1d['EMA200'] = ta.EMA(sector_1d['Close'], timeperiod=200)
        sector_1wk['SMA200'] = ta.SMA(sector_1wk['Close'], timeperiod=200)
        sector_1wk['EMA200'] = ta.EMA(sector_1wk['Close'], timeperiod=200)
        sector_1mo['SMA200'] = ta.SMA(sector_1mo['Close'], timeperiod=200)
        sector_1mo['EMA200'] = ta.EMA(sector_1mo['Close'], timeperiod=200)
    except Exception:
        print(f"Problem was accured during extract MA data, Details: \n {traceback.format_exc()}")

def oscillators_extract_data(sector_1d, sector_1wk, sector_1mo):
    try:
        sector_1d['RSI'] = RSIIndicator(sector_1d['Close']).rsi()
        sector_1wk['RSI'] = RSIIndicator(sector_1wk['Close']).rsi()
        sector_1mo['RSI'] = RSIIndicator(sector_1mo['Close']).rsi()

        sector_1d['STOCH_S'] = StochasticOscillator(sector_1d['High'],sector_1d['Low'],sector_1d['Close'], window=14,smooth_window=3).stoch_signal()
        sector_1wk['STOCH_S'] = StochasticOscillator(sector_1wk['High'],sector_1wk['Low'],sector_1wk['Close']).stoch_signal()
        sector_1mo['STOCH_S'] = StochasticOscillator(sector_1mo['High'],sector_1mo['Low'],sector_1mo['Close']).stoch_signal()

        sector_1d['STOCH_M'] = SMAIndicator(sector_1d['STOCH_S'],window=3).sma_indicator()
        sector_1wk['STOCH_M'] = SMAIndicator(sector_1wk['STOCH_S'],window=3).sma_indicator()
        sector_1mo['STOCH_M'] = SMAIndicator(sector_1mo['STOCH_S'],window=3).sma_indicator()

        sector_1d['CCI'] = CCIIndicator(sector_1d['High'],sector_1d['Low'],sector_1d['Close']).cci()
        sector_1wk['CCI'] = CCIIndicator(sector_1wk['High'],sector_1wk['Low'],sector_1wk['Close']).cci()
        sector_1mo['CCI'] = CCIIndicator(sector_1mo['High'],sector_1mo['Low'],sector_1mo['Close']).cci()

        sector_1d['ADX'] = ADXIndicator(sector_1d['High'],sector_1d['Low'],sector_1d['Close']).adx()
        sector_1wk['ADX'] = ADXIndicator(sector_1wk['High'],sector_1wk['Low'],sector_1wk['Close']).adx()
        sector_1mo['ADX'] = ADXIndicator(sector_1mo['High'],sector_1mo['Low'],sector_1mo['Close']).adx()

        sector_1d['ADX_D+'] = ADXIndicator(sector_1d['High'],sector_1d['Low'],sector_1d['Close']).adx_pos()
        sector_1wk['ADX_D+'] = ADXIndicator(sector_1wk['High'],sector_1wk['Low'],sector_1wk['Close']).adx_pos()
        sector_1mo['ADX_D+'] = ADXIndicator(sector_1mo['High'],sector_1mo['Low'],sector_1mo['Close']).adx_pos()

        sector_1d['ADX_D-'] = ADXIndicator(sector_1d['High'],sector_1d['Low'],sector_1d['Close']).adx_neg()
        sector_1wk['ADX_D-'] = ADXIndicator(sector_1wk['High'],sector_1wk['Low'],sector_1wk['Close']).adx_neg()
        sector_1mo['ADX_D-'] = ADXIndicator(sector_1mo['High'],sector_1mo['Low'],sector_1mo['Close']).adx_neg()

        sector_1d['AWS'] = AwesomeOscillatorIndicator(sector_1d['High'],sector_1d['Low']).awesome_oscillator()
        sector_1wk['AWS'] = AwesomeOscillatorIndicator(sector_1wk['High'],sector_1wk['Low']).awesome_oscillator()
        sector_1mo['AWS'] = AwesomeOscillatorIndicator(sector_1mo['High'],sector_1mo['Low']).awesome_oscillator()

        sector_1d['MOM'] = ta.MOM(sector_1d['Close'], timeperiod=10)
        sector_1wk['MOM'] = ta.MOM(sector_1wk['Close'], timeperiod=10)
        sector_1mo['MOM'] = ta.MOM(sector_1mo['Close'], timeperiod=10)

        sector_1d['MACD'] = MACD(sector_1d['Close']).macd()
        sector_1wk['MACD'] = MACD(sector_1wk['Close']).macd()
        sector_1mo['MACD'] = MACD(sector_1mo['Close']).macd()

        sector_1d['MACD_S'] = MACD(sector_1d['Close']).macd_signal()
        sector_1wk['MACD_S'] = MACD(sector_1wk['Close']).macd_signal()
        sector_1mo['MACD_S'] = MACD(sector_1mo['Close']).macd_signal()

        sector_1d['STOCHRSI_K'] = StochRSIIndicator(sector_1d['Close']).stochrsi_k()*100
        sector_1wk['STOCHRSI_K'] = StochRSIIndicator(sector_1wk['Close']).stochrsi_k()*100
        sector_1mo['STOCHRSI_K'] = StochRSIIndicator(sector_1mo['Close']).stochrsi_k()*100

        sector_1d['STOCHRSI_D'] = StochRSIIndicator(sector_1d['Close']).stochrsi_d()*100
        sector_1wk['STOCHRSI_D'] = StochRSIIndicator(sector_1wk['Close']).stochrsi_d()*100
        sector_1mo['STOCHRSI_D'] = StochRSIIndicator(sector_1mo['Close']).stochrsi_d()*100

        sector_1d['WILLIAM'] = WilliamsRIndicator(sector_1d['High'],sector_1d['Low'],sector_1d['Close']).williams_r()
        sector_1wk['WILLIAM'] = WilliamsRIndicator(sector_1wk['High'],sector_1wk['Low'],sector_1wk['Close']).williams_r()
        sector_1mo['WILLIAM'] = WilliamsRIndicator(sector_1mo['High'],sector_1mo['Low'],sector_1mo['Close']).williams_r()

        sector_1d['ULTIMATE'] = UltimateOscillator(sector_1d['High'],sector_1d['Low'],sector_1d['Close']).ultimate_oscillator()
        sector_1wk['ULTIMATE'] = UltimateOscillator(sector_1wk['High'],sector_1wk['Low'],sector_1wk['Close']).ultimate_oscillator()
        sector_1mo['ULTIMATE'] = UltimateOscillator(sector_1mo['High'],sector_1mo['Low'],sector_1mo['Close']).ultimate_oscillator()
    except Exception:
        print(f"Problem was accured during extract OSCILLATORS data, Details: \n {traceback.format_exc()}")


def articles_week_analyzer(articles, date,start_run_time):
    global articles_score
    counter = 1
    sum = 0
    market_articles_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
    results_path = Path.cwd() / 'Results' / 'csv_files' / 'Market Articles'
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

def run_articles_news_processor(start_date, stop_date,start_run_time):
    articles = {}
    articles_id = articles_sentiment(start_date, stop_date)
    count = 0
    with ThreadPoolExecutor(max_workers=6) as executor:
        all_articles = executor.map(get_all_articles, articles_id)
        executor.shutdown(wait=True)
    for article in all_articles:
        articles[count] = article
        count += 1
    articles_week_analyzer(articles,start_date,start_run_time)


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

def run_sectors_news_processor(start_date, stop_date,sector,start_run_time):
    market_news_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
    date = datetime.now().strftime("%d.%m.%Y-%I.%M")
    results_path = Path.cwd() / 'Results' / 'csv_files' /'Sectors news' / sector
    if not results_path.exists():
        results_path.mkdir(parents=True)
    news_data = get_news_dict(start_date, stop_date,sector)
    if(news_data == 0): return
    market_news_sentiment_df = news_extractor(news_data, start_date, sector,start_run_time)
    try:       
        market_news_sentiment_df.to_csv(results_path / f"{sector} news sentiment {date}.csv")
    except Exception:
        print(f"Problem was accured while saving the market news csv file, Details: \n {traceback.format_exc()}")

def news_extractor(news_data, date, sector,start_run_time):
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
            news_score[sector] += score
            new_row['HeadLine'] = title
            new_row['Sentiment'] = score
            new_row['Date'] = date_time
            new_row["URL"] = url
            market_news_sentiment_df = market_news_sentiment_df.append(new_row, ignore_index=True)
            stocks_news_dict.clear()
            new_row.clear()
            print(f'Finish analyse {counter} news in sector {sector} at week {date} | TOTAL RUN TIME: {round((time.time() - start_run_time)/60, 2)} minutes')
            counter += 1
        except Exception as e:
            print(f"f'Problem accured in NEW No.{counter}, Error details: {e}")
            stocks_news_dict.clear()
            new_row.clear()
            counter += 1
    return market_news_sentiment_df


def get_news_dict(start_date, stop_date,sector):    
    global news_properties
    news = {}
    stop = False
    start_date += timedelta(days=1)
    start_date = datetime.strptime(f'{start_date} 06:59:59', '%Y-%m-%d %H:%M:%S')
    since_timestamp = int(start_date.timestamp())
    category = sector_to_category(sector)
    if(category == "None"): return 0
    url = "https://seeking-alpha.p.rapidapi.com/news/v2/list"
    for page in range(0,20):
        if(stop): break
        querystring = {"until":since_timestamp,"since":"0","size":"40","number":page,"category":category}
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
                    news_properties[sector] += 1
        except Exception as e:
            print(f'EXCEPTION was accured during network connection trying get News, DETAILS: {e}')
    return news
    

def sector_to_category(sector):
    # "market-news::mlps"
    if(sector == 'XLK'):
        return "market-news::technology"
    elif(sector == "XLV"):
        return "market-news::healthcare"
    elif(sector == "XLF"):
        return "market-news::financials"
    elif(sector == "XLE"):
        return "market-news::energy"
    elif(sector == "XLP" or sector == "XLY" or sector == "XLC"):
        return "market-news::consumer"
    elif(sector == "XLRE"):
        return "market-news::reits"
    elif(sector == "XLB"):
        return "market-news::commodities"
    else:
        return "None"

def concat_stocks(stocks_news_dict):
    stocks = ""
    for key,value in stocks_news_dict.items():
        if(stocks == ""):
            stocks = value
        else:
            stocks = stocks +", "+ value
    return stocks


def zacks_to_score(score):
    if(score == 1 or score ==2): return 1
    if(score == 3): return 0
    if(score == 4 or score == 5): return -1





def run_sectors_news_processor2(start_date, stop_date):
    sectors = ['XLB','XLC','XLY','XLP','XLE','XLF','XLV','XLI','XLK','XLU','XLRE']
    market_news_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
    # date = datetime.now().strftime("%d.%m.%Y-%I.%M")
    # results_path = Path.cwd() / 'Results' / 'csv_files' /'Sectors news' / sector #! need to wwrite code for resualt path
    # if not results_path.exists():
    #     results_path.mkdir(parents=True)
    with ThreadPoolExecutor(max_workers=6) as executor:
        all_news = executor.map(get_news_dict2,sectors)
        executor.shutdown(wait=True)
        print("ALL THE NEWS IS!: ")
        print(all_news)
    for news in all_news:
        print("SINGLE NEWS IS: ")
        print(news)
        # articles[count] = article
    # articles_week_analyzer(articles,start_date)
    # market_news_sentiment_df = news_extractor2(news_data, start_date, sector)
    # try:       
    #     market_news_sentiment_df.to_csv(results_path / f"{sector} news sentiment {date}.csv")
    # except Exception:
    #     print(f"Problem was accured while saving the market news csv file, Details: \n {traceback.format_exc()}")

def news_extractor2(news_data, date, sector,start_run_time):
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
            news_score[sector] += score
            new_row['HeadLine'] = title
            new_row['Sentiment'] = score
            new_row['Date'] = date_time
            new_row["URL"] = url
            market_news_sentiment_df = market_news_sentiment_df.append(new_row, ignore_index=True)
            stocks_news_dict.clear()
            new_row.clear()
            print(f'Finish analyse {counter} news in sector {sector} at week {date} | TOTAL RUN TIME: {round((time.time() - start_run_time)/60, 2)} minutes')
            counter += 1
        except Exception as e:
            print(f"f'Problem accured in NEW No.{counter}, Error details: {e}")
            stocks_news_dict.clear()
            new_row.clear()
            counter += 1
    return market_news_sentiment_df


def get_news_dict2(sector):    
    global news_properties, sector_1dd, sector_1wkk, sector_1moo
    news = {}
    stop = False
    start_date = date.today()
    stop_date = sector_1wkk.loc[sector_1wkk.index[-1]]["Date"].date() - timedelta(days=3)
    start_date += timedelta(days=1)
    start_date = datetime.strptime(f'{start_date} 06:59:59', '%Y-%m-%d %H:%M:%S')
    since_timestamp = int(start_date.timestamp())
    category = sector_to_category(sector)
    if(category == "None"): return 0
    url = "https://seeking-alpha.p.rapidapi.com/news/v2/list"
    for page in range(0,1):
        if(stop): break
        querystring = {"until":since_timestamp,"since":"0","size":"40","number":page,"category":category}
        try:
            news_data = requests.request("GET", url, headers=headers, params=querystring)
            news_data = json.loads(news_data.text)
            news_data = news_data['data']
            for new in news_data:
                new_date = new['attributes']['publishOn']
                new_date = new_date.replace('T'," ")
                new_date =  new_date[:-6]
                date_t = datetime.strptime(new_date, '%Y-%m-%d %H:%M:%S')
                if(stop_date >= date_t.date()) : stop = True
                elif(stop == False):
                    news[f"{sector} {new_date}"] = new
                    news_properties[sector] += 1
        except Exception as e:
            print(f'EXCEPTION was accured during network connection trying get News, DETAILS: {e}')
    return news
    


# sector_1dd, sector_1wkk, sector_1moo = download_symbol_data("XLK")
# sector_1dd, sector_1wkk, sector_1moo = clean_df_nans(sector_1dd, sector_1wkk, sector_1moo)
# add_technical_data(sector_1dd, sector_1wkk, sector_1moo)
# SectorsSentiment()