PROJECT_ID='spatial-flag-427113-n0'
import os
import pyaudio
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from six.moves import queue



# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms chunks


class MicrophoneStream:
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self._closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self._closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self._closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self._closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b"".join(data)


def listen_print_loop(responses):
    for response in responses:
        for result in response.results:
            # Check if the result is final
            if result.is_final:
                print(f"Final Transcript: {result.alternatives[0].transcript}")
            else:
                print(f"Interim Transcript: {result.alternatives[0].transcript}")


def transcribe_streaming_audio():
    client = SpeechClient()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="long",
    )

    streaming_config = cloud_speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )

    recognizer = f"projects/{PROJECT_ID}/locations/global/recognizers/_"

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (cloud_speech.StreamingRecognizeRequest(
            recognizer=recognizer,
            config=streaming_config if i == 0 else None,
            content=content)
                    for i, content in enumerate(audio_generator))

        responses = client.streaming_recognize(requests=requests)

        listen_print_loop(responses)


if __name__ == "__main__":
    transcribe_streaming_audio()
