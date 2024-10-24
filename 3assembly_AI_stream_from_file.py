import assemblyai as aai
import soundfile as sf  # Library to read audio files
from pprint import pprint as pp

aai.settings.api_key = "6a5baf29628a4325947088a4fb6343ac"

def on_open(session_opened: aai.RealtimeSessionOpened):
    print("Session ID:", session_opened.session_id)

def on_data(transcript: aai.RealtimeTranscript):
    if not transcript.text:
        return

    if isinstance(transcript, aai.RealtimeFinalTranscript):
        print("Final Transcript:", transcript.text)
    else:
        print("Interim Transcript:", transcript.text)

def on_error(error: aai.RealtimeError):
    print("An error occurred:", error)

def on_close():
    print("Closing session")

# Custom streamer for audio file input
def stream_audio_file(file_path, transcriber):
    # Open the audio file
    with sf.SoundFile(file_path, 'r') as audio_file:
        # Read the audio file in chunks
        while True:
            data = audio_file.read(4000, dtype='int16')  # Adjust chunk size based on your file/sample rate
            if len(data) == 0:
                break
            transcriber.stream(data.tobytes())  # Send the audio data to the transcriber in real-time chunks

# Initialize the transcriber
transcriber = aai.RealtimeTranscriber(
    sample_rate=16_000,
    on_data=on_data,
    on_error=on_error,
    on_open=on_open,
    on_close=on_close,
)

transcriber.connect()

# Stream audio from a file
audio_file_path = '_pyspark_2.mp3'  # Replace this with the path to your audio file
stream_audio_file(audio_file_path, transcriber)

transcriber.close()
