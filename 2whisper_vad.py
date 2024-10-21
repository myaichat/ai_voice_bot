import pyaudio
import wave
import openai
import time
import os
import numpy as np
from pyAudioAnalysis import audioBasicIO
from pyAudioAnalysis import ShortTermFeatures

# OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Initialize PyAudio
p = pyaudio.PyAudio()

# Audio stream configuration
chunk_size = 1024
sample_format = pyaudio.paInt16  # 16-bit resolution
channels = 1  # Mono
rate = 16000  # 16kHz sample rate

# Open the microphone stream
stream = p.open(format=sample_format,
                channels=channels,
                rate=rate,
                frames_per_buffer=chunk_size,
                input=True)

# Recording duration for each chunk (in seconds)
chunk_duration = 5  # 5 seconds per chunk

# Initialize variables to track total audio duration and cost
total_audio_duration = 0  # in seconds
cost_per_minute = 0.006  # Example cost per minute (update with actual Whisper API pricing)

# Function to check if the recorded audio contains speech
def is_speech_detected(audio_chunk, rate):
    # Convert raw audio to numpy array
    audio_chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
    
    # Use pyAudioAnalysis to extract short-term features and detect if speech is present
    [fs, x] = audioBasicIO.read_audio_file_from_numpy(audio_chunk_np, rate)
    F, f_names = ShortTermFeatures.feature_extraction(x, fs, 0.05*fs, 0.025*fs)
    
    # Simple energy threshold to detect if speech is present
    energy = np.mean(F[1, :])  # Energy feature
    if energy > 0.01:  # Adjust this threshold as needed
        return True
    else:
        return False

print("Recording and transcribing in real time...")

try:
    while True:
        # Start timing for each chunk processing
        start_time = time.time()
        frames = []

        # Record audio chunk
        for i in range(0, int(rate / chunk_size * chunk_duration)):
            data = stream.read(chunk_size)
            frames.append(data)

        # Combine frames into a single chunk
        audio_chunk = b''.join(frames)

        # Check if the audio chunk contains speech
        if is_speech_detected(audio_chunk, rate):
            print("Speech detected, processing...")

            # Update total audio duration (in seconds)
            total_audio_duration += chunk_duration

            # Save the audio chunk to a temporary file
            file_name = "temp_audio_chunk.wav"
            wf = wave.open(file_name, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(rate)
            wf.writeframes(audio_chunk)
            wf.close()

            # Send the chunk to Whisper API for transcription
            with open(file_name, 'rb') as audio_file:
                response = openai.audio.transcriptions.create(
                    model="whisper-1",  # Specify the Whisper model
                    file=audio_file
                )
                transcription = response.text
                print(f"Transcription: {transcription}")

            # Calculate estimated cost based on total audio duration
            estimated_cost = (total_audio_duration / 60) * cost_per_minute
            print(f"Total audio duration: {total_audio_duration / 60:.2f} minutes")
            print(f"Estimated cost: ${estimated_cost:.4f}")
        else:
            print("No speech detected, skipping...")

        # Add delay to simulate real-time processing (based on chunk duration)
        time.sleep(chunk_duration)

except KeyboardInterrupt:
    # Stop the audio stream
    print("Stopping...")
    stream.stop_stream()
    stream.close()
    p.terminate()
