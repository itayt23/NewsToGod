from ctypes import sizeof
from tracemalloc import stop
import requests
import json
import yfinance as yf
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from datetime import date,datetime,timedelta
import time
from pathlib import Path
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor


load_dotenv("api.env")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
# url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
headers = {
 "X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com",
 "X-RapidAPI-Key": os.getenv('sa_api_key')
}



class SentimentProcessor:

    def __init__(self,news_number):
        load_dotenv("api.env")
        self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        self.news_number = news_number
        self.news_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Tickers', 'Sector','Industery', 'Change', 'Date', "URL"])
        self.market_news_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Tickers', 'Sector','Industery', 'Change', 'Date', "URL"])
        self.market_articles_sentiment_df = pd.DataFrame(columns=['HeadLine', 'Sentiment', 'Date', "URL"])
        

    def get_news_df(self):
        return self.news_sentiment_df

    def get_market_articles_df(self):
        return self.market_articles_sentiment_df
    
    def get_market_news_df(self):
        return self.market_news_sentiment_df

    def get_news_number(self):
        return self.news_number

    def run_news_processor(self):
        date = datetime.now().strftime("%d.%m.%Y-%I.%M")
        results_path = Path.cwd() / 'Results' / 'csv_files' /'All news'
        if not results_path.exists():
            results_path.mkdir(parents=True)
        news_data = get_news_dict(self)
        news_extractor(self,news_data)
        self.news_sentiment_df.to_csv(results_path / f"news_sentiment_{date}.csv")
    
    def run_market_news_processor(self):
        date = datetime.now().strftime("%d.%m.%Y-%I.%M")
        results_path = Path.cwd() / 'Results' / 'csv_files' /'Market news'
        if not results_path.exists():
            results_path.mkdir(parents=True)
        news_data = get_news_dict(self, 'market')
        news_extractor(self,news_data,'market')
        del self.market_news_sentiment_df['Tickers']
        del self.market_news_sentiment_df['Sector']
        del self.market_news_sentiment_df['Industery']
        del self.market_news_sentiment_df['Change']        
        self.market_news_sentiment_df.to_csv(results_path / f"market_news_sentiment_{date}.csv")
    

    
    def run_articles_news_processor(self, start_date, stop_date):
        articles = {}
        articles_id = articles_sentiment(start_date, stop_date)
        count = 0
        with ThreadPoolExecutor(max_workers=6) as executor:
            all_articles = executor.map(get_all_articles, articles_id)
            executor.shutdown(wait=True)
        for article in all_articles:
            articles[count] = article
            count += 1
        self.articles_week_analyzer(articles,start_date)


    def run_market_articles_processor_old(self):
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        stop_date = start_week - timedelta(days=3)
        articles = []
        new_row = {}
        counter = 1 
        sum = 0
        date = datetime.now().strftime("%d.%m.%Y-%I.%M")
        results_path = Path.cwd() / 'Results' / 'csv_files' /'Articles'
        if not results_path.exists():
            results_path.mkdir(parents=True)

        url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
        for page in range(0,5):
            querystring = {"until":"0","since":"0","size":"40","number":page,"category":"market-outlook"}

            articels_list = requests.request("GET", url, headers=headers, params=querystring)
            articels_list = json.loads(articels_list.text)
            articels_list = articels_list['data']
            for article_id in articels_list:
                articles.append(article_id['id'])

        print("STARTING TO ANALYSE ARTICLES")
        print("--------------------------------------------------------------")
        url = "https://seeking-alpha.p.rapidapi.com/articles/get-details"
        for id in articles:
            querystring = {"id": id}
            article = requests.request("GET", url, headers=headers, params=querystring)
            article = json.loads(article.text)
            article_url = article['data']['links']['canonical']
            article = article['data']['attributes']
            article_title = article['title']
            article_date = article['publishOn']
            article_content = article['content']
            article_content = clean_content(article_content)
            article_content_score = sentiment_score(self,article_content)
            article_summary = article['summary']
            for article_no in article_summary:
                sum += (sentiment_score(self,article_no))
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

            self.market_articles_sentiment_df = self.market_articles_sentiment_df.append(new_row, ignore_index=True)
            new_row.clear()
            print(f'Finish analyse {counter} articles')
            counter += 1
            sum = 0
        self.market_articles_sentiment_df.to_csv(results_path / f"articles_sentiment_{date}.csv")

            
    def get_market_news_sentiment(self):
        sentiment = self.market_news_sentiment_df['Sentiment'].sum()
        return score_to_sentiment(sentiment/ self.market_news_sentiment_df.shape[0])

    def get_market_articles_sentiment(self):
        sentiment = self.market_articles_sentiment_df['Sentiment'].sum()
        return score_to_sentiment(sentiment/self.market_articles_sentiment_df.shape[0])

    def get_news_sentiment(self):
        sentiment = self.news_sentiment_df['Sentiment'].sum()
        return score_to_sentiment(sentiment/self.news_number)

    def plot_news(self):
        data = pd.DataFrame(self.news_sentiment_df)
        results_path = Path.cwd() / 'Results' / 'Stats plots' 
        if not results_path.exists():
            results_path.mkdir(parents=True)
        try:
            spx = yf.Ticker('SPY').history(period='2d')
            spx_change = ((spx['Close'][1]/spx['Close'][0])-1)*100
            spx_change = round(spx_change, 2)
            date = datetime.now().strftime("%d_%m_%Y")
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


    def articles_week_analyzer(self, articles, date):
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
                self.market_articles_sentiment_df = self.market_articles_sentiment_df.append(new_row, ignore_index=True)
            except Exception as e:
                print(f'Problem accured in article No.{counter}, Error details: {e}')
            new_row.clear()
            print(f'Finish analyse {counter} articles')
            counter += 1
            sum = 0
        self.market_articles_sentiment_df.to_csv(results_path / f"articles_sentiment_{date}.csv")


def news_extractor(self,news_data,category = 'all'):
    stocks_news_dict = {}
    all_stocks_dict = {}
    new_row = {}
    change = 0
    counter = 1
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
        new_row['HeadLine'] = title
        new_row['Sentiment'] = score
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
        print(f'Finish analyse {counter} news')
        counter += 1


def get_news_dict(self, category = 'all'):
        if(category == 'market'):
            querystring = {"category":"market-news::us-economy","until":"0","since":"0","size":self.get_news_number(),"number":"0"}
        else:
            querystring = {"category":"market-news::all","until":"0","since":"0","size":self.get_news_number(),"number":"0"}

        url = "https://seeking-alpha.p.rapidapi.com/news/v2/list"
        news = requests.request("GET", url, headers=headers, params=querystring)
        news_data = json.loads(news.text)
        return news_data


def get_articels_list(self):
    url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
    querystring = {"until":"0","since":"0","size":"20","number":"1","category":"market-outlook"} # here its const.... need to chage it
    articels_list = requests.request("GET", url, headers=headers, params=querystring)
    articels_list = json.loads(articels_list.text)
    return articels_list

def sentiment_score(self,headline):
    tokens = self.tokenizer(headline,padding = True, truncation = True,  return_tensors='pt')
    result = self.model(**tokens)
    result = torch.nn.functional.softmax(result.logits, dim=-1)
    return score_num(int(torch.argmax(result))+1)

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

def score_to_sentiment(score):
    if(-1 <= score < -0.5): return ("Strong Sell")
    elif( -0.5 <= score < -0.1): return ("Sell")
    elif(-0.1 <= score <= 0.1): return ("Netural")
    elif(0.1 < score <= 0.5): return ("Buy")
    elif(0.5 < score <=1): return ("Strong Buy")



def get_all_articles(id):
    url = "https://seeking-alpha.p.rapidapi.com/articles/get-details"
    querystring = {"id": id}
    try:
        article = requests.request("GET", url, headers=headers, params=querystring)
        article = json.loads(article.text)
    except Exception as e:
        print(f'Problem at one of the articles ENCODING PROBLEM: {e}')
    return article

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


