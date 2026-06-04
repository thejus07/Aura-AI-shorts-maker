import os
import json
import logging
import streamlit as st



from pathlib import Path
from config import (
    ASSETS_DIR, 
    TEMP_DIR, 
    OUTPUT_DIR, 
    VOICES, 
    NICHE_TEMPLATES, 
    CREDENTIALS_FILE, 
    TOKEN_FILE, 
    USER_CONFIG_FILE,
    ROYALTY_FREE_MUSIC
)
from script_agent import ScriptAgent
from voice_engine import VoiceEngine
from asset_manager import AssetManager
from video_compiler import VideoCompiler
from youtube_uploader import YouTubeUploader

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")



# Page Configuration for Premium Dashboard
st.set_page_config(
    page_title="AURA - AI Shorts Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling & Theme Injections
st.markdown("""
<style>
    /* Dark glassmorphic styling */
    .stApp {
        background-color: #0c0d12;
        color: #f1f2f6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #12131a !important;
        border-right: 1px solid #232530;
    }
    
    /* Headings */
    h1, h2, h3 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Premium components cards */
    .glass-card {
        background: rgba(25, 27, 38, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .status-card {
        padding: 10px 15px;
        border-radius: 8px;
        margin: 5px 0;
        font-weight: 600;
    }
    
    /* Custom buttons */
    div.stButton > button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 242, 254, 0.6) !important;
        color: #ffffff !important;
    }
    
    /* Secondary/Action buttons */
    div.stButton > button[type="secondary"] {
        background: #1b1c26 !important;
        border: 1px solid #2d2f3f !important;
        color: #c9ccd6 !important;
        box-shadow: none !important;
    }
    div.stButton > button[type="secondary"]:hover {
        background: #232533 !important;
        color: #ffffff !important;
        border-color: #4facfe !important;
        transform: none !important;
    }
    
    /* Subtitles highlights */
    .highlight-active {
        color: #FFCC00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- USER CONFIG STORAGE HELPER ---
def load_user_config() -> dict:
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"gemini_key": "", "pexels_key": "", "default_niche": "Intriguing Facts & Sci-Fi", "default_voice": "Male (Andrew - Professional)", "upload_privacy": "private"}

def save_user_config(config_data: dict):
    with open(USER_CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=2)

# Load global configurations
user_config = load_user_config()

# Initialize API Keys in State
if "gemini_key" not in st.session_state:
    st.session_state.gemini_key = os.environ.get("GEMINI_API_KEY", user_config.get("gemini_key", ""))
if "pexels_key" not in st.session_state:
    st.session_state.pexels_key = os.environ.get("PEXELS_API_KEY", user_config.get("pexels_key", ""))

# Initialize Core Services
script_agent = ScriptAgent(st.session_state.gemini_key)
voice_engine = VoiceEngine()
asset_manager = AssetManager(st.session_state.pexels_key)
video_compiler = VideoCompiler()
youtube_uploader = YouTubeUploader()

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h2 style='text-align: center; margin-bottom: 2px;'>AURA</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #8888aa; font-size: 0.85rem; margin-top:0;'>AI Video Shorts Studio v1.0</p>", unsafe_allow_html=True)
st.sidebar.write("---")

nav = st.sidebar.radio(
    "Navigation",
    ["📱 Creator Studio", "📂 Video Gallery", "⚙️ System Settings", "📘 YouTube Setup Guide"]
)

# Status info in sidebar footer
st.sidebar.write("---")
auth_status = youtube_uploader.get_auth_status()
st.sidebar.markdown("### YouTube Channel Connection")
if auth_status["authenticated"]:
    st.sidebar.markdown("<div class='status-card' style='background: rgba(46, 204, 113, 0.15); color: #2ecc71; border: 1px solid #2ecc71;'>🟢 Authenticated & Linked</div>", unsafe_allow_html=True)
elif auth_status["client_secrets_configured"]:
    st.sidebar.markdown("<div class='status-card' style='background: rgba(241, 196, 15, 0.15); color: #f1c40f; border: 1px solid #f1c40f;'>🟡 OAuth secrets loaded (Login required)</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<div class='status-card' style='background: rgba(231, 76, 60, 0.15); color: #e74c3c; border: 1px solid #e74c3c;'>🔴 client_secret.json missing</div>", unsafe_allow_html=True)

# ----------------- SYSTEM CONFIGURATION TAB -----------------
if nav == "⚙️ System Settings":
    st.title("System Configuration")
    st.write("Configure your API credentials and styling presets for automatic short creation.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🔑 API Key Configuration")
        
        gemini_input = st.text_input("Gemini API Key", value=st.session_state.gemini_key, type="password", help="Required to generate scripts and metadata. Get from Google AI Studio.")
        pexels_input = st.text_input("Pexels API Key (Free)", value=st.session_state.pexels_key, type="password", help="Highly recommended for dynamic stock videos. Get a free key on pexels.com.")
        
        if st.button("Save API Credentials"):
            st.session_state.gemini_key = gemini_input
            st.session_state.pexels_key = pexels_input
            
            user_config["gemini_key"] = gemini_input
            user_config["pexels_key"] = pexels_input
            save_user_config(user_config)
            
            script_agent.set_api_key(gemini_input)
            asset_manager.set_api_key(pexels_input)
            st.success("API Keys saved and updated successfully!")
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Styling Defaults")
        default_niche = st.selectbox("Default Niche Preset", list(NICHE_TEMPLATES.keys()), index=list(NICHE_TEMPLATES.keys()).index(user_config.get("default_niche", "Intriguing Facts & Sci-Fi")))
        default_voice = st.selectbox("Default Edge-TTS Voice", list(VOICES.keys()), index=list(VOICES.keys()).index(user_config.get("default_voice", "Male (Andrew - Professional)")))
        default_privacy = st.selectbox("YouTube Upload Privacy", ["private", "unlisted", "public"], index=["private", "unlisted", "public"].index(user_config.get("upload_privacy", "private")))
        
        if st.button("Save Styling Defaults"):
            user_config["default_niche"] = default_niche
            user_config["default_voice"] = default_voice
            user_config["upload_privacy"] = default_privacy
            save_user_config(user_config)
            st.success("Styling defaults updated!")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🔒 YouTube OAuth Authorization Manager")
        st.write("Upload your `client_secret.json` from the Google Cloud Console to establish a secure link with your YouTube account.")
        
        uploaded_secret = st.file_uploader("Upload client_secret.json", type="json")
        if uploaded_secret is not None:
            # Check if we already processed this upload to avoid infinite rerun loops
            upload_key = f"uploaded_{uploaded_secret.name}_{uploaded_secret.size}"
            if st.session_state.get("last_uploaded_secret_key") != upload_key:
                try:
                    secret_data = json.load(uploaded_secret)
                    # Verify standard credentials schema
                    if "installed" in secret_data or "web" in secret_data:
                        with open(CREDENTIALS_FILE, "w") as f:
                            json.dump(secret_data, f, indent=2)
                        st.session_state.last_uploaded_secret_key = upload_key
                        st.success("Successfully saved client_secret.json to workspace directory!")
                        st.rerun()
                    else:
                        st.error("Invalid JSON format: JSON must contain 'installed' or 'web' authorization schemas.")
                except Exception as e:
                    st.error(f"Error parsing uploaded file: {e}")
        
        st.write("---")
        st.markdown("### Establish YouTube Handshake")
        st.write("Click below to run authorization. **Note:** This will open a browser tab to log in with your YouTube Google Account. Once authenticated, subsequent uploads run 100% headless.")
        
        if not auth_status["client_secrets_configured"]:
            st.warning("Please upload a client_secret.json file above to unlock authentication.")
        else:
            if st.button("💡 Authenticate YouTube Channel"):
                with st.spinner("Waiting for YouTube authentication in browser..."):
                    success = youtube_uploader.authenticate(run_interactive=True)
                    if success:
                        st.success("YouTube integration authorized successfully! Cached in token.json")
                        st.rerun()
                    else:
                        st.error("Authentication failed. Make sure you accepted all scopes and authorized successfully.")
                        
            if auth_status["authenticated"]:
                if st.button("❌ Disconnect / Clear Authentication", type="secondary"):
                    if TOKEN_FILE.exists():
                        TOKEN_FILE.unlink()
                        st.success("Successfully logged out and deleted token credentials cache.")
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------- INTRODUCTORY GUIDE TAB -----------------
elif nav == "📘 YouTube Setup Guide":
    st.title("YouTube API Setup Guide")
    st.write("Setting up your Google Cloud project is a one-time requirement that takes less than 5 minutes. Follow these instructions:")
    
    st.markdown("""
    ### 🛠️ How to get your `client_secret.json`
    
    1. **Go to Google Cloud Console:**
       Visit [Google Cloud Console](https://console.cloud.google.com/) and sign in with your Google account.
       
    2. **Create a New Project:**
       - Click on the project dropdown in the top left and select **"New Project"**.
       - Give it a name like `Aura Shorts Creator` and click **"Create"**.
       
    3. **Enable YouTube Data API v3:**
       - In the search bar at the top, search for **"YouTube Data API v3"**.
       - Click on the API result and click the blue **"ENABLE"** button.
       
    4. **Configure OAuth Consent Screen:**
       - In the left sidebar, click **"APIs & Services"** > **"OAuth consent screen"**.
       - Choose User Type **"External"** and click **"Create"**.
       - Fill in the required fields:
         - **App Name:** `Aura Video Agent`
         - **User Support Email:** Your email address
         - **Developer contact info:** Your email address
       - Click **"Save and Continue"** through scopes (no special scopes needed here).
       - **Test Users:** Under "Test Users", add **your own Gmail address** (the channel you want to upload to). This is critical since the app is in testing mode!
       - Click **"Save and Continue"** to finish.
       
    5. **Create OAuth Credentials:**
       - Go to the **"Credentials"** tab in the left sidebar.
       - Click **"+ CREATE CREDENTIALS"** at the top and select **"OAuth client ID"**.
       - Choose Application type: **"Desktop app"**.
       - Name it `Aura Shorts Agent` and click **"Create"**.
       
    6. **Download Client Secret:**
       - A popup will show. Click the **"DOWNLOAD JSON"** button next to your client credentials.
       - Rename the downloaded file to `client_secret.json` and upload it under **System Settings** in this dashboard!
       
    ---
    > [!TIP]
    > **Adding Test Users:** Make sure to add the Google account of the YouTube channel you intend to upload to under the *Test Users* section of the *OAuth Consent Screen* inside the Google Cloud Console. Otherwise, Google will return an `Access Blocked` error during authentication.
    """)

# ----------------- VIDEO GALLERY TAB -----------------
elif nav == "📂 Video Gallery":
    st.title("Generated Videos Gallery")
    st.write("View and upload all previously generated vertical shorts.")
    
    videos = list(OUTPUT_DIR.glob("*.mp4"))
    
    if not videos:
        st.info("No videos found. Go to **Creator Studio** to make your first short!")
    else:
        st.write(f"Found {len(videos)} created shorts.")
        
        # Grid display
        cols = st.columns(3)
        for idx, video_path in enumerate(videos):
            with cols[idx % 3]:
                st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
                st.markdown(f"**{video_path.name}**")
                st.video(str(video_path))
                
                # Check YouTube status to let user upload old videos
                if auth_status["authenticated"]:
                    st.write("---")
                    st.write("Publish to YouTube Channel")
                    priv = st.selectbox(f"Privacy {idx}", ["private", "unlisted", "public"], key=f"priv_{idx}")
                    
                    if st.button(f"🚀 Upload Video", key=f"up_{idx}"):
                        with st.spinner("Uploading to YouTube..."):
                            try:
                                vid_id = youtube_uploader.upload_video(
                                    video_path=str(video_path),
                                    title=f"{video_path.stem.replace('_', ' ').title()} #shorts",
                                    description="Created automatically using Aura AI Shorts Agent.",
                                    privacy_status=priv
                                )
                                st.success(f"Video uploaded successfully! ID: {vid_id}")
                                st.markdown(f"[Watch on YouTube](https://youtube.com/shorts/{vid_id})")
                            except Exception as e:
                                st.error(f"Upload failed: {e}")
                st.markdown("</div>", unsafe_allow_html=True)

# ----------------- CREATOR STUDIO TAB -----------------
else:
    st.title("AURA Creator Studio")
    st.write("Formulate, render, and deploy engaging vertical shorts in a couple of steps.")
    
    # Verify API Key exists before creating
    if not st.session_state.gemini_key:
        st.warning("Please configure your Gemini API Key in the 'System Settings' tab to continue.")
        st.stop()

    # Step-by-Step UI wizard
    # We maintain states in st.session_state to persist generated content
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1
        
    if "generated_data" not in st.session_state:
        st.session_state.generated_data = None
        
    if "compiled_video_path" not in st.session_state:
        st.session_state.compiled_video_path = None

    # Horizontal step tracker
    step_cols = st.columns(4)
    steps = ["1. Idea & Settings", "2. Script & Prompts Review", "3. Rendering Pipeline", "4. Share & Publish"]
    for idx, s in enumerate(steps):
        with step_cols[idx]:
            is_active = (st.session_state.current_step == idx + 1)
            color = "#00f2fe" if is_active else "#8888aa"
            weight = "bold" if is_active else "normal"
            st.markdown(f"<p style='color: {color}; font-weight: {weight}; text-align: center; margin-bottom:0;'>{s}</p>", unsafe_allow_html=True)
            st.markdown(f"<div style='height: 4px; background: {color}; border-radius: 2px;'></div>", unsafe_allow_html=True)
            
    st.write("---")

    # --- STEP 1: CONFIGURE & GENERATE SCRIPT ---
    if st.session_state.current_step == 1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("💡 Core Inspiration & Video settings")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            topic_input = st.text_input("Enter Topic/Idea", placeholder="e.g., Why time speeds up as you get older", help="The core concept Gemini will expand on.")
            selected_niche = st.selectbox("Channel Niche Preset", list(NICHE_TEMPLATES.keys()), index=list(NICHE_TEMPLATES.keys()).index(user_config.get("default_niche", "Intriguing Facts & Sci-Fi")))
            
        with col_s2:
            selected_voice = st.selectbox("Edge-TTS Voice Preset", list(VOICES.keys()), index=list(VOICES.keys()).index(user_config.get("default_voice", "Male (Andrew - Professional)")))
            music_option = st.selectbox("Select Background Music style", ["Niche Default", "No Music", "Custom/Upload"])
            
            custom_music_file = None
            if music_option == "Custom/Upload":
                custom_music_file = st.file_uploader("Upload custom background MP3 music track", type="mp3")
                
        st.write("---")
        
        if st.button("🔮 Formulate AI Script & Visual Prompts"):
            if not topic_input.strip():
                st.error("Please enter a valid topic or idea!")
            else:
                with st.spinner("AI Scriptwriter Agent researching and structuring your video content..."):
                    try:
                        # Load keys
                        script_agent.set_api_key(st.session_state.gemini_key)
                        # Generate structured JSON
                        result = script_agent.generate_short_data(topic_input, selected_niche)
                        
                        # Store in state
                        st.session_state.generated_data = result
                        st.session_state.selected_niche = selected_niche
                        st.session_state.selected_voice = VOICES[selected_voice]
                        
                        # Handle Custom Music file if uploaded
                        if music_option == "Custom/Upload" and custom_music_file is not None:
                            temp_music_path = TEMP_DIR / "custom_bg_music.mp3"
                            with open(temp_music_path, "wb") as f:
                                f.write(custom_music_file.read())
                            st.session_state.music_path = str(temp_music_path)
                        elif music_option == "No Music":
                            st.session_state.music_path = "NO_MUSIC"
                        else:
                            st.session_state.music_path = None # Will fall back to downloading niche default
                            
                        # Advance step
                        st.session_state.current_step = 2
                        st.rerun()
                    except Exception as e:
                        st.error(f"Script generation failed: {e}")
                        
        st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 2: REVIEW & EDIT SCRIPT/PROMPTS ---
    elif st.session_state.current_step == 2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("✍️ AI Scriptwriter Review Panel")
        st.write("Review, edit, and tailor the generated script, search terms, and YouTube metadata before sending them to the rendering pipeline.")
        
        data = st.session_state.generated_data
        
        # YouTube SEO Meta section
        st.markdown("### 🏷️ YouTube SEO Metadata")
        meta = data.get("metadata", {})
        title_val = st.text_input("SEO Video Title", value=meta.get("title", ""))
        desc_val = st.text_area("SEO Video Description", value=meta.get("description", ""), height=100)
        tags_val = st.text_input("SEO Video Tags (comma-separated)", value=", ".join(meta.get("tags", [])))
        
        st.write("---")
        
        # Scene editing section
        st.markdown("### 🎬 Script Narration & Matching Visual Keywords")
        st.write("Each block is a separate video segment. Keep sentences short and concise.")
        
        edited_scenes = []
        for idx, scene in enumerate(data.get("scenes", [])):
            st.markdown(f"**Scene {scene.get('scene_number', idx+1)}**")
            col_sc1, col_sc2 = st.columns([3, 2])
            
            with col_sc1:
                narration = st.text_area(f"Spoken Narration (Scene {idx+1})", value=scene.get("narration", ""), height=68, key=f"narr_{idx}")
            with col_sc2:
                keyword = st.text_input(f"Stock Video Search Keyword (Scene {idx+1})", value=scene.get("search_keyword", ""), help="Used to query Pexels portrait clips", key=f"key_{idx}")
                
            edited_scenes.append({
                "scene_number": scene.get("scene_number", idx+1),
                "narration": narration,
                "search_keyword": keyword,
                "visual_prompt": scene.get("visual_prompt", "")
            })
            st.write("")
            
        col_nav1, col_nav2 = st.columns([1, 1])
        
        with col_nav1:
            if st.button("⬅️ Back to Settings", type="secondary"):
                st.session_state.current_step = 1
                st.rerun()
                
        with col_nav2:
            if st.button("🔥 Confirm Script & Compile Video"):
                # Save edited contents into session state
                st.session_state.generated_data["metadata"] = {
                    "title": title_val,
                    "description": desc_val,
                    "tags": [t.strip() for t in tags_val.split(",") if t.strip()]
                }
                st.session_state.generated_data["scenes"] = edited_scenes
                
                # Advance step
                st.session_state.current_step = 3
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 3: RENDERING PIPELINE & PROGRESS ---
    elif st.session_state.current_step == 3:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("⚙️ Video Compilation Pipeline")
        st.write("Compiling synthetic assets. **Please do not close or refresh this tab.**")
        
        # We run the compile pipeline
        data = st.session_state.generated_data
        niche = st.session_state.selected_niche
        voice = st.session_state.selected_voice
        music_path = st.session_state.music_path
        
        # Status indicators
        t_tts = st.empty()
        t_assets = st.empty()
        t_render = st.empty()
        
        pbar = st.progress(0.0)
        
        try:
            # Step 3.1: TTS Synthesis
            t_tts.markdown("💬 **Step 3.1:** Generating studio synthetic voiceover with edge-tts...")
            pbar.progress(0.15)
            
            full_script_text = " ".join([s["narration"] for s in data["scenes"]])
            temp_voice_path = TEMP_DIR / "final_voiceover.mp3"
            
            words_timestamps = voice_engine.generate_voiceover(
                text=full_script_text,
                voice=voice,
                output_audio_path=str(temp_voice_path)
            )
            
            t_tts.markdown("💬 **Step 3.1:** Generating studio synthetic voiceover... `🟢 COMPLETE`")
            pbar.progress(0.40)
            
            # Step 3.2: Download Visual Stock Videos
            t_assets.markdown("📹 **Step 3.2:** Searching and downloading matching vertical clips from Pexels API...")
            
            # Update key dynamically
            asset_manager.set_api_key(st.session_state.pexels_key)
            
            scenes_to_compile = []
            num_scenes = len(data["scenes"])
            
            for idx, scene in enumerate(data["scenes"]):
                kw = scene["search_keyword"]
                t_assets.markdown(f"📹 **Step 3.2:** Sourcing vertical background video {idx+1}/{num_scenes} for keyword: *'{kw}'*...")
                
                vid_path = asset_manager.search_and_download_video(kw)
                
                scene_copy = scene.copy()
                scene_copy["local_video_path"] = vid_path
                scenes_to_compile.append(scene_copy)
                
                progress_step = 0.40 + (0.30 * (idx + 1) / num_scenes)
                pbar.progress(progress_step)
                
            t_assets.markdown("📹 **Step 3.2:** Sourcing vertical background videos... `🟢 COMPLETE`")
            pbar.progress(0.70)
            
            # Step 3.3: Compose and Render MoviePy
            t_render.markdown("🎬 **Step 3.3:** Rendering composite video tracks (MoviePy + Pillow text overlays)...")
            
            output_name = f"aurashort_{niche.lower().split(' ')[0]}_{hash(full_script_text) % 10000}.mp4"
            final_video_output = OUTPUT_DIR / output_name
            
            m_path = None if music_path == "NO_MUSIC" else music_path
            
            # Compile video
            compiled_path = video_compiler.compile_video(
                scenes_data=scenes_to_compile,
                voiceover_audio_path=str(temp_voice_path),
                words_timestamps=words_timestamps,
                output_video_path=str(final_video_output),
                niche=niche,
                user_music_path=m_path
            )
            
            t_render.markdown("🎬 **Step 3.3:** Rendering composite video tracks... `🟢 COMPLETE`")
            pbar.progress(1.00)
            
            # Store in session state
            st.session_state.compiled_video_path = compiled_path
            st.session_state.current_step = 4
            
            # Clean temp folder files (optional, keeping for now)
            st.success("Short video compiled successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error in rendering pipeline: {e}")
            logging.error(f"Pipeline failure: {e}", exc_info=True)
            if st.button("⬅️ Go Back to Review"):
                st.session_state.current_step = 2
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- STEP 4: PREVIEW & PUBLISH ON YOUTUBE ---
    elif st.session_state.current_step == 4:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🎉 Video Ready for Publishing!")
        st.write("Watch your generated Short in-app and deploy it to YouTube with a single click.")
        
        col_p1, col_p2 = st.columns([1, 1])
        
        with col_p1:
            st.markdown("### 📱 Video Preview Player (1080x1920)")
            video_path = st.session_state.compiled_video_path
            if video_path and Path(video_path).exists():
                st.video(video_path)
                st.markdown(f"💾 **Local File Location:** `{video_path}`")
            else:
                st.error("Compiled video file missing.")
                
        with col_p2:
            st.markdown("### 🚀 Publish on YouTube")
            meta = st.session_state.generated_data.get("metadata", {})
            
            title = st.text_input("Publish Title", value=meta.get("title", ""))
            desc = st.text_area("Publish Description", value=meta.get("description", ""), height=150)
            
            privacy = st.selectbox("Video Visibility", ["private", "unlisted", "public"], index=0, help="'private' is recommended for testing first!")
            
            st.write("---")
            
            # YouTube Status Check
            auth_info = youtube_uploader.get_auth_status()
            if not auth_info["authenticated"]:
                st.warning("⚠️ YouTube Channel is not connected. Connect under 'System Settings' first to auto-upload.")
                
                # Manual download fallback
                if video_path:
                    with open(video_path, "rb") as file:
                        btn = st.download_button(
                            label="💾 Download MP4 File",
                            data=file,
                            file_name=Path(video_path).name,
                            mime="video/mp4"
                        )
            else:
                if st.button("🚀 Push Automatically to My Channel"):
                    upload_progress = st.empty()
                    up_pbar = st.progress(0.0)
                    
                    def callback(prog):
                        up_pbar.progress(prog)
                        upload_progress.write(f"Uploading to YouTube API: {int(prog*100)}% complete...")
                    
                    try:
                        video_id = youtube_uploader.upload_video(
                            video_path=video_path,
                            title=title,
                            description=desc,
                            tags=meta.get("tags", []),
                            privacy_status=privacy,
                            progress_callback=callback
                        )
                        st.success(f"🎉 Short successfully uploaded to YouTube! Video ID: {video_id}")
                        st.markdown(f"🔗 **YouTube Short URL:** [youtube.com/shorts/{video_id}](https://youtube.com/shorts/{video_id})")
                    except Exception as e:
                        st.error(f"YouTube upload failed: {e}")
                        
            st.write("")
            if st.button("➕ Create Another Video", type="secondary"):
                st.session_state.current_step = 1
                st.session_state.generated_data = None
                st.session_state.compiled_video_path = None
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)
