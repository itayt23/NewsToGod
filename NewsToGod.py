from distutils.command.build_scripts import first_line_re
import sys
import asyncio
from wsgiref.headers import tspecials
from api_context import Context
from sectors_sentiment import SectorsSentiment
from sentimentprocessor import SentimentProcessor
from market_sentiment import MarketSentiment
import time
from window import Layout
import PySimpleGUI as sg
import threading
import pickle
from pathlib import Path
import os.path
from datetime import datetime, timedelta, date
import requests
import json


MAX_PROG_BAR = 1000
layout = Layout()
window = layout.setWindow(layout.getMainLayout())
working = False
sectors = markets = "None"
ts_manager = 0
ts_connect = False
# object_path = Path.cwd() / 'Results' / 'objects files' / 'Markets' 
# object_path = str(object_path)
# markets_file = open(object_path + f"/Markets_{date.today()}.obj","rb")
# object_file = pickle.load(markets_file)

# window.close()
# window = sg.Window('Caller Finder',layout.getWhatsAppLayout(), size=(750,350),element_justification='c')

def run_market_sentiment():
    global working, markets
    bar_thread = threading.Thread(target=update_progrees_bar, args=("markets",))
    bar_thread.start()
    markets = MarketSentiment()
    save_object(markets,"markets")
    working = False
    bar_thread.join()
    window["-PROG-"].UpdateBar(MAX_PROG_BAR)
    print(f"program was finish successfully! =)")

def run_sectors_sentiment():
    global working, sectors
    bar_thread = threading.Thread(target=update_progrees_bar)
    bar_thread.start()
    sectors = SectorsSentiment()
    save_object(sectors,"sectors")
    working = False
    bar_thread.join()
    window["-PROG-"].UpdateBar(MAX_PROG_BAR)
    print(f"program was finish successfully! =)")

def run_news_processor(news_num):
    news = SentimentProcessor(news_num)
    news.run_market_articles_processor()
    # news.run_news_processor()
    # news.plot_news()


def update_progrees_bar(kind='sectors'):
    global working, window
    counter = 2
    while(counter < 970 and working):
        time.sleep(1.5)
        counter= counter + 1 if kind == "sectors" else counter + 3
        window["-PROG-"].UpdateBar(counter)

def get_markets_sentiment():
    global window, working
    if not working:
        working = True
        window["-PROG-"].UpdateBar(1)
        window.perform_long_operation(run_market_sentiment, '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until finish running the program",auto_close_duration=5)

def get_sectors_sentiment():
    global window, working
    if not working:
        working = True
        window["-PROG-"].UpdateBar(1)
        window.perform_long_operation(run_sectors_sentiment, '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until finish running the program",auto_close_duration=5)

def connect_trade_station():
    global window, working, sectors, markets
    if not working:
        working = True
        window["-PROG-"].UpdateBar(1)
        window.perform_long_operation(make_connection, '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until finish running the program",auto_close_duration=5)

def make_connection():
    global working, window,ts_connect
    bar_thread = threading.Thread(target=update_progrees_bar, args=("ts",))
    bar_thread.start()
    asyncio.run(run_connection())
    working = False
    bar_thread.join()
    window["-PROG-"].UpdateBar(MAX_PROG_BAR)
    print(f"TradeStation connected successfully =)")
    time.sleep(1)
    ts_connect = True
   
async def run_connection():
    global ts_manager
    ts_manager = Context()
    await ts_manager.initialize()    

def load_sectors_object():
    global sectors
    if(sectors != 'None'):
        print("object already exist")
        return
    sectors = load_object("sectors")
    if(sectors == 0):
        print("Cannot load Sectors sentiment, PLEASE GET SECTORS SENTIMENT FIRST")
    else:
        print("LOAD sectors sentiment successfully :)")


def load_markets_object():
    global markets
    if(markets != 'None'):
        print("object already exist")
        return
    markets = load_object("markets")
    if(markets == 0):
        print("Cannot load Markets sentiment, PLEASE GET MARKETS SENTIMENT FIRST")
    else:
        print("LOAD markets sentiment successfully :)")

def save_object(object,type):
    try:
        if(type == "sectors"):
            object_path = Path.cwd() / 'Results' / 'objects files' / 'Sectors'  
            if not object_path.exists():
                object_path.mkdir(parents=True)
            object_path = str(object_path)
            sectors_file = open(object_path + f"/Sectors_{date.today()}.obj","wb")
            pickle.dump(object,sectors_file)
            sectors_file.close()
        else:
            object_path = Path.cwd() / 'Results' / 'objects files' / 'Markets'  
            if not object_path.exists():
                object_path.mkdir(parents=True)
            object_path = str(object_path)
            markets_file = open(object_path + f"/Markets_{date.today()}.obj","wb")
            pickle.dump(object,markets_file)
            markets_file.close()
    except:
        print("Problem with saving object")
    
def load_object(type):
    try:
        if(type == "sectors"):
            object_path = Path.cwd() / 'Results' / 'objects files' / 'Sectors'  
            object_path = str(object_path)
            if(os.path.exists(object_path + f"/Sectors_{date.today()}.obj")):
                sectors_file = open(object_path + f"/Sectors_{date.today()}.obj","rb")
                object_file = pickle.load(sectors_file)
                sectors_file.close()
                return object_file
        else:
            object_path = Path.cwd() / 'Results' / 'objects files' / 'Markets' 
            object_path = str(object_path)
            if(os.path.exists(object_path + f"/Markets_{date.today()}.obj")):
                markets_file = open(object_path + f"/Markets_{date.today()}.obj","rb")
                object_file = pickle.load(markets_file)
                markets_file.close()
                return object_file
    except:
        return 0
    return 0

def update_ts_data():
    global window, working
    if not working:
        working = True
        window.perform_long_operation(get_account_details, '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until finish running the program",auto_close_duration=5)

def get_account_details():
    print("Getting Data...")
    global sectors,markets,window,ts_manager,working
    window['-SECTORS_SENTIMENT-'].update(sectors.get_sentiment())
    window['-MARKETS_SENTIMENT-'].update(markets.get_sentiment())
    url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/balances"
    headers = {"Authorization":f'Bearer {ts_manager.TOKENS.access_token}'}
    account_details = requests.request("GET", url, headers=headers)
    account_details = json.loads(account_details.text)
    window['-ACCOUNT_ID-'].update(account_details['Balances'][0]['AccountID'])
    window['-ACCOUNT_CASH-'].update(account_details['Balances'][0]['CashBalance'])
    window['-ACCOUNT_EQUITY-'].update(account_details['Balances'][0]['Equity'])
    working = False
    print('Finish')

def process_user_input():
    global window, working, sectors, markets, ts_connect,ts_manager
    start_time = time.time()
    first_connect = True
    event, values = window.read(timeout=100)
    while not (event == sg.WIN_CLOSED or event=="Exit"):
        if ts_connect and first_connect:
            if first_connect:
                window.close()
                window = layout.setWindow(layout.get_tradestation_layout())
                first_connect = False
        if event == "Get Markets Sentiment":
            get_markets_sentiment()
        if event == "Get Sectors Sentiment":
            get_sectors_sentiment()
        if event == "Load Sectors Sentiment":
            load_sectors_object()
        if event == "Load Markets Sentiment":
            load_markets_object()
        if event == "Connect TradeStation":
            if sectors != "None" and markets != "None":
                connect_trade_station()
            else: sg.popup_quick_message("Get Sentiments Before Connection!",auto_close_duration=5)
        if event == 'Update Data':
            update_ts_data()

        event, values = window.read(timeout=100)
    window.close()
    sectors.print_all_sentiment()
    sys.exit()


if __name__ == '__main__':
    process_user_input()





















# layout = Layout()
# window = layout.setWindow(layout.getMainLayout())
# begin = False
# done = False

# def run_market_sentiment(news_num):
#     MarketSentiment(news_num)

# def run_news_processor(news_num):
#     news = NewsProcessor('all',news_num)
#     news.plot_news()

# def update_progrees_bar():
#     global done, window
#     while(done == False):
#         counter = 0
#         while(counter < 1000 and begin):
#             time.sleep(1)
#             counter += 1
#             window["-PROG-"].UpdateBar(counter)
#     sys.exit()

# def window_ui():
#     global begin, done, window
#     while(done == False):
#         if(begin):
#             event, values = window.read()
#             while not (event == sg.WIN_CLOSED or event=="Exit"):
#                 event, values = window.read()
#             window.close()
#             sys.exit()

# def process_user_input():
#     global begin, done, window
#     start_time = time.time()
#     event, values = window.read()
#     while not (event == sg.WIN_CLOSED or event=="Exit"):
#         if event == "Get Markets Sentiment":
#             begin = True
#             news_num = values["-NEWS_NUMBER-"]
#             run_market_sentiment(news_num)
#             done = True
#         if event == "Visualize News Sentiment":
#             begin = True
#             window["-PROG-"].UpdateBar(1)
#             news_num = values["-NEWS_NUMBER-"]
#             run_news_processor(news_num)
#             window["-PROG-"].UpdateBar(2)
#             window["-PROG-"].UpdateBar(3)
#             done = True
#         if(done):
#             print("NewsToGod was finish successfully! =)")
#             print(f"Total runtime of the program is {round((time.time() - start_time)/60, 2)} minutes")
#         event, values = window.read()
#     window.close()
#     sys.exit()
    

# if __name__ == '__main__':

#     main_thread = threading.Thread(target=process_user_input,args=())
#     main_thread.start()

#     # updating_bar_thread = threading.Thread(target=update_progrees_bar,args=())
#     # updating_bar_thread.start()

#     # break_tread = threading.Thread(target=window_ui,args=())
#     # break_tread.start()
    
#     main_thread.join()
#     # updating_bar_thread.join()
#     # break_tread.join()

#     # process_user_input()
#     # lock.acquire()
#     #need to change news sentiment score calculate







# global counter
# def run_market_sentiment(news_num,lock):
#     lock.acquire()
#     MarketSentiment(news_num)
#     lock.release()

# def run_news_processor(news_num,lock):
#     lock.acquire()
#     news = NewsProcessor('all',news_num)
#     news.plot_news()
#     lock.release()

# def update_progress_bar(window):
#     lock.acquire()
#     global counter
#     counter = 0
#     while(counter < 600):
#         time.sleep(1)
#         counter += 1
#         window["-PROG-"].UpdateBar(counter)
#     lock.release()


# def process_user_input(window,event, values,lock):
#     done = False
#     start_time = time.time()
#     while not (event == sg.WIN_CLOSED or event=="Exit"):
#         if event == "Get Markets Sentiment":
#             update_progress_bar(window)
#             news_num = values["-NEWS_NUMBER-"]
#             run_market_sentiment(news_num,lock)
#             done = True
#         if event == "Visualize News Sentiment":
#             update_progress_bar(window)
#             news_num = values["-NEWS_NUMBER-"]
#             run_news_processor(news_num)
#             done = True
#         if(done):
#             window["-PROG-"].UpdateBar(600)
#             print("NewsToGod was finish successfully! =)")
#             print(f"Total runtime of the program is {round((time.time() - start_time)/60, 2)} minutes")
#         event, values = window.read()
#     window.close()
    

# if __name__ == '__main__':
#     layout = Layout()
#     window = layout.setWindow(layout.getMainLayout())
#     event, values = window.read()
#     lock = threading.Lock()
#     main_thread = threading.Thread(target=process_user_input,args=(window,event, values, lock,))
#     updating_bar_thread = threading.Thread(target=process_user_input,args=(window, event, values,lock,))

#     main_thread.start()
#     updating_bar_thread.start()
#     main_thread.join()
#     updating_bar_thread.join()
#     # process_user_input()
#     #need to change news sentiment score calculate



