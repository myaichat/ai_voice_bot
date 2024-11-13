import os
import time
import queue
import pyaudio
from pprint import pprint as pp
from google.cloud import speech_v2
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types
from six.moves import queue

# Constants
RATE = 44100
CHUNK = int(RATE / 10)
PROJECT_ID = 'spatial-flag-427113-n0'

class GoogMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True
        self._audio_interface = None
        self._audio_stream = None

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        
        # Find Yeti GX device index
        yeti_index = None
        for i in range(self._audio_interface.get_device_count()):
            info = self._audio_interface.get_device_info_by_index(i)
            if 'Yeti GX' in info.get('name', ''):
                yeti_index = info['index']
                break

        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            input_device_index=yeti_index,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get_nowait()
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b''.join(data)

def get_recognition_config(model="long"):
    """Creates recognition config with specified parameters."""
    return cloud_speech_types.RecognitionConfig(
        auto_decoding_config=cloud_speech_types.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model=model,
        features=cloud_speech_types.RecognitionFeatures(
            enable_automatic_punctuation=True,
            enable_spoken_punctuation=True
        )
    )

def process_responses(responses_iterator):
    """Process and print responses from the API."""
    responses = []
    for response in responses_iterator:
        responses.append(response)
        for result in response.results:
            if result.alternatives:
                transcript = result.alternatives[0].transcript
                is_final = result.is_final
                if is_final:
                    print(f"\nFinal transcript: {transcript}")
                else:
                    print(f"\rInterim transcript: {transcript}", end='', flush=True)
    return responses

def transcribe_file(file_path: str) -> list:
    """Transcribes audio from a file using Google Cloud Speech-to-Text API."""
    print(f"Transcribing file: {file_path}")
    client = SpeechClient()

    # Read file and chunk it
    with open(file_path, "rb") as f:
        audio_content = f.read()

    chunk_length = len(audio_content) // 10
    stream = [
        audio_content[start : start + chunk_length]
        for start in range(0, len(audio_content), chunk_length)
    ]
    audio_requests = (
        cloud_speech_types.StreamingRecognizeRequest(audio=audio)
        for audio in stream
    )

    recognition_config = get_recognition_config()
    streaming_config = cloud_speech_types.StreamingRecognitionConfig(
        config=recognition_config
    )
    config_request = cloud_speech_types.StreamingRecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        streaming_config=streaming_config,
    )

    def requests(config, audio):
        yield config
        yield from audio

    responses_iterator = client.streaming_recognize(
        requests=requests(config_request, audio_requests)
    )
    
    return process_responses(responses_iterator)

def transcribe_microphone():
    """Transcribes audio from microphone using Google Cloud Speech-to-Text API."""
    print("Starting microphone transcription...")
    client = SpeechClient()

    recognition_config = get_recognition_config(model="latest_short")
    streaming_config = cloud_speech_types.StreamingRecognitionConfig(
        config=recognition_config,
        streaming_features=cloud_speech_types.StreamingRecognitionFeatures(
            interim_results=True
        )
    )
    config_request = cloud_speech_types.StreamingRecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        streaming_config=streaming_config,
    )

    with GoogMicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        
        def request_generator():
            yield config_request
            for content in audio_generator:
                print(111)
                yield cloud_speech_types.StreamingRecognizeRequest(audio=content)

        responses = client.streaming_recognize(requests=request_generator())
        return process_responses(responses)

def main():
    """Main function to handle both file and microphone transcription."""
    import argparse
    parser = argparse.ArgumentParser(description="Speech Recognition System")
    parser.add_argument("--file", type=str, help="Path to audio file to transcribe")
    args = parser.parse_args()

    try:
        if args.file:
            responses = transcribe_file(args.file)
            print("\nFull response details:")
            pp(responses)
        else:
            print("Starting microphone transcription (Ctrl+C to exit)...")
            while True:
                try:
                    responses = transcribe_microphone()
                except KeyboardInterrupt:
                    print("\nStopping transcription...")
                    break
                except Exception as e:
                    print(f"Error occurred: {e}")
                    time.sleep(2)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()