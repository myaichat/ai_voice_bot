import asyncio
import websockets
import json
import pyaudio
import base64
import logging
import os
from pprint import pprint as pp 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

# WebSocket configuration
WS_URL = "wss://api.openai.com/v1/realtime"
MODEL = "gpt-4o-realtime-preview-2024-10-01"

# Load environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class RealtimeClient:
    def __init__(self):
        logger.info("Initializing RealtimeClient")
        self.ws = None
        self.p = pyaudio.PyAudio()
        self.stream = None

    async def connect(self):
        logger.info(f"Connecting to WebSocket: {WS_URL}")
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
        self.ws = await websockets.connect(f"{WS_URL}?model={MODEL}", extra_headers=headers)
        logger.info("Successfully connected to OpenAI Realtime API")

    async def send_event(self, event):
        logger.debug(f"Sending event: {event}")
        await self.ws.send(json.dumps(event))
        logger.debug("Event sent successfully")

    async def receive_events(self):
        logger.info("Starting to receive events")
        async for message in self.ws:
            #logger.debug(f"Received raw message: {message}")
            event = json.loads(message)
            await self.handle_event(event)

    async def handle_event(self, event):
        event_type = event.get("type")
        if event_type == "error":
            if 0:
                pp(event)
                logger.error(f"Error event received: {event['error']['message']}")


        elif event_type == "response.audio_transcript.delta":
            #pp(event)
            print(event["delta"], end="", flush=True)
            #logger.debug(f"Text delta received: {event['delta']}")
            #print(event["delta"], end="", flush=True)
        elif event_type == "response.done":
            print()
        else:
            pass
            #logger.info(f"Received other event type: {event_type}")

    def start_audio_stream(self):
        logger.info("Starting audio input stream")
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=CHUNK)
        logger.debug("Audio input stream started successfully")

    def stop_audio_stream(self):
        logger.info("Stopping audio input stream")
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        logger.debug("Audio input stream stopped successfully")

    def record_audio(self, duration):
        logger.info(f"Recording audio for {duration} seconds")
        frames = []
        
        try:
            for i in range(0, int(RATE / CHUNK * duration)):
                data = self.stream.read(CHUNK, exception_on_overflow=False)  # Capture audio data
                frames.append(data)
                if i % 10 == 0:  # Log every 10th frame
                    logger.debug(f"Recorded frame {i}")
                    
            if not frames:
                logger.error("No audio frames captured!")
                return None
            
            audio_data = b''.join(frames)
            logger.info(f"Audio recording complete, total size: {len(audio_data)} bytes")
            return audio_data
        except Exception as e:
            logger.error(f"Error during audio recording: {e}")
            return None


    async def send_audio(self, duration):
        logger.info(f"Preparing to send audio of duration: {duration} seconds")
        self.start_audio_stream()
        audio_data = self.record_audio(duration)
        self.stop_audio_stream()

        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        logger.debug(f"Audio encoded to base64, length: {len(base64_audio)}")
        
        event = {
            "type": "input_audio_buffer.append",
            "audio": base64_audio
        }
        await self.send_event(event)
        logger.debug("Audio buffer appended, committing buffer")
        await self.send_event({"type": "input_audio_buffer.commit"})
        logger.debug("Audio buffer committed, creating response")
        await self.send_event({"type": "response.create"})

    async def run(self):
        logger.info("Starting RealtimeClient run")
        await self.connect()
        
        # Create a task for receiving events
        receive_task = asyncio.create_task(self.receive_events())
        
        logger.info("Sending initial message to start the conversation")
        await self.send_event({
            "type": "response.create",
            "response": {
                "modalities": ["text"],
                "instructions": "You are a helpful AI assistant. Respond to the user's messages.",
            }
        })

        try:
            while True:
                command = await asyncio.get_event_loop().run_in_executor(None, input, ">>>: ")
                if command == 'a':
                    logger.info("Audio input selected")
                    print("Recording for 5 seconds...")
                    await self.send_audio(5)
                elif command == 'q':
                    logger.info("Quit command received")
                    break
                else:
                    logger.warning(f"Invalid command received: {command}")

                # Give some time for the response to be processed
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"An error occurred: {e}")
        finally:
            logger.info("Ending conversation and closing connection")
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
            await self.ws.close()

async def main():
    logger.info("Starting main function")
    client = RealtimeClient()
    try:
        await client.run()
    except Exception as e:
        logger.error(f"An error occurred in main: {e}")
    finally:
        logger.info("Main function completed")

if __name__ == "__main__":
    logger.info("Script started")
    asyncio.run(main())
    logger.info("Script completed")
