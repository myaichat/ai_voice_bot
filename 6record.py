import pyaudio
import wave
from pydub import AudioSegment

# Settings
FORMAT = pyaudio.paInt16  # Audio format (16-bit)
CHANNELS = 1              # Mono audio
RATE = 44100              # Sample rate (44.1 kHz)
CHUNK = 1024              # Buffer size
RECORD_SECONDS = 5       # Duration of the recording
WAVE_OUTPUT_FILENAME = "output.wav"
MP3_OUTPUT_FILENAME = "output.mp3"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Start recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

print("Recording...")

frames = []

# Capture the audio data in chunks
for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Finished recording.")

# Stop and close the stream
stream.stop_stream()
stream.close()
audio.terminate()

# Save the recorded data as a WAV file
wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

# Convert the WAV file to MP3 using pydub
sound = AudioSegment.from_wav(WAVE_OUTPUT_FILENAME)
sound.export(MP3_OUTPUT_FILENAME, format="mp3")

print(f"File saved as {MP3_OUTPUT_FILENAME}")
