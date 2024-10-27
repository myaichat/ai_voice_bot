import wx
import wx.lib.agw.customtreectrl as CT
import wx.html
from pubsub import pub

class CustomHtmlListBox(wx.html.HtmlListBox):
    def __init__(self, parent, items, tree_ctrl, tree_item, id=wx.ID_ANY, size=(200, 80)):
        super(CustomHtmlListBox, self).__init__(parent, id, size=size)
        self.items = items
        self.tree_ctrl = tree_ctrl  # Reference to the tree control
        self.tree_item = tree_item  # Reference to the corresponding tree item
        self.history_items = []
        self.SetItemCount(0)  # Initial item count
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_single_click)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        # Remove the border by setting a simple style
        self.SetWindowStyleFlag(wx.BORDER_NONE)
        self.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost)
        self.single_click_delayed = None
        self.add_history_item(items)
        self.Bind(wx.EVT_PAINT, self.on_paint) 
        
    def add_history_item(self, item):
        """Add a new history item with multiline text to the HtmlListBox."""
        pp(item)

        #self.history_items.append(formatted_text)
        #self.SetItemCount(len(self.history_items))
        self.adjust_size_to_fit_content(item)
        self.Refresh()

    def adjust_size_to_fit_content(self, item):
        """Calculate and adjust the size of the list box based on the content and LeftPanel width, with scroll check."""
        # Get the width of the LeftPanel (parent's parent in this case)
        max_width = self.GetParent().GetSize().width - 75  # Padding to prevent overflow

        # Use a device context to measure the text size
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        text = item[1]

        # Measure each line of text and wrap if necessary
        lines = text.split("\n")
        wrapped_lines = []
        total_height = 0

        for line in lines:
            line_width, line_height = dc.GetTextExtent(line)
            if line_width > max_width:
                # Wrap the line manually if it exceeds max width
                wrapped_line = ""
                for word in line.split(" "):
                    test_line = f"{wrapped_line} {word}".strip()
                    test_width, _ = dc.GetTextExtent(test_line)
                    if test_width > max_width:
                        wrapped_lines.append(wrapped_line)
                        wrapped_line = word
                        total_height += line_height
                    else:
                        wrapped_line = test_line
                wrapped_lines.append(wrapped_line)
                total_height += line_height
            else:
                wrapped_lines.append(line)
                total_height += line_height

        # Set the total width and height with padding
        text_length = len(text)
        dynamic_padding = 20 + int(text_length / 25)  # Adjust base padding for longer text

        # Check the height-to-width ratio and adjust padding accordingly
        if total_height > max_width:
            # Increase padding further if the content height is greater than the available width
            dynamic_padding += int(total_height / 20)  # Increase padding based on height

        # Set the total width and height with dynamic padding
        adjusted_height = total_height + dynamic_padding

        # Check if the item would require scrolling by comparing the adjusted height to the current height
        current_height = self.GetSize().height
        if  0 and adjusted_height > current_height:
            # If the adjusted height is greater, increase the height a bit more to avoid scrolling
            adjusted_height += 20  # Additional height if scrolling is needed

        # Set the size of the list box, limiting the width to max_width
        self.SetSize((max_width, adjusted_height))

        # Refresh with wrapped content if necessary
        html_text = text.replace("\n", "<br>")
        formatted_text = f"""<span style="color: #2d2d2d; font-size: 14px; font-family: Arial, sans-serif;"><b>>></b>{html_text}</span>"""        

        self.history_items.append(formatted_text)
        self.SetItemCount(len(self.history_items))
        self.Refresh()


        # Update the size of the HtmlListBox
        #self.SetSize((max_width, total_height))
    def on_paint(self, event):
        """Handle paint event to draw scroll indicators if needed."""
        # First call the default paint method
        event.Skip()
        if 0:
            # Check if content is overflowing
            if self.is_content_overflowing():
                dc = wx.PaintDC(self)
                width, height = self.GetSize()

                # Draw indicators at the top or bottom if content is hidden
                if self.has_hidden_top_content():
                    dc.DrawText("^ More above", 5, 5)  # Top indicator

                if self.has_hidden_bottom_content():
                    dc.DrawText("v More below", 5, height - 20)  # Bottom indicator


    def has_hidden_top_content(self):
        """Check if any content is hidden at the top (i.e., user scrolled down)."""
        # Placeholder: logic for detecting top hidden content
        return self.GetViewStart()[1] > 0  # `GetViewStart` gives the current scroll offset

    def has_hidden_bottom_content(self):
        """Check if any content is hidden at the bottom."""
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())

        # Calculate total content height
        total_content_height = 0
        for item in self.history_items:
            _, item_height = dc.GetTextExtent(item)
            total_content_height += item_height + 5  # Adding small padding between items

        # Check if scrolled to the bottom
        visible_height = self.GetSize().height
        current_scroll_position = self.GetScrollPos(wx.VERTICAL)
        return (total_content_height - current_scroll_position) > visible_height
    def on_focus(self, event):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #self.Refresh()
        event.Skip()

    def on_focus_lost(self, event):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #self.Refresh()
        event.Skip()

    def on_single_click(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()        
        # Highlight the corresponding tree item on single click
        print("Single click in HtmlListBox")
        self.tree_ctrl.SelectItem(self.tree_item)
        self.SetBackgroundColour(wx.Colour(211, 211, 211)) 
        #event.Skip()
        #self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.single_click_delayed = wx.CallLater(160, self.ProcessSingleClick, self.tree_item, event)        
    def ProcessSingleClick(self, item, event):
        if item:
            # self.SelectItem(item)
            print("Single click detected on item in tree")
        self.single_click_delayed = None
    def on_double_click(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None        
        # Highlight the corresponding tree item on double click
        print("Double click in HtmlListBox")
        self.tree_ctrl.SelectItem(self.tree_item)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #item_index = self.tree_ctrl.GetIndexOfItem(self.tree_item)  # or define an index if needed
        #if item_index < len(self.history_items):
        pp( self.history_items[0])        
        #
        #event.Skip()
        print('is_scrollable:', self.is_scrollable())
        #print ('has_hidden_top_content:',self.has_hidden_top_content())
        print ('is_content_overflowing:',self.is_content_overflowing())

    def is_content_overflowing(self):
        """Check if the content height exceeds the visible height of the list box."""
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        
        total_content_height = 0
        for item in self.history_items:
            # Measure each line accurately, including wrapped lines
            text_lines = item.split("<br>")  # Assuming HTML <br> tags are used for new lines
            for line in text_lines:
                _, item_height = dc.GetTextExtent(line)
                total_content_height += item_height + 5  # Adding small padding between lines
                
        # Print the calculated content height and control height for debugging
        control_height = self.GetSize().height
        print(f"Total Content Height: {total_content_height}, Control Height: {control_height}")
        
        # Check if total content height is greater than the current control height
        is_overflowing = total_content_height > control_height
        print("is_content_overflowing:", is_overflowing)  # Debug statement
        return is_overflowing

    def is_scrollable(self):
        """Check if any part of the content is scrollable by comparing content and control height."""
        return self.is_content_overflowing()        

    def OnGetItem(self, index):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        return f"<div style='padding: 10px; background-color: #ffffff;'>{self.history_items[index]}</div>"



class MultiLineHtmlTreeCtrl(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        agwStyle = (CT.TR_HAS_VARIABLE_ROW_HEIGHT |
                    CT.TR_HAS_BUTTONS |
                    CT.TR_NO_LINES |
                    CT.TR_FULL_ROW_HIGHLIGHT)
        super(MultiLineHtmlTreeCtrl, self).__init__(parent, id, pos, size, 
                                                agwStyle=agwStyle,
                                                style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnSingleClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.single_click_delayed = None
        self.set_custom_expand_collapse_icons()
        pub.subscribe(self.OnAddItem, "ADD_ITEM")
        self.root = self.AddRoot("Root")
        pub.subscribe(self.on_stream_closed, "stream_closed")
    def on_stream_closed(self, data):
        transcript, corrected_time, tid = data
        # Ensure UI updates happen in the main thread
        wx.CallAfter(self.update_tree_with_transcript, transcript)

    def update_tree_with_transcript(self, transcript):
        if transcript.strip():
            parent1 = self.AppendMultilineItem(self.root, 
                                            ["<b>Transcript</b>", f"<i>{transcript}</i>"])
            self.ExpandAll()  # Expanding within the main thread       

        
    def OnAddItem(self):    
        root = self.GetRootItem()
        parent1 = self.AppendMultilineItem(root,
                                            ["<b>Parent Info 1</b>", "<i>Additional Info</i>"])
        child1 = self.AppendMultilineItem(parent1,
                                           ["<b>Child Info 1</b>", "<i>Extra Info</i>"])
        child2 = self.AppendMultilineItem(parent1,
                                           ["<b>Child Info 2</b>", "<i>Extra Details</i>"])
        self.ExpandAll()
    def set_custom_expand_collapse_icons(self):
        # Create a larger "+" and "-" bitmap for expand/collapse
        expand_bmp = wx.Bitmap(20, 20)
        collapse_bmp = wx.Bitmap(20, 20)

        # Draw a "+" icon for expand
        dc = wx.MemoryDC(expand_bmp)
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 3))
        dc.DrawLine(10, 5, 10, 15)
        dc.DrawLine(5, 10, 15, 10)
        dc.SelectObject(wx.NullBitmap)

        # Draw a "-" icon for collapse
        dc = wx.MemoryDC(collapse_bmp)
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 3))
        dc.DrawLine(5, 10, 15, 10)
        dc.SelectObject(wx.NullBitmap)

        # Create an image list and add custom bitmaps
        image_list = wx.ImageList(20, 20)
        image_list.Add(expand_bmp)   # The first image is the expand icon
        image_list.Add(expand_bmp) # The second image is the collapse icon
        image_list.Add(collapse_bmp) # The second image is the collapse icon
        image_list.Add(collapse_bmp)
        # Assign the image list to the tree control
        self.SetButtonsImageList(image_list)

    def AppendMultilineItem(self, parent, html_items, data=None):
        # Append an item with an empty string as the text
        item = self.AppendItem(parent, "")
        if data is not None:
            self.SetItemData(item, data)

        # Create an instance of CustomHtmlListBox with specific items, passing tree control and item references
        html_list_box = CustomHtmlListBox(self, html_items, self, item, size=(200, 80))
        self.SetItemWindow(item, html_list_box)
        
        # Add sample history items to the HtmlListBox
        #html_list_box.add_history_item("First line\nSecond line\nThird line")
        return item

    def OnSingleClick(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()

        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        if flags & CT.TREE_HITTEST_ONITEMBUTTON:
            event.Skip()
            return

        self.single_click_delayed = wx.CallLater(160, self.ProcessSingleClick, item, event)

    def ProcessSingleClick(self, item, event):
        if item:
            self.SelectItem(item)
            print("Single click detected on item in tree")
        self.single_click_delayed = None

    def OnDoubleClick(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None

        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        if item:
            self.SelectItem(item)
            print("Double-clicked on item in tree")
        event.Skip()

class LeftPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
         # Create Notebook
        left_notebook = wx.Notebook(self)
        
        self.tree = MultiLineHtmlTreeCtrl(left_notebook)
        
        left_notebook.AddPage(self.tree, "HtmlTree")


        
        #left_notebook.SetSelection(3)

        self.button = wx.Button(self, label="Populate List")
        self.button.Bind(wx.EVT_BUTTON, self.on_button_click)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(left_notebook, 1, wx.EXPAND)
        sizer.Add(self.button, 0, wx.ALL, 5)
        self.SetSizer(sizer)
       
    def on_button_click(self, event):
        pub.sendMessage("test_populate")
import sys

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

SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
STREAMING_LIMIT = 240000  # 4 minutes
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

import threading
class ExampleFrame(wx.Frame):
    def __init__(self,queue, title, size):
        super(ExampleFrame, self).__init__(None, title=title, 
                                           size=size)
        panel= wx.Panel(self)
        left_panel = LeftPanel(panel)
        #self.tree = MultiLineHtmlTreeCtrl(panel, size=(380, 480))
        button = wx.Button(panel, label="Add Item")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(left_panel, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(button, 0, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON, self.OnAddItem, button)
        if 0:
            
            root = self.tree.AddRoot("Root")
            
            # Add parent and child items with unique HTML content for each HtmlListBox
            parent1 = self.tree.AppendMultilineItem(root,
                                                    ["<b>Parent Info 1</b>", "<i>Additional Info</i>"])
            child1 = self.tree.AppendMultilineItem(parent1,
                                                ["<b>Child Info 1</b>", "<i>Extra Info</i>"])
            child2 = self.tree.AppendMultilineItem(parent1,
                                                ["<b>Child Info 2</b>", "<i>Extra Details</i>"])
            self.tree.ExpandAll()
            
            self.Layout()
            self.Bind(wx.EVT_SIZE, self.OnSize)
        self.content_buffer = ""  # Buffer to store content before updating WebView

        # Start the long-running process in a background thread

    

        if 1:        
            self.long_running_thread = threading.Thread(target=_long_running_process)
            self.long_running_thread.start()            

    def OnSize(self, event):
        self.Layout()
        event.Skip()
    def OnAddItem(self, event):
        pub.sendMessage("ADD_ITEM")
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

  
from wxasync import WxAsyncApp, AsyncBind 
import wxasync
import asyncio


async def main():
    
    queue = asyncio.Queue()
    app = WxAsyncApp()  # Use WxAsyncApp for async compatibility
    #Resumable Microphone Streaming 
    frame = ExampleFrame(queue,  title="RMS Transcribe for Google Speech", size=(400, 300))
    frame.SetSize((1200, 1000)) 
    frame.Show()
    #apc.processor = AsyncProcessor(queue)
    # Start the queue consumer task
    asyncio.create_task(frame.consume_queue())
    asyncio.create_task(frame.update_webview_periodically())
    await app.MainLoop()  # Run the app's main loop asynchronously

if __name__ == "__main__":
    asyncio.run(main())  # Use asyncio.run() to start the main function   