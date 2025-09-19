from wpf_helper import get_wpf_path
from pyrevit.framework import wpf
from pyrevit import script
from System.Windows import Window

class MainWindow(Window):
    def __init__(self):
        xaml_path = get_wpf_path("MainWindow.xaml")
        wpf.LoadComponent(self, xaml_path)
        self.Closing += self.on_closing
        self.ShowDialog()

    def Button_Click(self, sender, e):
        print("Clicked!")

    def on_closing(self, sender, args):
        self.Close()
        script.exit()

MainWindow().ShowDialog()
