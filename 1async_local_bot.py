import  asyncio
import unittest
from unittest.mock import AsyncMock, patch
from pprint import pprint as pp
import os, time
import numpy as np
import pyaudio

from typing import Optional

from ai_voice_bot.transcribe.LocalWhisper import LocalWhisper
from ai_voice_bot.transcribe.ApiWhisper import ApiWhisper
from ai_voice_bot.transcribe.GooTranscribe import GooTranscribe   


from colorama import Fore, Back, Style, init

#from ai_voice_bot.mock.MockAudioHandler import MockAudioHandler
#from ai_voice_bot.client.TextRealtimeClient import RealtimeClient
# AudioHandler class

init(autoreset=True)

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
        self.tid=0

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
                data = self.stream.read(self.chunk * 8, exception_on_overflow=False)

                # Check if the chunk contains speech
                if self.is_speech(data):
                    if not self.speech_started:
                        # Speech has just started
                        print("\n[Speech detected]")
                        self.tid +=1
                        tid=self.tid                        
                        await client.handle_event("input_audio_buffer.speech_started",tid)
                        self.speech_started = True

                    # Reset the silence duration
                    self.last_speech_time = asyncio.get_event_loop().time()

                else:
                    # Check if it's been quiet for longer than the threshold
                    if self.speech_started and (asyncio.get_event_loop().time() - self.last_speech_time > self.silence_duration_threshold):
                        print("\n[Speech ended]")

                        
                        tid=self.tid
                        await client.handle_event("input_audio_buffer.speech_stopped", tid)
                        self.speech_started = False

                # Stream the audio to the client only if speech is ongoing
                if self.speech_started:

                    await client.stream_audio(tid,data)

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


class MockRealtimeClient:
    def __init__(self, on_audio_transcript_delta=None):
        """Initialize the mock client with optional callback."""
        self.audio = {} #b''
        if 0:
            self.local_whisper = LocalWhisper()
        self.api_whisper = ApiWhisper()
        self.goo_transcribe = GooTranscribe()
        

    async def connect(self) -> None:
        """Mock WebSocket connection for testing."""
        print("Connected to Mock WebSocket")

    async def stream_audio(self, tid, audio_chunk: bytes):
        """Mock method to stream audio chunks to WebSocket."""
        if tid not in self.audio:
            self.audio[tid] = b''
        self.audio[tid]  += audio_chunk

    async def handle_event(self, event_type, tid):
        """Handle events such as speech_started and speech_stopped."""
        if event_type == "input_audio_buffer.speech_started":
            pass
        elif event_type == "input_audio_buffer.speech_stopped":
            # When speech stops, trigger transcription in parallel
           
            
            asyncio.create_task(self.on_audio_transcript(tid))

    async def on_audio_transcript(self, tid):
        """Transcribe audio chunk in parallel while streaming continues."""
        print("\nTranscribing audio...", tid)
        #await asyncio.sleep(10)  # Simulate processing delay
        start_time = time.time()
        file_name: str = f"{tid}_temp_audio_chunk.wav"
        audio = self.audio[tid]
        self.api_whisper.write_audio(audio, file_name)
        if 1:

            tasks = [
                #asyncio.to_thread(self.local_whisper.local_transcribe_audio, audio,file_name),
                asyncio.to_thread(self.api_whisper.transcribe_audio, audio,file_name),
                asyncio.to_thread(self.goo_transcribe.transcribe_audio, audio,file_name)
            ]
        else:
            tasks = [
                #asyncio.create_task(self.local_whisper.write_audio(audio,file_name)),
                #asyncio.create_task(self.local_whisper.local_transcribe_audio(audio,file_name)),
                asyncio.create_task(self.api_whisper.transcribe_audio(audio,file_name)),
                asyncio.create_task(self.goo_transcribe.transcribe_audio(audio,file_name))
            ]
        if 1:
            results= await asyncio.gather(*tasks)
            pp( results)
            self.chunk = b''  # Reset the chunk after processing
            for res in results:
                if res:
                    print(res[1], end=" ")

            print()
            for res in results:
                if res:
                    print(res[2], end=" ")

            print()            
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("Transcription complete", tid, elapsed_time)



# Test case for the RealtimeClient with mock WebSocket
class TestRealtimeClient(unittest.TestCase):
    @patch('websockets.connect', new_callable=AsyncMock)
    def test_mock_realtime_client(self, mock_websocket_connect):
        async def run_test():
            audio_handler = MockAudioHandler()

            # Initialize the mocked client
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
