from vosk import Model, KaldiRecognizer
import pyaudio
import json
import sys
import re
import time
import audioop
import wave
from modul_jarvis import Jarvis

sys.stdout.reconfigure(encoding='utf-8')

RATE = 16000
CHUNK = 2048

def words_to_numbers(text):
    number_map = {
        "нуль": 0, "один": 1, "два": 2, "три": 3, "чотири": 4,
        "п'ять": 5, "шість": 6, "сім": 7, "вісім": 8, "дев'ять": 9,
        "десять": 10, "двадцять": 20, "тридцять": 30, "сорок": 40,
        "п'ятдесят": 50, "шістдесят": 60, "сімдесят": 70, "вісімдесят": 80, "дев'яносто": 90,
        "сто": 100, "двісті": 200, "триста": 300, "чотириста": 400,
        "п'ятсот": 500, "шістсот": 600, "сімсот": 700, "вісімсот": 800, "дев'ятсот": 900
    }

    def parse_number_phrase(phrase):
        return str(sum(number_map.get(p, 0) for p in phrase.split()))

    pattern = r"\b(?:триста|двісті|сто|чотириста|п'ятсот|шістсот|сімсот|вісімсот|дев'ятсот)?(?:\s(?:двадцять|тридцять|сорок|п'ятдесят|шістдесят|сімдесят|вісімдесят|дев'яносто))?(?:\s(?:нуль|один|два|три|чотири|п'ять|шість|сім|вісім|дев'ять))?\b"
    for match in re.findall(pattern, text, flags=re.IGNORECASE):
        if match.strip():
            text = text.replace(match, parse_number_phrase(match))
    return text

def save_audio_and_transcription(audio_data, transcription):
    """
    Saves audio data and its transcription for future training.

    Args:
        audio_data (bytes): The raw audio data.
        transcription (str): The transcribed text.
    """
    # Save audio to a WAV file
    audio_filename = f"training_data/audio_{int(time.time())}.wav"
    with wave.open(audio_filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # Assuming 16-bit audio
        wf.setframerate(RATE)
        wf.writeframes(audio_data)

    # Save transcription to a text file
    transcription_filename = f"training_data/transcription_{int(time.time())}.txt"
    with open(transcription_filename, 'w', encoding='utf-8') as tf:
        tf.write(transcription)

    print(f"Saved audio to {audio_filename} and transcription to {transcription_filename}")

def capture_text_from_microphone():
    """
    Captures text from the microphone using the Vosk library.
    Continuously listens until the word 'стоп' is detected.
    Outputs results only after 5 seconds of silence.

    Returns:
        str: The transcribed text from the microphone input.
    """
    # Load the Vosk model for Ukrainian language
    model_path = r"C:\Users\apple_man\Desktop\projects\Jarvis_project\model\vosk-model-uk-v3-lgraph"  # Ensure this is the correct Ukrainian model
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, RATE)

    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    stream.start_stream()

    print("Listening...")
    final_text = ""
    last_sound_time = time.time()

    try:
        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if len(data) == 0:
                continue

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                text = words_to_numbers(text)  # Convert written numbers to digits

                if "шухер" in text.lower():
                    print("Detected stop command. Exiting...")
                    save_audio_and_transcription(data, text)  # Save the last audio and transcription
                    break

                # Normalize text to commands
                jarvis = Jarvis(text)
                final_text += text + " "
                last_sound_time = time.time()
                save_audio_and_transcription(data, text)  # Save audio and transcription for each result
            else:
                partial_result = json.loads(recognizer.PartialResult())
                print("Debug: Partial result:", partial_result)  # Debugging partial results

            # Check for 5 seconds of silence
            if time.time() - last_sound_time > 2:
                if final_text.strip():
                    print("Final output after silence:", final_text.strip())
                    final_text = ""  # Reset final text after output
                last_sound_time = time.time()  # Reset silence timer

    except KeyboardInterrupt:
        print("Stopped listening.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    capture_text_from_microphone()
