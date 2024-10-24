from pydub import AudioSegment

# Load the audio file to inspect and ensure it's a valid file
try:
    audio_file_path = "_how_are_you_fixed.wav"
    audio = AudioSegment.from_file(audio_file_path)
    print(f"File loaded successfully. Duration: {len(audio) / 1000} seconds")
except Exception as e:
    print(f"Failed to load audio file: {e}")