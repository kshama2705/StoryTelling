# 🌈 Interactive StoryTelling App

An engaging, kid‑friendly Flask web app that uses LLaMA 4 and ElevenLabs TTS to generate choose‑your‑own‑adventure stories in multiple languages.

---

## 🚀 Features

- **Dynamic story generation** with LLaMA 4  
- **Interactive choices** at each story beat  
- **Multilingual support**: English, Spanish, French, German, Japanese  
- **Text‑to‑speech narration** via ElevenLabs  
- **Colorful, playful UI** with custom characters and settings  
- **“Random Adventure”** that picks character, setting & mood, while preserving user’s language choice  

---

## 📂 Project Structure

StoryTelling/
├── app.py # Flask routes & session handling
├── llama_logic.py # Core story, translation, and TTS functions
├── requirements.txt # Python dependencies
├── static/
│ ├── css/
│ │ └── style.css # Main stylesheet
│ └── images/ # Corner graphics (dragon.png, fox.png, owl.png, robot.png, unicorn.png)
└── templates/
├── picker.html # Character/setting/mood/language picker
├── choice.html # Story continuation & choices
└── end.html # Story ending screen
---

## 🔧 Prerequisites

- Python 3.8+  
- An OpenAI‑compatible LLaMA 4 API endpoint & key  
- An ElevenLabs API key  

---

## ⚙️ Setup & Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/kshama2705/StoryTelling.git
   cd StoryTelling
2. **Installing Dependencies**
   python3 -m venv venv
   source venv/bin/activate
3. **Set environment variables**
   Create a .env file or export directly in your shell
   export OPENAI_API_KEY="sk-…"
   export ELEVEN_API_KEY="your‑elevenlabs‑key"
4. **Run the app**
   flask run --host=0.0.0.0 --port=10000
   Open http://localhost:10000 in your browser
   
  or go to https://storytelling-tfdi.onrender.com/ (Deployed here)
 

