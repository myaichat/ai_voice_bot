import re, asyncio
import unittest
from unittest.mock import AsyncMock, patch

import numpy as np

from colorama import Fore, Back, Style, init

from ai_voice_bot.mock.MockAudioHandler import MockAudioHandler

import pyaudio
import wave
import io
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types

PROJECT_ID = 'spatial-flag-427113-n0'


init(autoreset=True)


import asyncio
import pyaudio
import numpy as np
from typing import Optional

FORMAT = pyaudio.paInt16  # Audio format (16-bit)
CHANNELS = 1              # Mono audio
RATE = 6400              # Sample rate (44.1 kHz)
CHUNK = 1024              # Buffer size
RECORD_SECONDS = 5        # Duration of the recording
audio = pyaudio.PyAudio()


class MockAudioHandler:
    def __init__(self):
        # Audio parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = RATE
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
        self.batch=[]

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
        frames=[]
        
        while self.streaming:
            try:
                # Read raw PCM data
                data = self.stream.read(self.chunk, exception_on_overflow=False)

                # Check if the chunk contains speech
                if self.is_speech(data):
                    if not self.speech_started:
                        # Speech has just started
                        print("\n[Speech detected] - Start streaming audio")
                        await client.handle_event("input_audio_buffer.speech_started")
                        self.speech_started = True
                        print("speech", len(data))
                        frames.append(data)
                    
                    # Reset the silence duration
                    self.last_speech_time = asyncio.get_event_loop().time()

                else:
                    # Check if it's been quiet for longer than the threshold
                    if self.speech_started and (asyncio.get_event_loop().time() - self.last_speech_time > self.silence_duration_threshold):
                        print("\n[Speech ended] - Stop streaming audio")
                        await client.handle_event("input_audio_buffer.speech_stopped", frames)
                        self.speech_started = False
                        frames=[]

                # Stream the audio to the client only if speech is ongoing
                if self.speech_started:
                    print("speech", len(data))
                    frames.append(data)
                    #await client.stream_audio(data)

            except Exception as e:
                print(f"Error streaming: {e}")
                raise
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
    def __init__(self):
        """Initialize the mock client with optional callback."""
        #super().__init__(api_key="mock")
        #self.on_audio_transcript_delta = on_audio_transcript_delta

    async def connect(self) -> None:
        """Mock WebSocket connection for testing."""
        print("Connected to Mock WebSocket")

    async def stream_audio(self, audio_chunk: bytes):
        """Mock method to stream audio chunks to WebSocket."""
        print(f"Streaming audio chunk of size {len(audio_chunk)}")

    async def handle_event(self, event_type, frames=None):
        """Handle events such as speech_started and speech_stopped."""
        if event_type == "input_audio_buffer.speech_started":
            print("[Mock Client] Handling speech started event.")

        elif event_type == "input_audio_buffer.speech_stopped":
            print("[Mock Client] Handling speech stopped event.")
            # Simulate receiving audio transcript delta after speech stops
            sentence = f"This is the {Fore.BLACK}{Back.YELLOW}>>>MOCKED<<<{Style.RESET_ALL} model answer to your question."

            # Apply wave transformations and write the audio data to memory
            output = io.BytesIO()
            wf = wave.open(output, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()

            # Get the WAV data from memory
            wav_data = output.getvalue()
            output.close()

            audio_data = frames
            ret = self.transcribe_streaming_v2(wav_data)

            # Print transcription results
            from pprint import pprint
            pprint(ret)
    def transcribe_streaming_v2(self, audio_data: bytes) -> cloud_speech_types.StreamingRecognizeResponse:
        """Transcribes in-memory audio data using Google Cloud Speech-to-Text API."""
        client = SpeechClient()

        # Split the audio data into smaller chunks for streaming
        chunk_length = len(audio_data) // 10
        print(111, chunk_length)    
        stream = [audio_data[start:start + chunk_length] for start in range(0, len(audio_data), chunk_length)]
        audio_requests = (
            cloud_speech_types.StreamingRecognizeRequest(audio=audio) for audio in stream
        )

        recognition_config = cloud_speech_types.RecognitionConfig(
            auto_decoding_config=cloud_speech_types.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="long",
        )
        streaming_config = cloud_speech_types.StreamingRecognitionConfig(
            config=recognition_config
        )
        config_request = cloud_speech_types.StreamingRecognizeRequest(
            recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
            streaming_config=streaming_config,
        )

        def requests(config: cloud_speech_types.RecognitionConfig, audio: list) -> list:
            yield config
            yield from audio

        # Transcribe the audio into text
        responses_iterator = client.streaming_recognize(
            requests=requests(config_request, audio_requests)
        )
        responses = []
        for response in responses_iterator:
            responses.append(response)
            for result in response.results:
                print(f"Transcript: {result.alternatives[0].transcript}")

        return responses
    async def simulate_audio_transcript_delta(self, word: str):
        """Simulate the response from the WebSocket with an audio transcript delta."""
        # Simulate a small delay after speech stops to receive the transcript
        await asyncio.sleep(0.07)
        
        # Simulated transcript response event
        event = {
            "type": "response.audio_transcript.delta",
            "delta": word
        }
        
        # Invoke the on_audio_transcript_delta callback if provided
        #if self.on_audio_transcript_delta:
        self.on_audio_transcript_delta(event)
    def on_audio_transcript_delta(self, event):
        print(f"Mocked Transcript Response: {event['delta']}")
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
