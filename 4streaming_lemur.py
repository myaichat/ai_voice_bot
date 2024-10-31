import assemblyai as aai

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

def on_open(session_opened: aai.RealtimeSessionOpened):
  "This function is called when the connection has been established."

  print("Session ID:", session_opened.session_id)

def on_data(transcript: aai.RealtimeTranscript):
  "This function is called when a new transcript has been received."

  global conversation_data

  if not transcript.text:
    return

  if isinstance(transcript, aai.RealtimeFinalTranscript):
    print(transcript.text, end="\r\n")
    conversation_data += f"{transcript.text} \n"
    if 1:
        
        print("Closing Session")
        result = aai.Lemur().task(
            """Answer this interviewquestion.""",
            input_text=conversation_data,
            final_model= aai.LemurModel.claude3_5_sonnet
        )

        print(result.response)

  else:
    print(888,transcript.text, end="\r")

def on_error(error: aai.RealtimeError):
  "This function is called when the connection has been closed."

  print("An error occured:", error)

def on_close():
  "This function is called when the connection has been closed."
  global conversation_data
  print("Closing Session")
  result = aai.Lemur().task(
    "You are a helpful coach. Provide an analysis of the transcript "
    "and offer areas to improve with exact quotes. Include no preamble. "
    "Start with an overall summary then get into the examples with feedback.",
    input_text=conversation_data
  )

  print(result.response)

# Create the Streaming Speech-to-Text transcriber
transcriber = aai.RealtimeTranscriber(
  on_data=on_data,
  on_error=on_error,
  sample_rate=44_100,
  on_open=on_open, # optional
  on_close=on_close, # optional
)

conversation_data = ""

# Start the connection
transcriber.connect()

# Open a microphone stream
microphone_stream = aai.extras.MicrophoneStream()

# Press CTRL+C to abort
transcriber.stream(microphone_stream)

transcriber.close()