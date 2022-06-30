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
from collections import Counter
import statsmodels.api as sm


#! plot regression
# data_path = Path.cwd() / 'Results' / 'BackTesting' / 'Weights'
# weights_df = pd.read_csv(data_path / "weights 1500.csv")
# y = weights_df[["My Yield"]]
# x = weights_df[["Daily Weight","Weekly Weight","Monthly Weight","News Weight","Articles Weight"]]
# x_daily = weights_df[["Daily Weight"]]
# x_weekly = weights_df[["Weekly Weight"]]
# x_monthly = weights_df[["Monthly Weight"]]
# x_news = weights_df[["News Weight"]]
# x_articles = weights_df[["Articles Weight"]]

# # x.drop(x.tail(500).index,inplace = True)
# # y.drop(y.tail(500).index,inplace=True)



# #add constant to predictor variables
# # x_articles = sm.add_constant(x_articles)

# #fit linear regression model
# model = sm.OLS(y,x_articles).fit()

# #view model summary
# # sns.regplot(y="My Yield", x="Technical Weight", data=weights_df)
# print(model.summary())

#! news stats plot
# data_path = Path.cwd() / 'Results' / 'csv_files' / 'all news'
# date = datetime.now().strftime("%Y_%m_%d")
# sentiment_news = pd.read_csv(data_path / "news_sentiment_2022_05_09-09_56_29.csv")
# spx = yf.Ticker('SPY').history(period='2d')
# change = ((spx['Close'][1]/spx['Close'][0])-1)*100
# change = round(change, 2)

# results_path = Path.cwd() / 'Results' / 'Stats plots' 
# if not results_path.exists():
#     results_path.mkdir(parents=True)

# plt.figure(figsize=(12,8), dpi=150)
# plt.xlabel(date)
# plt.rcParams.update({'axes.facecolor':'silver'})
# plt.rc('font', size =5)
# plt.subplot(2,2,3)
# sns.violinplot(data=sentiment_news, x='Sector', y='Sentiment', linewidth=1, bw=0.3, width=1.3)
# sns.swarmplot(data=sentiment_news, x='Sector', y='Sentiment', color='black')
# plt.xticks(rotation=45)
# plt.ylabel("Sentiment",fontsize=6)
# plt.grid(axis = 'y')

# plt.subplot(2,2,2)
# plt.xticks(rotation=45)
# sns.swarmplot(data=sentiment_news, x='Sector', y='Change')
# plt.grid(axis = 'y')
# plt.axhline(y = change, color = 'black', linestyle = '--', label='SPX')
# plt.legend()

# plt.subplot(2,2,1)
# plt.xticks(rotation=45)
# sns.scatterplot(data=sentiment_news, x="Sentiment", y="Change", hue="Sector",size="Change", sizes=(10,180))
# plt.axhline(y = change, color = 'black', linestyle = '--', label='SPX')
# plt.legend(bbox_to_anchor=(1.01, 1),borderaxespad=0)
# plt.grid(axis = 'y')


# plt.subplot(2,2,4)
# plt.xticks(rotation=45)
# # colors = {'-1':'tab:red', '0':'tab:green', '1':'tab:blue'}
# sns.stripplot(data=sentiment_news, x="Change", y="Sector", hue="Sentiment", palette=['red','orange','green'])
# plt.ylabel("")
# plt.axvline(x = change, color = 'black', linestyle = '--', label='SPX')
# plt.legend(bbox_to_anchor=(1.09, 1),borderaxespad=0)
# plt.grid(axis = 'y')


# plt.subplots_adjust(left=0.1,
#                     bottom=0.1, 
#                     right=0.95, 
#                     top=0.9, 
#                     wspace=0.4, 
#                     hspace=0.4)
# plt.savefig(results_path / f'results_{date}', dpi=300)
# plt.show()


# fig = px.scatter(data_frame=sentiment_news, x="Sentiment", y="Change", hover_name="Sector", hover_data=['Tickers','HeadLine'])
# fig.show()

# fig2 = px.scatter(data_frame=sentiment_news, x="Sector", y="Change", hover_name="Tickers", hover_data=['HeadLine'])
# fig2.show()




#!interactive chart file
# data_path = Path('C:/Users/itayt/Documents/Programming/NewsToGod','results','csv_files')
# date = datetime.now().strftime("%Y_%m_%d")
# sentiment_news = pd.read_csv(data_path / "news_sentiment_2022_04_12-10_44_21.csv")

# ###############make a HyperLink#############################
# for i ,j in sentiment_news["URL"].iteritems():
#     url = sentiment_news["URL"].iloc[i]
#     sentiment_news["URL"].iloc[i] = f'<a href={url}>link</a>'

# #####Finding most common sectors by sentiment###########################
# df = sentiment_news[['Sentiment', "Sector"]]
# positive_sector = []
# negative_sector = []
# for index, row in df.iterrows():
#     if(row["Sentiment"] == 1):
#         positive_sector.append(row["Sector"])
#     if(row["Sentiment"] == 0):
#         negative_sector.append(row["Sector"])

# negative_sector = Counter(negative_sector)
# positive_sector = Counter(positive_sector)

# positive_sector = positive_sector.most_common(2)
# negative_sector = negative_sector.most_common(2)

# most_positive_sector = positive_sector[0][0]
# most_negative_sector =  negative_sector[0][0]

# ########################################################################

# fig = px.scatter(data_frame=sentiment_news, x="Sentiment", y="Change", hover_name="Sector", hover_data=['Tickers',"HeadLine"])
# fig.show()
