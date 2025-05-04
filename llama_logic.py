import os
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import random

# ─────────────────────────────────────────────────────────────
# Config & Constants (shared)
# ─────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY   = os.getenv("ELEVEN_API_KEY")
if not OPENAI_API_KEY or not ELEVEN_API_KEY:
    raise ValueError("Set OPENAI_API_KEY and ELEVEN_API_KEY in your environment")

CHARACTER_OPTIONS = [
    "Luna the Space Fox", "RoboMax the Friendly Robot", "Zara the Jungle Explorer",
    "Kai the Sky Pirate", "Mira the Time Traveler", "Finn the Ice Wizard"
]
SETTING_OPTIONS = [
    "a glowing jungle on Planet Zoog", "a deep underwater city",
    "a magical candy kingdom", "an enchanted forest",
    "a futuristic cityscape", "a haunted castle"
]
MOOD_OPTIONS = [
    "funny and adventurous", "mysterious and exciting",
    "calm and whimsical", "thrilling and suspenseful"
]
LANGUAGE_OPTIONS = ["English","Spanish","French","German","Japanese"]

# ─────────────────────────────────────────────────────────────
# API Clients
# ─────────────────────────────────────────────────────────────
llama = OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.llama.com/compat/v1/")
tts   = ElevenLabs(api_key=ELEVEN_API_KEY)

# ─────────────────────────────────────────────────────────────
# Story & Translation Functions
# ─────────────────────────────────────────────────────────────
def generate_initial_story(character, setting, mood):
    system = (
        "You are a storytelling assistant for an 8‑year‑old. "
        "Write fun, vivid, short stories with dialogue. End each segment with two choices:\n"
        "**Which way should [Character] go?**\n- A: ...\n- B: ..."
    )
    prompt = f"Character: {character}\nSetting: {setting}\nMood: {mood}\n\nBegin the story."
    resp = llama.chat.completions.create(
        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
    )
    return resp.choices[0].message.content


def continue_story(prev_en, choice):
    system = (
        "Continue the interactive children's story. Keep it playful and short. "
        "End again with two choices in the same format."
    )
    prompt = f"{prev_en}\n\nThe child chose: {choice}\nContinue the story."
    resp = llama.chat.completions.create(
        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
    )
    return resp.choices[0].message.content


def translate_text(en_text, target_lang):
    if target_lang.lower() == "english":
        return en_text
    system = (
        f"You are a translation assistant. Translate the following English text into {target_lang}, "
        "preserving formatting and choice markers exactly."
    )
    resp = llama.chat.completions.create(
        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role":"system","content":system},{"role":"user","content":en_text}],
    )
    return resp.choices[0].message.content


def extract_options(text):
    lines = [l for l in text.splitlines() if l.strip().startswith("- ")]
    if len(lines) < 2:
        return "Option A", "Option B"
    return [l.split(":",1)[1].strip() for l in lines[:2]]


def story_has_ended(text):
    endings = ["the end.", "they lived happily", "that was the end", "our story ends here"]
    tl = text.lower()
    return any(e in tl for e in endings)


def narrate_text(text):
    try:
        stream = tts.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="mp3_44100_128"
        )
        path = "/tmp/story_audio.mp3"
        with open(path, "wb") as f:
            for chunk in stream:
                f.write(chunk)
        return path
    except Exception as e:
        print(f"[Narration Error]: {e}")
        return None