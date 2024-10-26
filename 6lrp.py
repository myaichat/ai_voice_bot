import wx
from multiprocessing import Process
import time

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Start processes from an external function
        self.start_long_running_processes()

    def start_long_running_processes(self):
        # Start the processes without passing self or GUI elements to them
        process_1 = Process(target=long_running_process)
        process_1.start()

        process_2 = Process(target=long_running_process)
        process_2.start()

def long_running_process():
    """Simulate a long-running process without interacting with the wx objects."""
    for i in range(5):
        print(f"Process running: {i}")
        time.sleep(1)

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, title="Google Transcribe", size=(400, 300))
        frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
