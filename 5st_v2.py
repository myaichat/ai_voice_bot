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


from google.cloud import speech_v1 as speech
from google.cloud.speech_v1 import types
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
            
client = speech.SpeechClient()

recognition_config = types.RecognitionConfig(
    encoding=types.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=RATE,
    language_code="en-US"
)
streaming_config = types.StreamingRecognitionConfig(config=recognition_config)

def transcribe_streaming_v1():
    with GoogMicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()

        requests = (
            types.StreamingRecognizeRequest(audio_content=audio_chunk)
            for audio_chunk in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        listen_print_loop(responses)

if __name__ == "__main__":
    transcribe_streaming_v1()
