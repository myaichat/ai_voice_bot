import io
import os
import time
from google.cloud import speech
import sounddevice as sd


from google.cloud import speech_v2  # or speech_v2
client = speech_v2.SpeechClient()

import google.cloud.speech

print(google.cloud.speech.__version__)
#exit()
# Configuration
SAMPLE_RATE_HZ = 16000
CHUNK_SIZE = 4096  # Adjust based on your system performance and needs

def streaming_recognize(client, language_code="en-US"):
    """Streams audio to the Speech API and prints the results."""
    
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE_HZ,
        language_code=language_code,
        enable_word_time_offsets=True,  # Get word timestamps
        enable_automatic_punctuation=True,  # Enable automatic punctuation
        model="default"
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True  # Get interim results as they are available
    )

    with sd.InputStream(samplerate=SAMPLE_RATE_HZ, channels=1, blocksize=CHUNK_SIZE, dtype="int16") as stream:
        def request_generator():
            try:
                while True:
                    # Convert the numpy array to bytes
                    data = stream.read(CHUNK_SIZE)[0].tobytes()
                    yield speech.StreamingRecognizeRequest(audio_content=data)
            except Exception as e:
                print(f"Error generating audio chunks: {e}")

        requests = request_generator()

        try:
            responses = client.streaming_recognize(streaming_config, requests)

            for response in responses:
                for result in response.results:
                    for alternative in result.alternatives:
                        print(f"Transcript: {alternative.transcript}")
                        print(f"Confidence: {alternative.confidence}")
                        print(f"Word time offsets: {alternative.words}")  # Optional for checking word timing
        except Exception as e:
            print(f"Error in streaming recognition: {e}")

if __name__ == "__main__":
    #client = speech.SpeechClient()
    client = speech_v2.SpeechClient()
    streaming_recognize(client)
