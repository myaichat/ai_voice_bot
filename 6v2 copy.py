
import io
import os
import time
from google.cloud import speech
#from google.cloud import speech_v2 as speech
from google.cloud.speech_v2 import types
#from google.cloud.speech_v2.types import CloudSpeechClient
#from google.cloud import speech_v2

# Replace with your desired configuration.
SAMPLE_RATE_HZ = 16000
CHUNK_SIZE = 4096  # adjust based on your system performance and needs
CHUNK_INTERVAL = 100  # in milliseconds

def streaming_recognize(client, language_code="en-US"):
    """Streams audio to the Speech API and prints the results."""

    # Check for valid language code
    try:
        speech.SpeechClient().recognize(
            config=speech.RecognitionConfig(language_code=language_code),
            audio=speech.RecognitionAudio(content=""),
        )
    except Exception as e:
        print(f"Invalid language code: {language_code}. Error: {e}")
        return

    config = {
        "encoding": types.RecognitionConfig.AudioEncoding.LINEAR16,
        "sample_rate_hertz": SAMPLE_RATE_HZ,
        "language_code": language_code,
        "enable_word_time_offsets": True,  # Get word timestamps
        "enable_automatic_punctuation": True, #Enable automatic punctuation
        "model": "default",
        "interim_results": True,  # Get interim results as they are available
    }

    streaming_config = {"config": config, "interim_results": True}

    if 1:  # Use microphone input
        import sounddevice as sd
        with sd.InputStream(samplerate=SAMPLE_RATE_HZ, channels=1, blocksize=CHUNK_SIZE, dtype="int16") as stream:
            requests = (
                {"audio": {"content": stream.read(CHUNK_SIZE)} } for _ in range(1000) # adjust 1000 to longer time for longer audio input.
            )

            responses = client.streaming_recognize(requests, streaming_config)

            for response in responses:
                for result in response.results:
                    for alternative in result.alternatives:
                        print(f"Transcript: {alternative.transcript}")
                        print(f"Confidence: {alternative.confidence}")
                        print(f"Word time offsets: {alternative.words}")  #optional for checking word timing


if __name__ == "__main__":
    client = speech.SpeechClient()
    #client = speech_v2.SpeechClient()
    streaming_recognize(client)
