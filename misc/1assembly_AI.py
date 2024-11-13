audio_file_path = "_pyspark_2.mp3" 

import requests
import assemblyai as aai
import time
from pprint import pprint as pp

# Set the API key
aai.settings.api_key = "6a5baf29628a4325947088a4fb6343ac"

# Upload the local audio file using requests

transcriber = aai.Transcriber()
transcript = transcriber.transcribe(audio_file_path)
#pp (dir(transcript))
print(transcript.text)    
exit()

headers = {
    'authorization': aai.settings.api_key,
}

# Specify the correct MIME type for a WAV file
with open(audio_file_path, 'rb') as f:
    files = {
        'file': (audio_file_path, f, 'audio/wav')
    }
    upload_response = requests.post(
        'https://api.assemblyai.com/v2/upload',
        headers=headers,
        files=files
    )

# Check if the upload was successful
if upload_response.status_code != 200:
    print(f"File upload failed: {upload_response.status_code} - {upload_response.text}")
    exit(1)

# Get the upload URL from the response
upload_url = upload_response.json()['upload_url']

# Initialize the Transcriber
transcriber = aai.Transcriber()

# Transcribe the uploaded file
config = aai.TranscriptionConfig(speaker_labels=True)
transcript = transcriber.transcribe(upload_url, config)

# Wait for the transcription to complete
while transcript.status not in [aai.TranscriptStatus.completed, aai.TranscriptStatus.error]:
    time.sleep(5)  # Check every 5 seconds
    transcript = transcriber.get_transcript(transcript.id)  # Get the latest status

# Check if transcription was successful
if transcript.status == aai.TranscriptStatus.error:
    print(f"Transcription failed: {transcript.error}")
    exit(1)

# Output the transcription result
print(transcript.text)

# Print each speaker's utterances
for utterance in transcript.utterances:
    print(f"Speaker {utterance.speaker}: {utterance.text}")
