import os
import wave
import pyaudio
import speech_recognition as sr

def record_audio(file_name="temp_audio_chunk.wav"):
    # Audio recording parameters
    channels = 1  # Mono
    sample_format = pyaudio.paInt16  # 16-bit resolution
    rate = 24000  # Sampling rate
    chunk_size = 1024  # Chunk size

    # Create a PyAudio object
    p = pyaudio.PyAudio()

    # Open a stream
    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=rate,
                    frames_per_buffer=chunk_size,
                    input=True)

    print("Recording... Speak now!")

    # Read the audio data and store it in a list
    frames = []

    # Record audio for 5 seconds
    for i in range(0, int(rate / chunk_size * 5)):
        data = stream.read(chunk_size)
        frames.append(data)

    # Stop and close the stream
    stream.stop_stream()
    stream.close()

    # Terminate the PyAudio object
    p.terminate()

    # Save the recorded audio as a .wav file
    wf = wave.open(file_name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"Audio recorded and saved as {file_name}")

    return file_name

def transcribe_audio(file_name):
    recognizer = sr.Recognizer()

    # Open the saved audio file for transcription
    with sr.AudioFile(file_name) as source:
        audio = recognizer.record(source)

    try:
        # Use Google Speech Recognition to transcribe the audio
        text = recognizer.recognize_google(audio)
        print(f"Transcription: {text}")
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from the speech recognition service; {e}")

if __name__ == "__main__":
    # Record the audio
    audio_file = record_audio()

    # Transcribe the recorded audio
    transcribe_audio(audio_file)
