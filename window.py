import PySimpleGUI as sg
MAX_PROG_BAR = 1000

class Layout:
    def __init__(self):
        sg.theme("DarkPurple4") 

        self.layout_main = [[sg.T("")],
        [sg.T("")],
        [sg.Button("Get Markets Sentiment",font=('11')), sg.T("     "),sg.Button("Get Sectors Sentiment",font=('11')), sg.T("     ")],
        [sg.Button("Load Markets Sentiment",font=('11')), sg.T("     "),sg.Button("Load Sectors Sentiment",font=('11')), sg.T("     ")],
        [sg.T("")],
        [sg.Button("TradeStation",font=('16'))],
        [sg.T("")],
        [sg.Text("Progress: ",font=('12')), sg.ProgressBar(max_value=MAX_PROG_BAR, orientation='h', size=(30,20), key="-PROG-",bar_color="gray")],
        [sg.Output(key='-OUT1-', size=(100, 8))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]

        self.tradestation_layout = [[sg.T("")],
        [sg.T()],
        [sg.Button("Make Connection",font=('12')), sg.T("     ")],
        [sg.T("")],
        [sg.Text("Progress: ",font=('12')), sg.ProgressBar(max_value=2, orientation='h', size=(30,20), key="-PROG-",bar_color="gray")],
        [sg.Output(key='-OUT1-', size=(100, 8))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]             

    def getMainLayout(self):
        return self.layout_main
    
    def get_tradestation_layout(self):
        return self.tradestation_layout
    
    def setWindow(self, layout):
        return sg.Window('NewsToGod',layout, size=(1000,500),element_justification='c')
    