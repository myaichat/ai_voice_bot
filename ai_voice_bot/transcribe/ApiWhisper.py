import os, io, openai, wave
import pyaudio
import time

class ApiWhisper:
    def __init__(self):
        #self.chunk = chunk
        pass
        #self.transcribe_audio()    
    def write_audio(self,  audio_chunk: bytes, file_name: str = "temp_audio_chunk.wav"):
                
        openai.api_key = os.environ.get("OPENAI_API_KEY")            
        p = pyaudio.PyAudio()
        channels = 1  # Mono
        sample_format = pyaudio.paInt16
        rate = 24000
        file_name = "temp_audio_chunk.wav"
        wf = wave.open(file_name, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(audio_chunk)
        wf.close()
    def transcribe_audio(self, audio_chunk, file_name: str = "temp_audio_chunk.wav"):

        with open(file_name, 'rb') as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1",  # Specify the Whisper model
                file=audio_file,
                language="en"
            )
            transcription = response.text
            print(f"API Transcription: {transcription}")  
            ratio = len(transcription)/len(audio_chunk)
            print (f"API Ratio: {ratio}")
            #self.chunk=b''  