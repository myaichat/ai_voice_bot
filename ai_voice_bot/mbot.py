import re, asyncio
import unittest
from unittest.mock import AsyncMock, patch

import numpy as np

from colorama import Fore, Back, Style, init

from voice_bot.mock.MockAudioHandler import MockAudioHandler
from voice_bot.client.TextRealtimeClient import RealtimeClient
# AudioHandler class

init(autoreset=True)
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
class MockRealtimeClient(RealtimeClient):
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

    async def handle_event(self, event_type):
        """Handle events such as speech_started and speech_stopped."""
        if event_type == "input_audio_buffer.speech_started":
            print("[Mock Client] Handling speech started event.")

        elif event_type == "input_audio_buffer.speech_stopped":
            print("[Mock Client] Handling speech stopped event.")
            # Simulate receiving audio transcript delta after speech stops
            sentence = f"This is the {Fore.BLACK}{Back.YELLOW}>>>MOCKED<<<{Style.RESET_ALL} model answer to your question."

            # Use regex to split the sentence while preserving spaces
            split = re.findall(r'\S+|\s+', sentence)

            for word in split:
                await self.simulate_audio_transcript_delta(word)

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
        if self.on_audio_transcript_delta:
            self.on_audio_transcript_delta(event)

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
