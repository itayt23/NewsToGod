from timeit import timeit
from numpy import sinc
import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
import time


load_dotenv("api.env")
times= '2022-02-16T09:10:32-05:00'
times = times.replace('T'," ").replace("-05:00","")
ma = datetime.strptime(times, '%Y-%m-%d %H:%M:%S')
ma = ma + timedelta(7)

start_date = datetime.strptime('2022-05-09 07:00:00', '%Y-%m-%d %H:%M:%S')
end_date = start_date - timedelta(3)
end_date = end_date.date()
since_timestamp = int(time.mktime(time.strptime('2022-05-09 07:00:00', '%Y-%m-%d %H:%M:%S')))
until_timestamp = time.mktime(time.strptime('2022-05-12 06:59:59', '%Y-%m-%d %H:%M:%S')) + 0.999

articles = {}
url = "https://seeking-alpha.p.rapidapi.com/articles/v2/list"
headers = {
 "X-RapidAPI-Host": "seeking-alpha.p.rapidapi.com",
 "X-RapidAPI-Key": os.getenv('sa_api_key')
}
for page in range(0,1):

    querystring = {"until":since_timestamp,"since":until_timestamp,"size":"40","number":page,"category":"market-outlook"}
    articels_list = requests.request("GET", url, headers=headers, params=querystring)
    articels_list = json.loads(articels_list.text)
    articels_list = articels_list['data']
    for article in articels_list:
        date = article['attributes']['publishOn']
        date = date.replace('T'," ")
        date =  date[:-6]
        date_t = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        if(end_date == date_t.date()) :break
        articles[article['id']] = date
    
print(articles)
print(len(articles))
