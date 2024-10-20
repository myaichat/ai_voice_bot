
# Basic Python Voice Bot Using Realtime OpenAI API

As I found myself with some downtime, it felt natural to use this opportunity to refine my interviewing skills. To streamline the process and make practice more engaging, I decided to develop another iteration of my "Interview Copilot." This time, I integrated it with the OpenAI Realtime API for dynamic, real-time interaction. In this blog, I'll walk you through the implementation of this voice bot, providing insights on how it works and how you can leverage it to sharpen your technical interview preparations.

## Fourth Time's the Charm

This fourth iteration of the "Interview Copilot" refines the core concept of using Python to practice interview skills, but with a sharper focus on real-time interaction. Unlike the earlier versions—one a simple CLI script, another a wxPython UI, and the third using Streamlit/Whisper for Speech-to-Text (STT)—this version fully harnesses the power of the OpenAI Realtime API. By integrating real-time voice capabilities into the CLI, this version allows for an immersive and responsive experience. The result is a faster, more accessible way to practice, streamlining the interaction process while retaining the simplicity of a command-line interface.

## Realtime Voice Bot

To implement a real-time voice bot using OpenAI's Realtime API, we'll walk through a simple Python CLI script that integrates voice input and output capabilities. Below is an example implementation that utilizes the AudioHandler for managing audio playback and streaming, alongside the RealtimeClient for interacting with OpenAI's API in real time.

This implementation supports continuous voice streaming, real-time transcription, and a natural flow of conversation. It also handles user input, allowing you to quit the session by pressing a specific key.

### Example Script

```python
import asyncio
import os
from pynput import keyboard

async def main():
    audio_handler = AudioHandler()
    input_handler = InputHandler()
    input_handler.loop = asyncio.get_running_loop()
    
    client = RealtimeClient(
        api_key=os.environ.get("OPENAI_API_KEY"),
        on_text_delta=lambda text: print(f"\nAssistant: {text}", end="", flush=True),
        on_audio_delta=lambda audio: audio_handler.play_audio(audio),
        on_interrupt=lambda: audio_handler.stop_playback_immediately(),
        turn_detection_mode=TurnDetectionMode.SERVER_VAD,
    )

    # Start keyboard listener in a separate thread
    listener = keyboard.Listener(on_press=input_handler.on_press)
    listener.start()
    
    try:
        await client.connect()
        print("Connected to OpenAI Realtime API!")
        print("Audio streaming will start automatically.")
        print("Press 'q' to quit")

        # Start continuous audio streaming
        streaming_task = asyncio.create_task(audio_handler.start_streaming(client))
        
        # Simple input loop for quit command
        while True:
            command, _ = await input_handler.command_queue.get()
            
            if command == 'q':
                break
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        audio_handler.stop_streaming()
        audio_handler.cleanup()
        await client.close()

if __name__ == "__main__":
    print("Starting Realtime API CLI with Server VAD...")
    asyncio.run(main())
```

### Key Components:
- **RealtimeClient**: Manages the connection to the OpenAI Realtime API, handling voice input/output and text generation in real time.
- **AudioHandler**: Streams audio and plays responses.
- **InputHandler**: Handles keyboard inputs like quitting the session using the 'q' key.
- **TurnDetectionMode**: SERVER_VAD is used to automatically detect when the user is speaking, making interaction seamless.

## Voice Input / Text Output

In this section, we created a script that takes voice input and outputs the response in text instead of voice. This version of the bot is ideal for situations where text-based output is preferred. Below is an implementation simulating the process of detecting speech and providing text-based responses.

### Sample Output:

```plaintext
C:\>tbot
Starting Realtime API CLI with Server VAD...
Connected to OpenAI Realtime API!
Audio streaming will start automatically.
Press 'q' to quit

[Speech detected]
<-- I ask "How ru"
[Speech ended]
I'm just a computer program, so I don't have feelings, but I'm here and ready to help!
```

## Mock Bot

To save on API costs, we implemented a mocked version of the bot. The mock version simulates audio streaming and response handling without connecting to OpenAI's API.

### Example Script

```python
import re, asyncio
import unittest
from unittest.mock import AsyncMock, patch
from colorama import Fore, Back, Style, init

class MockRealtimeClient(RealtimeClient):
    async def connect(self):
        print("Connected to Mock WebSocket")

    async def stream_audio(self, audio_chunk: bytes):
        print(f"Streaming audio chunk of size {len(audio_chunk)}")

    async def handle_event(self, event_type):
        if event_type == "input_audio_buffer.speech_started":
            print("[Speech detected] - Start streaming audio")
        elif event_type == "input_audio_buffer.speech_stopped":
            print("[Speech ended] - Stop streaming audio")
```

## Editable Install

You can install the voice-bot package:

```bash
git clone https://github.com/myaichat/voice_bot.git
cd voice_bot
pip install -e .
```

## Build and Upload

To build the wheel and upload it to PyPI:

```bash
pip install wheel twine
python setup.py sdist bdist_wheel
twine upload dist/*
```

## Conclusion

In this blog, we explored how to build a real-time Python voice bot using the OpenAI Realtime API, from a basic CLI implementation to a mock version for cost-effective testing. By integrating real-time voice recognition and text responses, this bot can be a powerful tool for interview preparation and other use cases, offering dynamic interactions in real-time.
