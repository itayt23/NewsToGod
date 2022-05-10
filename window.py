import PySimpleGUI as sg

class Layout:
    def __init__(self):
        sg.theme("DarkPurple4") 

        self.layout_main = [[sg.T("")],
        [sg.Text("Please Choose how many news to analyze: ",font=('12')), sg.Combo(key="-NEWS_NUMBER-" ,values=[2,10,25,40], default_value=25,size=(5,5),font=('12'))],
        [sg.T("")],
        [sg.Button("Get Markets Sentiment",font=('12')), sg.T("     "), sg.Button("Visualize News Sentiment",font=('12'))],
        [sg.T("")],
        [sg.Text("Progress: ",font=('12')), sg.ProgressBar(max_value=2, orientation='h', size=(30,20), key="-PROG-",bar_color="gray")],
        [sg.Output(key='-OUT1-', size=(100, 8))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]              

    def getMainLayout(self):
        return self.layout_main
    
    def setWindow(self, layout):
        return sg.Window('NewsToGod',layout, size=(1000,500),element_justification='c')
    