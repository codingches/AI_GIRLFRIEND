import argparse
import os
import sys
from io import BytesIO
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Missing dependency: openai. Install with `pip install -r ../requirements.txt`.\n")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


def load_api_key():
    if load_dotenv is not None:
        env_path = Path(__file__).resolve().parents[1] / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found. Set it in the environment or in a .env file.")
        sys.exit(1)
    return api_key


def build_system_prompt():
    return (
        "You are Hikari, a friendly anime waifu assistant. "
        "Speak softly, warmly, and playfully. Keep your replies cute and supportive, "
        "using gentle language and light emoji where appropriate. "
        "Avoid anything explicit and focus on being kind, fun, and easy to chat with."
    )


def get_model_name():
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def init_voice():
    recognizer = None
    tts_engine = None

    if sr is not None:
        try:
            recognizer = sr.Recognizer()
        except Exception as exc:
            print(f"Warning: failed to initialize speech recognition: {exc}")
            recognizer = None

    if pyttsx3 is not None:
        try:
            tts_engine = pyttsx3.init()
            tts_engine.setProperty("rate", 170)
            tts_engine.setProperty("volume", 1.0)
        except Exception as exc:
            print(f"Warning: failed to initialize TTS engine: {exc}")
            tts_engine = None

    return recognizer, tts_engine


def listen_to_mic(recognizer):
    if recognizer is None:
        return None

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            print("Listening... please speak now.")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=12)
    except sr.WaitTimeoutError:
        print("No speech detected. Try again or type your message.")
        return None
    except Exception as exc:
        print(f"Microphone error: {exc}")
        return None

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        return text.strip()
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand that. Please try again.")
    except sr.RequestError as exc:
        print(f"Speech recognition service error: {exc}")
    except Exception as exc:
        print(f"Speech recognition error: {exc}")
    return None


def transcribe_whisper(recognizer, client):
    if recognizer is None:
        return None

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.6)
            print("Listening for Whisper... please speak now.")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
    except sr.WaitTimeoutError:
        print("No speech detected. Try again or type your message.")
        return None
    except Exception as exc:
        print(f"Microphone error: {exc}")
        return None

    try:
        wav_data = audio.get_wav_data(convert_rate=16000)
        audio_file = BytesIO(wav_data)
        audio_file.name = "speech.wav"
        transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file, 
                    response_format="verbose_json"
    )
        return transcript.text.strip()
    except Exception as exc:
        print(f"Whisper transcription error: {exc}")
        return None


def speak_text(text, tts_engine):
    if tts_engine is None:
        return

    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as exc:
        print(f"TTS playback error: {exc}")


def print_header(voice_enabled, whisper_enabled):
    print("=== Anime Waifu Chat ===")
    print("Type 'exit' or 'quit' to stop.")
    print("Type 'voice' to speak when voice mode is enabled.")
    if voice_enabled:
        print("Voice mode is enabled. Speak after entering 'voice'.")
    if whisper_enabled:
        print("Whisper transcription is enabled. Speak after entering 'voice'.")
    if not voice_enabled and not whisper_enabled:
        print("Voice mode is disabled. Run with --voice or --whisper and install optional packages to enable it.")
    print("You can change the model with OPENAI_MODEL environment variable.")
    print()


def main():
    parser = argparse.ArgumentParser(description="Anime waifu chat with optional voice support.")
    parser.add_argument("--voice", action="store_true", help="Enable local voice input/output if available")
    parser.add_argument("--whisper", action="store_true", help="Enable Whisper-based speech transcription")
    parser.add_argument("--no-voice", action="store_true", help="Disable voice even if available")
    args = parser.parse_args()

    client = OpenAI(api_key=load_api_key())
    model = get_model_name()

    recognizer, tts_engine = None, None
    voice_enabled = False
    whisper_enabled = False

    if args.voice and not args.no_voice:
        recognizer, tts_engine = init_voice()
        voice_enabled = recognizer is not None or tts_engine is not None
        if not voice_enabled:
            print("Voice support is unavailable. Continuing with text-only chat.")

    if args.whisper and not args.no_voice:
        if sr is None:
            print("Whisper needs SpeechRecognition to access the microphone.")
        else:
            recognizer = sr.Recognizer()
            whisper_enabled = True

    messages = [{"role": "system", "content": build_system_prompt()}]

    print_header(voice_enabled, whisper_enabled)

    while True:
        try:
            prompt = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye! Take care.")
            break

        if not prompt:
            continue

        if prompt.lower() == "voice":
            if recognizer is None:
                print("Voice input is not available. Install SpeechRecognition and a microphone driver.")
                continue

            if whisper_enabled:
                prompt = transcribe_whisper(recognizer, client)
            else:
                prompt = listen_to_mic(recognizer)

            if not prompt:
                continue

            print(f"You (voice): {prompt}")

        if prompt.lower() in {"exit", "quit", "bye"}:
            print("Hikari: It was lovely talking with you. Come back soon! 💖")
            break

        messages.append({"role": "user", "content": prompt})

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.8,
                max_tokens=400,
            )
        except Exception as exc:
            print(f"Error calling OpenAI API: {exc}")
            break

        assistant_text = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": assistant_text})

        print(f"\nHikari: {assistant_text}\n")
        if tts_engine is not None:
            speak_text(assistant_text, tts_engine)


if __name__ == "__main__":
    main()

#     #import speech_recognition as sr

# recognizer = sr.Recognizer()

# ''' recording the sound '''

# with sr.Microphone() as source:
#     print("Adjusting noise ")
#     recognizer.adjust_for_ambient_noise(source, duration=1)
#     print("Recording for 4 seconds")
#     recorded_audio = recognizer.listen(source, timeout=4)
#     print("Done recording")

# ''' Recorgnizing the Audio '''
# try:
#     print("Recognizing the text")
#     text = recognizer.recognize_google(
#             recorded_audio, 
#             language="en-US"
#         )
#     print("Decoded Text : {}".format(text))

# except Exception as ex:
#     print(ex)
