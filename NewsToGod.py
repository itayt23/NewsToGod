
import sys
import asyncio
from api_context import Context
from sectors_sentiment import SectorsSentiment
from sentimentprocessor import SentimentProcessor
from market_sentiment import MarketSentiment
import time
from window import Layout
import PySimpleGUI as sg
import threading


MAX_PROG_BAR = 1000
layout = Layout()
window = layout.setWindow(layout.getMainLayout())
working = False

# window.close()
# window = sg.Window('Caller Finder',layout.getWhatsAppLayout(), size=(750,350),element_justification='c')

def run_market_sentiment():
    global working
    bar_thread = threading.Thread(target=update_progrees_bar, args=("markets",))
    bar_thread.start()
    market = MarketSentiment()
    working = False
    bar_thread.join()
    window["-PROG-"].UpdateBar(MAX_PROG_BAR)
    print(f"program was finish successfully! =)")

def run_sectors_sentiment():
    global working
    bar_thread = threading.Thread(target=update_progrees_bar)
    bar_thread.start()
    sectors = SectorsSentiment()
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
    while(counter < 990 and working):
        time.sleep(1.5)
        counter= counter + 1 if kind == "sectors" else counter + 5 
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
    global window, working
    if not working:
        working = True
        window["-PROG-"].UpdateBar(1)
        window.perform_long_operation(make_connection, '-OPERATION DONE-')
    else: sg.popup_quick_message("Running other program right now\nPlease wait until finish running the program",auto_close_duration=5)

def make_connection():
    global working
    bar_thread = threading.Thread(target=update_progrees_bar, args=("ts",))
    bar_thread.start()
    asyncio.run(run_connection())
    working = False
    bar_thread.join()
    window["-PROG-"].UpdateBar(MAX_PROG_BAR)
    print(f"TradeStation connection successfully =)")

async def run_connection():
    ctx = Context()
    await ctx.initialize()

def process_user_input():
    global window, working
    start_time = time.time()
    event, values = window.read()
    while not (event == sg.WIN_CLOSED or event=="Exit"):
        if event == "Get Markets Sentiment":
            get_markets_sentiment()
        if event == "Get Sectors Sentiment":
            get_sectors_sentiment()
        if event == "Make TradeStation Connection":
            connect_trade_station()
        event, values = window.read()
    window.close()
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



