import asyncio
import os
from pynput import keyboard
from openai_realtime_client_1 import RealtimeClient, InputHandler, AudioHandler
from llama_index.core.tools import FunctionTool

# Example tool
def get_phone_number(name: str) -> str:
    """Get my phone number."""
    if name == "Jerry":
        return "1234567890"
    elif name == "Logan":
        return "0987654321"
    else:
        return "Unknown"

tools = [FunctionTool.from_defaults(fn=get_phone_number)]

async def main():
    audio_handler = AudioHandler()
    input_handler = InputHandler()
    input_handler.loop = asyncio.get_running_loop()

    client = RealtimeClient(
        api_key=os.environ.get("OPENAI_API_KEY"),
        on_text_delta=lambda text: print(f"\nAssistant: {text}", end="", flush=True),
        on_audio_delta=lambda audio: audio_handler.play_audio(audio),
        tools=tools,
    )

    listener = keyboard.Listener(on_press=input_handler.on_press)
    listener.start()

    recording = False  # Track the recording state
    processing_command = False  # Track if there is an active command

    async def handle_audio_commands():
        nonlocal recording, processing_command
        while True:
            if processing_command:
                await asyncio.sleep(0.1)  # Wait for other commands to finish
                continue

            command, _ = await input_handler.command_queue.get()

            if command == 'r' and not recording:
                print("[Starting recording...]")
                recording = True
                audio_handler.start_recording()

            elif command == 'space' and recording:
                print("[Stopping recording...]")
                audio_data = audio_handler.stop_recording()
                recording = False

                if audio_data:
                    print("[Sending audio...]")
                    processing_command = True
                    try:
                        await client.send_audio(audio_data)
                        print("[Audio sent]")
                    except Exception as e:
                        print(f"Error sending audio: {e}")
                    processing_command = False
                else:
                    print("Error: No audio data captured.")

            await asyncio.sleep(0.01)

    async def handle_text_commands():
        nonlocal processing_command
        while True:
            if processing_command:
                await asyncio.sleep(0.1)  # Wait for other commands to finish
                continue

            command, data = await input_handler.command_queue.get()

            if command == 'enter' and data:
                processing_command = True
                try:
                    await client.send_text(data)
                    print("[Text sent]")
                except Exception as e:
                    print(f"Error sending text: {e}")
                processing_command = False

            elif command == 'q':
                return

            await asyncio.sleep(0.01)

    try:
        await client.connect()
        print("Connected to OpenAI Realtime API!")
        print("Commands: \n- Press 'r' to record, 'space' to stop recording, 'enter' to send text, 'q' to quit.")

        # Run tasks concurrently
        await asyncio.gather(
            client.handle_messages(),
            handle_audio_commands(),
            #handle_text_commands(),
        )

    except Exception as e:
        print(f"Error: {e}")
    finally:
        listener.stop()
        audio_handler.cleanup()
        await client.close()

if __name__ == "__main__":
    print("Starting Realtime API CLI...")
    asyncio.run(main())
