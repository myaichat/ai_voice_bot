import assemblyai as aai
from pprint import pprint as pp 

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


def on_open(session_opened: aai.RealtimeSessionOpened):
    print("Session ID:", session_opened.session_id)


def on_data(transcript: aai.RealtimeTranscript):
    #print(333, transcript.text)
    if not transcript.text:
        return

    if isinstance(transcript, aai.RealtimeFinalTranscript):
        #print(111)
        print(777,transcript.text, end="\r\n")
        #pp(dir(transcript))
    else:
        #print(222)
        print(transcript.text, end="\r")


def on_error(error: aai.RealtimeError):
    print("An error occured:", error)


def on_close():
    print("Closing Session")


transcriber = aai.RealtimeTranscriber(
    sample_rate=16_000,
    on_data=on_data,
    on_error=on_error,
    on_open=on_open,
    on_close=on_close,
)

transcriber.connect()

microphone_stream = aai.extras.MicrophoneStream(sample_rate=16_000)
transcriber.stream(microphone_stream)

transcriber.close()