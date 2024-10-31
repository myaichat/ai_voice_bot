import assemblyai as aai
import sounddevice as sd
import requests
import numpy as np
import wave
import os
import time
from pprint import pprint as pp 

# Set the API key for AssemblyAI
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Audio capture settings
sample_rate = 16000
channels = 1
chunk_duration = 5  # Duration of each chunk in seconds
chunk_size = chunk_duration * sample_rate

# Upload the audio chunk to AssemblyAI
def upload_audio_chunk(chunk_path):
    headers = {'authorization': aai.settings.api_key}
    with open(chunk_path, 'rb') as f:
        response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, files={'file': f})
        response.raise_for_status()
        return response.json()['upload_url']

# Submit uploaded audio chunk for transcription
def transcribe_audio(upload_url):
    headers = {'authorization': aai.settings.api_key}
    transcript_request = {
        'audio_url': upload_url
    }
    response = requests.post('https://api.assemblyai.com/v2/transcript', json=transcript_request, headers=headers)
    response.raise_for_status()
    pp(response.json())
    return response.json()['id']

# Function to record audio and save to a WAV file
def record_and_save_chunk(filename, duration=chunk_duration):
    print("Recording...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='int16')
    sd.wait()  # Wait until the recording is finished

    # Save the recorded chunk as a WAV file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 2 bytes per sample (16 bits)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

# Periodically capture microphone data and upload it
def stream_and_upload_microphone_data():
    chunk_counter = 0
    while True:
        chunk_filename = f'chunk_{chunk_counter}.wav'
        record_and_save_chunk(chunk_filename)

        # Upload the chunk to AssemblyAI
        upload_url = upload_audio_chunk(chunk_filename)
        print(f"Uploaded chunk {chunk_counter}, URL: {upload_url}")

        # Request transcription for the uploaded chunk
        transcript_id = transcribe_audio(upload_url)
        print(f"Transcription requested, Transcript ID: {transcript_id}")

        # Remove the chunk file after uploading
        os.remove(chunk_filename)

        # Increment chunk counter and add a small delay between recordings
        chunk_counter += 1
        time.sleep(1)

# Start streaming microphone data
stream_and_upload_microphone_data()
