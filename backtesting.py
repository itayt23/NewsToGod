from timeit import timeit
from numpy import sinc
import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, date
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


tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
headers = {
 "X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com",
 "X-RapidAPI-Key": os.getenv('sa_api_key')
}

class BackTesting:   
    def __init__(self):
        load_dotenv("api.env")
        indices = ['spy','qqq','dia']
        for market in indices:
            market_index = convert_indicies(market)
            market_1d, market_1wk, market_1mo, market_price = download_symbol_data(market)
            market_1d, market_1wk, market_1mo = clean_df_nans(market_1d, market_1wk, market_1mo)
            market_1d.to_csv(f"market_1d_{market}.csv")
            market_1wk.to_csv(f"market_1wk_{market}.csv")
            market_1mo.to_csv(f"market_1mo_{market}.csv")
            technical_score(self,market_1d, market_1wk, market_1mo, market_price,market_index)
            final_score(self,market_index,total_properties=100) #need to change total proporties
            self.all_technical_df = self.all_technical_df.append(self.technical_df)
            self.total_scores = 0
        start_date = datetime.strptime('2022-05-10 06:59:59', '%Y-%m-%d %H:%M:%S')
        interval = 7
        end_date = start_date
        end_date -= timedelta(interval-1)
        since_timestamp = int(time.mktime(time.strptime('2022-05-10 06:59:59', '%Y-%m-%d %H:%M:%S')))
        until_timestamp = time.mktime(time.strptime('2022-05-12 06:59:59', '%Y-%m-%d %H:%M:%S')) + 0.999



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



def articles_week_analyzer(articles, date):
    counter = 1
    sum = 0
    market_articles_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
    results_path = Path.cwd() / 'Results' / 'BackTesting' / 'Articles Sentiment'
    if not results_path.exists():
        results_path.mkdir(parents=True)
    new_row ={}
    url = "https://seeking-alpha.p.rapidapi.com/articles/get-details"
    for id in articles.keys():
        try:
            querystring = {"id": id}
            article = requests.request("GET", url, headers=headers, params=querystring)
            article = json.loads(article.text)
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
            new_row['HeadLine'] = article_title
            new_row['Sentiment'] = final_score
            new_row['Date'] = article_date
            new_row["URL"] = article_url
            market_articles_sentiment_df = market_articles_sentiment_df.append(new_row, ignore_index=True)
            print(f'Finish analyse {counter} articles')
        except Exception as e:
            print(f'Problem accured in article No.{counter}')
            print(f'Error details: {e}')

        new_row.clear()
        counter += 1
        sum = 0
    market_articles_sentiment_df.to_csv(results_path / f"articles_sentiment_week{date.date()}.csv")
# articles = {}
# cut = False
# url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
# headers = {
#  "X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com",
#  "X-RapidAPI-Key": os.getenv('sa_api_key')
# }
# for week in range(0,3):
#     for page in range(0,7):
#         if(cut): break
#         querystring = {"until":since_timestamp,"since":until_timestamp,"size":"40","number":page,"category":"market-outlook"}
#         articels_list = requests.request("GET", url, headers=headers, params=querystring)
#         articels_list = json.loads(articels_list.text)
#         articels_list = articels_list['data']
#         for article in articels_list:
#             date = article['attributes']['publishOn']
#             date = date.replace('T'," ")
#             date =  date[:-6]
#             date_t = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
#             if(end_date.date() == date_t.date()) : cut = True
#             elif(cut == False): articles[article['id']] = date

#     articles_week_analyzer(articles, start_date)
#     start_date -= timedelta(interval)
#     end_date -= timedelta(interval)
#     since_timestamp = int(time.mktime(time.strptime(start_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')))
#     cut = False
#     articles.clear()






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



BackTesting()