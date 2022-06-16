import PySimpleGUI as sg

class Layout:
    def __init__(self):
        sg.theme("DarkPurple4") 

        self.layout_main = [[sg.T("")],
        [sg.T("")],
        [sg.Button("Get Market Sentiment",font=('11')), sg.T("     "),sg.Button("Get Sectors Sentiment",font=('11')), sg.T("     ")],
        [sg.T("")],
        [sg.Text("Progress: ",font=('12')), sg.ProgressBar(max_value=2, orientation='h', size=(30,20), key="-PROG-",bar_color="gray")],
        [sg.Output(key='-OUT1-', size=(100, 8))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]

        self.sectors_layout = [[sg.T("")],
        [sg.Text(f"The Market Sentiment Right Now Is:")],
        [sg.Button("Get Sectors Sentiment",font=('12')), sg.T("     ")],
        [sg.T("")],
        [sg.Text("Progress: ",font=('12')), sg.ProgressBar(max_value=2, orientation='h', size=(30,20), key="-PROG-",bar_color="gray")],
        [sg.Output(key='-OUT1-', size=(100, 8))],
        [sg.Button("Exit",size=(8,1),font=('12'))]]             

    def getMainLayout(self):
        return self.layout_main
    
    def get_sectors_layout(self):
        return self.sectors_layout
    
    def setWindow(self, layout):
        return sg.Window('NewsToGod',layout, size=(1000,500),element_justification='c')
    