import os
from flask import Flask, request, render_template_string, send_file
from openai import OpenAI
from elevenlabs.client import ElevenLabs

# ─── Setup ───────────────────────────────────────────────────────────────────────
# Read API keys from the environment
openai_key = os.getenv("OPENAI_API_KEY")
eleven_key = os.getenv("ELEVEN_API_KEY")

# Initialize clients
llama = OpenAI(api_key=openai_key, base_url="https://api.llama.com/compat/v1/")
tts = ElevenLabs(api_key=eleven_key)  # :contentReference[oaicite:0]{index=0}

# ─── HTML Template ───────────────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html>
<head><title>Story Picker</title></head>
<body>
  <h1>Select a Character and Scene</h1>
  <form method="POST">
    <label>Select a character:</label><br/>
    <input type="radio" name="character" value="Luna the Space Fox" required> Luna the Space Fox<br/>
    <input type="radio" name="character" value="RoboMax the Friendly Robot"> RoboMax the Friendly Robot<br/>
    <input type="radio" name="character" value="Zara the Jungle Explorer"> Zara the Jungle Explorer<br/><br/>

    <label>Select a setting:</label><br/>
    <select name="setting">
      <option value="a glowing jungle on Planet Zoog">Alien Jungle</option>
      <option value="a deep underwater city">Underwater City</option>
      <option value="a magical candy kingdom">Candy Kingdom</option>
    </select><br/><br/>

    <label>Mood:</label>
    <select name="mood">
      <option value="funny and adventurous">Funny & Adventurous</option>
      <option value="mysterious and exciting">Mysterious & Exciting</option>
    </select><br/><br/>

    <input type="submit" value="Start Story">
  </form>
</body>
</html>
"""

# ─── Story Generation ─────────────────────────────────────────────────────────────
def get_story(character, setting, mood):
    system_prompt = (
        "You are a fun, kind, and creative storytelling assistant for an 8-year-old child. "
        "Tell the story in short, vivid, easy-to-understand language with fun dialogue. "
        "End with a choice prompt. Do not continue the story until the child decides."
    )
    user_prompt = f"""
The child has chosen:
- Character: {character}
- Setting: {setting}
- Mood: {mood}

Start the story with 1–2 short paragraphs, then ask the child to choose what happens next.

Use this format:

[Story]

**Which way should {character} go?**
- A: [option A]
- B: [option B]
"""    
    resp = llama.chat.completions.create(
        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content

# ─── Text‑to‑Speech ───────────────────────────────────────────────────────────────
def narrate_story(text):
    try:
        audio_stream = tts.text_to_speech.convert(
            voice_id="Rachel",
            model_id="eleven_multilingual_v2",
            text=text,
            output_format="mp3_44100_128"
        )
        path = "/tmp/story_audio.mp3"
        with open(path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        return path
    except Exception as e:
        print(f"Error in narrate_story: {e}")
        return None


# ─── Flask App ───────────────────────────────────────────────────────────────────
app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        char    = request.form["character"]
        setting = request.form["setting"]
        mood    = request.form["mood"]

        story     = get_story(char, setting, mood)
        audio_fp  = narrate_story(story)

        return (
            "<h2>Your Story:</h2>"
            + f"<p>{story.replace(chr(10), '<br/>')}</p>"
            + "<audio controls src='/audio'></audio>"
            + "<br/><a href='/'>Start Over</a>"
        )

    return render_template_string(HTML)

@app.route("/audio")
def serve_audio():
    return send_file("/tmp/story_audio.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
