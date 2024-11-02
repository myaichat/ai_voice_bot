import pyaudio
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import numpy as np
import webrtcvad
import time

# Set up the Whisper speech-to-text model
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "openai/whisper-large-v3"
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)
processor = AutoProcessor.from_pretrained(model_id)

# Audio capture settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK_DURATION_MS = 20  # Process 20 ms chunks at a time for VAD
CHUNK = int(RATE * CHUNK_DURATION_MS / 1000)  # Convert to number of samples per chunk
DURATION = 5  # Duration of each chunk to process (in seconds)

# Set up WebRTC VAD
vad = webrtcvad.Vad()
vad.set_mode(2)  # Set VAD sensitivity (higher value = more sensitive, 0-3)

# Function to calculate the audio energy (volume) to filter out low-level noise
def calculate_energy(audio_data):
    # Avoid runtime warnings by handling empty arrays or invalid values
    if audio_data.size == 0:
        return 0
    return np.sqrt(np.mean(np.square(audio_data)))

# Function to detect if the audio chunk contains speech
def is_speech(audio_chunk, energy_threshold=40):
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
    energy = calculate_energy(audio_data)
    if 0 and energy >60:
           
        print(f"Audio energy: {energy}")  # Log the audio energy for debugging

    # Only consider it speech if both VAD detects it and energy exceeds the threshold
    speech_detected = vad.is_speech(audio_chunk, RATE) and energy > energy_threshold
    #print(f"Speech detected: {speech_detected}, Energy: {energy}")
    return speech_detected

# Function to stream and convert voice to text
def stream_voice_to_text():
    audio_interface = pyaudio.PyAudio()
    
    # Open the stream for the default microphone (or WASAPI loopback for system sound)
    stream = audio_interface.open(format=FORMAT, channels=CHANNELS,
                                  rate=RATE, input=True, frames_per_buffer=CHUNK)
    
    print("Recording and transcribing...")

    try:
        while True:
            frames = []
            start_time = time.time()

            # Capture audio in chunks of CHUNK_DURATION_MS milliseconds
            for _ in range(0, int(RATE / CHUNK * DURATION)):
                data = stream.read(CHUNK)
                if 1:
                    frames.append(np.frombuffer(data, dtype=np.int16))
                else:
                    # Process each chunk for VAD and energy threshold
                    if is_speech(data):
                        #print("Speech detected!")
                        frames.append(np.frombuffer(data, dtype=np.int16))
                    else:
                        #print("No speech detected.")
                        pass

            # If no speech detected for a long time, timeout
            if time.time() - start_time > DURATION:
                print("No speech detected in this interval, skipping processing.")
                continue

            # If we have speech frames, concatenate and process
            if frames:
                # Convert frames to numpy array for processing
                audio_data = np.concatenate(frames, axis=0).astype(np.float32)
                
                # Preprocess the audio data with the processor
                inputs = processor(audio_data, return_tensors="pt", sampling_rate=RATE)
                inputs = {key: value.to(device, dtype=torch_dtype) for key, value in inputs.items()}  # Cast to appropriate dtype

                # Process the raw audio data with Whisper
                print("Transcribing...")
                with torch.no_grad():
                    generated_ids = model.generate(
                        inputs["input_features"], 
                        forced_decoder_ids=processor.get_decoder_prompt_ids(language="en")
                    )
                transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                
                # Print the transcription
                print(f"Transcription: {transcription}")
            else:
                print("No frames to process, skipping transcription.")

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        stream.stop_stream()
        stream.close()
        audio_interface.terminate()

# Start streaming voice to text
if __name__ == "__main__":
    stream_voice_to_text()
