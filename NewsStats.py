from cProfile import label
from time import process_time_ns
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from transformers import RobertaForQuestionAnswering
from pathlib import Path
from datetime import datetime
import plotly.express as px
import yfinance as yf

data_path = Path.cwd() / 'Results' / 'csv_files' / 'all news'
date = datetime.now().strftime("%Y_%m_%d")
sentiment_news = pd.read_csv(data_path / "news_sentiment_2022_05_03-03_36_39.csv")
spx = yf.Ticker('SPY').history(period='2d')
change = ((spx['Close'][1]/spx['Close'][0])-1)*100
change = round(change, 2)

results_path = Path.cwd() / 'Results' / 'Stats plots' 
if not results_path.exists():
    results_path.mkdir(parents=True)

plt.figure(figsize=(12,8), dpi=150)
plt.xlabel(date)
plt.rcParams.update({'axes.facecolor':'silver'})
plt.rc('font', size =5)
plt.subplot(2,2,3)
sns.violinplot(data=sentiment_news, x='Sector', y='Sentiment', linewidth=1, bw=0.3, width=1.3)
sns.swarmplot(data=sentiment_news, x='Sector', y='Sentiment', color='black')
plt.xticks(rotation=45)
plt.ylabel("Sentiment",fontsize=6)
plt.grid(axis = 'y')

plt.subplot(2,2,2)
plt.xticks(rotation=45)
sns.swarmplot(data=sentiment_news, x='Sector', y='Change')
plt.grid(axis = 'y')
plt.axhline(y = change, color = 'black', linestyle = '--', label='SPX')
plt.legend()

plt.subplot(2,2,1)
plt.xticks(rotation=45)
sns.scatterplot(data=sentiment_news, x="Sentiment", y="Change", hue="Sector",size="Change", sizes=(10,180))
plt.axhline(y = change, color = 'black', linestyle = '--', label='SPX')
plt.legend(bbox_to_anchor=(1.01, 1),borderaxespad=0)
plt.grid(axis = 'y')


plt.subplot(2,2,4)
plt.xticks(rotation=45)
colors = {'0':'tab:red', '1':'tab:green', '2':'tab:blue'}
sns.stripplot(data=sentiment_news, x="Change", y="Sector", hue="Sentiment", palette=['red','green','orange'])
plt.ylabel("")
plt.axvline(x = change, color = 'black', linestyle = '--', label='SPX')
plt.legend(bbox_to_anchor=(1.09, 1),borderaxespad=0)
plt.grid(axis = 'y')


plt.subplots_adjust(left=0.1,
                    bottom=0.1, 
                    right=0.95, 
                    top=0.9, 
                    wspace=0.4, 
                    hspace=0.4)
plt.savefig(results_path / f'results_{date}', dpi=300)
# plt.show()


fig = px.scatter(data_frame=sentiment_news, x="Sentiment", y="Change", hover_name="Sector", hover_data=['Tickers','HeadLine'])
fig.show()

fig2 = px.scatter(data_frame=sentiment_news, x="Sector", y="Change", hover_name="Tickers", hover_data=['HeadLine'])
fig2.show()