import pyaudio
from pprint import pprint as pp
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types

PROJECT_ID = 'spatial-flag-427113-n0'
CHUNK_SIZE = 1024  # Size of each audio chunk
FORMAT = pyaudio.paInt16  # Audio format (16-bit)
CHANNELS = 1  # Number of audio channels (1 = mono)
RATE = 16000  # Sampling rate in Hz


def list_input_devices():
    """List available input devices."""
    p = pyaudio.PyAudio()
    info = []
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:
            print(f"Device {i}: {device_info['name']}")
            info.append((i, device_info['name']))
    p.terminate()
    return info


def transcribe_streaming_v2(device_index=None):
    """Streams audio from the microphone using Google Cloud Speech-to-Text API."""
    client = SpeechClient()

    # Configure recognition
    recognition_config = cloud_speech_types.RecognitionConfig(
        auto_decoding_config=cloud_speech_types.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="long",
    )
    
    # Configure streaming
    streaming_config = cloud_speech_types.StreamingRecognitionConfig(
        config=recognition_config,
    )

    # Initial config request
    config_request = cloud_speech_types.StreamingRecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        streaming_config=streaming_config,
    )

    def audio_generator():
        """Generator for audio chunks."""
        yield config_request

        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK_SIZE,
        )

        print("Listening... Press Ctrl+C to stop.")
        
        try:
            while True:
                # Read audio chunk and create request
                chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                yield cloud_speech_types.StreamingRecognizeRequest(audio=chunk)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    try:
        # Stream recognition requests
        requests_iterator = audio_generator()
        responses = client.streaming_recognize(requests=requests_iterator)

        # Process responses
        for response in responses:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            if not result.is_final:
                print(f"\rPartial: {result.alternatives[0].transcript}", end="")
            else:
                transcript = result.alternatives[0].transcript
                print(f"\nFinal: {transcript}")

    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        return None

if __name__ == "__main__":
    print("Available input devices:")
    devices = list_input_devices()
    
    if not devices:
        print("No input devices found!")
        exit(1)
        
    try:
        device_index = int(input("Enter the device index to use for the microphone: "))
        transcribe_streaming_v2(device_index=device_index)
    except ValueError:
        print("Please enter a valid device index number")
    except KeyboardInterrupt:
        print("\nExiting...")