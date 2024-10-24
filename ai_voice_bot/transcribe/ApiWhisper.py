import os, io, openai, wave
import pyaudio
import time

class ApiWhisper:
    def __init__(self):
        #self.chunk = chunk
        openai.api_key = os.environ.get("OPENAI_API_KEY")            #self.transcribe_audio()    
    def write_audio(self,  audio_chunk: bytes, file_name):  
        p = pyaudio.PyAudio()
        channels = 1  # Mono
        sample_format = pyaudio.paInt16
        rate = 16000  # Whisper expects 16kHz audio
        #file_name = "temp_audio_chunk.wav"

        # Save the audio chunk to a WAV file
        wf = wave.open(file_name, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(audio_chunk)
        wf.close()  
    def transcribe_audio(self, audio_chunk, file_name: str = "temp_audio_chunk.wav"):
        start_time = time.time()
        with open(file_name, 'rb') as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1",  # Specify the Whisper model
                file=audio_file,
                language="en"
            )
            transcription = response.text
            if 0:
                print(f"API Transcription: {transcription}")  
                ratio = len(transcription)/len(audio_chunk)
                print (f"API Ratio: {ratio}")
                #self.chunk=b'' 
            end_time = time.time()
            elapsed_time = end_time - start_time
            ratio = len(transcription)/len(audio_chunk)
            return response, elapsed_time