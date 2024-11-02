import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import click

@click.command()
@click.option('--in', 'input_file', required=True, type=click.Path(exists=True), help="Path to the input audio file")
@click.option('--out', 'output_file', required=True, type=str, help="Path to the output text file")
def main(input_file, output_file):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model_id = "openai/whisper-large-v3"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True, cache_dir="cache"
    )
    model.to(device)
    processor = AutoProcessor.from_pretrained(model_id)    
    while True:
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=device
        )

        # Process the input audio file
        result = pipe(input_file)
        transcription = result["text"]
        
        # Write the transcription to the output file
        with open(output_file, "w") as f:
            f.write(transcription)
        print(f"Transcription saved to {output_file}")
        print(transcription)

if __name__ == "__main__":

 
    main()

 
