
from newsprocessor import NewsProcessor
from marketsentiment import MarketSentiment
import time
from window import Layout
import PySimpleGUI as sg


def run():
    pass
  

def process_user_input():
    done = False
    start_time = time.time()
    name = str(time.ctime().replace('"',"").replace(':',".").replace('?',"").replace('\\',"").replace('/',"").replace('<',"").replace('>',"").replace('*',"").replace('|',""))
    layout = Layout()
    window = layout.setWindow(layout.getMainLayout())
    event, values = window.read()
    while not (event == sg.WIN_CLOSED or event=="Exit"):
        if event == "Get Markets Sentiment":
            window["-PROG-"].UpdateBar(1)
            news_num = values["-NEWS_NUMBER-"]
            MarketSentiment(news_num)
            window["-PROG-"].UpdateBar(2)
            done = True
        if event == "Visualize News Sentiment":
            window["-PROG-"].UpdateBar(1)
            news_num = values["-NEWS_NUMBER-"]
            NewsProcessor('all',news_num)
            window["-PROG-"].UpdateBar(2)
            done = True
        if(done):
            print("NewsToGod was finish successfully! =)")
            print(f"Total runtime of the program is {round((time.time() - start_time)/60, 2)} minutes")
        event, values = window.read()
    window.close()
    

if __name__ == '__main__':
    process_user_input()
    #need to change news sentiment score calculate

