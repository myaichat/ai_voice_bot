import os
import wave
import pyaudio
import speech_recognition as sr
import openai

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Audio recording parameters
channels = 1
sample_format = pyaudio.paInt16
rate = 24000
chunk_size = 1024
file_name = "temp_audio_chunk.wav"

def record_audio_in_chunks(duration=10):
    """
    Record audio in chunks and save to a WAV file.
    Returns the filename of the recorded audio.
    """
    p = pyaudio.PyAudio()

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=rate,
                    frames_per_buffer=chunk_size,
                    input=True)

    print("Recording... Speak now!")

    frames = []
    for _ in range(0, int(rate / chunk_size * duration)):
        data = stream.read(chunk_size)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(file_name, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"Audio recorded and saved as {file_name}")
    return file_name

def transcribe_audio_google(file_name):
    """
    Transcribe audio using Google Speech Recognition.
    """
    recognizer = sr.Recognizer()

    # Load the audio file
    with sr.AudioFile(file_name) as source:
        audio = recognizer.record(source)

    try:
        # Use Google Speech Recognition to transcribe the audio
        text = recognizer.recognize_google(audio)
        print(f"Google Transcription: {text}")
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio.")
    except sr.RequestError as e:
        print(f"Google Speech Recognition request error: {e}")

def transcribe_audio_openai(file_name):
    """
    Transcribe audio using OpenAI's Whisper API.
    """
    with open(file_name, 'rb') as audio_file:
        try:
            # Use OpenAI Whisper API to transcribe the audio
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            print(f"OpenAI Transcription: {transcript['text']}")
            return transcript['text']
        except Exception as e:
            print(f"OpenAI Whisper API request error: {e}")

def transcribe_audio_real_time(duration=10):
    """
    Record and transcribe audio in real-time using Google Speech Recognition.
    """
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            print("Listening... Speak now!")

            # Record audio in real-time
            audio = recognizer.listen(source, timeout=duration)

            # Use Google Speech Recognition to transcribe the audio
            text = recognizer.recognize_google(audio)
            print(f"Real-Time Transcription: {text}")
            return text
    except sr.UnknownValueError:
        print("Real-time transcription failed. Could not understand the audio.")
    except sr.RequestError as e:
        print(f"Real-time transcription service error: {e}")

if __name__ == "__main__":
    # Option 1: Record and transcribe with Google Speech Recognition
    audio_file = record_audio_in_chunks(duration=10)
    google_transcription = transcribe_audio_google(audio_file)

    # Option 2: Use OpenAI Whisper API for transcription
    #openai_transcription = transcribe_audio_openai(audio_file)

    # Option 3: Real-time transcription (without saving audio to file)
    real_time_transcription = transcribe_audio_real_time(duration=10)
