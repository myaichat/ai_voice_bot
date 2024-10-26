

import wx
import sys
import time
from itertools import tee
from pubsub import pub
from google.cloud import speech
from ai_voice_bot.goog.ResumableMicrophoneStream import ResumableMicrophoneStream, listen_print_loop
#from ai_voice_bot.goog.ResumableMicrophoneMultiStream import ResumableMicrophoneMultiStream, listen_print_loop
import threading
import openai
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
STREAMING_LIMIT = 240000  # 4 minutes
class TranscriptionListCtrl(wx.ListCtrl):
    def __init__(self, parent):
        super(TranscriptionListCtrl, self).__init__(parent, style=wx.LC_REPORT)

        # Setup columns
        self.InsertColumn(0, 'Id', width=50)
        self.InsertColumn(1, 'Transcription', width=150)
        font = self.GetFont()
        font.SetPointSize(12)  # Increase point size for larger font
        self.SetFont(font)        

    def populate_list(self, data):
        """Populate the ListCtrl with data."""
        self.DeleteAllItems()  # Clear existing items
        for i, transcription in enumerate(data):
            index = self.InsertItem(i, str(i))
            self.SetItem(index, 1, transcription)
    def test(self):
        # Clear the list before populating
        self.DeleteAllItems()

        # Add rows to the list control
        data = [("1", "Hi how are you"),
                ("2", "Doing well, how are you"),
                ("3", "Can you tell me more about pyspark")]

        for row in data:
            index = self.InsertItem(self.GetItemCount(), row[0])
            self.SetItem(index, 1, row[1])
            #pub.sendMessage("applog", msg=row[1], type="info")
            #self.list_ctrl.SetItem(index, 2, row[2])                    

class TranscriptionListPanel(wx.Panel):
    def __init__(self, parent):
        super(TranscriptionListPanel, self).__init__(parent)

        # Create the ListCtrl within this panel
        self.list_ctrl = TranscriptionListCtrl(self)

        # Layout for the ListCtrl in this panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)        
        list_width = self.list_ctrl.GetSize().GetWidth()    
        self.list_ctrl.SetColumnWidth(1, list_width - self.list_ctrl.GetColumnWidth(0) - 20) 
        self.conversation_history = []
        self.client= openai.OpenAI()
        pub.subscribe(self.on_stream_closed, "stream_closed")  
    def  on_stream_closed(self, data):
        transcript, corrected_time, tid=    data
        #print (7777, tid, transcript, corrected_time, tid)
        if transcript.strip():

            self.add_row((str(tid), transcript))
    def add_row(self, row):
        index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), row[0])
        self.list_ctrl.SetItem(index, 1, row[1])
        #self.list_ctrl.SetItem(index, 2, row[2])
        self.list_ctrl.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list_ctrl.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        #self.list_ctrl.SetColumnWidth(2, wx.LIST_AUTOSIZE)   
        list_width = self.list_ctrl.GetSize().GetWidth()
        self.list_ctrl.SetColumnWidth(1, list_width - self.list_ctrl.GetColumnWidth(0) - 20)   
        self.list_ctrl.EnsureVisible(index)
        #asyncio.run(self.async_process(row[0]))
        #threading.Thread(target=self.threaded_process, args=(row[0],)).start()

    def test(self):
        self.list_ctrl.test()
    def populate_list(self, data):
        """Interface method to populate the list in the embedded ListCtrl."""
        self.list_ctrl.populate_list(data)
    def on_item_activated(self, event):
        # Get the selected row index and the data in the row
        index = event.GetIndex()
        id_value = self.list_ctrl.GetItemText(index, 0)
        transcription_value = self.list_ctrl.GetItemText(index, 1)
        
        # Display a message box with the clicked row's data
        print(f"You double-clicked on:\nId: {id_value}\nTranscription: {transcription_value}")
        self.stream_response(transcription_value)  

    def mock_stream_response(self, prompt):
        """Mock streaming response for testing."""
        responses = [
            f'{prompt}\n',
            "This is the second response.\n",
            "This is the third response.\n",
            "This is the fourth response.\n",
            "This is the fifth response.\n",
        ]

        for response in responses:
            pub.sendMessage("display_response", response=response)
            time.sleep(1)
        pub.sendMessage("done_display", response=())

    def stream_response(self, prompt):
        threading.Thread(target=self._run_stream_response, args=(prompt,), daemon=True).start()

    def _run_stream_response(self, prompt):
        #pub.sendMessage("applog", msg='test', type="info")    
        if 0:
            self.mock_stream_response(prompt)
            return None
        ch, client=self.conversation_history, self.client
        ch.append({"role": "user", "content": prompt})
        # Create a chat completion request with streaming enabled
        #pp(conversation_history)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=ch, 

            stream=True
        )

        # Print each response chunk as it arrives
        out=[]

        for chunk in response:
                  
            if hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content
                if not content:
                    continue

                print(content, end='', flush=True)
                pub.sendMessage("display_response", response=content)
                pub.sendMessage("applog", msg=content, type="partial")
                

        

        ch.append({"role": "assistant", "content": ''.join(out)})
        pub.sendMessage("done_display", response=())
        return None         
     
    def on_resize(self, event):
        # Get the width of the ListCtrl and adjust the second column
        list_width = self.list_ctrl.GetSize().GetWidth()
        # Adjust the second column to take the remaining width
        self.list_ctrl.SetColumnWidth(1, list_width - self.list_ctrl.GetColumnWidth(0) - 20)
        event.Skip()
class TranscriptionTextPanel(wx.Panel):
    def __init__(self, parent):
        super(TranscriptionTextPanel, self).__init__(parent)

        # Create the TextCtrl within this panel
        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE )
        font = self.text_ctrl.GetFont()
        font.SetPointSize(12)  # Set to a larger font size, adjust as needed
        self.text_ctrl.SetFont(font)
        # Layout for the TextCtrl in this panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
        pub.subscribe(self.display_response, "display_response")
        pub.subscribe(self.done_display, "done_display")
        self.done_display=True
        self.old_display=''
    def done_display(self, response):
        self.done_display=True
        new=self.text_ctrl.GetValue()
        self.text_ctrl.SetValue(new+self.old_display)

    def display_response(self, response):
        """Method to set text in the TextCtrl."""
        if self.done_display:
            self.old_display=self.text_ctrl.GetValue()
            self.done_display=False
            self.text_ctrl.SetValue('')
        old=self.text_ctrl.GetValue()
        self.text_ctrl.SetValue(old+response)
import wx.html2
class _WebViewPanel(wx.Panel):
    def __init__(self, parent):
        super(WebViewPanel, self).__init__(parent)

        # Create the WebView control
        self.web_view = wx.html2.WebView.New(self)

        # Load a default page or URL
        self.web_view.LoadURL("https://www.example.com")  # Set the URL as needed

        # Layout for the WebView in this panel
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.web_view, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)
def long_running_process():
    """start bidirectional streaming from microphone input to speech API"""
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-US",
        max_alternatives=3,
        model='latest_long',
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
    print(mic_manager.chunk_size)
    sys.stdout.write(YELLOW)
    sys.stdout.write('\nListening, say "Quit" or "Exit" to stop.\n\n')
    sys.stdout.write("End (ms)       Transcript Results/Status\n")
    sys.stdout.write("=====================================================\n")

    with mic_manager as stream:
        while not stream.closed:
            sys.stdout.write(YELLOW)
            sys.stdout.write(
                "\n" + str(STREAMING_LIMIT * stream.restart_counter) + ": NEW REQUEST\n"
            )

            stream.audio_input = []
            #print("NEW STREAM")
            #stream.start_stream()
            audio_generator = stream.generator()

            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            responses = client.streaming_recognize(streaming_config, requests)

            # Now, put the transcription responses to use.
            listen_print_loop(responses, stream)

            if stream.result_end_time > 0:
                stream.final_request_end_time = stream.is_final_end_time
            stream.result_end_time = 0
            stream.last_audio_input = []
            stream.last_audio_input = stream.audio_input
            stream.audio_input = []
            stream.restart_counter = stream.restart_counter + 1

            if not stream.last_transcript_was_final:
                sys.stdout.write("\n")
            stream.new_stream = True
            print("NEW STREAM")
class AppLog_Controller():
    def __init__(self):
        self.set_log()
        pub.subscribe(self.on_log, "applog")
        pub.subscribe(self.done_display, "done_display")
    def done_display(self, response):
        
        self.applog.append('<br><br>')
        wx.CallAfter(self.refresh_log)
    def display_response(self, response):
        #e()
        
        self.applog.append(response)
        #self.refresh_log()  
        self.web_view.SetPage(response, "")      
    def on_log(self, msg, type):
        #print(333333, msg)

        if type == "partial":
            if not self.applog:
                self.applog.append(msg)
            else:
                msg = self.applog[-1] +msg.replace("\n", "<br>")
                self.applog[-1]=msg
        else:

            if type == "error":
                msg = f'<span style="color:red">{msg}</span>'            
            self.applog.append(msg)
            #self.web_view.SetPage(msg, "")  
            #self.web_view.Reload()
            #self.refresh_log()
        wx.CallAfter(self.refresh_log)
    def set_log(self):
        self.applog = []

    def get_log(self):
        return self.applog

    def get_log_html(self):
        out="<table>"
        for log in self.applog:
            out += f'<tr><td>{log}</td></tr>'   
        out += "</table>"
        return out

    def refresh_log(self):
        html=self.get_log_html()
        new_html = """
        <html>
        <body>
        <pre>
        %s
        </pre>
        </body>
        </html>
        """   % html 
        #print(444444, new_html)     
        self.web_view.SetPage(new_html, "")
class CustomSchemeHandler_Log(wx.html2.WebViewHandler):
    def __init__(self, web_view_panel):
        wx.html2.WebViewHandler.__init__(self, "app")
        self.web_view_panel = web_view_panel

    def OnRequest(self, webview, request):
        print(f"Log: OnRequest called with URL: {request.GetURL()}")
        if request.GetResourceType() == wx.html2.WEBVIEW_RESOURCE_TYPE_MAIN_FRAME:
            if request.GetURL() == "app:test":
                wx.CallAfter(self.web_view_panel.on_test_button)
            elif request.GetURL() == "app:url_test":
                wx.CallAfter(self.web_view_panel.on_url_test)
        return None        
class Log_WebViewPanel(wx.Panel,AppLog_Controller):
    def __init__(self, parent):
        super().__init__(parent)
        AppLog_Controller.__init__(self)
        
        # Create the WebView control
        self.web_view = wx.html2.WebView.New(self)
        
        # Attach custom scheme handler
        self.attach_custom_scheme_handler()

        # Bind navigation and error events
        self.web_view.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_navigating)
        #self.web_view.Bind(wx.html2.EVT_WEBVIEW_ERROR, self.on_webview_error)

        # Set initial HTML content
        self.set_initial_content()

        # Create sizer to organize the WebView
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.web_view, 1, wx.EXPAND, 0)
        self.SetSizer(sizer)

    def attach_custom_scheme_handler(self):
        handler = CustomSchemeHandler_Log(self)
        self.web_view.RegisterHandler(handler)
    

    def set_initial_content(self):
        html=self.get_log_html()
        initial_html = """
        <html>
        <body>
        %s
        </body>
        </html>
        """   % html      
        self.web_view.SetPage(initial_html, "")



    def on_navigating(self, event):
        url = event.GetURL()
        #print(f"Log Navigating to: {url[:50]}")
        if url.startswith("app:"):
            event.Veto()  # Prevent actual navigation for our custom scheme

    def on_webview_error(self, event):
        print(f"WebView error: {event.GetString()}")

class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)

        panel = wx.Panel(self)

        # Create a splitter window
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)

         # Create Notebook
        left_notebook = wx.Notebook(splitter)

        # Create a panel for the notebook tab and add the ListCtrl to it
        self.list_panel = TranscriptionListPanel(left_notebook)
        left_notebook.AddPage(self.list_panel, "Transcriptions")


       # Right Notebook for TextCtrl
        right_notebook = wx.Notebook(splitter)

        # Create TranscriptionTextPanel and add it to the right notebook
        self.text_panel = TranscriptionTextPanel(right_notebook)
        right_notebook.AddPage(self.text_panel, "Text")
        # Add WebView Panel tab
        self.web_view_panel = Log_WebViewPanel(right_notebook)
        right_notebook.AddPage(self.web_view_panel, "WebView")   
        right_notebook.SetSelection(1)     

        # Split the main splitter window vertically between the left and right notebooks
        splitter.SplitVertically(left_notebook, right_notebook)
        splitter.SetSashGravity(0.5)  # Set initial split at 50% width for each side
        splitter.SetMinimumPaneSize(500)  # Minimum pane width to prevent collapsing

        # Create button
        self.button = wx.Button(panel, label='Populate List')
        self.button.Bind(wx.EVT_BUTTON, self.on_button_click)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        sizer.Add(self.button, 0, wx.CENTER | wx.ALL, 5)
        panel.SetSizer(sizer)

        # Start the long-running process in a background thread

        if 0:
            from multiprocessing import Process
            long_running_process_1 = Process(target=long_running_process)
            long_running_process_1.start()
            if 0:
                time.sleep(1)
                # Second process
                long_running_process_2 = Process(target=long_running_process)
                long_running_process_2.start()
                time.sleep(1)
                long_running_process_3 = Process(target=long_running_process)
                long_running_process_3.start()
                time.sleep(1)
                long_running_process_4 = Process(target=long_running_process)
                long_running_process_4.start()                

            # Optionally, wait for both processes to complete
            #long_running_process_1.join()
            if 0:
                long_running_process_2.join()  
                long_running_process_3.join() 
                long_running_process_4.join()         

        if 1:        
            self.long_running_thread = threading.Thread(target=long_running_process)
            self.long_running_thread.start()


        #self.list_ctrl.EnsureVisible(index)        






    def threaded_process(self, pid):
        """Wrapper to replace asyncio with threading."""
        self.async_th_process(pid)

    def async_th_process(self, pid):
        # Example process: simulate a task with a delay (no need for asyncio)
        time.sleep(5)  # Simulate long task with a blocking delay
        #print(pid, "completed!")



    def enable_button(self):
        # Enable the button when the long-running task is done
        self.button.Enable()

    def on_button_click(self, event):
        #pub.sendMessage("applog", msg="Button clicked", type="info")
        self.list_panel.test()

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, title="Google Transcribe", size=(400, 300))
        frame.SetSize((1200, 1000)) 
        frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()



