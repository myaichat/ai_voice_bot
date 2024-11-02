import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import librosa 

def setup_whisper_model(model_id="openai/whisper-large-v3", cache_dir="cache"):
    # Set device and dtype
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    
    # Load processor first
    processor = AutoProcessor.from_pretrained(model_id)
    
    # Load the model with proper configuration
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
        use_safetensors=True,
        cache_dir=cache_dir,
    )
    model.to(device)
    
    # Create pipeline without conflicting configurations
    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
        model_kwargs={
            "use_flash_attention_2": False,
        },
        generate_kwargs={
            "task": "transcribe",
            "language": "en",
        }
    )
    
    return pipe, processor, model

# Function to transcribe audio with the setup pipeline
def transcribe_audio(pipe, processor, audio_path):
    # Load and preprocess the audio file
    audio_input, sampling_rate = librosa.load(audio_path, sr=16000)
    
    # Process with the pipeline directly
    # The pipeline handles the preprocessing internally
    result = pipe(
        audio_input,
        batch_size=32,  # Adjust based on your GPU memory
        return_timestamps=True  # Optional, remove if you don't need timestamps
    )
    
    return result

# Example usage
pipe, processor, model = setup_whisper_model()
audio_path = "_pyspark_2.mp3"
transcription = transcribe_audio(pipe, processor, audio_path)
print(transcription['text'])  # The transcribed text will be in the 'text' field