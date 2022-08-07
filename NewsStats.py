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


# # ! plot regression
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
# model = sm.OLS(y,x).fit()

# #view model summary
# # sns.regplot(y="My Yield", x="Technical Weight", data=weights_df)
# print(model.summary())
# print('bla bla')

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



import PySimpleGUI as sg

"""
    Color names courtesy of Big Daddy's Wiki-Python
    http://www.wikipython.com/tkinter-ttk-tix/summary-information/colors/
    
    Shows a big chart of colors... give it a few seconds to create it
    Once large window is shown, you can click on any color and another window will popup 
    showing both white and black text on that color
"""


COLORS = ['snow', 'ghost white', 'white smoke', 'gainsboro', 'floral white', 'old lace',
          'linen', 'antique white', 'papaya whip', 'blanched almond', 'bisque', 'peach puff',
          'navajo white', 'lemon chiffon', 'mint cream', 'azure', 'alice blue', 'lavender',
          'lavender blush', 'misty rose', 'dark slate gray', 'dim gray', 'slate gray',
          'light slate gray', 'gray', 'light gray', 'midnight blue', 'navy', 'cornflower blue', 'dark slate blue',
          'slate blue', 'medium slate blue', 'light slate blue', 'medium blue', 'royal blue', 'blue',
          'dodger blue', 'deep sky blue', 'sky blue', 'light sky blue', 'steel blue', 'light steel blue',
          'light blue', 'powder blue', 'pale turquoise', 'dark turquoise', 'medium turquoise', 'turquoise',
          'cyan', 'light cyan', 'cadet blue', 'medium aquamarine', 'aquamarine', 'dark green', 'dark olive green',
          'dark sea green', 'sea green', 'medium sea green', 'light sea green', 'pale green', 'spring green',
          'lawn green', 'medium spring green', 'green yellow', 'lime green', 'yellow green',
          'forest green', 'olive drab', 'dark khaki', 'khaki', 'pale goldenrod', 'light goldenrod yellow',
          'light yellow', 'yellow', 'gold', 'light goldenrod', 'goldenrod', 'dark goldenrod', 'rosy brown',
          'indian red', 'saddle brown', 'sandy brown',
          'dark salmon', 'salmon', 'light salmon', 'orange', 'dark orange',
          'coral', 'light coral', 'tomato', 'orange red', 'red', 'hot pink', 'deep pink', 'pink', 'light pink',
          'pale violet red', 'maroon', 'medium violet red', 'violet red',
          'medium orchid', 'dark orchid', 'dark violet', 'blue violet', 'purple', 'medium purple',
          'thistle', 'snow2', 'snow3',
          'snow4', 'seashell2', 'seashell3', 'seashell4', 'AntiqueWhite1', 'AntiqueWhite2',
          'AntiqueWhite3', 'AntiqueWhite4', 'bisque2', 'bisque3', 'bisque4', 'PeachPuff2',
          'PeachPuff3', 'PeachPuff4', 'NavajoWhite2', 'NavajoWhite3', 'NavajoWhite4',
          'LemonChiffon2', 'LemonChiffon3', 'LemonChiffon4', 'cornsilk2', 'cornsilk3',
          'cornsilk4', 'ivory2', 'ivory3', 'ivory4', 'honeydew2', 'honeydew3', 'honeydew4',
          'LavenderBlush2', 'LavenderBlush3', 'LavenderBlush4', 'MistyRose2', 'MistyRose3',
          'MistyRose4', 'azure2', 'azure3', 'azure4', 'SlateBlue1', 'SlateBlue2', 'SlateBlue3',
          'SlateBlue4', 'RoyalBlue1', 'RoyalBlue2', 'RoyalBlue3', 'RoyalBlue4', 'blue2', 'blue4',
          'DodgerBlue2', 'DodgerBlue3', 'DodgerBlue4', 'SteelBlue1', 'SteelBlue2',
          'SteelBlue3', 'SteelBlue4', 'DeepSkyBlue2', 'DeepSkyBlue3', 'DeepSkyBlue4',
          'SkyBlue1', 'SkyBlue2', 'SkyBlue3', 'SkyBlue4', 'LightSkyBlue1', 'LightSkyBlue2',
          'LightSkyBlue3', 'LightSkyBlue4', 'Slategray1', 'Slategray2', 'Slategray3',
          'Slategray4', 'LightSteelBlue1', 'LightSteelBlue2', 'LightSteelBlue3',
          'LightSteelBlue4', 'LightBlue1', 'LightBlue2', 'LightBlue3', 'LightBlue4',
          'LightCyan2', 'LightCyan3', 'LightCyan4', 'PaleTurquoise1', 'PaleTurquoise2',
          'PaleTurquoise3', 'PaleTurquoise4', 'CadetBlue1', 'CadetBlue2', 'CadetBlue3',
          'CadetBlue4', 'turquoise1', 'turquoise2', 'turquoise3', 'turquoise4', 'cyan2', 'cyan3',
          'cyan4', 'DarkSlategray1', 'DarkSlategray2', 'DarkSlategray3', 'DarkSlategray4',
          'aquamarine2', 'aquamarine4', 'DarkSeaGreen1', 'DarkSeaGreen2', 'DarkSeaGreen3',
          'DarkSeaGreen4', 'SeaGreen1', 'SeaGreen2', 'SeaGreen3', 'PaleGreen1', 'PaleGreen2',
          'PaleGreen3', 'PaleGreen4', 'SpringGreen2', 'SpringGreen3', 'SpringGreen4',
          'green2', 'green3', 'green4', 'chartreuse2', 'chartreuse3', 'chartreuse4',
          'OliveDrab1', 'OliveDrab2', 'OliveDrab4', 'DarkOliveGreen1', 'DarkOliveGreen2',
          'DarkOliveGreen3', 'DarkOliveGreen4', 'khaki1', 'khaki2', 'khaki3', 'khaki4',
          'LightGoldenrod1', 'LightGoldenrod2', 'LightGoldenrod3', 'LightGoldenrod4',
          'LightYellow2', 'LightYellow3', 'LightYellow4', 'yellow2', 'yellow3', 'yellow4',
          'gold2', 'gold3', 'gold4', 'goldenrod1', 'goldenrod2', 'goldenrod3', 'goldenrod4',
          'DarkGoldenrod1', 'DarkGoldenrod2', 'DarkGoldenrod3', 'DarkGoldenrod4',
          'RosyBrown1', 'RosyBrown2', 'RosyBrown3', 'RosyBrown4', 'IndianRed1', 'IndianRed2',
          'IndianRed3', 'IndianRed4', 'sienna1', 'sienna2', 'sienna3', 'sienna4', 'burlywood1',
          'burlywood2', 'burlywood3', 'burlywood4', 'wheat1', 'wheat2', 'wheat3', 'wheat4', 'tan1',
          'tan2', 'tan4', 'chocolate1', 'chocolate2', 'chocolate3', 'firebrick1', 'firebrick2',
          'firebrick3', 'firebrick4', 'brown1', 'brown2', 'brown3', 'brown4', 'salmon1', 'salmon2',
          'salmon3', 'salmon4', 'LightSalmon2', 'LightSalmon3', 'LightSalmon4', 'orange2',
          'orange3', 'orange4', 'DarkOrange1', 'DarkOrange2', 'DarkOrange3', 'DarkOrange4',
          'coral1', 'coral2', 'coral3', 'coral4', 'tomato2', 'tomato3', 'tomato4', 'OrangeRed2',
          'OrangeRed3', 'OrangeRed4', 'red2', 'red3', 'red4', 'DeepPink2', 'DeepPink3', 'DeepPink4',
          'HotPink1', 'HotPink2', 'HotPink3', 'HotPink4', 'pink1', 'pink2', 'pink3', 'pink4',
          'LightPink1', 'LightPink2', 'LightPink3', 'LightPink4', 'PaleVioletRed1',
          'PaleVioletRed2', 'PaleVioletRed3', 'PaleVioletRed4', 'maroon1', 'maroon2',
          'maroon3', 'maroon4', 'VioletRed1', 'VioletRed2', 'VioletRed3', 'VioletRed4',
          'magenta2', 'magenta3', 'magenta4', 'orchid1', 'orchid2', 'orchid3', 'orchid4', 'plum1',
          'plum2', 'plum3', 'plum4', 'MediumOrchid1', 'MediumOrchid2', 'MediumOrchid3',
          'MediumOrchid4', 'DarkOrchid1', 'DarkOrchid2', 'DarkOrchid3', 'DarkOrchid4',
          'purple1', 'purple2', 'purple3', 'purple4', 'MediumPurple1', 'MediumPurple2',
          'MediumPurple3', 'MediumPurple4', 'thistle1', 'thistle2', 'thistle3', 'thistle4',
          'grey1', 'grey2', 'grey3', 'grey4', 'grey5', 'grey6', 'grey7', 'grey8', 'grey9', 'grey10',
          'grey11', 'grey12', 'grey13', 'grey14', 'grey15', 'grey16', 'grey17', 'grey18', 'grey19',
          'grey20', 'grey21', 'grey22', 'grey23', 'grey24', 'grey25', 'grey26', 'grey27', 'grey28',
          'grey29', 'grey30', 'grey31', 'grey32', 'grey33', 'grey34', 'grey35', 'grey36', 'grey37',
          'grey38', 'grey39', 'grey40', 'grey42', 'grey43', 'grey44', 'grey45', 'grey46', 'grey47',
          'grey48', 'grey49', 'grey50', 'grey51', 'grey52', 'grey53', 'grey54', 'grey55', 'grey56',
          'grey57', 'grey58', 'grey59', 'grey60', 'grey61', 'grey62', 'grey63', 'grey64', 'grey65',
          'grey66', 'grey67', 'grey68', 'grey69', 'grey70', 'grey71', 'grey72', 'grey73', 'grey74',
          'grey75', 'grey76', 'grey77', 'grey78', 'grey79', 'grey80', 'grey81', 'grey82', 'grey83',
          'grey84', 'grey85', 'grey86', 'grey87', 'grey88', 'grey89', 'grey90', 'grey91', 'grey92',
          'grey93', 'grey94', 'grey95', 'grey97', 'grey98', 'grey99']

sg.set_options(button_element_size=(12, 1),
               element_padding=(0, 0),
               auto_size_buttons=False,
               border_width=0)

layout = [[sg.Text('Click on a color square to see both white and black text on that color',
                text_color='blue', font='Any 15')]]
row = []
layout = []

# -- Create primary color viewer window --
for rows in range(40):
    row = []
    for i in range(12):
        try:
            color = COLORS[rows+40*i]
            row.append(sg.Button(color, button_color=('black', color), key=color))
        except:
            pass
    layout.append(row)

window = sg.Window('Color Viewer', layout, grab_anywhere=False, font=('any 9'))

# -- Event loop --
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    # -- Create a secondary window that shows white and black text on chosen color
    layout2 = [[sg.DummyButton(event, button_color=('white', event)),
                sg.DummyButton(event, button_color=('black', event))]]
    sg.Window('Buttons with white and black text', layout2, keep_on_top=True).read(timeout=0)

window.close()