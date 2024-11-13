import os
import time
from google.cloud import speech_v1p1beta1 as speech
from six.moves import queue
from ai_voice_bot.handlers.GoogMicrophoneStream import GoogMicrophoneStream  
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types

# Audio recording parameters
RATE = 14000
CHUNK = int(RATE / 10)  # 100ms

PROJECT_ID='spatial-flag-427113-n0'

def listen_print_loop(responses):
    """Iterates through server responses and prints them."""
    start_time = None
    for response in responses:
        if not start_time:
            start_time = time.time()
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        is_final = result.is_final

        if is_final:
            print(f"{is_final} Transcript: {transcript}")
            print("Time elapsed: ", time.time() - start_time)
            start_time = None

def transcribe_streaming_v2():
    """Streams microphone input to the Google Cloud Speech API for real-time transcription."""
    # Instantiates a client
    client = SpeechClient()
    
    # Configuration for the speech recognition
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
    
    # Generator function to create requests
    def request_generator(audio_stream):
        # First request sends the config
        yield cloud_speech_types.StreamingRecognizeRequest(streaming_config=config_request)
        # Following requests send the audio data
        for audio_chunk in audio_stream:
            yield cloud_speech_types.StreamingRecognizeRequest(audio=audio_chunk)

    # Initialize microphone stream
    with GoogMicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        
        # Call the streaming recognition API
        responses_iterator = client.streaming_recognize(requests=request_generator(audio_generator))

        # Handle the responses
        listen_print_loop(responses_iterator)

if __name__ == "__main__":
    transcribe_streaming_v2()
