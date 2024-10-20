import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from typing import List
import websockets
from MyRealtimeClient import RealtimeClient
from MyAudioHandler import AudioHandler

import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from typing import List
import websockets

import asyncio
import pyaudio
import wave
import queue
import io
from typing import Optional

from pydub import AudioSegment
import threading
import numpy as np

class AudioHandler:
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
        self.recording_thread = None
        self.recording = False

        # streaming params
        self.streaming = False
        self.stream = None

        self.last_speech_time = None

    def is_speech(self, audio_chunk: bytes) -> bool:
        """Determine if an audio chunk contains speech based on amplitude."""
        # Convert audio chunk to numpy array
        audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
        # Get the maximum amplitude in the chunk
        max_amplitude = np.max(np.abs(audio_data))
        return max_amplitude > self.speech_threshold

    async def start_streaming(self, client: 'RealtimeClient'):
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
        
        print("\nStreaming audio...")

        speech_started = False
        self.last_speech_time = None
        
        while self.streaming:
            try:
                # Read raw PCM data
                data = self.stream.read(self.chunk, exception_on_overflow=False)

                # Check if the chunk contains speech
                if self.is_speech(data):
                    if not speech_started:
                        # Speech has just started
                        print("\n[Speech detected] - Start streaming audio")
                        await client.handle_event("input_audio_buffer.speech_started")
                        speech_started = True
                    
                    # Reset the silence duration
                    self.last_speech_time = asyncio.get_event_loop().time()

                else:
                    # Check if it's been quiet for longer than the threshold
                    if speech_started and (asyncio.get_event_loop().time() - self.last_speech_time > self.silence_duration_threshold):
                        print("\n[Speech ended] - Stop streaming audio")
                        await client.handle_event("input_audio_buffer.speech_stopped")
                        speech_started = False

                # Stream the audio to the client
                await client.stream_audio(data)

            except Exception as e:
                print(f"Error streaming: {e}")
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


# Mocked RealtimeClient class inheriting the original
class MockRealtimeClient(RealtimeClient):
    async def connect(self) -> None:
        """Mock WebSocket connection for testing."""
        self.ws = AsyncMock()  # Mock the WebSocket connection
        self.ws.send = AsyncMock()  # Mock sending messages
        self.ws.recv = AsyncMock()  # Mock receiving messages
    
    async def handle_messages(self) -> None:
        """Mock message handling."""
        while True:
            # Simulate waiting for events
            await asyncio.sleep(0.1)

            # Simulate the event where speech is detected
            event_type = "input_audio_buffer.speech_started"
            
            if event_type == "input_audio_buffer.speech_started":
                print("\n[Speech detected] - Start streaming audio")
                
                # Start streaming the audio when speech is detected
                streaming_task = asyncio.create_task(self.start_streaming_audio())
                await asyncio.sleep(3)  # Simulate some duration for speech
            
            elif event_type == "input_audio_buffer.speech_stopped":
                print("\n[Speech ended] - Stop streaming audio")
                break  # Stop after this event in the mock

    async def start_streaming_audio(self):
        """Mock starting audio streaming for speech detection."""
        # Mock sending audio data to the WebSocket
        for i in range(3):  # Simulate streaming for a few iterations
            await asyncio.sleep(1)
            print(f"Streaming audio chunk {i+1}")
            # You can simulate the actual audio data processing here

        print("Finished streaming audio.")

# Test case for the RealtimeClient with mock WebSocket
class TestRealtimeClient(unittest.TestCase):
    @patch('websockets.connect', new_callable=AsyncMock)
    def test_mock_realtime_client(self, mock_websocket_connect):
        async def run_test():
            audio_handler = AudioHandler()

            # Initialize the mocked client
            client = MockRealtimeClient(
                api_key="dummy_key",
                on_text_delta=lambda text: print(f"Mocked Assistant: {text}"),
                on_audio_transcript_delta=lambda transcript: print(f"Audio Transcript: {transcript}")
            )

            # Call connect (which will use the mocked WebSocket)
            await client.connect()

            # Simulate handling the input_audio_buffer.speech_started event
            await client.handle_messages()

        asyncio.run(run_test())  # Run the test using asyncio

# Run the test
if __name__ == "__main__":
    unittest.main(argv=[''], exit=False)
