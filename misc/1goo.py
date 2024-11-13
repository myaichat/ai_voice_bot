import speech_recognition as sr

def transcribe_audio():
    # Create a recognizer object
    recognizer = sr.Recognizer()

    # Use the default microphone as the audio source
    with sr.Microphone() as source:
        print("Listening... Speak now!")
        
        # Adjust for ambient noise and set a timeout
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=1)

    try:
        # Use Google Speech Recognition to transcribe the audio
        text = recognizer.recognize_google(audio)
        print(f"Transcription: {text}")
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from the speech recognition service; {e}")

if __name__ == "__main__":
    transcribe_audio()