
import time
from google.cloud import speech_v1p1beta1 as speech
from six.moves import queue
from pprint import pprint as pp
from ai_voice_bot.handlers.GoogMicrophoneStream import GoogMicrophoneStream  
# Audio recording parameters
RATE = 24000
CHUNK = int(RATE / 10)  # 100ms
import pyaudio
import wave
import io
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types

PROJECT_ID = 'spatial-flag-427113-n0'
import os

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

def listen_print_loop(responses):
    start_time = None
    #print ("start_time: ", start_time)
    for response in responses:
        if not start_time:
            start_time = time.time()
        if not response.results:
            continue
        result = response.results[0]
        #pp(result)
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript
        is_final = result.is_final
        
        if is_final:
            print(f"{is_final} Transcript: {transcript}")
            print("Time elapsed: ", time.time() - start_time)
            start_time = None

def transcribe_streaming_audio():
    client = SpeechClient()



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


    with GoogMicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        audio_requests = (
            cloud_speech_types.StreamingRecognizeRequest(audio=audio) for audio in audio_generator
        )        
        requests = (cloud_speech_types.StreamingRecognizeRequest(audio=content)
                    for content in audio_generator)




        def requests(config: cloud_speech_types.RecognitionConfig, audio: list) -> list:
            yield config
            yield from audio

        # Transcribe the audio into text
        responses_iterator = client.streaming_recognize(
            requests=requests(config_request, audio_requests)
        )
        responses = []
        for response in responses_iterator:
            responses.append(response)
            for result in response.results:
                print(f"Transcript: {result.alternatives[0].transcript}")

        


        listen_print_loop(responses)

if __name__ == "__main__":
    transcribe_streaming_audio()
