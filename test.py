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

articles = {}
load_dotenv("api.env")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
# url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
# headers = {
#  "X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com",
#  "X-RapidAPI-Key": os.getenv('sa_api_key')
# }


def articles_sentiment(start_date, stop_date):
    since_timestamp = int(start_date.timestamp())
    until_timestamp = time.mktime(time.strptime('2022-10-12 06:59:59', '%Y-%m-%d %H:%M:%S')) + 0.999
    # articles = {}
    articles = []
    dates = []
    stop = False
    # url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
    # url = "https://seekingalpha.com/api/v3/articles"
    url = "https://seekingalpha.com/api/v3/articles"
    # headers = {
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36" ,
    #     'referer':'https://seekingalpha.com/api/v3/market_open'
    # }
    for page in range(0,7):
        if(stop): break
        querystring = {"until":"0","since":"0","size":"40","number":"1","category":"sectors::energy"}
        try:
            articels_list = requests.request("GET", url, params=querystring)
            articels_list = json.loads(articels_list.text)
            articels_list = articels_list['data']
            for article in articels_list:
                date = article['attributes']['publishOn']
                date = date.replace('T'," ")
                date =  date[:-6]
                date_t = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                if(stop_date.date() == date_t.date()) : stop = True
                elif(stop == False):
                    articles.append(article['id'])
                    dates.append(date)
                    # articles[article['id']] = date
        except Exception as e:
            print(f'EXCEPTION was accured during network connection trying get articles, DETAILS: {e}')
    return articles



def articles_week_analyzer(articles):
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
    market_articles_sentiment_df.to_csv(results_path / f"articles_sentiment_week_wowowowwo.csv")


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

def fetch(id):
    url = "https://seeking-alpha.p.rapidapi.com/articles/get-details"
    querystring = {"id": id}
    try:
        article = requests.request("GET", url, params=querystring)
        article = json.loads(article.text)
        print(id)
    except:
        print('Problem at one of the articles ENCODING PROBLEM')
    return article
    
##############-U.S. Sector-##############
# Materials - XLB
# Communication Services - XLC
# Consumer Discretionary = XLY
# Consumer Staples - XLP
# Energy - XLE
# Finance = XLF -> V
# Healthcare - XLV
# Industrials - XLI
# Technology - XLK
# Utilities = XLU
# Real Estate - XLRE






# market_1d = pd.read_csv("market_1d.csv")
# market_1wk = pd.read_csv("market_1wk.csv")
# market_1mo = pd.read_csv("market_1mo.csv")
# start_date = datetime.strptime('2022-05-17 06:59:59', '%Y-%m-%d %H:%M:%S')
# stop_date = datetime.strptime('2022-05-14 06:59:59', '%Y-%m-%d %H:%M:%S')
# sector = yf.download("xlre",interval="1d",period="1y")
# print(sector)


# articles_id = articles_sentiment(start_date, stop_date)
# count = 0
# with ThreadPoolExecutor(max_workers=6) as executor:
#     articlesss = executor.map(fetch, articles_id)
#     executor.shutdown(wait=True)
# for article in articlesss:
#     articles[count] = article
#     count += 1


# articles_week_analyzer(articles)
            



url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"

querystring = {"until":"0","since":"0","size":"20","number":"1","category":"gold-and-precious-metals"}

headers = {
	"X-RapidAPI-Key": "cc6a8d8228mshafc0d4b0ccd770ap1b399cjsna358d8033ba0",
	"X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com"
}

articles =[]
response = requests.request("GET", url, headers=headers, params=querystring)
response = json.loads(response.text)
articels_list = response['data']
for article_id in articels_list:
    articles.append(article_id['id'])
print(articles)
print('blalblablab')







