import io
import openai
from pydub import AudioSegment

fname = "file.mp3"
audio = AudioSegment.from_file(fname, format="mp3")
# only use first 5sec
audio = audio[:5000]

buffer = io.BytesIO()
# you need to set the name with the extension
buffer.name = fname
audio.export(buffer, format="mp3")

transcript = openai.Audio.transcribe("whisper-1", buffer)


if 0:


    @strawberry.type
    class Mutation:
        @strawberry.mutation
        async def transcribe(self, audio_file: Upload) -> str:
            audio_data = await audio_file.read()
            buffer = io.BytesIO(audio_data)
            buffer.name = "file.mp3"  # this is the important line
            transcription = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=buffer,
            )
            return transcription.text