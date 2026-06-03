import os
from pathlib import Path

# --- DIRECTORY STRUCTURE ---
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"

# Create directories if they don't exist
for folder in [ASSETS_DIR, TEMP_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Sub-assets folders
FONTS_DIR = ASSETS_DIR / "fonts"
MUSIC_DIR = ASSETS_DIR / "music"
VIDEOS_DIR = ASSETS_DIR / "videos"

for folder in [FONTS_DIR, MUSIC_DIR, VIDEOS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# --- FONTS & ASSETS SEEDING ---
# We will download a high-end font like Montserrat-Black or LilitaOne if they don't exist
DEFAULT_FONT_URL = "https://raw.githubusercontent.com/googlefonts/montserrat/master/fonts/ttf/Montserrat-Black.ttf"
DEFAULT_FONT_NAME = "Montserrat-Black.ttf"
FONT_PATH = FONTS_DIR / DEFAULT_FONT_NAME

# Background music URLs (royalty-free tracks for templates)
ROYALTY_FREE_MUSIC = {
    "motivational": {
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", # Fallback placeholders, user can upload their own
        "name": "cinematic_inspiration.mp3"
    },
    "facts": {
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "name": "upbeat_curiosity.mp3"
    },
    "history": {
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "name": "epic_history.mp3"
    },
    "storytelling": {
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "name": "lofi_storytime.mp3"
    }
}

# --- EDGE-TTS VOICE PRESETS ---
VOICES = {
    "Male (Andrew - Professional)": "en-US-AndrewNeural",
    "Male (Brian - Clear & Deep)": "en-US-BrianNeural",
    "Male (Ryan - British Classic)": "en-GB-RyanNeural",
    "Female (Emma - Conversational)": "en-US-EmmaNeural",
    "Female (Ava - Warm & Friendly)": "en-US-AvaNeural",
    "Female (Sonia - British Premium)": "en-GB-SoniaNeural",
}

# --- TEMPLATE SPECIFICATIONS (Stunning Visual Styles) ---
NICHE_TEMPLATES = {
    "Motivational & Growth": {
        "system_prompt_niche": "focusing on self-discipline, resilience, achievement, and overcoming obstacles. Use impactful, bold, short sentences. Create dramatic build-ups.",
        "search_keywords": ["motivation", "discipline", "running in rain", "workout", "sunset peaks", "success", "office hustle"],
        "subtitle_color": "#FFCC00", # Vivid yellow
        "outline_color": "#000000", # Deep black
        "font_size": 72,
        "default_music": "motivational"
    },
    "Intriguing Facts & Sci-Fi": {
        "system_prompt_niche": "focusing on mind-blowing, bizarre, or lesser-known scientific, space, or cosmic facts. Start with a massive hook, keep a fast tempo, and end with a curiosity question.",
        "search_keywords": ["space nebula", "deep ocean", "quantum physics", "macro insect", "cyberpunk city", "galaxy vertical", "microscope view"],
        "subtitle_color": "#00E5FF", # Neon cyan
        "outline_color": "#0D0D11",
        "font_size": 72,
        "default_music": "facts"
    },
    "Ancient Secrets & History": {
        "system_prompt_niche": "focusing on dark, forgotten, or fascinating stories from ancient Rome, Greece, Egypt, or medieval times. Set a serious, epic, and storytelling tone.",
        "search_keywords": ["ancient pyramids", "roman ruins", "knights armor", "dusty scrolls", "old cathedral", "archaeology", "foggy castle"],
        "subtitle_color": "#E6C687", # Warm gold
        "outline_color": "#1C150A",
        "font_size": 70,
        "default_music": "history"
    },
    "Immersive Storytelling & Horror": {
        "system_prompt_niche": "focusing on short horror stories, unexplained mysteries, or highly immersive suspense stories. Use slow, dramatic pacing, long pauses, and extremely vivid, atmospheric imagery.",
        "search_keywords": ["dark woods fog", "creepy old house", "shadowy figure", "rainy window night", "haunted corridor", "flickering streetlamp"],
        "subtitle_color": "#FF3333", # Crimson blood red
        "outline_color": "#000000",
        "font_size": 72,
        "default_music": "storytelling"
    }
}

# --- SYSTEM & API DEFAULTS ---
DEFAULT_VIDEO_WIDTH = 1080
DEFAULT_VIDEO_HEIGHT = 1920 # Vertical YouTube Shorts standard (9:16)
MAX_SHORT_DURATION = 58 # Max seconds for YouTube Shorts (under 60s)

# File names for local API credentials storage
CREDENTIALS_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token.json"
USER_CONFIG_FILE = BASE_DIR / "user_config.json"
