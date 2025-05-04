import os
import random
from uuid import uuid4
from flask import Flask, request, render_template, send_file, session

from llama_logic import (
    CHARACTER_OPTIONS,
    SETTING_OPTIONS,
    MOOD_OPTIONS,
    LANGUAGE_OPTIONS,
    generate_initial_story,
    continue_story,
    translate_text,
    extract_options,
    story_has_ended,
    narrate_text
)

# ─────────────────────────────────────────────────────────────
# Config & Flask Setup
# ─────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.urandom(24)
story_sessions = {}

@app.route("/", methods=["GET", "POST"])
def index():
    # ── 1) Handle all POSTs first ─────────────────────────────────
    if request.method == "POST":
        form   = request.form
        action = form.get("action")

        # ── New Story (submit or random) ───────────────────────────
        if action in ("submit", "random"):
            language  = form.get("language")
            if action == "random":
                character = random.choice(CHARACTER_OPTIONS)
                setting   = random.choice(SETTING_OPTIONS)
                mood      = random.choice(MOOD_OPTIONS)
            else:
                character = form.get("custom_character") or form.get("character")
                setting   = form.get("custom_setting") or form.get("setting")
                mood      = form.get("mood")

            # generate & translate
            en_story = generate_initial_story(character, setting, mood)
            tr_story = translate_text(en_story, language)

            # initialize session state
            sid = str(uuid4())
            session["sid"] = sid
            story_sessions[sid] = {
                "en": en_story,
                "translated": tr_story,
                "lang": language,
                "ended": False
            }

            narrate_text(tr_story)
            option_a, option_b = extract_options(tr_story)
            return render_template("choice.html",
                                   story_text=tr_story,
                                   option_a=option_a,
                                   option_b=option_b)

        # ── Continue or End the Story ──────────────────────────────
        sid   = session.get("sid")
        state = story_sessions.get(sid, {})
        choice = form.get("choice")

        # End explicitly
        if choice == "END":
            finale_en = "And so, the story ends here—just as our explorers wished."
            state["en"] += "\n\n" + finale_en
            finale_tr = translate_text(finale_en, state["lang"])
            state["translated"] += "\n\n" + finale_tr
            state["ended"] = True

            narrate_text(state["translated"])
            return render_template("end.html", story_text=state["translated"])

        # Continue
        new_en = continue_story(state["en"], choice)
        state["en"] += "\n\n" + new_en
        new_tr = translate_text(new_en, state["lang"])
        state["translated"] += "\n\n" + new_tr
        narrate_text(state["translated"])

        # If story logic says it’s over
        if story_has_ended(new_en):
            state["ended"] = True
            return render_template("end.html", story_text=state["translated"])

        # Otherwise show next choices
        option_a, option_b = extract_options(new_tr)
        return render_template("choice.html",
                               story_text=new_tr,
                               option_a=option_a,
                               option_b=option_b)

    # ── 2) GET requests: reset session & show picker ───────────────
    session.pop("sid", None)
    return render_template(
        "picker.html",
        CHARACTER_OPTIONS=CHARACTER_OPTIONS,
        SETTING_OPTIONS=SETTING_OPTIONS,
        MOOD_OPTIONS=MOOD_OPTIONS,
        LANGUAGE_OPTIONS=LANGUAGE_OPTIONS
    )

@app.route("/audio")
def serve_audio():
    return send_file("/tmp/story_audio.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10001)
