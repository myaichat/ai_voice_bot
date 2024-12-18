
import pyaudio
import speech_recognition as sr
import time
class GooTranscribe:
    def __init__(self):
        #self.chunk = chunk    
        pass
    def write_audio(self, audio_chunk: bytes, file_name):
        import os, io, openai, wave
        
        p = pyaudio.PyAudio()
        channels = 1  # Mono
        sample_format = pyaudio.paInt16
        rate = 24000
        #file_name = "temp_audio_chunk.wav"
        wf = wave.open(file_name, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(audio_chunk)
        wf.close()

    def transcribe_audio(self, audio_chunk, file_name):
        start_time = time.time()
        recognizer = sr.Recognizer()
        # Open the saved audio file for transcription
        with sr.AudioFile(file_name) as source:
            audio = recognizer.record(source)
        try:
            # Use Google Speech Recognition to transcribe the audio
            text = recognizer.recognize_google(audio)
            end_time = time.time()
            elapsed_time = end_time - start_time            
            ratio = len(text)/len(audio_chunk)
            return text, elapsed_time, ratio
            if 0:
                print(f"GOO Transcription: {text}")
                ratio = len(text)/len(audio_chunk)
                print (f"GOO Ratio: {ratio}")              
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand the audio.")
            
            return None, time.time() - start_time, 0
            return 
        except sr.RequestError as e:
            print(f"Could not request results from the speech recognition service; {e}")