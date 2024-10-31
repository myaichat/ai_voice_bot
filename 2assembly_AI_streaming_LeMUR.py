import assemblyai as aai

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

transcriber = aai.Transcriber()

# Define the audio file to stream
audio_file_url = "https://assembly.ai/sports_injuries.mp3"

# Initialize a streaming session
stream = transcriber.stream()

# Start streaming the audio from a publicly-accessible URL
stream.start(audio_file_url)

# Process the transcription results as they come in
for transcript in stream.get_transcript():
    print(f"Partial Transcript: {transcript['text']}")

# Finish and close the stream after the transcription is done
stream.finish()

# Now, let's provide a summary of the complete transcript
prompt = "Answer the question."

# Assuming you have the final transcript stored in a variable after the streaming:
complete_transcript = stream.get_full_transcript()

# Generate a summary using the Lemur task model
result = complete_transcript.lemur.task(
    prompt, final_model=aai.LemurModel.claude3_5_sonnet
)

print(result.response)
