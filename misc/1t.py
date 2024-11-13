import asyncio
from typing import Any, Dict

# Base class RealtimeClient
class RealtimeClient:
    def __init__(self, on_audio_transcript_delta=None):
        """Initialize the client with optional callback."""
        self.on_audio_transcript_delta = on_audio_transcript_delta

    async def simulate_audio_transcript_delta(self):
        """Simulate the response from the WebSocket with an audio transcript delta."""
        await asyncio.sleep(0.5)
        event = {
            "type": "response.audio_transcript.delta",
            "delta": "This is the transcript of your voice message!"
        }
        
        # Trigger the on_audio_transcript_delta callback if defined
        if self.on_audio_transcript_delta:
            self.on_audio_transcript_delta(event)

    def on_audio_transcript_delta(self, event):
        """Default method in RealtimeClient to handle transcript delta events."""
        print(f"[{self.__class__.__name__}] Received transcript: {event['delta']}")

# Derived class MockRealtimeClient inheriting RealtimeClient
class MockRealtimeClient(RealtimeClient):
    async def handle_event(self, event_type):
        """Handle events such as speech_started and speech_stopped."""
        if event_type == "input_audio_buffer.speech_started":
            print("[Mock Client] Handling speech started event.")

        elif event_type == "input_audio_buffer.speech_stopped":
            print("[Mock Client] Handling speech stopped event.")
            # Simulate receiving audio transcript delta after speech stops
            await self.simulate_audio_transcript_delta()

# Test case to demonstrate functionality
async def run_test():
    # Initialize the mocked client
    client = MockRealtimeClient()

    # Simulate handling the input_audio_buffer.speech_stopped event
    await client.handle_event("input_audio_buffer.speech_stopped")

# Run the test using asyncio
asyncio.run(run_test())
