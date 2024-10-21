import pyaudio
import wave
import openai
import time
import os

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

        elapsed_time = time.time() - start_time
        print(f"Elapsed time for input: {elapsed_time:.2f} seconds")
        
        # Update total audio duration (in seconds)
        total_audio_duration += chunk_duration

        start_time = time.time()
        # Save the audio chunk to a temporary file
        file_name = "temp_audio_chunk.wav"
        wf = wave.open(file_name, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        elapsed_time = time.time() - start_time
        print(f"Elapsed time for file: {elapsed_time:.2f} seconds")
        
        # Send the chunk to Whisper API for transcription
        start_time = time.time()
        with open(file_name, 'rb') as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1",  # Specify the Whisper model
                file=audio_file
            )
            transcription = response.text
            print(f"Transcription: {transcription}")

        # Calculate and print elapsed time for transcription
        elapsed_time = time.time() - start_time
        print(f"Elapsed time for transcript: {elapsed_time:.2f} seconds")

        # Calculate estimated cost based on total audio duration
        estimated_cost = (total_audio_duration / 60) * cost_per_minute
        print(f"Total audio duration: {total_audio_duration / 60:.2f} minutes")
        print(f"Estimated cost: ${estimated_cost:.4f}")

        # Add delay to simulate real-time processing (based on chunk duration)
        time.sleep(chunk_duration)

except KeyboardInterrupt:
    # Stop the audio stream
    print("Stopping...")
    stream.stop_stream()
    stream.close()
    p.terminate()


r"""
(myenv) C:\Users\alex_\aichat\voice_bot>python 1c.py
Recording and transcribing in real time...
Elapsed time for input: 5.03 seconds
Elapsed time for file: 0.00 seconds
Transcription: Hey, how are you?
Elapsed time for transcript: 2.19 seconds
Total audio duration: 0.08 minutes
Estimated cost: $0.0005
Elapsed time for input: 4.81 seconds
Elapsed time for file: 0.00 seconds
Transcription: .
Elapsed time for transcript: 1.86 seconds
Total audio duration: 0.17 minutes
Estimated cost: $0.0010
Stopping...

"""