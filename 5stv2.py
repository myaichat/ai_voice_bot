import pyaudio
import wave
import io, time
import numpy as np
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech as cloud_speech_types
speech_threshold = 500 
PROJECT_ID = 'spatial-flag-427113-n0'

def is_speech( audio_chunk: bytes) -> bool:
    """Determine if an audio chunk contains speech based on amplitude."""
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
    max_amplitude = np.max(np.abs(audio_data))
    return max_amplitude > speech_threshold

def record_audio_to_memory() -> bytes:
   
    """Records audio and returns the audio data as bytes in WAV format."""
    # Settings
    FORMAT = pyaudio.paInt16  # Audio format (16-bit)
    CHANNELS = 1              # Mono audio
    RATE = 14400              # Sample rate (44.1 kHz)
    CHUNK = 1024*2             # Buffer size
    RECORD_SECONDS = 5        # Duration of the recording

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Start recording
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Recording...")
    
    speech_started=False

    silence_duration_threshold = 1.0
    frames = []
    tframes=[]
    streaming=True
    last_speech_time = None
    # Capture the audio data in chunks
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        if 1:
            if is_speech(data):
                if not speech_started:    
                    speech_started = True
                    last_speech_time = time.time()
                else:
                    if speech_started and (time.time() - last_speech_time > silence_duration_threshold):
                        print("speech stopped")
                        speech_started = False
                        streaming=False
                if speech_started:
                    print("speech")
                    tframes.append(data)

    

    print("Finished recording.")
    print(len(frames), len(tframes  ))  

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Apply wave transformations and write the audio data to memory
    output = io.BytesIO()
    wf = wave.open(output, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # Get the WAV data from memory
    wav_data = output.getvalue()
    output.close()

    # Apply wave transformations and write the audio data to memory
    output = io.BytesIO()
    wf = wave.open(output, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(tframes))
    wf.close()

    # Get the WAV data from memory
    wav_data2 = output.getvalue()
    output.close()

    return wav_data, wav_data2


def transcribe_streaming_v2(audio_data: bytes) -> cloud_speech_types.StreamingRecognizeResponse:
    """Transcribes in-memory audio data using Google Cloud Speech-to-Text API."""
    client = SpeechClient()

    # Split the audio data into smaller chunks for streaming
    chunk_length = len(audio_data) // 10
    print(111, chunk_length)    
    stream = [audio_data[start:start + chunk_length] for start in range(0, len(audio_data), chunk_length)]
    audio_requests = (
        cloud_speech_types.StreamingRecognizeRequest(audio=audio) for audio in stream
    )

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

    return responses


# Record audio directly into memory and transcribe without saving to a file
audio_data, tdata = record_audio_to_memory()
ret = transcribe_streaming_v2(tdata)

# Print transcription results
from pprint import pprint
pprint(ret)
