import sys
import asyncio
from turtle import update
from sequencing import SequenceMethod, SequenceMethodSymbol
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
import traceback
from portfolio import Portfolio

MAX_PROG_BAR = 1000
# sequence_spy = SequenceMethodSymbol('SPY')
# sequence_qqq = SequenceMethodSymbol('QQQ')
layout = Layout()
window = layout.setWindow(layout.getMainLayout())
working = False
updating_account = False
sectors = markets = "None"
ts_manager = 0
ts_connect = False
portfolio = None
# object_path = Path.cwd() / 'Results' / 'objects files' / 'Markets' 
# object_path = str(object_path)
# markets_file = open(object_path + f"/Markets_{date.today()}.obj","rb")
# object_file = pickle.load(markets_file)

# window.close()
# window = sg.Window('Caller Finder',layout.getWhatsAppLayout(), size=(750,350),element_justification='c')

#TODO: SHOW HOLDINGS BUTTON
#TODO: SHOW ORDERS BUTTON
#TODO: SHOW PORTFOLIO BUTTON
#TODO: RUN BUY AND SELL ALGO
#TODO HOWCOME IN THE MAIN WINDOW I GOT OTHER SENTIMENT THEN THE SECOND?

def run_market_recommendation():
    global working, markets, window
    bar_thread = threading.Thread(target=update_progrees_bar, args=("markets",))
    bar_thread.start()
    markets = MarketSentiment()
    save_object(markets,"markets")
    # score, sentiment = get_recommendation(markets,sequence_spy,sequence_qqq)
    # window['-RECOMMENDATION-'].update(sentiment)
    # if(score < 0):  window['-RECOMMENDATION-'].update(text_color='red')
    # elif(score > 0):  window['-RECOMMENDATION-'].update(text_color='green')
    working = False
    bar_thread.join()
    window["-PROG-"].UpdateBar(MAX_PROG_BAR)
    print(f"program was finish successfully! =)")

def get_recommendation(markets,sequence_spy,sequence_qqq):
    sentiment = markets.get_sentiment_score() #More wheigt on sentiment
    seq_weekly_spy = sequence_spy.get_week_rank()
    seq_monthly_spy = sequence_spy.get_month_rank()
    seq_weekly_qqq = sequence_qqq.get_week_rank()
    seq_monthly_qqq = sequence_qqq.get_month_rank()
    score = sentiment  + seq_weekly_spy + seq_monthly_spy + seq_monthly_qqq + seq_weekly_qqq
    if(score <= -4): return score, "Strong Sell"
    elif(score < 0): return score, "Sell"
    elif(score == 0): return score, "Netural"
    elif(score > 0 and score < 4): return score, "Buy"
    elif(score >= 4): return score, "Strong Buy"


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

def run_my_strategy(kind):
    global working, portfolio
    if(kind == 'Full'):
        portfolio.run_buy_and_sell_strategy_full_automate()
    elif(kind == 'Semi'):
        portfolio.run_buy_and_sell_strategy_semi_automate()
    working = False
    print(f"Strategy was finish successfully! =) ---------> check your portfolio")

def run_news_processor(news_num):
    news = SentimentProcessor(news_num)
    news.run_market_articles_processor()
    # news.run_news_processor()
    # news.plot_news()


def update_progrees_bar(kind='sectors'):
    global working, window
    counter = 2
    while(counter < 900 and working):
        time.sleep(1.5)
        counter= counter + 1 if kind == "sectors" else counter + 3
        window["-PROG-"].UpdateBar(counter)
    while(counter < 980 and working):
        time.sleep(2.5)
        counter= counter + 0.5 if kind == "sectors" else counter + 1
        window["-PROG-"].UpdateBar(counter)

def get_markets_recommendation():
    global window, working
    if not working:
        working = True
        window["-PROG-"].UpdateBar(1)
        window.perform_long_operation(run_market_recommendation, '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until the program finish to run",auto_close_duration=5)

def get_sectors_sentiment():
    global window, working
    if not working:
        working = True
        window["-PROG-"].UpdateBar(1)
        window.perform_long_operation(run_sectors_sentiment, '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until the program finish to run",auto_close_duration=5)

def run_strategy(kind):
    global window, working
    if not working:
        print("-"*40)
        print("Starting Strategy")
        print("-"*40)
        working = True
        window.perform_long_operation(lambda: run_my_strategy(kind), '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until the program finish to run",auto_close_duration=5)

def connect_trade_station():
    global window, working, sectors, markets
    if not working:
        working = True
        window["-PROG-"].UpdateBar(1)
        window.perform_long_operation(make_connection, '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until the program finish to run",auto_close_duration=5)

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
    global working
    global sectors
    if not working:
        working = True
        if(sectors != 'None'):
            print("object already exist")
            return
        sectors = load_object("sectors")
        if(sectors == 0):
            print("Cannot load Sectors sentiment, PLEASE GET SECTORS SENTIMENT FIRST")
        else:
            print("LOAD sectors sentiment successfully :)")
    else: sg.popup_quick_message("Running other program right now\nPlease wait until the program finish to run",auto_close_duration=5)
    working = False 


def load_markets_object():
    global working, markets, window
    if not working:
        working = True  
        if(markets != 'None'):
            print("object already exist")
            return
        markets = load_object("markets")
        if(markets == 0):
            print("Cannot load Markets sentiment, PLEASE GET MARKETS SENTIMENT FIRST")
        else:
            # score, sentiment = get_recommendation(markets,sequence_spy,sequence_qqq)
            # window['-RECOMMENDATION-'].update(sentiment)
            # if(score < 0):  window['-RECOMMENDATION-'].update(text_color='red')
            # elif(score > 0):  window['-RECOMMENDATION-'].update(text_color='green')
            print("LOAD markets sentiment successfully :)")
    else: sg.popup_quick_message("Running other program right now\nPlease wait until the program finish to run",auto_close_duration=5)
    working = False
    
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
    global window, updating_account
    if not updating_account:
        updating_account = True
        window.perform_long_operation(get_account_details, '-OPERATION DONE-')
    else: sg.popup_quick_message("Already Updating Account Details",auto_close_duration=4)

def get_account_details():
    global sectors,markets,window,ts_manager,updating_account
    try:
        window['-SECTORS_SENTIMENT-'].update(sectors.get_sentiment())
        window['-MARKETS_SENTIMENT-'].update(markets.get_sentiment())
    except Exception:
        print(f"Problem with Getting Market\Sectors data, please restart and get them again. Problem Details: \n {traceback.format_exc()}")
        updating_account = False 
        return
    while(True):
        try:
            url = "https://api.tradestation.com/v3/brokerage/accounts/11509188/balances"
            headers = {"Authorization":f'Bearer {ts_manager.TOKENS.access_token}'}
            account_details = requests.request("GET", url, headers=headers)
            account_details = json.loads(account_details.text)
            window['-ACCOUNT_ID-'].update(account_details['Balances'][0]['AccountID'])
            window['-ACCOUNT_CASH-'].update(account_details['Balances'][0]['CashBalance'])
            window['-ACCOUNT_EQUITY-'].update(account_details['Balances'][0]['MarketValue'])
            window['-TODAY_RETURN-'].update(account_details['Balances'][0]['TodaysProfitLoss'])
            window['-REALIZED_RETURN-'].update(account_details['Balances'][0]['BalanceDetail']['RealizedProfitLoss'])
            window['-UNREALIZED_RETURN-'].update(account_details['Balances'][0]['BalanceDetail']['UnrealizedProfitLoss'])
        except Exception:
            print(f"problem connection TradeStation Api, Details: \n {traceback.format_exc()}\nThread update account stopped")
            updating_account = False
            return
    updating_account = False

def process_user_input():
    global window, working, sectors, markets, ts_connect,ts_manager,sequence_qqq,sequence_spy, portfolio
    start_time = time.time()
    first_connect = True
    event, values = window.read(timeout=100)
    while not (event == sg.WIN_CLOSED or event=="Exit"):
        if ts_connect and first_connect:
            if first_connect:
                portfolio = Portfolio(ts_manager,markets,sectors)
                window.close()
                window = layout.setWindow(layout.get_tradestation_layout())
                event, values = window.read(timeout=100)
                update_ts_data()
                first_connect = False
        if event == "Get Market Sentiment":
            get_markets_recommendation()
        if event == "Get Sectors Sentiment":
            get_sectors_sentiment()
        if event == "Load Sectors Sentiment":
            load_sectors_object()
        if event == "Load Markets Recommendation":
            load_markets_object()
        if event == "Connect TradeStation":
            # if (sectors != "None" or sectors != 0) and (markets != "None" or markets != 0):
            if sectors != "None" and markets != "None":
                connect_trade_station()
            else: sg.popup_quick_message("Get Sentiments Before Connection!",auto_close_duration=5)
        if event == 'Run Full Automate Strategy':
            run_strategy('Full')
        if event == 'Run Semi Automate Strategy':
            run_strategy('Semi')
        if event == 'Update Account':
            update_ts_data()
        event, values = window.read(timeout=100)
    window.close()
    sys.exit()


if __name__ == '__main__':

    process_user_input()



    # # growth etf, value etf
    # etfs_xlc = ['XLC','FCOM','FIVG', 'IXP','IYZ','VR']
    # etfs_xly = ['XLY','VCR','XHB', 'PEJ', 'IBUY','BJK','BETZ''AWAY','SOCL','BFIT','KROP']
    # etfs_xlp = ['XLP','FTXG','KXI','PBJ']
    # etfs_xle = ['XLE','XES','CNRG','PXI','FTXN','XOP','FCG','SOLR','ICLN','QCLN','EDOC','AGNG']
    # etfs_xlf = ['XLF','KIE','KBE','KCE','XRE']
    # etfs_xlv = ['XLV','FHLC','XHE','XHS','IHF','GNOM','HTEC','PPH','IXJ','IHE']
    # etfs_xli = ['XLI','XAR','XTN','PRN','EXI','AIRR','IFRA','TOLZ','IGF','SIMS','HYDR']
    # etfs_xlk = ['XLK','VGT','FTEC','IGM','XSD','HERO','FDN','IRBO','FINX','IHAK','BUG','CLOU','SNSR','AIQ','CTEC','RAY']
    # etfs_xlu = ['XLU','JXI','UTES','ECLN','RNRG','PUI','AQWA','WNDY']
    # etfs_xlre = ['XLRE','FREL','RWR','REET','VNQ','REZ','KBWY','SRET','SRVR','VPN','GRNR']
    # etfs_xlb = ['XLB','VAW','FMAT','PYZ','XME','HAP','MXI','IGE','MOO','FIW','WOOD','COPX','PHO','IYM','FXZ','URA','LIT','SIL']
    # etfs_extra = ['PBD','XT','ACES','DRIV','PBW','IPAY','FAN','ICLN','MJ','VCLN','POTX','HYDR','WNDY','MJUS','JETS','TOKE','BOTZ','OCEN','SPFF']

