import wave
import json
from vosk import Model, KaldiRecognizer

def transcribe_vosk(audio_file):
    model = Model("model")
    wf = wave.open(audio_file, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            print(res['text'])
    print(json.loads(rec.FinalResult())['text'])

transcribe_vosk("how_are_you.wav")
