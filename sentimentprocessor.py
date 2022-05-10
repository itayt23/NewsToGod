import requests
import json
import yfinance as yf
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import seaborn as sns


class SentimentProcessor:

    def __init__(self,news_number):
        load_dotenv("api.env")
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        self.news_number = news_number
        self.news_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Tickers', 'Sector','Industery', 'Change', 'Date', "URL"])
        self.market_news_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Tickers', 'Sector','Industery', 'Change', 'Date', "URL"])
        self.articles_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Tickers', 'Sector','Industery', 'Change', 'Date', "URL"])
        

    def get_news_df(self):
        return self.news_sentiment_df

    def get_articles_df(self):
        return self.articles_sentiment_df

    def get_news_number(self):
        return self.news_number

    def run_news_processor(self):
        date = datetime.now().strftime("%Y_%m_%d-%I_%M_%S")
        results_path = Path.cwd() / 'Results' / 'csv_files' /'all news'
        if not results_path.exists():
            results_path.mkdir(parents=True)
        news_data = get_all_news_dict(self)
        news_extractor(self,news_data)
        self.news_sentiment_df.to_csv(results_path / f"news_sentiment_{date}.csv")
    
    def run_market_news_processor(self):
        date = datetime.now().strftime("%Y_%m_%d-%I_%M_%S")
        results_path = Path.cwd() / 'Results' / 'csv_files' /'Market news'
        if not results_path.exists():
            results_path.mkdir(parents=True)
        news_data = get_all_news_dict(self, 'market')
        news_extractor(self,news_data,'market')
        del self.market_news_sentiment_df['Tickers']
        del self.market_news_sentiment_df['Sector']
        del self.market_news_sentiment_df['Industery']
        del self.market_news_sentiment_df['Change']        
        self.market_news_sentiment_df.to_csv(results_path / f"news_sentiment_{date}.csv")

    def run_articles_processor(self):
        pass
    
    def get_market_news_sentiment(self):
        sentiment = self.market_news_sentiment_df['Sentiment'].sum()
        if(sentiment < 0): return 'Negative'
        if sentiment > 0 : return 'Positive'
        else: return 'Netural'

    def get_news_sentiment(self):
        sentiment = self.news_sentiment_df['Sentiment'].sum()
        if(sentiment < 0): return 'Negative'
        if sentiment > 0 : return 'Positive'
        else: return 'Netural'

    def plot_news(self):
        print(type(self.news_sentiment_df))
        data = pd.DataFrame(self.news_sentiment_df)
        print(type(data))
        results_path = Path.cwd() / 'Results' / 'Stats plots' 
        if not results_path.exists():
            results_path.mkdir(parents=True)
        try:
            spx = yf.Ticker('SPY').history(period='2d')
            spx_change = ((spx['Close'][1]/spx['Close'][0])-1)*100
            spx_change = round(spx_change, 2)
            date = datetime.now().strftime("%Y_%m_%d")
            plt.figure(figsize=(12,8), dpi=150)
            plt.xlabel(date)
            plt.rcParams.update({'axes.facecolor':'silver'})
            plt.rc('font', size =5)
            plt.subplot(2,2,3)
            # is throwing wxception dont know whyyyyyyy godamet
            # sns.violinplot(data=data, x='Sector', y='Sentiment', linewidth=1, bw=0.3, width=1.3)
            sns.swarmplot(data=data, x='Sector', y='Sentiment', color='black')
            plt.xticks(rotation=45)
            plt.ylabel("Sentiment",fontsize=6)
            plt.grid(axis = 'y')

            plt.subplot(2,2,2)
            plt.xticks(rotation=45)
            sns.swarmplot(data=data, x='Sector', y='Change')
            plt.grid(axis = 'y')
            plt.axhline(y = spx_change, color = 'black', linestyle = '--', label='SPX')
            plt.legend()

            plt.subplot(2,2,1)
            plt.xticks(rotation=45)
            sns.scatterplot(data=data, x="Sentiment", y="Change", hue="Sector",size="Change", sizes=(10,180))
            plt.axhline(y = spx_change, color = 'black', linestyle = '--', label='SPX')
            plt.legend(bbox_to_anchor=(1.01, 1),borderaxespad=0)
            plt.grid(axis = 'y')


            plt.subplot(2,2,4)
            plt.xticks(rotation=45)
            sns.stripplot(data=data, x="Change", y="Sector", hue="Sentiment", palette=['red','green','orange'])
            plt.ylabel("")
            plt.axvline(x = spx_change, color = 'black', linestyle = '--', label='SPX')
            plt.legend(bbox_to_anchor=(1.09, 1),borderaxespad=0)
            plt.grid(axis = 'y')


            plt.subplots_adjust(left=0.1,
                                bottom=0.1, 
                                right=0.95, 
                                top=0.9, 
                                wspace=0.4, 
                                hspace=0.4)
            plt.savefig(results_path / f'results_{date}', dpi=300)
            plt.show()
        except:
            print("Error occured while trying to plotting news analysis...")


def news_extractor(self,news_data,category = 'all'):
    stocks_news_dict = {}
    all_stocks_dict = {}
    new_row = {}
    change = 0
    for stocks_keys in news_data['included']:
        try:
            all_stocks_dict[stocks_keys['id']] = stocks_keys['attributes']['name']
        except:
            all_stocks_dict[stocks_keys['id']] = 'None'
    for new in news_data['data']:
        title = new['attributes']['title']
        date_time = new['attributes']['publishOn']
        content = new['attributes']['content']
        url = new['links']['canonical']
        url = str(url).replace('"',"")
        content = clean_content(content)
        score = sentiment_score(self,content)
        # new_row['Sentiment'] = score_string(score)
        new_row['HeadLine'] = title
        new_row['Sentiment'] = score_num(score)
        new_row['Date'] = date_time
        new_row["URL"] = url
        for stock in new['relationships']['primaryTickers']['data']:
            stocks_news_dict[stock['id']]= ''
        for key,value in all_stocks_dict.items():
            if key in stocks_news_dict.keys():
                stocks_news_dict[key] = value
        new_row['Tickers'] = concat_stocks(stocks_news_dict)
        if(stocks_news_dict):
            try:
                first_ticker = yf.Ticker(list(stocks_news_dict.values())[0])
                new_row['Industery'] = first_ticker.get_info()['industry']
                new_row['Sector'] = first_ticker.get_info()['sector']
            except:
               new_row['Industery'] =""
               new_row['Sector'] =""
            try:
                ticker_data = first_ticker.history(period='2d')
                change = ((ticker_data['Close'][1]/ticker_data['Close'][0])-1)*100
                new_row["Change"] = change
            except:
                new_row["Change"] = ""
            if(category == 'market'): self.market_news_sentiment_df = self.market_news_sentiment_df.append(new_row, ignore_index=True)
            else: self.news_sentiment_df = self.news_sentiment_df.append(new_row, ignore_index=True)
            stocks_news_dict.clear()
            new_row.clear()


def get_all_news_dict(self, category = 'all'):
        if(category == 'market'):
            querystring = {"category":"market-news::us-economy","until":"0","since":"0","size":self.get_news_number(),"number":"1"}
        else:
            querystring = {"category":"market-news::all","until":"0","since":"0","size":self.get_news_number(),"number":"1"}

        url = "https://seeking-alpha.p.rapidapi.com/news/v2/list"
        headers = {
        	"X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com",
        	"X-RapidAPI-Key": os.getenv('sa_api_key')
        }
        news = requests.request("GET", url, headers=headers, params=querystring)
        news_data = json.loads(news.text)
        return news_data

def sentiment_score(self,headline):
    tokens = self.tokenizer(headline,padding = True, truncation = True,  return_tensors='pt')
    result = self.model(**tokens)
    result = torch.nn.functional.softmax(result.logits, dim=-1)
    return int(torch.argmax(result))+1

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

def score_string(score):
    if(score == 1):
        return "Positive"
    if(score == 2):
        return "Negative"
    if(score == 3):
        return "Neutral"
    return "None"

def score_num(score):
    if(score == 1):
        return 1
    if(score == 2):
        return -1
    if(score == 3):
        return 0
    return 0

def concat_stocks(stocks_news_dict):
    stocks = ""
    for key,value in stocks_news_dict.items():
        if(stocks == ""):
            stocks = value
        else:
            stocks = stocks +", "+ value
    return stocks




