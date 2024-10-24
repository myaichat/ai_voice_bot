
import time
from google.cloud import speech_v1p1beta1 as speech
from six.moves import queue
from pprint import pprint as pp
from ai_voice_bot.handlers.GoogMicrophoneStream import GoogMicrophoneStream  
# Audio recording parameters
RATE = 24000
CHUNK = int(RATE / 10)  # 100ms


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
    client = speech.SpeechClient()

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True,
    )

    with GoogMicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(config=streaming_config, requests=requests)

        listen_print_loop(responses)

if __name__ == "__main__":
    transcribe_streaming_audio()
