from turtle import up
from grpc import UnaryStreamClientInterceptor
from importlib_metadata import entry_points
from openpyxl import load_workbook
from regex import P
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
        self.symbol_data_1d = pd.DataFrame(yf.download(ticker, period='5y',interval='1d')).dropna()
        self.symbol_data_1d = self.symbol_data_1d.rename_axis('Date').reset_index()
        self.symbol_data_1wk = pd.DataFrame(yf.download(ticker, period='5y',interval='1wk')).dropna()
        self.symbol_data_1wk = self.symbol_data_1wk.rename_axis('Date').reset_index()
        self.symbol_data_1mo = pd.DataFrame(yf.download(ticker, period='10y',interval='1mo')).dropna()
        self.symbol_data_1mo = self.symbol_data_1mo.rename_axis('Date').reset_index()
        self.sequence_1d = pd.DataFrame(columns=['Date', 'Entry Price', 'Sequence', 'Days', "Yield"])
        self.sequence_1wk = pd.DataFrame(columns=['Date', 'Entry Price', 'Sequence', 'Days', "Yield"])
        self.sequence_1mo = pd.DataFrame(columns=['Date', 'Entry Price', 'Sequence', 'Days', "Yield"])
        self.sequence_1d,self.sequence_1wk,self.sequence_1mo = build_sequences(self)

    def print_sequence_data(self,interval):
        if(interval == 'day'):
            print(self.sequence_1d)
        if(interval == 'week'):
            print(self.sequence_1wk)
        if(interval == 'month'):
            print(self.sequence_1mo)
           
    def plot_graph(self,interval):
        up_seq_x = []
        up_seq_y = []
        down_seq_x = []
        down_seq_y = []
        seq_df = pd.DataFrame
        symbol_df = pd.DataFrame
        width = 0
        if(interval == 'day'):
            seq_df = self.sequence_1d
            symbol_df =  self.symbol_data_1d
            width = 1
            size = 10 
        if(interval == 'week'):
            seq_df = self.sequence_1wk
            symbol_df =  self.symbol_data_1wk
            width = 2
            size = 10 
        if(interval == 'month'):
            seq_df = self.sequence_1mo
            symbol_df =  self.symbol_data_1mo
            width = 4
            size = 20 
        for index,row in seq_df.iterrows():
            if(row["Sequence"] == 1):
                up_seq_x.append(row["Date"])
                up_seq_y.append(row["Entry Price"])
            else:
                down_seq_x.append(row["Date"])
                down_seq_y.append(row["Entry Price"])

        plt.style.use('seaborn-dark')
        # plt.style.use('ggplot')
        # plt.style.use('dark_background')
        # plt.style.use('fivethirtyeight')
        # plt.style.use('grayscale')
        
        # convert into datetime object
        symbol_df['Date'] = pd.to_datetime(symbol_df['Date'])

        # apply map function
        symbol_df['Date'] = symbol_df['Date'].map(mpdates.date2num)
        
        # creating Subplots
        fig, ax = plt.subplots()
        
        # plotting the data
    
        candlestick_ohlc(ax, symbol_df.values, width = width,
                        colorup = 'green', colordown = 'red',
                        alpha = 0.8)
        
        # allow grid
        ax.grid(True)
        
        # Setting labels
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        
        # setting title
        plt.title('Candelsticks')
        # Formatting Date
        date_format = mpdates.DateFormatter('%d-%m-%Y')
        ax.xaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()
        fig.tight_layout()
        plt.scatter(up_seq_x,up_seq_y,marker='^',facecolors='green',s=size)
        plt.scatter(down_seq_x,down_seq_y,marker='v',facecolors='red',s=size)
        plt.show()

def build_sequences(self):
    seq_1d = pd.DataFrame
    seq_1wk = pd.DataFrame
    seq_1mo = pd.DataFrame
    for interval in range(0,3):
        match interval:
            case 0:
                symbol_df = self.symbol_data_1d
            case 1:
                symbol_df = self.symbol_data_1wk
            case 2:
                symbol_df = self.symbol_data_1mo
        sequence = pd.DataFrame(columns=['Date', 'Sequence', 'Days', "Yield"])
        seq_df_index = 0
        down_seq = up_seq = False
        down_seq_list = up_seq_list =[]
        close_price = low_price = high_price =  enter_price = sell_price = seq_yield = 1
        days = 0
        in_sequence = False
        first = True
        for i in range(len(symbol_df)):
            if first:
                first = False
                continue
        
            close_price = symbol_df.loc[i, "Close"]
            low_price = symbol_df.loc[i-1, "Low"]
            high_price = symbol_df.loc[i-1, "High"]
            if not in_sequence:
                if(close_price > low_price):
                    up_seq = True
                    up_seq_list.append((high_price,low_price))
                    up_seq_list.append((symbol_df.loc[i, "High"],symbol_df.loc[i, "Low"]))
                    sequence.loc[seq_df_index,'Date'] = symbol_df.loc[i, "Date"]
                    sequence.loc[seq_df_index,'Sequence'] = 1
                    sequence.loc[seq_df_index,'Entry Price'] = symbol_df.loc[i, "Low"]
                    enter_price = symbol_df.loc[i, "Close"]
                    in_sequence = True
                elif(close_price < high_price):
                    down_seq = True
                    down_seq_list.append((low_price,high_price))
                    down_seq_list.append((symbol_df.loc[i, "Low"],symbol_df.loc[i, "High"]))
                    sequence.loc[seq_df_index,'Date'] = symbol_df.loc[i, "Date"]
                    sequence.loc[seq_df_index,'Sequence'] = -1
                    sequence.loc[seq_df_index,'Entry Price'] = symbol_df.loc[i, "High"]
                    sell_price = symbol_df.loc[i, "Close"]
                    in_sequence = True
            else:
                if(up_seq):
                    days = days + 1
                    if(close_price > max(up_seq_list)[1]):
                        up_seq_list.append((symbol_df.loc[i, "High"],symbol_df.loc[i, "Low"]))
                        continue
                    else: #finsih up trend and starting down trend
                        sell_price = symbol_df.loc[i, "Close"]
                        seq_yield = (sell_price - enter_price)/enter_price*100
                        sequence.loc[seq_df_index,'Yield'] = seq_yield
                        sequence.loc[seq_df_index,'Days'] = days
                        days = seq_yield = 0
                        up_seq_list = down_seq_list =[]
                        up_seq = False
                        down_seq = True
                        seq_df_index = seq_df_index + 1
                        down_seq_list.append((symbol_df.loc[i, "Low"],symbol_df.loc[i, "High"]))
                        sequence.loc[seq_df_index,'Date'] = symbol_df.loc[i, "Date"]
                        sequence.loc[seq_df_index,'Sequence'] = -1
                        sequence.loc[seq_df_index,'Entry Price'] = symbol_df.loc[i, "High"]
                        enter_price = symbol_df.loc[i, "Close"]
                elif(down_seq):
                    days = days + 1
                    if(close_price < min(down_seq_list)[1]):
                        down_seq_list.append((symbol_df.loc[i, "Low"],symbol_df.loc[i, "High"]))
                        continue
                    else: #turning from dowm trend to up trend
                        sell_price = symbol_df.loc[i, "Close"]
                        seq_yield = (sell_price - enter_price)/enter_price*100
                        sequence.loc[seq_df_index,'Yield'] = seq_yield*(-1)
                        sequence.loc[seq_df_index,'Days'] = days
                        days = seq_yield = 0
                        up_seq_list = down_seq_list =[]
                        down_seq = False
                        up_seq = True
                        seq_df_index = seq_df_index + 1
                        up_seq_list.append((symbol_df.loc[i, "High"],symbol_df.loc[i, "Low"]))
                        sequence.loc[seq_df_index,'Date'] = symbol_df.loc[i, "Date"]
                        sequence.loc[seq_df_index,'Sequence'] = 1
                        sequence.loc[seq_df_index,'Entry Price'] = symbol_df.loc[i, "Low"]
                        enter_price = symbol_df.loc[i, "Close"]
        if(interval == 0):
            seq_1d = sequence
        if(interval == 1):
            seq_1wk = sequence
        if(interval == 2):
            seq_1mo = sequence
    return seq_1d,seq_1wk,seq_1mo


   
se = SequenceMethod('SPY')
# se.plot_graph('day')
# se.print_sequence_data('day')
se.print_sequence_data('week')
se.plot_graph('week')
se.print_sequence_data('month')
se.plot_graph('month')
print('blala')