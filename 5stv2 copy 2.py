import os
from pprint import pprint as pp
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types

PROJECT_ID = 'spatial-flag-427113-n0'

def audio_requests(stream_file: str):
    """Generator that yields chunks of audio data to be used in streaming requests."""
    # Reads a file as bytes
    with open(stream_file, "rb") as f:
        audio_content = f.read()

    # Chunk the audio data into smaller pieces for streaming
    chunk_length = len(audio_content) // 10
    stream = [
        audio_content[start: start + chunk_length]
        for start in range(0, len(audio_content), chunk_length)
    ]

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
    responses_iterator = client.streaming_recognize(
        requests=requests(config_request, audio_requests(stream_file))
    )
    
    responses = []
    for response in responses_iterator:
        responses.append(response)
        for result in response.results:
            print(f"Transcript: {result.alternatives[0].transcript}")

    return responses

ret = transcribe_streaming_v2('_pyspark.mp3')
pp(ret)
