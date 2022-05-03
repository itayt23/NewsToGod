from doctest import FAIL_FAST
import imp
from multiprocessing import parent_process
from statistics import mean
from unittest.result import failfast
from urllib import request
import prompt_toolkit
# from pyrsistent import T
import requests
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from numpy import empty, vander
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from newsprocessor import NewsProcessor
from marketsentiment import MarketSentiment
from sre_constants import SUCCESS
from PySimpleGUI.PySimpleGUI import WINDOW_CLOSE_ATTEMPTED_EVENT
import time
from window import Layout
import PySimpleGUI as sg
from pathlib import Path
import pymannkendall as mk
import numpy as np
import yfinance as yf
import json


done = False
def run(scrapper):
    global done
    stocks_df = scrapper.getDataFrame()
    try:
        for index, stock in enumerate(stocks_df['Symbol']):
            scrapper.scrap(stock, index)
            print(f"Finish {index+1} Symbol")
    except Exception as e:
        print('Problem accured during scarp: '+str(e))
        print(f'the data was export to excel, scarp was stop at symbol No.{index}')
    if(not stocks_df['Final Score'].empty): done = True


def process_user_input():
    global done
    start_time = time.time()
    name = str(time.ctime().replace('"',"").replace(':',".").replace('?',"").replace('\\',"").replace('/',"").replace('<',"").replace('>',"").replace('*',"").replace('|',""))
    layout = Layout()
    window = layout.setWindow(layout.getMainLayout())
    event, values = window.read()
    while not (event == sg.WIN_CLOSED or event=="Exit"):
        if event == "Submit":
            window["-PROG-"].UpdateBar(1)
            file_path = values["-FILE-"]
            stock_interval = values["-INTERVAL_NAME-"]
            # scrapper = ClientsScraper(file_path, stock_interval)
            # run(scrapper)
            window["-PROG-"].UpdateBar(2)
            if(done):
                #results_scrap_path = Path('..','results')
                results_scrap_path = Path.cwd() / 'results'
                if not results_scrap_path.exists():
                    results_scrap_path.mkdir(parents=True)
                file_name = "Rank" +name+".xlsx"
                # scrapper.getDataFrame().to_excel(results_scrap_path / file_name)
                print("Scrap was finish successfully! =)")
            print(f"Total runtime of the program is {round((time.time() - start_time)/60, 2)} minutes")
        event, values = window.read()
    window.close()
    






if __name__ == '__main__':
  # Need to do:
  #make MarketSentiment a Generic calss
  #got from investing information

    # url = "https://www.investing.com/indices/us-spx-500-scoreboard"
    # news = requests.request("GET", url)
    # print(news.text)
    # news_data = json.loads(news.text)
    # print(news_data)
    news = NewsProcessor('all',5)
    news.plot_news()
    # market = MarketSentiment()

    # process_user_input()
