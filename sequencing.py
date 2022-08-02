from turtle import up
from grpc import UnaryStreamClientInterceptor
from importlib_metadata import entry_points
from openpyxl import load_workbook
import yfinance as yf
import pandas as pd
from datetime import date,datetime,timedelta
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import pandas as pd
import matplotlib.dates as mpdates
import numpy as np




class SequenceMethod:

    def __init__(self,ticker):
        # load_dotenv("api.env")
        self.symbol_data_1d = pd.DataFrame(yf.download(ticker, period='1y',interval='1d')).dropna()
        self.symbol_data_1d = self.symbol_data_1d.rename_axis('Date').reset_index()
        self.symbol_data_1wk = pd.DataFrame(yf.download(ticker, period='5y',interval='1wk')).dropna()
        self.symbol_data_1wk = self.symbol_data_1wk.rename_axis('Date').reset_index()
        self.symbol_data_1mo = pd.DataFrame(yf.download(ticker, period='10y',interval='1mo')).dropna()
        self.symbol_data_1mo = self.symbol_data_1mo.rename_axis('Date').reset_index()
        self.sequence_1d = pd.DataFrame(columns=['Date', 'Entry Price', 'Sequence', 'Days', "Yield"])
        self.sequence_1wk = pd.DataFrame(columns=['Date', 'Entry Price', 'Sequence', 'Days', "Yield"])
        self.sequence_1mo = pd.DataFrame(columns=['Date', 'Entry Price', 'Sequence', 'Days', "Yield"])
        self.sequence_1mo = build_sequences(self)

    def show_graph(self):
        pass
    
    def plot_monthly_graph(self):
        up_seq_x = up_seq_y = down_seq_x = down_seq_y = []
        for i in range(len(self.sequence_1mo)):
            if(self.sequence_1mo.loc[i, "Sequence"] == 1):
                up_seq_x.append(self.sequence_1mo.loc[i, "Date"])
                up_seq_y.append(self.sequence_1mo.loc[i, "Entry Price"])
            else:
                down_seq_x.append(self.sequence_1mo.loc[i, "Date"])
                down_seq_y.append(self.sequence_1mo.loc[i, "Entry Price"])

        plt.style.use('dark_background')

        # convert into datetime object
        self.symbol_data_1mo['Date'] = pd.to_datetime(self.symbol_data_1mo['Date'])

        # apply map function
        self.symbol_data_1mo['Date'] = self.symbol_data_1mo['Date'].map(mpdates.date2num)
        
        # creating Subplots
        fig, ax = plt.subplots()
        
        # plotting the data
        candlestick_ohlc(ax, self.symbol_data_1mo.values, width = 2.5,
                        colorup = 'green', colordown = 'red',
                        alpha = 0.8)
        
        # allow grid
        ax.grid(True)
        
        # Setting labels
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        
        # setting title
        plt.title('Candelsticks')
        plt.scatter(up_seq_x,up_seq_y,marker='^',facecolors='green',s=20)
        plt.scatter(down_seq_x,down_seq_y,marker='v',facecolors='red',s=20)
        # plt.plot(up_seq_x,up_seq_y,"ro", alpha=0.5, marker="^", markersize=4,facecolor='green')
        
        # Formatting Date
        date_format = mpdates.DateFormatter('%d-%m-%Y')
        ax.xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()
        fig.tight_layout()
        plt.show()

def build_sequences(self):
    sequence = pd.DataFrame(columns=['Date', 'Sequence', 'Days', "Yield"])
    seq_df_index = 0
    down_seq = up_seq = False
    down_seq_list = up_seq_list =[]
    close_price = low_price = high_price =  enter_price = sell_price = seq_yield = 1
    days = 0
    in_sequence = False
    first = True
    for i in range(len(self.symbol_data_1mo)):
        if first:
            first = False
            continue
       
        close_price = self.symbol_data_1mo.loc[i, "Close"]
        low_price = self.symbol_data_1mo.loc[i-1, "Low"]
        high_price = self.symbol_data_1mo.loc[i-1, "High"]
        if not in_sequence:
            if(close_price > low_price):
                up_seq = True
                up_seq_list.append((high_price,low_price))
                up_seq_list.append((self.symbol_data_1mo.loc[i, "High"],self.symbol_data_1mo.loc[i, "Low"]))
                sequence.loc[seq_df_index,'Date'] = self.symbol_data_1mo.loc[i, "Date"]
                sequence.loc[seq_df_index,'Sequence'] = 1
                sequence.loc[seq_df_index,'Entry Price'] = self.symbol_data_1mo.loc[i, "Low"]
                enter_price = self.symbol_data_1mo.loc[i, "Close"]
                in_sequence = True
            elif(close_price < high_price):
                down_seq = True
                down_seq_list.append((low_price,high_price))
                down_seq_list.append((self.symbol_data_1mo.loc[i, "Low"],self.symbol_data_1mo.loc[i, "High"]))
                sequence.loc[seq_df_index,'Date'] = self.symbol_data_1mo.loc[i, "Date"]
                sequence.loc[seq_df_index,'Sequence'] = -1
                sequence.loc[seq_df_index,'Entry Price'] = self.symbol_data_1mo.loc[i, "High"]
                sell_price = self.symbol_data_1mo.loc[i, "Close"]
                in_sequence = True
        else:
            if(up_seq):
                days = days + 1
                if(close_price > max(up_seq_list)[1]):
                    up_seq_list.append((self.symbol_data_1mo.loc[i, "High"],self.symbol_data_1mo.loc[i, "Low"]))
                    continue
                else: #finsih up trend and starting down trend
                    sell_price = self.symbol_data_1mo.loc[i, "Close"]
                    seq_yield = (sell_price - enter_price)/enter_price*100
                    sequence.loc[seq_df_index,'Yield'] = seq_yield
                    sequence.loc[seq_df_index,'Days'] = days
                    days = seq_yield = 0
                    up_seq_list = down_seq_list =[]
                    up_seq = False
                    down_seq = True
                    seq_df_index = seq_df_index + 1
                    down_seq_list.append((self.symbol_data_1mo.loc[i, "Low"],self.symbol_data_1mo.loc[i, "High"]))
                    sequence.loc[seq_df_index,'Date'] = self.symbol_data_1mo.loc[i, "Date"]
                    sequence.loc[seq_df_index,'Sequence'] = -1
                    sequence.loc[seq_df_index,'Entry Price'] = self.symbol_data_1mo.loc[i, "High"]
                    enter_price = self.symbol_data_1mo.loc[i, "Close"]
            elif(down_seq):
                days = days + 1
                if(close_price < min(down_seq_list)[1]):
                    down_seq_list.append((self.symbol_data_1mo.loc[i, "Low"],self.symbol_data_1mo.loc[i, "High"]))
                    continue
                else: #turning from dowm trend to up trend
                    sell_price = self.symbol_data_1mo.loc[i, "Close"]
                    seq_yield = (sell_price - enter_price)/enter_price*100
                    sequence.loc[seq_df_index,'Yield'] = seq_yield*(-1)
                    sequence.loc[seq_df_index,'Days'] = days
                    days = seq_yield = 0
                    up_seq_list = down_seq_list =[]
                    down_seq = False
                    up_seq = True
                    seq_df_index = seq_df_index + 1
                    up_seq_list.append((self.symbol_data_1mo.loc[i, "High"],self.symbol_data_1mo.loc[i, "Low"]))
                    sequence.loc[seq_df_index,'Date'] = self.symbol_data_1mo.loc[i, "Date"]
                    sequence.loc[seq_df_index,'Sequence'] = 1
                    sequence.loc[seq_df_index,'Entry Price'] = self.symbol_data_1mo.loc[i, "Low"]
                    enter_price = self.symbol_data_1mo.loc[i, "Close"]
    return sequence


   
se = SequenceMethod('SPY')
se.plot_monthly_graph()
print('blala')