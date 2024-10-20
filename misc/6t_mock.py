import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from typing import List
import websockets
from MyRealtimeClient import RealtimeClient

# Mocked RealtimeClient class inheriting the original
class MockRealtimeClient(RealtimeClient):
    async def connect(self) -> None:
        """Mock WebSocket connection for testing."""
        self.ws = AsyncMock()  # Mock the WebSocket connection
        self.ws.send = AsyncMock()  # Mock sending messages
        self.ws.recv = AsyncMock()  # Mock receiving messages
    
    async def handle_messages(self) -> None:
        """Mock message handling."""
        # Simulate receiving a response event
        event = {
            "type": "response.text.delta",
            "delta": "Hello, this is a mocked response from on_audio_transcript_delta!"
        }
        await asyncio.sleep(0.1)  # Simulate async delay
        if self.on_audio_transcript_delta:
            self.on_audio_transcript_delta(event)
        if 0:
            if self.on_text_delta:
                self.on_text_delta(event["delta"])  # Remove 'await' as it's not an async function

# Test case for the RealtimeClient with mock WebSocket
class TestRealtimeClient(unittest.TestCase):
    @patch('websockets.connect', new_callable=AsyncMock)
    def test_mock_realtime_client(self, mock_websocket_connect):
        async def run_test():
            # Initialize the mocked client
            client = MockRealtimeClient(
                api_key="dummy_key",
                on_text_delta=lambda text: print(f"Mocked Assistant: {text}")
            )

            # Call connect (which will use the mocked WebSocket)
            await client.connect()

            # Simulate sending a text message (you can add more tests for audio and other events)
            await client.send_text("Test message")
            
            # Run the message handler (which uses a mocked WebSocket response)
            await client.handle_messages()

        asyncio.run(run_test())  # Run the test using asyncio

# Run the test
if __name__ == "__main__":
    unittest.main(argv=[''], exit=False)
