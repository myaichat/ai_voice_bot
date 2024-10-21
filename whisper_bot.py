import re, asyncio
import unittest
from unittest.mock import AsyncMock, patch

import numpy as np

from colorama import Fore, Back, Style, init

#from ai_voice_bot.mock.MockAudioHandler import MockAudioHandler
#from ai_voice_bot.client.TextRealtimeClient import RealtimeClient
# AudioHandler class

init(autoreset=True)


import asyncio
import pyaudio
import numpy as np
from typing import Optional




class MockAudioHandler:
    def __init__(self):
        # Audio parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 24000
        self.chunk = 1024  # Buffer size for each read

        self.audio = pyaudio.PyAudio()

        # Threshold for detecting speech (based on amplitude)
        self.speech_threshold = 500  # Adjust this value as needed
        self.silence_duration_threshold = 1.0  # 1 second of silence considered speech stop
        
        # Recording params
        self.recording_stream: Optional[pyaudio.Stream] = None
        self.recording = False

        # streaming params
        self.streaming = False
        self.stream = None

        self.last_speech_time = None
        self.speech_started = False

    def is_speech(self, audio_chunk: bytes) -> bool:
        """Determine if an audio chunk contains speech based on amplitude."""
        audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
        max_amplitude = np.max(np.abs(audio_data))
        return max_amplitude > self.speech_threshold

    async def start_streaming(self, client: 'MockRealtimeClient'):
        """Start continuous audio streaming."""
        if self.streaming:
            return
        
        self.streaming = True
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print("\nListening for speech...")

        self.last_speech_time = None
        self.speech_started = False
        
        while self.streaming:
            try:
                # Read raw PCM data
                data = self.stream.read(self.chunk*8, exception_on_overflow=False)

                # Check if the chunk contains speech
                if self.is_speech(data):
                    if not self.speech_started:
                        # Speech has just started
                        print("\n[Speech detected]")
                        await client.handle_event("input_audio_buffer.speech_started")
                        self.speech_started = True
                    
                    # Reset the silence duration
                    self.last_speech_time = asyncio.get_event_loop().time()

                else:
                    # Check if it's been quiet for longer than the threshold
                    if self.speech_started and (asyncio.get_event_loop().time() - self.last_speech_time > self.silence_duration_threshold):
                        print("\n[Speech ended]")
                        await client.handle_event("input_audio_buffer.speech_stopped")
                        self.speech_started = False

                # Stream the audio to the client only if speech is ongoing
                if self.speech_started:
                    await client.stream_audio(data)

            except Exception as e:
                print(f"Error streaming: {e}")
                raise e
                break
            await asyncio.sleep(0.01)

    def stop_streaming(self):
        """Stop audio streaming."""
        self.streaming = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def cleanup(self):
        """Clean up audio resources"""
        self.stop_streaming()
        self.audio.terminate()


if 0:
    print(Back.YELLOW + 'This is highlighted text in yellow!')
    print('This is normal text.')

    # ANSI escape code for yellow background
    highlight = '\033[43m'
    reset = '\033[0m'

    # Print text with yellow background
    print( f"This is the {Fore.BLACK}{Back.YELLOW}>>>MOCKED<<<{Style.RESET_ALL} model answer to your question.")

    exit()

# MockRealtimeClient class updated to handle dynamic speech events
class MockRealtimeClient():
    def __init__(self, on_audio_transcript_delta=None):
        """Initialize the mock client with optional callback."""
        #super().__init__(api_key="mock")
        #self.on_audio_transcript_delta = on_audio_transcript_delta
        self.chunk=b''

    async def connect(self) -> None:
        """Mock WebSocket connection for testing."""
        print("Connected to Mock WebSocket")

    async def stream_audio(self, audio_chunk: bytes):
        """Mock method to stream audio chunks to WebSocket."""
        #print(f"Streaming audio chunk of size {len(audio_chunk)}")
        self.chunk +=audio_chunk
        #print(f"Streaming audio chunk of size {len(audio_chunk)}, {len(self.chunk)}")


    async def handle_event(self, event_type):
        """Handle events such as speech_started and speech_stopped."""
        #print(event_type)
        if event_type == "input_audio_buffer.speech_started":
            #print("[Mock Client] Handling speech started event.")
            pass

        elif event_type == "input_audio_buffer.speech_stopped":
            #print("[Mock Client 111] Handling speech stopped event.")
            # Simulate receiving audio transcript delta after speech stops
            self.on_audio_transcript()
    def on_audio_transcript(self):
        """Default method in RealtimeClient to handle transcript delta events."""
        from pprint import pprint as pp
       
        if 1:
            import os, io, openai, wave
            openai.api_key = os.environ.get("OPENAI_API_KEY")            
            p = pyaudio.PyAudio()
            channels = 1  # Mono
            sample_format = pyaudio.paInt16
            rate = 24000
            file_name = "temp_audio_chunk.wav"
            wf = wave.open(file_name, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(rate)
            wf.writeframes(self.chunk)
            wf.close()
            with open(file_name, 'rb') as audio_file:
                response = openai.audio.transcriptions.create(
                    model="whisper-1",  # Specify the Whisper model
                    file=audio_file
                )
                transcription = response.text
                print(f"Transcription: {transcription}")  
                ratio = len(transcription)/len(self.chunk)
                print (f"Ratio: {ratio}")
            self.chunk=b''          

        if 0:
            p = pyaudio.PyAudio()

            # Audio stream configuration
            chunk_size = 1024
            sample_format = pyaudio.paInt16  # 16-bit resolution
            channels = 1  # Mono

            import os, io, openai, wave
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            buffer = io.BytesIO(self.chunk)

            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(chunk_size)
                wf.writeframes(self.chunk)
            
            buffer.seek(0)
            buffer.name = "audio.wav"

            response = openai.audio.transcriptions.create(
                        model="whisper-1",  # Specify the Whisper model
                        file=buffer
                    )
            transcription = response.text
            print(f"\t\tTranscription: {transcription}")

        

        
# Test case for the RealtimeClient with mock WebSocket
class TestRealtimeClient(unittest.TestCase):
    @patch('websockets.connect', new_callable=AsyncMock)
    def test_mock_realtime_client(self, mock_websocket_connect):
        async def run_test():
            audio_handler = MockAudioHandler()

            # Initialize the mocked client with an audio transcript delta callback
            if 0:
                client = MockRealtimeClient(
                    on_audio_transcript_delta=lambda event: print(f"Mocked Transcript Response: {event['delta']}")
                )
            client = MockRealtimeClient()
            # Call connect (which will use the mocked WebSocket)
            await client.connect()

            # Start streaming and handling events (mock speech detection)
            await audio_handler.start_streaming(client)

            # Simulate some speech, then stop
            await asyncio.sleep(5)
            audio_handler.stop_streaming()

        asyncio.run(run_test())  # Run the test using asyncio

# Run the test
def main():
    unittest.main(argv=[''], exit=False)
if __name__ == "__main__":
    main()
