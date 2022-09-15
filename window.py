from turtle import pos
import PySimpleGUI as sg
MAX_PROG_BAR = 1000

class Layout:
    def __init__(self):
        sg.theme("DarkPurple4") 

        self.layout_main = [
        [sg.T("")],
        [sg.Button("Get Market Sentiment",font=('11')),sg.T(" "),sg.VSeparator(),sg.T(" "),sg.Button("Get Sectors Sentiment",font=('11'))],
        [sg.T("")],
        [sg.T("")],
        [sg.Button("Load Markets Recommendation",font=('11')), sg.T("     "),sg.Button("Load Sectors Sentiment",font=('11')), sg.T("     ")],
        [sg.T("")],
        [sg.T("")],
        [sg.Button("Connect TradeStation",font=('16'),button_color=('black','goldenrod2'))],
        [sg.T("")],
        [sg.Text("Progress: ",font=('12')), sg.ProgressBar(max_value=MAX_PROG_BAR, orientation='h', size=(30,20), key="-PROG-",bar_color="gray")],
        [sg.Output(key='-OUT1-', size=(150, 15))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]

        account_details_column = [
        [sg.Button("Run Full Automate Strategy",font=('16'),button_color=('black','goldenrod2')), sg.T("   "), sg.Button("Run Semi Automate Strategy",font=('16'),button_color=('black','goldenrod2'))],
        [sg.T("")],
        [sg.Button("Update Account",font=('12')),sg.Button("Show Portfolio",font=('12')),sg.Button("Show Orders",font=('12'))],
        [sg.Text("Sectors Sentiment: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-SECTORS_SENTIMENT-'),sg.Text("Markets Sentiment: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-MARKETS_SENTIMENT-')],
        [sg.Text("Account ID: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-ACCOUNT_ID-')],
        [sg.Text("Cash Balance: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-ACCOUNT_CASH-')],
        [sg.Text("Equity: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-ACCOUNT_EQUITY-')],
        ]

        orders_column = [
        [sg.Text("Today Return: ",font=('14')),sg.Text(text_color='white',font=('14'),key='-TODAY_RETURN-')],
        [sg.Text("Realized Return(%): ",font=('14')),sg.Text(text_color='white',font=('14'),key='-REALIZED_RETURN-')],
        [sg.Text("Unrealized Return(%): ",font=('14')),sg.Text(text_color='white',font=('14'),key='-UNREALIZED_RETURN-')]]

        self.tradestation_layout = [
        [sg.Column(account_details_column,justification='left'),sg.VSeparator(pad=(100,0)),sg.Column(orders_column)],
        [sg.T("")],
        [sg.Output(key='-OUT1-', size=(150, 20))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]             

    def getMainLayout(self):
        return self.layout_main
    
    def get_tradestation_layout(self):
        return self.tradestation_layout
    
    def setWindow(self, layout,position='c'):
        return sg.Window('NewsToGod',layout, size=(1250,750),element_justification=position)
    