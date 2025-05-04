import os
import random
from uuid import uuid4
from flask import Flask, request, render_template_string, send_file, session

from openai import OpenAI
from elevenlabs.client import ElevenLabs

# ─────────────────────────────────────────────────────────────
# Config & Constants
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
# Flask Setup
# ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.urandom(24)
story_sessions = {}

# ─────────────────────────────────────────────────────────────
# HTML Templates (with CSS whitespace handling)
# ─────────────────────────────────────────────────────────────
HTML_PICKER = """
<!DOCTYPE html>
<html>
<head><title>Interactive Story</title></head>
<body>
  <h1>Pick Your Adventure</h1>
  <form method="POST">
    <button type="submit" name="action" value="submit">Begin Story</button>
    <button type="submit" name="action" value="random">Random Story</button>
    <hr/>

    <label><strong>Choose a character:</strong></label><br/>
    {% for c in CHARACTER_OPTIONS %}
      <input type="radio" name="character" value="{{c}}"> {{c}}<br/>
    {% endfor %}
    <br/>
    <label>Or describe your own:</label><br/>
    <input type="text" name="custom_character" placeholder="E.g. Zara the Cloud Whisperer">
    <hr/>

    <label><strong>Choose a setting:</strong></label><br/>
    <select name="setting">
      {% for s in SETTING_OPTIONS %}
        <option value="{{s}}">{{s}}</option>
      {% endfor %}
    </select><br/><br/>
    <label>Or describe your own:</label><br/>
    <input type="text" name="custom_setting" placeholder="E.g. a floating island of dreams">
    <hr/>

    <label><strong>Mood:</strong></label><br/>
    <select name="mood">
      {% for m in MOOD_OPTIONS %}
        <option value="{{m}}">{{m}}</option>
      {% endfor %}
    </select><br/><br/>

    <label><strong>Language:</strong></label><br/>
    <select name="language">
      {% for l in LANGUAGE_OPTIONS %}
        <option value="{{l}}">{{l}}</option>
      {% endfor %}
    </select><br/><br/>
  </form>
</body>
</html>
"""

HTML_CHOICE = """
<!DOCTYPE html>
<html>
<head><title>Continue Story</title></head>
<body>
  <h2>Your Story:</h2>
  <div style="white-space: pre-wrap; border:1px solid #ccc; padding:10px; border-radius:5px;">
    {{ story_text }}
  </div>
  <form method="POST">
    <input type="hidden" name="action" value="continue">
    <p><strong>What should happen next?</strong></p>
    <input type="radio" name="choice" value="A" required> {{ option_a }}<br/>
    <input type="radio" name="choice" value="B"> {{ option_b }}<br/>
    <input type="radio" name="choice" value="END"> End the story here<br/><br/>
    <button type="submit">Submit Choice</button>
  </form>
  <audio controls src="/audio"></audio>
  <p><a href="/">Start Over</a></p>
</body>
</html>
"""

HTML_END = """
<!DOCTYPE html>
<html>
<head><title>The End</title></head>
<body>
  <h2>Final Story:</h2>
  <div style="white-space: pre-wrap; border:1px solid #ccc; padding:10px; border-radius:5px;">
    {{ story_text }}
  </div>
  <p><strong>The End.</strong></p>
  <audio controls src="/audio"></audio>
  <p><a href="/">Start Another Story</a></p>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────
# Story & Translation Logic
# ─────────────────────────────────────────────────────────────
def generate_initial_story(character, setting, mood):
    system = (
        "You are a storytelling assistant for an 8‑year‑old. Write fun, vivid, short stories with dialogue. "
        "End each segment with two choices:\n"
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

def story_has_ended(text):
    endings = ["the end.", "they lived happily", "that was the end", "our story ends here"]
    tl = text.lower()
    return any(e in tl for e in endings)

def extract_options(text):
    lines = [l for l in text.splitlines() if l.strip().startswith("- ")]
    if len(lines) < 2:
        return "Option A","Option B"
    return lines[0].split(":",1)[1].strip(), lines[1].split(":",1)[1].strip()

def narrate_text(text):
    try:
        stream = tts.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM",
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="mp3_44100_128"
        )
        path = "/tmp/story_audio.mp3"
        with open(path,"wb") as f:
            for chunk in stream:
                f.write(chunk)
        return path
    except Exception as e:
        print(f"[Narration Error]: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# Flask Routes
# ─────────────────────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        # ── Random story ────────────────────────────────────────
        if action == "random":
            character = random.choice(CHARACTER_OPTIONS)
            setting   = random.choice(SETTING_OPTIONS)
            mood      = random.choice(MOOD_OPTIONS)
            language  = request.form.get("language","English")

        # ── Manual / custom story ───────────────────────────────
        else:  # action == "submit"
            # Character
            custom_char = request.form.get("custom_character","").strip()
            character   = custom_char or request.form.get("character")

            # Setting
            custom_set = request.form.get("custom_setting","").strip()
            setting    = custom_set or request.form.get("setting")

            mood     = request.form.get("mood")
            language = request.form.get("language")

        # ── Initialize session & first segment ──────────────────
        en_story = generate_initial_story(character, setting, mood)
        tr_story = translate_text(en_story, language)

        sid = str(uuid4())
        session["sid"] = sid
        story_sessions[sid] = {
            "en": en_story,
            "translated": tr_story,
            "lang": language,
            "ended": False
        }
        narrate_text(tr_story)
        A,B = extract_options(tr_story)

        return render_template_string(
            HTML_CHOICE,
            story_text=tr_story,
            option_a=A,
            option_b=B
        )

    # ── Continue or End ─────────────────────────────────────
    sid   = session.get("sid")
    state = story_sessions.get(sid)
    if not state:
        return render_template_string(
            HTML_PICKER,
            CHARACTER_OPTIONS=CHARACTER_OPTIONS,
            SETTING_OPTIONS=SETTING_OPTIONS,
            MOOD_OPTIONS=MOOD_OPTIONS,
            LANGUAGE_OPTIONS=LANGUAGE_OPTIONS
        )

    choice = request.form.get("choice")
    if choice == "END":
        finale_en = "And so, the story ends here—just as our explorers wished."
        finale_tr = translate_text(finale_en, state["lang"])
        state["en"]        += "\n\n" + finale_en
        state["translated"]+= "\n\n" + finale_tr
        state["ended"] = True
        narrate_text(state["translated"])
        return render_template_string(
            HTML_END,
            story_text=state["translated"]
        )

    # ── Normal continuation ───────────────────────────────────
    new_en = continue_story(state["en"], choice)
    state["en"]         += "\n\n" + new_en
    new_tr = translate_text(new_en, state["lang"])
    state["translated"] += "\n\n" + new_tr
    narrate_text(state["translated"])

    if story_has_ended(new_en):
        state["ended"] = True
        return render_template_string(
            HTML_END,
            story_text=state["translated"]
        )

    A,B = extract_options(new_tr)
    return render_template_string(
        HTML_CHOICE,
        story_text=new_tr,
        option_a=A,
        option_b=B
    )

@app.route("/audio")
def serve_audio():
    return send_file("/tmp/story_audio.mp3", mimetype="audio/mpeg")

# ─────────────────────────────────────────────────────────────
# Run App
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

