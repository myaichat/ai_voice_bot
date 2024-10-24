import requests
import time
import assemblyai as aai
from pprint import pprint as pp
aai.settings.api_key = "6a5baf29628a4325947088a4fb6343ac"

# Function to check the transcription status
def check_transcription_status(transcript_id):
    headers = {'authorization': aai.settings.api_key}
    response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
    response.raise_for_status()
    pp(response.json())
    return response.json()

# Function to continuously check the status until transcription is completed
def get_transcription(transcript_id):
    while True:
        result = check_transcription_status(transcript_id)
        status = result['status']
        
        if status == 'completed':
            print("Transcription completed. Transcript text:")
            print(result['text'])
            break
        elif status == 'failed':
            print("Transcription failed.")
            break
        else:
            print(f"Transcription is {status}... Checking again in 5 seconds.")
            time.sleep(5)  # Wait 5 seconds before checking again

# Example usage to retrieve transcription
transcript_id = '09a83de6-e871-4743-9518-b84162baa4d8'  # Replace with your actual transcript ID
get_transcription(transcript_id)
