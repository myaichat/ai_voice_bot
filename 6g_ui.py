

import wx
import wx.html2
import wx.adv
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
        pub.subscribe(self.on_test_populate, "test_populate")       

    def populate_list(self, data):
        """Populate the ListCtrl with data."""
        self.DeleteAllItems()  # Clear existing items
        for i, transcription in enumerate(data):
            index = self.InsertItem(i, str(i))
            self.SetItem(index, 1, transcription)
    def on_test_populate(self):
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
        
        #self.conversation_history = []
        #self.client= openai.OpenAI()
        pub.subscribe(self.on_stream_closed, "stream_closed")  
        pub.subscribe(self.on_ask_model_event, "ask_model")
      
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


    def populate_list(self, data):
        """Interface method to populate the list in the embedded ListCtrl."""
        self.list_ctrl.populate_list(data)
    async def on_item_activated(self, event):
        
        # Get the selected row index and the data in the row
        index = event.GetIndex()
        id_value = self.list_ctrl.GetItemText(index, 0)
        transcription_value = self.list_ctrl.GetItemText(index, 1)
        await self.ask_model(transcription_value) 
    def on_ask_model_event(self, prompt):
        """Await the async ask_model function directly."""
        asyncio.create_task(self.ask_model(prompt))
    async  def ask_model(self, prompt):
        print(8888, 'ask_model', prompt)
        # Display a message box with the clicked row's data
        #print(f"You double-clicked on:\nId: {id_value}\nTranscription: {prompt}")
        pub.sendMessage("set_header", msg=prompt)
        #apc.processor.conversation_history=[]
        if 0:
            await apc.processor.run_stream_response(prompt)

        else:
            await self.mock_stream_response(prompt)              

    async def mock_stream_response(self, prompt):
        """Mock streaming response for testing."""
        print(9999, 'mock_stream_response', prompt)
        responses = [
            f'{prompt}<br>',
            "This is the second response.<br>",
            "This is the third response.<br>",
            "This is the fourth response.<br>",
            "This is the fifth response.<br>",
        ]

        for response in responses:
            #pub.sendMessage("display_response", response=response)
            await apc.processor.queue.put(response)
            await asyncio.sleep(0.1)   
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

def _long_running_process():
    """start bidirectional streaming from microphone input to speech API"""
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="en-US",
        max_alternatives=1,
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
            listen_print_loop(0,responses, stream)

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
        #ch=[]
        ch.append({"role": "user", "content": prompt})
        # Create a chat completion request with streaming enabled
        #pp(conversation_history)
        #pp(ch)  
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            #model="gpt-3.5-turbo",
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
                #print(content, end='', flush=True)
                await self.queue.put(content)
                await asyncio.sleep(0)   
                out.append(content)               
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
        pub.sendMessage("done_display", response=())
        ch.append({"role": "assistant", "content": ''.join(out)})
            

import re
import markdown2
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
class AppLog_Controller():
    def __init__(self):
        self.set_log()
        self.header='App Log'
        self.history=[]
        self.page_history=[]
        self.page_forward=[]
        #pub.subscribe(self.on_log, "applog")
        pub.subscribe(self.done_display, "done_display")
        pub.subscribe(self.display_response, "display_response")
        pub.subscribe(self.set_header, "set_header")
        pub.subscribe(self.on_page_back, "back")
        pub.subscribe(self.on_page_forward, "forward")  
    def on_page_back(self):
        if self.page_history:

            if 1:
                print(333333, self.page_history)
                forward=self.page_history.pop()
                self.page_forward.append(forward)   
                self.update_back()
                self.update_forward() 
            self.load_from_file(self.page_history[-1])              
    def on_page_forward(self):
        print('on_page_forward')
        if self.page_forward:
            print(333333, 'on_page_forward', self.page_forward)


           
            forward=self.page_forward.pop()
            self.page_history.append(forward)    
            self.load_from_file(forward)
            self.update_forward()
            self.update_back()
    def update_forward(self):
        if self.page_forward:
            self.enable_forward()
        else:
            self.disable_forward()
    def set_header(self, msg):
        self.history +=self.applog
        self.applog=[]  
                
        self.applog.append({'text':msg,'type':'header'})
        self.applog.append({'text':'','type':'info'})
        self.replace_header(msg)
  
    def done_display(self, response):
        print(333333, 'done_display')
        #self.applog.append('<br><br>')
        tmp_file=self.save_html()
        self.page_history.append(tmp_file) 
        self.update_back()

    def update_back(self):
        if len(self.page_history)>1:
            self.enable_back()
        else:
            self.disable_back()
        #wx.CallAfter(self.refresh_log_with_history)
    def display_response(self, response):
        #e()
        if not self.applog:
            row={'text':response,'type':'info'}
            self.applog.append(row)
        else:
            row = self.applog[-1] 
            row["text"] +=response #.replace("\n", "<br>")
            self.applog[-1]=row
        #self.add_log_entry(response)
        
        self.replace_log_content(row["text"] )   
        #wx.CallAfter(self.refresh_log)
       
    def replace_log_content(self, content):
        # Step 1: Convert Markdown to HTML with fenced code blocks enabled
        html_content = markdown2.markdown(content, extras=["fenced-code-blocks"])

        # Step 2: Initialize Pygments formatter with inline CSS for syntax highlighting
        formatter = HtmlFormatter(nowrap=True, style="colorful")
        css_styles = formatter.get_style_defs('.highlight')

        # Custom block code styling (includes font-size and background)
        block_code_style = (
            "background-color: #f4f4f4; color: #008000; padding: 10px; "
            "border-radius: 5px; font-family: monospace;  line-height: 1.8; font-size: 10px;"
        )
        # Inline code styling (for single-line inline code snippets)
        inline_code_style = "background-color: #f4f4f4; color: #008000; font-family: monospace; font-size: 14px; padding: 2px 4px; border-radius: 3px;"

        custom_code_style = """
                code {
                    font-family: "Courier New", Courier, monospace;
                    font-size: 0.875em;
                    color: #2d2d2d;
                    background-color: #f6f6f6;
                    padding: 2px 4px;
                    border-radius: 3px;
                    white-space: nowrap;
                    overflow-wrap: break-word;
                }
                pre code {
                    font-family: "Courier New", Courier, monospace;
                    font-size: 0.875em;
                    color: #2d2d2d;
                    background-color: #f6f6f6;
                    padding: 2px 4px;
                    border-radius: 3px;
                    white-space: pre;
                    overflow-wrap: break-word;
                }
            """



        # Replace <pre><code>...</code></pre> blocks with highlighted HTML
        highlighted_html_content =  html_content.replace(
                    '<code>', f'<code style="{inline_code_style}">'
                ).replace(
                    '<pre><code>', f'<pre style="{block_code_style}"><code>'
                ).replace(
                    '</code></pre>', '</code></pre>'
                )


        # Step 4: Assemble final HTML with Pygments CSS for syntax colors
        final_content = f"""
        <style>
            {css_styles}
            {custom_code_style}
            /* Specific token coloring to make keywords and operators green */
            .highlight .k, .highlight .n, .highlight .o {{ color: #008000; }}
        </style>
        {highlighted_html_content}
        """

        # Escape backticks for JavaScript compatibility
        sanitized_content = final_content.replace("`", "\\`")
        
        # Inject the processed HTML content into the webview
        self.web_view.RunScript(f"replaceLogContent(`{sanitized_content}`);")
    def replace_header(self, content):
        # Use JavaScript to replace content in the header row
        sanitized_content = content.replace("`", "\\`")  # Escape backticks for JavaScript
        self.web_view.RunScript(f"replaceHeader(`{sanitized_content}`);")
    def append_log_content(self, content):
        # Use JavaScript to append content to the single row
        sanitized_content = content.replace("`", "\\`")  # Escape backticks for JavaScript
        self.web_view.RunScript(f"appendToLog(`{sanitized_content}`);")
   
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
            "background-color: #f4f4f4; color: #008000; padding: 10px; "
            "border-radius: 5px; font-family: monospace;  line-height: 1.8; font-size: 10px;"
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
class EditTextDialog(wx.Dialog):
    """Custom dialog with a multi-line text control for editing text."""
    def __init__(self, parent, title, initial_text):
        super().__init__(parent, title=title, size=(400, 300))
        
        # Multi-line text control
        self.text_ctrl = wx.TextCtrl(self, value=initial_text, style=wx.TE_MULTILINE | wx.TE_WORDWRAP)
        
        # OK and Cancel buttons
        ok_button = wx.Button(self, wx.ID_OK, label="OK")
        cancel_button = wx.Button(self, wx.ID_CANCEL, label="Cancel")
        
        # Layout
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        self.CenterOnParent()

    def GetEditedText(self):
        return self.text_ctrl.GetValue()    
from urllib.parse import unquote
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
        #self.web_view.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)
        #self.web_view.Bind(wx.html2.EVT_WEBVIEW_ERROR, self.on_webview_error)
        #self.web_view.Bind(wx.EVT_CONTEXT_MENU, self.show_popup_menu)
        self.create_navigation_panel()
        # Set initial HTML content
        self.set_initial_content()

        # Create sizer to organize the WebView
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.web_view, 1, wx.EXPAND, 0)
        sizer.Add(self.nav_panel, 0, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(sizer)

    def enable_forward(self):
        self.forward_button.Enable(True)
        self.forward_button.SetForegroundColour(wx.Colour(0, 0, 255))  # Active blue
        font = self.forward_button.GetFont()
        font.SetUnderlined(True)
        self.forward_button.SetFont(font)          
    def disable_forward(self):
        self.forward_button.Enable(False)
        self.forward_button.Enable(False)  
        self.forward_button.SetForegroundColour(wx.Colour(150, 150, 150))  # Disabled gray
        font = self.forward_button.GetFont()
        font.SetUnderlined(False)
        self.forward_button.SetFont(font)         
    def enable_back(self):
        self.back_button.Enable(True)
        self.back_button.SetForegroundColour(wx.Colour(0, 0, 255))  # Active blue
        font = self.back_button.GetFont()
        font.SetUnderlined(True)
        self.back_button.SetFont(font)        
    def disable_back(self):
        self.back_button.Enable(False)  
        self.back_button.SetForegroundColour(wx.Colour(150, 150, 150))  # Disabled gray
        font = self.back_button.GetFont()
        font.SetUnderlined(False)
        self.back_button.SetFont(font)                       
    def create_navigation_panel(self):
        """Creates the navigation panel with Back and Forward buttons in opposite corners."""
        self.nav_panel = wx.Panel(self)
        nav_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.nav_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        # Back Button
        self.back_button = back_button=wx.StaticText(self.nav_panel, label="Back")
              
        back_button.Bind(wx.EVT_LEFT_DOWN, self.on_back)
        nav_sizer.Add(back_button, 0, wx.ALL, 5)
        font = back_button.GetFont()
        font.SetUnderlined(True)
        font.SetPointSize(12)  # Set to desired font size
        back_button.SetFont(font)           
        self.back_button.SetForegroundColour(wx.Colour(0, 0, 255))  # Blue for active state
        self.disable_back()
     

        # Add a spacer to push the "Forward" button to the far right
        nav_sizer.AddStretchSpacer(1)

        # Forward Button
        self.forward_button=forward_button = wx.StaticText(self.nav_panel, label="Forward")


        forward_button.Bind(wx.EVT_LEFT_DOWN, self.on_forward)
        nav_sizer.Add(forward_button, 0, wx.ALL, 5)  # Removed wx.ALIGN_RIGHT
        font = forward_button.GetFont()
        font.SetPointSize(12)  # Set to desired font size
        forward_button.SetFont(font)  
        self.nav_panel.SetSizer(nav_sizer)
        self.disable_forward()
        # Add padding to the top to remove the visible line
        #self.nav_panel.SetMinSize((-1, 25))  # Adjust height to fit the links with some padding

        # Optionally remove the border from WebView too
        self.web_view.SetWindowStyle(wx.NO_BORDER)        

      
    def on_right_click(self, event):
        # Display the context menu only when there's selected text
        selected_text = self.get_selected_text()
        if selected_text:
            self.show_context_menu()

    def show_context_menu(self):
        # Create a custom context menu
        menu = wx.Menu()
        ask_model_item = menu.Append(wx.ID_ANY, "Ask Model")
        
        # Bind the menu item to an action
        self.Bind(wx.EVT_MENU, self.on_ask_model, ask_model_item)
        
        # Show the context menu at the cursor position
        self.PopupMenu(menu)
        menu.Destroy()
    def on_ask_model(self, event):
        # Use the selected text (stored when intercepted by on_navigating)
        selected_text = getattr(self, 'selected_text', "No text selected")
        
        # Check if Ctrl key is pressed
        if wx.GetKeyState(wx.WXK_CONTROL):
            # Show an editable dialog if Ctrl is pressed
            dialog = EditTextDialog(self, "Edit Selection", selected_text)
            if dialog.ShowModal() == wx.ID_OK:
                edited_text = dialog.GetEditedText()
                print(f"Edited text: {edited_text}")
                pub.sendMessage("ask_model", prompt=edited_text)
                # Here you can handle the edited text (e.g., pass it to the model)
            dialog.Destroy()
        else:
            # Default behavior when Ctrl is not pressed
            print(f"Selected text for model: {selected_text}")
            # Pass selected_text to your model for inference
            pub.sendMessage("ask_model", prompt=selected_text)


    def on_navigating(self, event):
        url = event.GetURL()
        if url.startswith("app://selection"):
            # Extract selected text from URL
            selected_text = url.split("text=")[-1]
            #pp(selected_text)
            self.selected_text = unquote(selected_text)  # Decode URL encoding
            #print(f"\n\n\n\tSelected text: {selected_text}")  # Handle the selected text as needed
            event.Veto()  # Prevent actual navigation for our custom scheme
            self.show_context_menu()
        elif url == "app://show_back_menu":
            event.Veto()  # Prevent navigation
            self.show_back_menu()   
    def show_back_menu(self):
        """Show a different context menu with 'Back' when no text is selected."""
        menu = wx.Menu()
        back_item = menu.Append(wx.ID_ANY, "Back")
        self.update_back()        
        # Bind the menu item to the on_back method
        self.Bind(wx.EVT_MENU, self.on_back, back_item)
        forward_item = menu.Append(wx.ID_ANY, "Forward")
        self.update_forward()
        
        # Bind the menu item to the on_back method
        self.Bind(wx.EVT_MENU, self.on_forward, forward_item)        
        # Show the context menu at the cursor position
        self.PopupMenu(menu)
        menu.Destroy()  
    def on_back(self, event):
       
        print ("back")
        """Handle the 'Back' action to navigate back in the WebView."""
        pub.sendMessage("back") 
    def on_forward(self, event):
        print ("forward")
        """Handle the 'Back' action to navigate back in the WebView."""
        pub.sendMessage("forward")                                    
    def attach_custom_scheme_handler(self):
        handler = CustomSchemeHandler_Log(self)
        self.web_view.RegisterHandler(handler)
        
    def save_html(self, html_source=None):
        import tempfile
        if not html_source:
            html_source= self.web_view.GetPageSource()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            tmp_file.write(html_source.encode('utf-8'))
            tmp_file_path = tmp_file.name
        return tmp_file_path
        # Load the HTML content from the temporary file to preserve navigation history
    def load_from_file(self, tmp_file_path):

        self.web_view.LoadURL(f"file://{tmp_file_path}")        
    def set_initial_content(self):
        initial_html = """
        <html>
        <head>
        <style>
            /* Apply styling to the table with a class */
            #log-table {
                font-family: Arial, sans-serif;   /* Basic, clean font */
                font-size: 16px;                  /* Regular font size */
                line-height: 1.5;                 /* Readable line spacing */
                color: #2d2d2d;                   /* Dark gray color */
                width: 100%;                      /* Full width */
                border-collapse: collapse;        /* Remove spacing between cells */
            }

            /* Styling for the header cell */
            #header-cell {
                font-weight: bold;
                font-size: 20px;
                padding: 10px;                    /* Add some padding */
                background-color: #f6f6f6;        /* Light background for header */
                border-bottom: 1px solid #ddd;    /* Border below header */
            }

            /* Styling for other table rows and cells */
            #log-cell {
                padding: 10px;
            }

            hr {
                border: 0;
                border-top: 1px solid #ddd;
                margin: 0;
            }
        </style>
        </head>
        <body>
            <table id="log-table">
                <tr id="header-row">
                    <td id="header-cell">Initial Header</td>
                </tr>
                <tr><td><hr></td></tr>
                <tr id="log-row">
                    <td id="log-cell"></td>
                </tr>
            </table>
            <script>
                // Function to replace header content
                function replaceHeader(content) {
                    const headerCell = document.getElementById('header-cell');
                    headerCell.innerHTML = content;
                }
                
                // Function to replace log content
                function replaceLogContent(content) {
                    const logCell = document.getElementById('log-cell');
                    logCell.innerHTML = content;
                }
                // Listen for mouseup events to detect selection
                document.addEventListener('mouseup', function() {
                    var selectedText = window.getSelection().toString();
                    if (selectedText) {
                        // Send the selected text to Python via custom scheme
                        window.location.href = 'app://selection?text=' + encodeURIComponent(selectedText);
                    }
                });      
                // Detect right-click and check if text is selected
                document.addEventListener('contextmenu', function(event) {
                    var selectedText = window.getSelection().toString();
                    if (selectedText) {
                        // Send the selected text to Python via custom scheme
                        event.preventDefault();  // Prevent the default context menu
                        window.location.href = 'app://selection?text=' + encodeURIComponent(selectedText);
                    } else {
                        // Send a different URL to Python to indicate no selection
                        event.preventDefault();
                        window.location.href = 'app://show_back_menu';
                    }
                });                          
            </script>
        </body>
        </html>
        """


        self.web_view.SetPage(initial_html, "")
        tmp_file=self.save_html(initial_html)
        self.page_history.append(tmp_file)


    def _set_initial_content(self):
        initial_html = """
        <html>
        <body>
        <table id="log-table" style="font-size: 16px;">
            <tr id="log-row">
                <td id="log-cell"></td>
            </tr>
        </table>
        <script>
            function replaceLogContent(content) {
                const cell = document.getElementById('log-cell');
                cell.innerHTML = content;
            }
        </script>
        </body>
        </html>
        """
        self.web_view.SetPage(initial_html, "")

    def _set_initial_content(self):
        initial_html = """
        <html>
        <body>
        <table id="log-table" style="font-size: 16px;">
            <tr id="log-row">
                <td id="log-cell"></td>
            </tr>
        </table>
        <script>
            function appendToLog(content) {
                const cell = document.getElementById('log-cell');
                cell.innerHTML += content + "<br>";
            }
        </script>
        </body>
        </html>
        """
        self.web_view.SetPage(initial_html, "")
    def _set_initial_content(self):
        html = self.get_log_html()
        initial_html = f"""
        <html>
        <body>
        <table id="log-table" style="font-size: 16px;">{html}</table>
        <script>
            function addLogEntry(content) {{
                const table = document.getElementById('log-table');
                const row = document.createElement('tr');
                const cell = document.createElement('td');
                cell.innerHTML = content;
                row.appendChild(cell);
                table.appendChild(row);
            }}
        </script>
        </body>
        </html>
        """
        self.web_view.SetPage(initial_html, "")    
    def add_log_entry(self, content):
        # Call the JavaScript function to add a log entry
        self.web_view.RunScript(f"addLogEntry(`{content}`);")

    def _set_initial_content(self):
        html=self.get_log_html()
        initial_html = """
        <html>
        <body>
        %s
        </body>
        </html>
        """   % html      
        self.web_view.SetPage(initial_html, "")



    def _on_navigating(self, event):
        url = event.GetURL()
        #print(f"Log Navigating to: {url[:50]}")
        if url.startswith("app:"):
            event.Veto()  # Prevent actual navigation for our custom scheme

    def on_webview_error(self, event):
        print(f"WebView error: {event.GetString()}")
import wx
import wx.html 
class NavigationHistoryHtmlListBox(wx.html.HtmlListBox):
    def __init__(self, parent):
        super().__init__(parent)
        
        # List to store HTML-formatted history items
        self.history_items = []
        self.SetItemCount(0)  # Initial item count
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
    def on_double_click(self, event):
        """Handle double-click on a list item."""
        # Get the position of the mouse click
        x, y = event.GetPosition()
        
        # Determine the item index at the clicked position
        item_index = self.HitTest(wx.Point(x, y))
        
        if item_index != wx.NOT_FOUND:
            # Fetch the item content (for demonstration)
            item_content = self.history_items[item_index]
            wx.MessageBox(f"{item_index}: You double-clicked on:\n\n{item_content}", "Item Double-Clicked")
        else:
            # No item found at this position
            wx.MessageBox("No item found at the clicked position.", "Info")
    def OnGetItem(self, index):
        """Return the HTML content for a given item index."""
        return f"<div style='padding: 10px;'>{self.history_items[index]}</div>"

    def add_history_item(self, text):
        """Add a new history item with multiline text to the HtmlListBox."""
        
        # Format the text to use <br> for line breaks
        html_text = text.replace("\n", "<br>")
        
        # Optional: Customize appearance with HTML and CSS
        formatted_text = f"""
            <b>History Item {len(self.history_items) + 1}</b><br>
            <span style="color: #2d2d2d; font-size: 14px; font-family: Arial, sans-serif;">
                {html_text}
            </span>
        """
        
        # Add formatted text to the list and update the control
        self.history_items.append(formatted_text)
        self.SetItemCount(len(self.history_items))
        self.Refresh()   

from ai_voice_bot.include.MultiLineTreeCtrl import MultiLineTreeCtrl
class TranscriptionTreePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = MultiLineTreeCtrl(self)
        # Add root and example items
        self.root = self.tree.AddRoot("Root")
        if 0:
            # Add multiline items
            parent1 = self.tree.AppendMultilineItem(root, "Parent Item 1\nWith multiple lines\nof text")
            child1 = self.tree.AppendMultilineItem(parent1, "This is a child item\nwith two lines")
            child2 = self.tree.AppendMultilineItem(parent1, "Another child Another child Another child Another child Another child Another child Another child Another child Another child\nwith even more\nlines of text\nto display")
            child3 = self.tree.AppendMultilineItem(child2, "Another child\nwith even more\nlines of text\nto display")
            parent2 = self.tree.AppendMultilineItem(root, "Parent Item 2\nAlso multiline")
            
            # Expand all items
            self.tree.ExpandAll()
        
        # Layout the frame
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        pub.subscribe(self.on_test_populate, "test_populate") 
        pub.subscribe(self.on_stream_closed, "stream_closed")  
        #pub.subscribe(self.on_ask_model_event, "ask_model")
      
    def  on_stream_closed(self, data):
        transcript, corrected_time, tid=    data
        #print (7777, tid, transcript, corrected_time, tid)
        if transcript.strip():
            parent = self.tree.AppendMultilineItem(self.root, f"{transcript}")
            self.tree.ExpandAll()
            self.tree.Refresh()

    def on_test_populate(self):
        print('on_test_populate')
        #self.tree.DeleteAllItems()
        root = self.root
        
        # Add multiline items
        parent1 = self.tree.AppendMultilineItem(root, "Tell me more about Oracle")
        child1 = self.tree.AppendMultilineItem(parent1, "Tell me more about Oracle PL/SQL")
        child2 = self.tree.AppendMultilineItem(parent1, "Tell me more about Oracle Hints")
        child3 = self.tree.AppendMultilineItem(child2, "Tell me more about Apache Pyspark")
        parent2 = self.tree.AppendMultilineItem(root, "Tell me more about Apache Airflow")
        
        # Expand all items
        self.tree.ExpandAll()
from ai_voice_bot.include.MultiLineHtmlTreeCtrl import MultiLineHtmlTreeCtrl
class TranscriptionHtmlTreePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = MultiLineHtmlTreeCtrl(self)
        # Add root and example items
        self.root = self.tree.AddRoot("Root")
        parent1 = self.tree.AppendMultilineItem(self.root, "Parent Item 1\nWith multiple lines\nof text")
        if 0:
            # Add multiline items
            parent1 = self.tree.AppendMultilineItem(root, "Parent Item 1\nWith multiple lines\nof text")
            child1 = self.tree.AppendMultilineItem(parent1, "This is a child item\nwith two lines")
            child2 = self.tree.AppendMultilineItem(parent1, "Another child Another child Another child Another child Another child Another child Another child Another child Another child\nwith even more\nlines of text\nto display")
            child3 = self.tree.AppendMultilineItem(child2, "Another child\nwith even more\nlines of text\nto display")
            parent2 = self.tree.AppendMultilineItem(root, "Parent Item 2\nAlso multiline")
            
            # Expand all items
            self.tree.ExpandAll()
        
        # Layout the frame
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        pub.subscribe(self.on_test_populate, "test_populate") 
        pub.subscribe(self.on_stream_closed, "stream_closed")  
        #pub.subscribe(self.on_ask_model_event, "ask_model")
      
    def  on_stream_closed(self, data):
        transcript, corrected_time, tid=    data
        #print (7777, tid, transcript, corrected_time, tid)
        if transcript.strip():
            parent1 = self.tree.AppendMultilineItem(self.root,
                                                ["<b>Parent Info 1</b>", "<i>Additional Info</i>"])
            #self.tree.ExpandAll()
            #self.tree.Refresh()  
        self.Layout()      
    def on_test_populate(self):
        print('on_test_populate')
        #self.tree.DeleteAllItems()
        root = self.root
        
        # Add multiline items
        
        # Add parent and child items with unique HTML content for each HtmlListBox
        parent1 = self.tree.AppendMultilineItem(root,
                                                ["<b>Parent Info 1</b>", "<i>Additional Info</i>"])
        child1 = self.tree.AppendMultilineItem(parent1,
                                               ["<b>Child Info 1</b>", "<i>Extra Info</i>"])
        child2 = self.tree.AppendMultilineItem(parent1,
                                               ["<b>Child Info 2</b>", "<i>Extra Details</i>"])
       
        
        # Expand all items
        self.tree.ExpandAll()
    def OnSize(self, event):
        self.Layout()
        event.Skip()        
class LeftPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
         # Create Notebook
        left_notebook = wx.Notebook(self)
        if 0:
            # Create a panel for the notebook tab and add the ListCtrl to it
            self.list_panel = TranscriptionListPanel(left_notebook)
            left_notebook.AddPage(self.list_panel, "Transcriptions")
        if 0:
            self.nav_history = NavigationHistoryHtmlListBox(left_notebook)
            left_notebook.AddPage(self.nav_history, "History")   
            long_text = "This is a long text that will wrap into multiple lines in wxHtmlListBox. " \
                "Each item can contain HTML tags, making it possible to add styling."
            self.nav_history.add_history_item(long_text)
        if 0:
            self.tree_panel = TranscriptionTreePanel(left_notebook)
            left_notebook.AddPage(self.tree_panel, "Tree")

        self.tree_panel = TranscriptionHtmlTreePanel(left_notebook)
        left_notebook.AddPage(self.tree_panel, "HtmlTree")


        
        #left_notebook.SetSelection(3)

        self.button = wx.Button(self, label="Populate List")
        self.button.Bind(wx.EVT_BUTTON, self.on_button_click)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(left_notebook, 1, wx.EXPAND)
        sizer.Add(self.button, 0, wx.ALL, 5)
        self.SetSizer(sizer)
    def on_button_click(self, event):
        pub.sendMessage("test_populate")
        
class MyFrame(wx.Frame):
    def __init__(self,queue, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)

        panel = wx.Panel(self)

        # Create a splitter window
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)

        left_panel = LeftPanel(splitter)

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
        splitter.SplitVertically(left_panel, right_notebook)
        splitter.SetSashGravity(0.5)  # Set initial split at 50% width for each side
        splitter.SetMinimumPaneSize(400)  # Minimum pane width to prevent collapsing

        # Create button

        self.queue = queue
        #self.abutton = wx.Button(panel, label='Async')
        #AsyncBind(wx.EVT_BUTTON, self.on_button_click_2, self.abutton)
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        #sizer.Add(self.button, 0, wx.CENTER | wx.ALL, 5)
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
    #Resumable Microphone Streaming 
    frame = MyFrame(queue, None, title="RMS Transcribe for Google Speech", size=(400, 300))
    frame.SetSize((1200, 1000)) 
    frame.Show()
    apc.processor = AsyncProcessor(queue)
    # Start the queue consumer task
    asyncio.create_task(frame.consume_queue())
    asyncio.create_task(frame.update_webview_periodically())
    await app.MainLoop()  # Run the app's main loop asynchronously

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run() to start the main function   




