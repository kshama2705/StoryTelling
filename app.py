import os
from flask import Flask, request, render_template_string, send_file
from openai import OpenAI
from elevenlabs import generate, save, set_api_key

# Load API keys from environment variables
openai_key = os.getenv("OPENAI_API_KEY")
eleven_key = os.getenv("ELEVEN_API_KEY")

client = OpenAI(api_key=openai_key, base_url="https://api.llama.com/compat/v1/")
set_api_key(eleven_key)

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><title>Story Picker</title></head>
<body>
  <h1>Select a Character and Scene</h1>
  <form method="POST">
    <label>Select a character:</label><br/>
    <input type="radio" name="character" value="Luna the Space Fox"> Luna the Space Fox<br/>
    <input type="radio" name="character" value="RoboMax the Friendly Robot"> RoboMax the Friendly Robot<br/>
    <input type="radio" name="character" value="Zara the Jungle Explorer"> Zara the Jungle Explorer<br/>

    <label>Select a setting:</label><br/>
    <select name="setting">
      <option value="a glowing jungle on Planet Zoog">Alien Jungle</option>
      <option value="a deep underwater city">Underwater City</option>
      <option value="a magical candy kingdom">Candy Kingdom</option>
    </select><br/><br/>

    <label>Mood:</label>
    <select name="mood">
      <option value="funny and adventurous">Funny and Adventurous</option>
      <option value="mysterious and exciting">Mysterious and Exciting</option>
    </select><br/><br/>

    <input type="submit" value="Start Story">
  </form>
</body>
</html>
"""

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

    response = client.chat.completions.create(
        model="Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content

def narrate_story(text, voice="Rachel"):
    audio = generate(text=text, voice=voice, model="eleven_monolingual_v1")
    save(audio, "/tmp/story_audio.mp3")
    return "/tmp/story_audio.mp3"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        character = request.form["character"]
        setting = request.form["setting"]
        mood = request.form["mood"]

        story = get_story(character, setting, mood)
        audio_path = narrate_story(story)
        return f"<h2>Your Story:</h2><p>{story.replace(chr(10), '<br/>')}</p><audio controls src='/audio'></audio><br/><a href='/'>Start Over</a>"

    return render_template_string(HTML)

@app.route("/audio")
def serve_audio():
    return send_file("/tmp/story_audio.mp3", mimetype="audio/mpeg")

if __name__ == "__main__":
    app.run(debug=True)