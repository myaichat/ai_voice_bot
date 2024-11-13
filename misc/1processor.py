import librosa

from transformers import WhisperProcessor, WhisperForConditionalGeneration
from datasets import Audio, load_dataset

MAX_INPUT_LENGTH = 16000 * 30

# load model and processor
processor = WhisperProcessor.from_pretrained("openai/whisper-small")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")
forced_decoder_ids = processor.get_decoder_prompt_ids(language="french", task="transcribe")

# load audio sample
sample, sr = librosa.load("audio.WAV", sr=16000)
sample_batch = [sample[i:i + MAX_INPUT_LENGTH] for i in range(0, len(sample), MAX_INPUT_LENGTH)]
input_features = processor(sample_batch, sampling_rate=sr, return_tensors="pt").input_features

# generate token ids
predicted_ids = model.generate(input_features, forced_decoder_ids=forced_decoder_ids)
# decode token ids to text
transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
print(transcription)