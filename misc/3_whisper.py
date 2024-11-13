import pyaudio
import wave
import openai
import time
import os
import webrtcvad
import numpy as np

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

# Initialize WebRTC VAD with higher mode (less sensitive to noise)
vad = webrtcvad.Vad()
vad.set_mode(2)  # Mode 2 or 3 is less sensitive to noise

# Function to check if a chunk contains speech using WebRTC VAD
def is_speech_detected(audio_chunk, rate):
    # WebRTC VAD expects audio in 10, 20, or 30 ms chunks
    frame_duration_ms = 30  # 30 ms frames
    num_bytes_per_frame = int(rate * 2 * (frame_duration_ms / 1000))  # 2 bytes per sample for 16-bit audio

    # Process each frame to check for speech
    for i in range(0, len(audio_chunk), num_bytes_per_frame):
        frame = audio_chunk[i:i + num_bytes_per_frame]
        if len(frame) < num_bytes_per_frame:
            break  # Ignore incomplete frames at the end of the audio chunk
        if vad.is_speech(frame, rate):
            return True
    return False

# Function to compute the energy of the audio chunk
def compute_energy(audio_chunk):
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
    energy = np.sqrt(np.mean(audio_data**2))  # RMS energy
    return energy

# Energy threshold (lower it for better sensitivity)
energy_threshold = 10  # Lowered threshold for testing

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

        # Compute the energy and print it for debugging
        energy = compute_energy(audio_chunk)
        print(f"Computed energy: {energy}")

        # Check if the audio chunk has sufficient energy
        if energy < energy_threshold:
            print("Low energy sound detected, skipping...")
            continue

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
                print(f"\t\tTranscription: {transcription}")

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


"""
Recording and transcribing in real time...
Computed energy: 40.29548422812022
Speech detected, processing...
                Transcription: What are new Python features?
Total audio duration: 0.17 minutes
Estimated cost: $0.0010
Stopping...
"""