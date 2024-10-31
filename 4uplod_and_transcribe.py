import assemblyai as aai
import requests

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

# Upload the audio file to AssemblyAI
def upload_audio(file_path):
    headers = {'authorization': aai.settings.api_key}
    with open(file_path, 'rb') as f:
        response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, files={'file': f})
        response.raise_for_status()  # Ensure the request was successful
        return response.json()['upload_url']

# Submit the uploaded audio URL for transcription
def transcribe_audio(upload_url):
    headers = {'authorization': aai.settings.api_key}
    transcript_request = {
        'audio_url': upload_url
    }
    response = requests.post('https://api.assemblyai.com/v2/transcript', json=transcript_request, headers=headers)
    response.raise_for_status()
    return response.json()['id']

# Check transcription status
def check_transcription_status(transcript_id):
    headers = {'authorization': aai.settings.api_key}
    response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
    response.raise_for_status()
    return response.json()

# Upload the audio file
audio_file_path = '_pyspark_2.mp3'  # Replace this with your audio file path
upload_url = upload_audio(audio_file_path)
print(f"Audio uploaded successfully: {upload_url}")

# Request transcription
transcript_id = transcribe_audio(upload_url)
print(f"Transcription requested, Transcript ID: {transcript_id}")

# Polling the transcription until it's ready
import time
while True:
    transcription_result = check_transcription_status(transcript_id)
    if transcription_result['status'] == 'completed':
        print("Transcription completed:", transcription_result['text'])
        break
    elif transcription_result['status'] == 'failed':
        print("Transcription failed.")
        break
    else:
        print("Transcription is processing...")
        time.sleep(5)  # Wait a few seconds before checking again
