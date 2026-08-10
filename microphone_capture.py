import audioop
import os
import re
import sys
import time
import wave
from typing import Callable

import numpy as np
import pyaudio

from config_loader import get_whisper_settings, load_settings
from text_normalizer import normalize_recognized_text

sys.stdout.reconfigure(encoding="utf-8")

RATE = 16000
CHUNK = 2048
SPEECH_RMS_THRESHOLD = 500
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINING_DIR = os.path.join(BASE_DIR, "training_data")

StopCheckFn = Callable[[], bool]

_whisper_model = None
_whisper_model_key: tuple[str, str, str] | None = None


def words_to_numbers(text: str) -> str:
    number_map = {
        "нуль": 0, "один": 1, "два": 2, "три": 3, "чотири": 4,
        "п'ять": 5, "шість": 6, "сім": 7, "вісім": 8, "дев'ять": 9,
        "десять": 10, "двадцять": 20, "тридцять": 30, "сорок": 40,
        "п'ятдесят": 50, "шістдесят": 60, "сімдесят": 70, "вісімдесят": 80, "дев'яносто": 90,
        "сто": 100, "двісті": 200, "триста": 300, "чотириста": 400,
        "п'ятсот": 500, "шістсот": 600, "сімсот": 700, "вісімсот": 800, "дев'ятсот": 900,
    }

    def parse_number_phrase(phrase: str) -> str:
        return str(sum(number_map.get(p, 0) for p in phrase.split()))

    pattern = (
        r"\b(?:триста|двісті|сто|чотириста|п'ятсот|шістсот|сімсот|вісімсот|дев'ятсот)?"
        r"(?:\s(?:двадцять|тридцять|сорок|п'ятдесят|шістдесят|сімдесят|вісімдесят|дев'яносто))?"
        r"(?:\s(?:нуль|один|два|три|чотири|п'ять|шість|сім|вісім|дев'ять))?\b"
    )
    for match in re.findall(pattern, text, flags=re.IGNORECASE):
        if match.strip():
            text = text.replace(match, parse_number_phrase(match))
    return text


def save_audio_and_transcription(audio_data: bytes, transcription: str) -> None:
    os.makedirs(TRAINING_DIR, exist_ok=True)
    stamp = int(time.time())
    audio_filename = os.path.join(TRAINING_DIR, f"audio_{stamp}.wav")
    with wave.open(audio_filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(audio_data)

    transcription_filename = os.path.join(TRAINING_DIR, f"transcription_{stamp}.txt")
    with open(transcription_filename, "w", encoding="utf-8") as tf:
        tf.write(transcription)

    print(f"Saved audio to {audio_filename} and transcription to {transcription_filename}")


def contains_stop_word(text: str, stop_words: list[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in stop_words)


def strip_stop_words(text: str, stop_words: list[str]) -> str:
    result = text
    for word in stop_words:
        result = re.sub(re.escape(word), " ", result, flags=re.IGNORECASE)
    return " ".join(result.split()).strip()


def get_whisper_model():
    global _whisper_model, _whisper_model_key
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise ImportError(
            "Пакет faster-whisper не встановлено. Виконайте: pip install faster-whisper"
        ) from e

    cfg = get_whisper_settings()
    key = (cfg["model_size"], cfg["device"], cfg["compute_type"])
    if _whisper_model is not None and _whisper_model_key == key:
        return _whisper_model, cfg

    print(
        f"Loading Whisper model '{cfg['model_size']}' "
        f"({cfg['device']}, {cfg['compute_type']})..."
    )
    try:
        _whisper_model = WhisperModel(
            cfg["model_size"],
            device=cfg["device"],
            compute_type=cfg["compute_type"],
        )
    except Exception as e:
        raise RuntimeError(
            f"Не вдалося завантажити Whisper '{cfg['model_size']}': {e}. "
            "Перевірте інтернет для першого завантаження або параметри whisper у settings.json."
        ) from e
    _whisper_model_key = key
    return _whisper_model, cfg


def pcm16_to_float32(audio_bytes: bytes) -> np.ndarray:
    audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
    return audio / 32768.0


def transcribe_audio(audio_bytes: bytes, language: str | None, whisper_cfg: dict) -> str:
    if not audio_bytes:
        return ""
    model, _cfg = get_whisper_model()
    audio = pcm16_to_float32(audio_bytes)
    if audio.size == 0:
        return ""
    beam_size = int(whisper_cfg.get("beam_size", 5))
    initial_prompt = str(whisper_cfg.get("initial_prompt") or "")
    segments, _info = model.transcribe(
        audio,
        language=language,
        task="transcribe",
        vad_filter=True,
        beam_size=beam_size,
        best_of=beam_size,
        patience=1.0,
        condition_on_previous_text=False,
        initial_prompt=initial_prompt or None,
        temperature=0.0,
    )
    parts = [segment.text.strip() for segment in segments if segment.text and segment.text.strip()]
    return " ".join(parts).strip()


def capture_text_from_microphone(
    should_stop: StopCheckFn | None = None,
    silence_sec: float = 2.0,
) -> str:
    settings = load_settings()
    stop_words = settings.get("stop_words", ["шухер", "стоп"])
    save_training = bool(settings.get("save_training_data", True))
    whisper_cfg = get_whisper_settings()
    max_record_sec = float(whisper_cfg.get("max_record_sec", 20))
    language = whisper_cfg.get("language")

    get_whisper_model()

    p = pyaudio.PyAudio()
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )
    except Exception as e:
        p.terminate()
        raise RuntimeError(f"Не вдалося відкрити мікрофон: {e}") from e

    stream.start_stream()
    print("Listening...")

    frames: list[bytes] = []
    speech_started = False
    last_speech_time = time.time()
    start_time = time.time()

    try:
        while True:
            if should_stop is not None and should_stop():
                print("Stop requested from UI.")
                break

            if time.time() - start_time > max_record_sec:
                print("Max record time reached.")
                break

            data = stream.read(CHUNK, exception_on_overflow=False)
            if len(data) == 0:
                continue

            frames.append(data)
            rms = audioop.rms(data, 2)
            if rms >= SPEECH_RMS_THRESHOLD:
                speech_started = True
                last_speech_time = time.time()
            elif speech_started and time.time() - last_speech_time > silence_sec:
                print("Silence detected, transcribing...")
                break

    except KeyboardInterrupt:
        print("Stopped listening.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    audio_bytes = b"".join(frames)
    if not speech_started or not audio_bytes:
        print("No speech detected.")
        return ""

    print("Transcribing with Whisper...")
    try:
        text = transcribe_audio(audio_bytes, language, whisper_cfg)
    except Exception as e:
        raise RuntimeError(f"Помилка транскрипції Whisper: {e}") from e

    text = words_to_numbers(text).strip()
    wake_word = settings.get("wake_word", "атас")
    aliases = settings.get("wake_word_aliases", [])
    text = normalize_recognized_text(text, wake_word, aliases)
    try:
        from neural_parser import neural_refine_text

        text = neural_refine_text(text)
    except Exception as e:
        print(f"Neural refine skipped: {e}")
    print(f"Recognized: {text}")

    if contains_stop_word(text, stop_words):
        text = strip_stop_words(text, stop_words)
        print("Stop word detected; cleaned text:", text)

    if save_training and text:
        save_audio_and_transcription(audio_bytes, text)

    return text


if __name__ == "__main__":
    print(capture_text_from_microphone())
