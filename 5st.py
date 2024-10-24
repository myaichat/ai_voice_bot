import time
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types
from ai_voice_bot.handlers.GoogMicrophoneStream import GoogMicrophoneStream  

# Audio recording parameters
RATE = 24000
CHUNK = int(RATE / 10)  # 100ms

PROJECT_ID = 'spatial-flag-427113-n0'
RECOGNIZER_ID = 'your-recognizer-id'  # Replace with your actual recognizer ID

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
    client = SpeechClient()

    # Configure recognizer and streaming
    recognition_config = cloud_speech_types.RecognitionConfig(
        auto_decoding_config=cloud_speech_types.AutoDetectDecodingConfig(),  # Automatic decoding
        language_codes=["en-US"],  # Language code for English (US)
        model="long",  # Model for long-form audio
    )

    streaming_config = cloud_speech_types.StreamingRecognitionConfig(
        config=recognition_config
    )

    config_request = cloud_speech_types.StreamingRecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        streaming_config=streaming_config,
    )

    def request_generator(audio_stream, max_chunks=30):
        # Send config first
        yield config_request
        # Send audio stream after config
        for aid, audio_chunk in enumerate(audio_stream):
            print(f"Chunk {aid}, Length: {len(audio_chunk)}")
            if aid >= max_chunks:
                print("Reached max chunks, stopping the stream.")
                break  # Stop after max_chunks
            yield cloud_speech_types.StreamingRecognizeRequest(audio=audio_chunk)

    with GoogMicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()

        # Stream recognition responses
        responses = client.streaming_recognize(requests=request_generator(audio_generator))

        # Process responses
        listen_print_loop(responses)

if __name__ == "__main__":
    transcribe_streaming_v2()
