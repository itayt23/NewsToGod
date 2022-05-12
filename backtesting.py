from timeit import timeit
from numpy import sinc
import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
import time
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from pathlib import Path
import pandas as pd


load_dotenv("api.env")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

start_date = datetime.strptime('2022-05-10 06:59:59', '%Y-%m-%d %H:%M:%S')
interval = 7
end_date = start_date
end_date -= timedelta(interval)
since_timestamp = int(time.mktime(time.strptime('2022-05-10 06:59:59', '%Y-%m-%d %H:%M:%S')))
until_timestamp = time.mktime(time.strptime('2022-05-12 06:59:59', '%Y-%m-%d %H:%M:%S')) + 0.999


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



def analyzer(articles, date):
    counter = 1
    sum = 0
    market_articles_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
    results_path = Path.cwd() / 'Results' / 'BackTesting' 
    if not results_path.exists():
        results_path.mkdir(parents=True)
    new_row ={}
    url = "https://seeking-alpha.p.rapidapi.com/articles/get-details"
    for id in articles.keys():
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
        new_row.clear()
        print(f'Finish analyse {counter} articles')
        counter += 1
        sum = 0
        market_articles_sentiment_df.to_csv(results_path / f"articles_sentiment_week{date.date()}.csv")

articles = {}
cut = False
url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
headers = {
 "X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com",
 "X-RapidAPI-Key": os.getenv('sa_api_key')
}
for week in range(0,3):
    for page in range(0,7):
        if(cut): break
        querystring = {"until":since_timestamp,"since":until_timestamp,"size":"40","number":page,"category":"market-outlook"}
        articels_list = requests.request("GET", url, headers=headers, params=querystring)
        articels_list = json.loads(articels_list.text)
        articels_list = articels_list['data']
        for article in articels_list:
            date = article['attributes']['publishOn']
            date = date.replace('T'," ")
            date =  date[:-6]
            date_t = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            if(end_date.date() == date_t.date()) : cut = True
            elif(cut == False): articles[article['id']] = date

    analyzer(articles, start_date)
    start_date -= timedelta(interval)
    end_date -= timedelta(interval)
    since_timestamp = int(time.mktime(time.strptime(start_date.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')))
    cut = False
    articles.clear()





