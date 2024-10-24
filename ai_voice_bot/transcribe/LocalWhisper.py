import pyaudio
import wave
import os, time
from pprint import pprint as pp 
import numpy as np
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from transformers import  AutoTokenizer
class LocalWhisper():
    def __init__(self):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model_id = "openai/whisper-large-v3"
        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, torch_dtype=self.torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
        )
        model.to(self.device)
        processor = AutoProcessor.from_pretrained(model_id)

        # Set up the speech recognition pipeline
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=self.torch_dtype,
            device=self.device
            
        )

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
    def local_transcribe_audio(self, audio_chunk, file_name="temp_audio_chunk.wav"):

        start_time = time.time()
        # Read the audio file and convert it to the format expected by the pipeline
        with wave.open(file_name, 'rb') as wav_file:
            wav_data = wav_file.readframes(wav_file.getnframes())
            audio_array = np.frombuffer(wav_data, dtype=np.int16).astype(np.float32) / 32768.0

        # Transcribe the audio using the Whisper pipeline
        #forced_decoder_ids = self.pipe.model.config.forced_decoder_ids = [[2, self.pipe.tokenizer.lang_code_to_id["en"]]]

        result = self.pipe(audio_array,generate_kwargs = {"task":"transcribe", "language":"<|en|>"} , return_timestamps=True)        
        #result = self.pipe(audio_array)
        transcription = result["text"]
        #pp(result)
        if 0:
            print(f"LOCAL Transcription: {transcription}")
            ratio = len(transcription)/len(audio_chunk)
            print (f"LOCAl Ratio: {ratio}")        

        # Clear the audio chunk
        #self.chunk = b''

        # Optionally, remove the temporary file
        #os.remove(file_name)
        ratio = len(transcription)/len(audio_chunk)
        return result, time.time() - start_time, ratio