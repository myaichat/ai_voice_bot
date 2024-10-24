

import wx
import sys
import time

from pubsub import pub
from google.cloud import speech
from ai_voice_bot.goog.ResumableMicrophoneStream import ResumableMicrophoneStream, listen_print_loop
import threading

SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
STREAMING_LIMIT = 240000  # 4 minutes

class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)

        panel = wx.Panel(self)

        # Create ListCtrl
        self.list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT)
        
        # Add columns to the list control
        self.list_ctrl.InsertColumn(0, 'Id',20)
        self.list_ctrl.InsertColumn(1, 'Transcription', width=100)

        #self.list_ctrl.InsertColumn(2, 'Column 3', width=100)

        # Create button
        self.button = wx.Button(panel, label='Populate List')
        self.button.Bind(wx.EVT_BUTTON, self.on_button_click)
        #self.button.Disable()  # Disable button until thread completes

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.button, 0, wx.CENTER | wx.ALL, 5)
        panel.SetSizer(sizer)

        # Start the long-running process in a background thread
        self.long_running_thread = threading.Thread(target=self.long_running_process)
        self.long_running_thread.start()
        pub.subscribe(self.on_stream_closed, "stream_closed")
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
    def on_item_activated(self, event):
        # Get the selected row index and the data in the row
        index = event.GetIndex()
        id_value = self.list_ctrl.GetItemText(index, 0)
        transcription_value = self.list_ctrl.GetItemText(index, 1)
        
        # Display a message box with the clicked row's data
        wx.MessageBox(f"You double-clicked on:\nId: {id_value}\nTranscription: {transcription_value}",
                      "Row Activated", wx.OK | wx.ICON_INFORMATION)
                
     
    def on_resize(self, event):
        # Get the width of the ListCtrl and adjust the second column
        list_width = self.list_ctrl.GetSize().GetWidth()
        # Adjust the second column to take the remaining width
        self.list_ctrl.SetColumnWidth(1, list_width - self.list_ctrl.GetColumnWidth(0) - 20)
        event.Skip()

    def  on_stream_closed(self, data):
        transcript, corrected_time, tid=    data
        #print (7777, tid, transcript, corrected_time, tid)
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
        threading.Thread(target=self.threaded_process, args=(row[0],)).start()


    def threaded_process(self, pid):
        """Wrapper to replace asyncio with threading."""
        self.async_th_process(pid)

    def async_th_process(self, pid):
        # Example process: simulate a task with a delay (no need for asyncio)
        time.sleep(5)  # Simulate long task with a blocking delay
        #print(pid, "completed!")

    async def async_process(self, pid):
        # Example async process: simulate a task with a delay
        await asyncio.sleep(5)
        print(pid, "completed!")
    def long_running_process(self):
        """start bidirectional streaming from microphone input to speech API"""
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="en-US",
            max_alternatives=1,
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

    def enable_button(self):
        # Enable the button when the long-running task is done
        self.button.Enable()

    def on_button_click(self, event):
        # Clear the list before populating
        self.list_ctrl.DeleteAllItems()

        # Add rows to the list control
        data = [("Item 1", "Value 1", "Info 1"),
                ("Item 2", "Value 2", "Info 2"),
                ("Item 3", "Value 3", "Info 3")]

        for row in data:
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), row[0])
            self.list_ctrl.SetItem(index, 1, row[1])
            self.list_ctrl.SetItem(index, 2, row[2])

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, title="wxPython List Control with Threading", size=(400, 300))
        frame.Show()
        return True

if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()



