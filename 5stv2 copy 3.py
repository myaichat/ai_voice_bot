import os
from pprint import pprint as pp
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types
import time, pyaudio, queue, threading
import numpy as np
PROJECT_ID = 'spatial-flag-427113-n0'


class AudioHandler:
    """
    Handles audio input and output for the chatbot.

    Uses PyAudio for audio input and output, and runs a separate thread for recording and playing audio.

    When playing audio, it uses a buffer to store audio data and plays it continuously to ensure smooth playback.

    Attributes:
        format (int): The audio format (paInt16).
        channels (int): The number of audio channels (1).
        rate (int): The sample rate (24000).
        chunk (int): The size of the audio buffer (1024).
        audio (pyaudio.PyAudio): The PyAudio object.
        recording_stream (pyaudio.Stream): The stream for recording audio.
        recording_thread (threading.Thread): The thread for recording audio.
        recording (bool): Whether the audio is currently being recorded.
        streaming (bool): Whether the audio is currently being streamed.
        stream (pyaudio.Stream): The stream for streaming audio.
        playback_stream (pyaudio.Stream): The stream for playing audio.
        playback_buffer (queue.Queue): The buffer for playing audio.
        stop_playback (bool): Whether the audio playback should be stopped.
    """
    def __init__(self):
        # Audio parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 24000
        self.chunk = 1024*10

        self.audio = pyaudio.PyAudio()

        # Recording params
        self.recording_stream: Optional[pyaudio.Stream] = None
        self.recording_thread = None
        self.recording = False

        # streaming params
        self.streaming = False
        self.stream = None

        # Threshold for detecting speech (based on amplitude)
        self.speech_threshold = 500  # Adjust this value as needed
        self.silence_duration_threshold = 1.0  # 1 second of silence considered speech stop        
        self.last_speech_time = None
        self.speech_started = False
        # Playback params
        self.playback_stream = None
        self.playback_buffer = queue.Queue(maxsize=20)
        self.playback_event = threading.Event()
        self.playback_thread = None
        self.stop_playback = False
    def is_speech(self, audio_chunk: bytes) -> bool:
        """Determine if an audio chunk contains speech based on amplitude."""
        audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
        max_amplitude = np.max(np.abs(audio_data))
        return max_amplitude > self.speech_threshold        
    def start_streaming(self):
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

        print("\nStreaming audio... Press 'q' to stop.")

        while self.streaming:
            try:
                # Read raw PCM data
                data = self.stream.read(self.chunk, exception_on_overflow=False)

                # Check if the chunk contains speech
                if self.is_speech(data):
                    if not self.speech_started:
                        # Speech has just started
                        print("\n[Speech detected]")
                        self.speech_started = True
                    
                    # Reset the silence duration
                    self.last_speech_time = time.time()

                else:
                    # Check if it's been quiet for longer than the threshold
                    if self.speech_started and (time.time() - self.last_speech_time > self.silence_duration_threshold):
                        print("\n[Speech ended]")
                        self.speech_started = False
                        yield None

                        # Stop yielding after speech ends, and wait for new speech
                        while not self.is_speech(data):
                            data = self.stream.read(self.chunk, exception_on_overflow=False)
                            time.sleep(0.01)  # Small delay before checking for new speech again

                        print("\n[New speech detected]")
                        self.speech_started = True  # Resume speech detection

                # Stream the audio to the client only if speech is ongoing
                if self.speech_started:
                    yield data

            except Exception as e:
                print(f"Error streaming: {e}")
                break

            time.sleep(0.01)
     

def audio_requests(stream_file: str):
    """Generator that yields chunks of audio data to be used in streaming requests."""
    # Reads a file as bytes
    with open(stream_file, "rb") as f:
        audio_content = f.read()

    # Chunk the audio data into smaller pieces for streaming
    chunk_length = len(audio_content) // 10
    if 0:
        stream = [
            audio_content[start: start + chunk_length]
            for start in range(0, len(audio_content), chunk_length)
        ]
        for s in stream:
            print(111, len(s))
    else:
        audio_handler=AudioHandler()
        stream=[s for s in audio_handler.start_streaming()]
        for s in stream:
            print(222, len(stream))
        exit()
    # Yield each chunk as a StreamingRecognizeRequest
    for audio in stream:
        yield cloud_speech_types.StreamingRecognizeRequest(audio=audio)

def transcribe_streaming_v2(stream_file: str) -> cloud_speech_types.StreamingRecognizeResponse:
    """Transcribes audio from an audio file stream using Google Cloud Speech-to-Text API.
    Args:
        stream_file (str): Path to the local audio file to be transcribed.
            Example: "resources/audio.wav"
    Returns:
        list[cloud_speech_types.StreamingRecognizeResponse]: A list of objects.
            Each response includes the transcription results for the corresponding audio segment.
    """
    # Instantiates a client
    client = SpeechClient()

    # Prepare the recognition configuration
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

    def requests(config_request, audio_requests):
        # Yield the configuration first
        yield config_request
        # Yield the audio chunks as streaming requests
        yield from audio_requests

    # Transcribes the audio into text
    audio_handler=AudioHandler()
    responses_iterator = client.streaming_recognize(
        requests=requests(config_request,audio_requests(stream_file) )
    )
    
    responses = []
    for response in responses_iterator:
        responses.append(response)
        for result in response.results:
            print(f"Transcript: {result.alternatives[0].transcript}")

    return responses

ret = transcribe_streaming_v2('_pyspark.mp3')
pp(ret)
