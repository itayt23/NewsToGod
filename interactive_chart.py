from time import process_time_ns
import pandas as pd
import matplotlib.pyplot as plt
from regex import F
import seaborn as sns
import numpy as np
from transformers import RobertaForQuestionAnswering
from pathlib import Path
from datetime import datetime
import plotly.express as px
from collections import Counter
import webbrowser
import plotly.graph_objects as go
import os as o

data_path = Path('C:/Users/itayt/Documents/Programming/NewsToGod','results','csv_files')
date = datetime.now().strftime("%Y_%m_%d")
sentiment_news = pd.read_csv(data_path / "news_sentiment_2022_04_12-10_44_21.csv")

###############make a HyperLink#############################
for i ,j in sentiment_news["URL"].iteritems():
    url = sentiment_news["URL"].iloc[i]
    sentiment_news["URL"].iloc[i] = f'<a href={url}>link</a>'

#####Finding most common sectors by sentiment###########################
df = sentiment_news[['Sentiment', "Sector"]]
positive_sector = []
negative_sector = []
for index, row in df.iterrows():
    if(row["Sentiment"] == 1):
        positive_sector.append(row["Sector"])
    if(row["Sentiment"] == 0):
        negative_sector.append(row["Sector"])

negative_sector = Counter(negative_sector)
positive_sector = Counter(positive_sector)

positive_sector = positive_sector.most_common(2)
negative_sector = negative_sector.most_common(2)

most_positive_sector = positive_sector[0][0]
most_negative_sector =  negative_sector[0][0]

########################################################################

fig = px.scatter(data_frame=sentiment_news, x="Sentiment", y="Change", hover_name="Sector", hover_data=['Tickers',"HeadLine"])
fig.show()
