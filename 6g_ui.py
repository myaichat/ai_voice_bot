

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
from pprint import pprint as pp
import ai_voice_bot.include.config.init_config as init_config 

init_config.init(**{})
apc = init_config.apc


apc.processor=None

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
        
        #self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)  
        #self.abutton = wx.Button(panel, label='Async')
        #AsyncBind(wx.EVT_LIST_ITEM_ACTIVATED, self.list_ctrl, self.on_item_activated)
        AsyncBind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated, self)
        #       
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
    async def on_item_activated(self, event):
        
        # Get the selected row index and the data in the row
        index = event.GetIndex()
        id_value = self.list_ctrl.GetItemText(index, 0)
        transcription_value = self.list_ctrl.GetItemText(index, 1)
        
        # Display a message box with the clicked row's data
        print(f"You double-clicked on:\nId: {id_value}\nTranscription: {transcription_value}")
        pub.sendMessage("set_header", msg=transcription_value)
        await apc.processor.run_stream_response(transcription_value)
        #self.stream_response(transcription_value)  

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

def _long_running_process():
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
from wxasync import WxAsyncApp, AsyncBind #, Start
from colorama import Fore, Style
class AsyncProcessor:
    def __init__(self, queue):
        self.queue = queue
        self.client= openai.OpenAI()
        self.conversation_history=[]

    async def run_stream_response(self, prompt):
       
        ch, client=self.conversation_history, self.client
        ch=[]
        ch.append({"role": "user", "content": prompt})
        # Create a chat completion request with streaming enabled
        #pp(conversation_history)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=ch, 

            stream=True
        )

        # Print each response chunk as it arrives
        out=[]
        inside_stars = False
        inside_backticks = False
        inside_hash = False
        
               
        for chunk in response:
                
            if hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content
               
                new_content = ''
                i = 0
                if not content:
                    continue
                print(content, end='', flush=True)
                await self.queue.put(content)
                await asyncio.sleep(0)                  
                while i < len(content):
                    if content[i:i+2] == '**':
                        if inside_stars:
                            new_content += f"{Style.RESET_ALL}"
                            inside_stars = False
                        else:
                            new_content += f"{Fore.GREEN}{Style.BRIGHT}"
                            inside_stars = True
                        i += 2  # Skip the next character
                    elif content[i:i+3] == '```':
                        if inside_backticks:
                            new_content += f"{Style.RESET_ALL}"
                            inside_backticks = False
                            i += 3 
                        else:
                            new_content += f"{Fore.RED}{Style.BRIGHT}"
                            inside_backticks = True
                            i += 3
                    # Skip the next two characters
                    elif content[i] == '#' and (i == 0 or content[i-1] == '\n'):  # If the line starts with '#'
                        new_content += f"{Fore.BLUE}{Style.BRIGHT}" + content[i]
                        inside_hash = True
                        i += 1
                    elif content[i] == '\n' and inside_hash:  # If the line ends and we're inside a hash line
                        new_content += f"{Style.RESET_ALL}" + content[i]
                        inside_hash = False
                        i += 1
                    else:
                        new_content += content[i]
                        i += 1
                print(new_content, end='', flush=True)
                #print(content, end='', flush=True)
               
                if new_content:
                    out.append(new_content)
            
            if inside_backticks:  # If we're still inside a code block, add the reset code
                out.append(Style.RESET_ALL)
            ch.append({"role": "assistant", "content": ''.join(out)})
            


    async def _run_stream_response(self, prompt):
        #pub.sendMessage("applog", msg='test', type="info")    
        if 0:
            self.mock_stream_response(prompt)
            return None
        ch, client=self.conversation_history, self.client
        ch.append({"role": "user", "content": prompt})
        # Create a chat completion request with streaming enabled
        #pp(conversation_history)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            #model="gpt-3.5-turbo",
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
                await self.queue.put(content)
                await asyncio.sleep(0)
                #await asyncio.sleep(0.1)
                #pub.sendMessage("display_response", response=content)
                #pub.sendMessage("applog", msg=content, type="partial")
                

        

        ch.append({"role": "assistant", "content": ''.join(out)})
        #pub.sendMessage("display_response", response='<br><br>')
        await self.queue.put('\n\n\n')    
        return None
class AppLog_Controller():
    def __init__(self):
        self.set_log()
        self.header='App Log'
        self.history=[]
        #pub.subscribe(self.on_log, "applog")
        pub.subscribe(self.done_display, "done_display")
        pub.subscribe(self.display_response, "display_response")
        pub.subscribe(self.set_header, "set_header")
    def set_header(self, msg):
        self.history +=self.applog
        self.applog=[]  
         
        self.applog.append({'text':msg,'type':'header'})
        self.applog.append({'text':'','type':'info'})
    def done_display(self, response):
        
        self.applog.append('<br><br>')
        wx.CallAfter(self.refresh_log_with_history)
    def display_response(self, response):
        #e()
        if not self.applog:
            self.applog.append({'text':response,'type':'info'})
        else:
            row = self.applog[-1] 
            row["text"] +=response #.replace("\n", "<br>")
            self.applog[-1]=row
        wx.CallAfter(self.refresh_log)
   
    def _on_log(self, msg, type):
    
        if 1:

            if type == "error":
                msg = f'<span style="color:red">{msg}</span>'            
            self.applog.append(msg)

        wx.CallAfter(self.refresh_log)
    def set_log(self):
        self.applog = []

    def get_log(self):
        return self.applog

    def get_log_html(self):
        #header="<h1>App Log</h1>"
        import markdown2
        out=f'<table style="font-size: 16px;">'
        # Block code styling (for fenced code blocks)
        block_code_style = (
            "background-color: #f4f4f4; color: #008000; padding: 12px; "
            "border-radius: 5px; font-family: monospace; line-height: 1.8;"
        )
        # Inline code styling (for single-line inline code snippets)
        inline_code_style = "background-color: #f4f4f4; color: #008000; font-family: monospace; padding: 2px 4px; border-radius: 3px;"


        for log in self.applog:
            text=log['text']
            rtype=log['type']
            #print(333333, rtype)
            if rtype=='header': 
                out += f'<tr><th style="text-align: left; font-size: 24px;">{text}</th></tr>'
            else:
                text = markdown2.markdown(text, extras=["fenced-code-blocks"])
            
                # Apply separate styling to block code and inline code
                text = text.replace(
                    '<code>', f'<code style="{inline_code_style}">'
                ).replace(
                    '<pre><code>', f'<pre style="{block_code_style}"><code>'
                ).replace(
                    '</code></pre>', '</code></pre>'
                )
                out += f'<tr><td>{text}</td></tr>'
        out += "</table>"
        #pp(out)
        return out
    def get_hist_log_html(self):
        #header="<h1>App Log</h1>"

        out=f'<table style="font-size: 16px;">'
        for log in self.history:
            text=log['text']
            rtype=log['type']
            #print(333333, rtype)
            if rtype=='header': 
                out += f'<tr><th style="text-align: left; font-size: 24px;">{text}</th></tr>'
            else:
                out += f'<tr><td>{text}</td></tr>'   
        out += "</table>"
        return out
    def refresh_log_with_history(self):
        html=self.get_log_html()
        hist=html=self.get_history_log_html()
        new_html = """
        <html>
        <body>
        <pre>
        %s
        </pre>
        <pre>
        %s
        </pre>        
        </body>
        </html>
        """   % (html,hist) 
        #print(444444, new_html)     
        self.web_view.SetPage(new_html, "")
    
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
    def __init__(self,queue, *args, **kw):
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
        self.queue = queue
        #self.abutton = wx.Button(panel, label='Async')
        #AsyncBind(wx.EVT_BUTTON, self.on_button_click_2, self.abutton)
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        sizer.Add(self.button, 0, wx.CENTER | wx.ALL, 5)
        #sizer.Add(self.abutton, 0, wx.CENTER | wx.ALL, 5)
        panel.SetSizer(sizer)
        self.content_buffer = ""  # Buffer to store content before updating WebView

        # Start the long-running process in a background thread

     

        if 1:        
            self.long_running_thread = threading.Thread(target=_long_running_process)
            self.long_running_thread.start()
        

        #self.list_ctrl.EnsureVisible(index)        

    async def consume_queue(self):
        # Continuously consume the queue and update WebView
        while True:
            content = await self.queue.get()
            #print('\n\tconsume_queue: ',content)
            #pub.sendMessage("display_response", response=content)  # Send the content to the WebView
            #wx.CallAfter(self.update_text, content)  # Update UI safely in the main thread
            self.queue.task_done()
            self.content_buffer += content
    async def update_webview_periodically(self):
        while True:
            if self.content_buffer:
                pub.sendMessage("display_response", response=self.content_buffer)
                #wx.CallAfter(self.update_text, self.content_buffer)
                self.content_buffer = ""  # Clear buffer after update
            await asyncio.sleep(0.2)  # Update every 200ms

    async def on_button_click_2(self, event):
        # Run the long-running process and the queue consumer
        #response = self.mock_response()  # Replace with the actual response
        #print(1111)
        apc.processor = AsyncProcessor(self.queue)
        await apc.processor.run_stream_response('Tell me more about oracle')

   

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
import wxasync
import asyncio
class MyApp(wxasync.WxAsyncApp):
    def OnInit(self):
        queue = asyncio.Queue()
        frame = MyFrame(queue,None, title="Google Transcribe", size=(400, 300))
        frame.SetSize((1200, 1000)) 
        frame.Show()
        return True

async def main():
    
    queue = asyncio.Queue()
    app = WxAsyncApp()  # Use WxAsyncApp for async compatibility
    frame = MyFrame(queue, None, title="Queue in wxPython", size=(400, 300))
    frame.SetSize((1200, 1000)) 
    frame.Show()
    apc.processor = AsyncProcessor(queue)
    # Start the queue consumer task
    asyncio.create_task(frame.consume_queue())
    asyncio.create_task(frame.update_webview_periodically())
    await app.MainLoop()  # Run the app's main loop asynchronously

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run() to start the main function   
if 0 and __name__ == "__main__":
    #app = MyApp()
    app = MyApp()
    #app.MainLoop()
    asyncio.get_event_loop().run_until_complete(app.MainLoop())



