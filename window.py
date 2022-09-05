from turtle import pos
import PySimpleGUI as sg
MAX_PROG_BAR = 1000

class Layout:
    def __init__(self):
        sg.theme("DarkPurple4") 

        self.layout_main = [
        [sg.T("")],
        [sg.Button("Get Recommendation",font=('11')),sg.VSeparator(),sg.Text("recommendation: ",font=('13')),sg.Text(text_color='white',font=('16'),key='-RECOMMENDATION-')],
        [sg.T("")],
        [sg.T("")],
        [sg.Button("Get Sectors Sentiment",font=('11')), sg.T("     ")],
        [sg.Button("Load Markets Recommendation",font=('11')), sg.T("     "),sg.Button("Load Sectors Sentiment",font=('11')), sg.T("     ")],
        [sg.T("")],
        [sg.T("")],
        [sg.Button("Connect TradeStation",font=('16'),button_color=('black','goldenrod2'))],
        [sg.T("")],
        [sg.Text("Progress: ",font=('12')), sg.ProgressBar(max_value=MAX_PROG_BAR, orientation='h', size=(30,20), key="-PROG-",bar_color="gray")],
        [sg.Output(key='-OUT1-', size=(150, 15))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]

        account_details_column = [
        [sg.Button("Run Strategy",font=('12'),button_color=('black','goldenrod2')),sg.Button("Show Portfolio",font=('12')),sg.Button("Show Orders",font=('12'))],
        [sg.Text("Sectors Sentiment: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-SECTORS_SENTIMENT-'),sg.Text("Markets Sentiment: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-MARKETS_SENTIMENT-')],
        [sg.Text("Account ID: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-ACCOUNT_ID-')],
        [sg.Text("Cash Balance: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-ACCOUNT_CASH-')],
        [sg.Text("Equity: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-ACCOUNT_EQUITY-')],
        ]

        orders_column = [
        [sg.Text("Symbol: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-SYMBOL-')],
        [sg.Text("Position: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-POSITION-')],
        [sg.Text("Order type: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-ORDER_TYPE-')]]

        self.tradestation_layout = [
        [sg.Column(account_details_column,justification='left'),sg.VSeparator(pad=(200,0)),sg.Column(orders_column)],
        [sg.Output(key='-OUT1-', size=(150, 20))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]             

    def getMainLayout(self):
        return self.layout_main
    
    def get_tradestation_layout(self):
        return self.tradestation_layout
    
    def setWindow(self, layout,position='c'):
        return sg.Window('NewsToGod',layout, size=(1250,750),element_justification=position)
    