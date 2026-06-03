import os
import urllib.request
import logging
from pathlib import Path
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import (
    VideoFileClip, 
    AudioFileClip, 
    ImageClip, 
    CompositeVideoClip, 
    CompositeAudioClip,
    concatenate_videoclips
)
from moviepy.audio.fx.all import volumex
from config import (
    FONT_PATH, 
    DEFAULT_FONT_URL, 
    DEFAULT_FONT_NAME,
    DEFAULT_VIDEO_WIDTH, 
    DEFAULT_VIDEO_HEIGHT,
    MUSIC_DIR,
    ROYALTY_FREE_MUSIC
)

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class VideoCompiler:
    def __init__(self):
        self._ensure_font_exists()

    def _ensure_font_exists(self):
        """
        Downloads a gorgeous premium bold font (Montserrat-Black) if it's not present locally.
        This guarantees stunning subtitle styling regardless of the user's OS fonts.
        """
        if not FONT_PATH.exists():
            try:
                logging.info(f"Downloading default aesthetic font '{DEFAULT_FONT_NAME}'...")
                FONT_PATH.parent.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(DEFAULT_FONT_URL, FONT_PATH)
                logging.info(f"Font downloaded successfully to: {FONT_PATH}")
            except Exception as e:
                logging.error(f"Failed to download default font: {e}. Subtitles will fall back to system defaults.")

    def _resize_and_crop(self, clip, target_w=DEFAULT_VIDEO_WIDTH, target_h=DEFAULT_VIDEO_HEIGHT):
        """
        Resizes and crops a VideoFileClip to fit exactly 1080x1920 (9:16) without stretching.
        Crops excess from center.
        """
        scale_w = target_w / clip.w
        scale_h = target_h / clip.h
        scale = max(scale_w, scale_h)
        
        new_w = int(clip.w * scale)
        new_h = int(clip.h * scale)
        
        resized_clip = clip.resize((new_w, new_h))
        
        # Calculate cropping offsets to center
        x1 = (new_w - target_w) // 2
        y1 = (new_h - target_h) // 2
        
        cropped_clip = resized_clip.crop(x1=x1, y1=y1, width=target_w, height=target_h)
        return cropped_clip

    def _download_bg_music_placeholder(self, niche: str) -> str:
        """
        Downloads a royalty-free background music placeholder if not present.
        """
        from config import NICHE_TEMPLATES
        template = NICHE_TEMPLATES.get(niche, NICHE_TEMPLATES["Intriguing Facts & Sci-Fi"])
        music_key = template.get("default_music", "facts")
        music_info = ROYALTY_FREE_MUSIC.get(music_key, ROYALTY_FREE_MUSIC["facts"])
        music_path = MUSIC_DIR / music_info["name"]
        
        if not music_path.exists():
            try:
                logging.info(f"Downloading royalty-free background music: '{music_info['name']}'...")
                urllib.request.urlretrieve(music_info["url"], music_path)
                logging.info(f"Background music downloaded successfully.")
            except Exception as e:
                logging.error(f"Failed to download background music: {e}")
                return None
        return str(music_path)

    def _group_words_into_phrases(self, words_data: list, words_per_phrase: int = 3) -> list:
        """
        Groups single words into short phrases (e.g. blocks of 3 words) suitable for vertical screen space.
        Returns a list of phrase groups with their respective word boundary dictionaries.
        """
        phrases = []
        for i in range(0, len(words_data), words_per_phrase):
            phrases.append(words_data[i:i+words_per_phrase])
        return phrases

    def _draw_subtitle_frame(self, phrase_words: list, active_word_index: int, font_size: int, text_color: str, outline_color: str) -> np.ndarray:
        """
        Uses Pillow to draw a transparent frame containing the phrase, 
        highlighting the active word with dynamic coloring and high contrast.
        Returns a numpy array representation of the transparent RGBA image.
        """
        w, h = DEFAULT_VIDEO_WIDTH, DEFAULT_VIDEO_HEIGHT
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load premium font or fallback
        try:
            font = ImageFont.truetype(str(FONT_PATH), font_size)
        except Exception:
            font = ImageFont.load_default()
            
        # Draw settings
        space_char = " "
        outline_width = 6
        
        # Step 1: Pre-calculate sizes of all words in the phrase
        word_widths = []
        space_width = draw.textlength(space_char, font=font)
        
        total_width = 0
        for word_dict in phrase_words:
            word_str = word_dict["word"].upper() # Modern viral shorts use uppercase text
            word_w = draw.textlength(word_str, font=font)
            word_widths.append(word_w)
            total_width += word_w
            
        total_width += space_width * (len(phrase_words) - 1)
        
        # Center alignment calculations
        x_start = (w - total_width) // 2
        # Position subtitles slightly lower than center for visual balance (middle-bottom)
        y_pos = int(h * 0.58) 
        
        # Step 2: Draw the words
        current_x = x_start
        for idx, word_dict in enumerate(phrase_words):
            word_str = word_dict["word"].upper()
            word_w = word_widths[idx]
            
            # Determine color: Active word is bright/highlighted, others are clean white
            is_active = (idx == active_word_index)
            fill_color = text_color if is_active else "#FFFFFF"
            
            # Draw outline/shadow for ultimate readability against dynamic backgrounds
            for ox in range(-outline_width, outline_width + 1):
                for oy in range(-outline_width, outline_width + 1):
                    # Make a circular outline
                    if ox*ox + oy*oy <= outline_width*outline_width:
                        draw.text((current_x + ox, y_pos + oy), word_str, font=font, fill=outline_color)
            
            # Draw actual text
            draw.text((current_x, y_pos), word_str, font=font, fill=fill_color)
            
            # Advance pointer
            current_x += word_w + space_width
            
        return np.array(img)

    def compile_video(self, scenes_data: list, voiceover_audio_path: str, words_timestamps: list, output_video_path: str, niche: str, user_music_path: str = None, style_overrides: dict = None) -> str:
        """
        Compiles the entire Short: joins background videos, loops audio, overlays Pillow captions,
        adds background music, and renders the final vertical MP4 video.
        """
        # Ensure directories exist
        Path(output_video_path).parent.mkdir(parents=True, exist_ok=True)
        
        logging.info("Starting video compilation workflow...")
        
        # Determine styling
        from config import NICHE_TEMPLATES
        template = NICHE_TEMPLATES.get(niche, NICHE_TEMPLATES["Intriguing Facts & Sci-Fi"])
        
        font_size = template["font_size"]
        text_color = template["subtitle_color"]
        outline_color = template["outline_color"]
        
        if style_overrides:
            font_size = style_overrides.get("font_size", font_size)
            text_color = style_overrides.get("subtitle_color", text_color)
            outline_color = style_overrides.get("outline_color", outline_color)

        # 1. Load Audio
        voiceover_audio = AudioFileClip(voiceover_audio_path)
        total_duration = voiceover_audio.duration
        
        # 2. Build Background Video Track
        # Calculate duration of each scene based on narration coverage or partition equally
        num_scenes = len(scenes_data)
        time_per_scene = total_duration / num_scenes
        
        video_clips = []
        
        for idx, scene in enumerate(scenes_data):
            video_path = scene.get("local_video_path")
            if not video_path or not Path(video_path).exists():
                logging.warning(f"Video file missing for scene {idx+1}. Skipping.")
                continue
                
            try:
                # Load stock clip
                clip = VideoFileClip(video_path)
                
                # Check clip length and crop/loop as needed to fit scene time duration
                scene_start_time = idx * time_per_scene
                scene_end_time = (idx + 1) * time_per_scene
                if idx == num_scenes - 1:
                    scene_end_time = total_duration # Capture remainder
                scene_duration = scene_end_time - scene_start_time
                
                # If clip is shorter than required scene duration, loop it. Else trim.
                if clip.duration < scene_duration:
                    # Loop clip
                    clip = clip.loop(duration=scene_duration)
                else:
                    # Trim clip from beginning/middle
                    clip = clip.subclip(0, scene_duration)
                    
                # Format to vertical 9:16
                formatted_clip = self._resize_and_crop(clip)
                video_clips.append(formatted_clip)
                
            except Exception as e:
                logging.error(f"Error loading and processing clip '{video_path}': {e}")
                
        if not video_clips:
            raise RuntimeError("No visual clips could be loaded or compiled for the background.")
            
        # Concatenate background clips
        background_video = concatenate_videoclips(video_clips, method="compose")
        background_video = background_video.set_duration(total_duration)
        
        # 3. Create Subtitle Overlay Track
        subtitle_clips = []
        phrases = self._group_words_into_phrases(words_timestamps, words_per_phrase=3)
        
        logging.info("Rendering Pillow dynamic caption clips...")
        for phrase in phrases:
            # Render a separate ImageClip for each word being highlighted in the phrase
            for active_idx, active_word in enumerate(phrase):
                # Start and duration for the specific word highlight
                word_start = active_word["start"]
                word_end = active_word["end"]
                word_duration = max(0.05, word_end - word_start) # avoid negative or tiny clips
                
                # Generate Pillow image frame as NumPy array
                rgba_frame = self._draw_subtitle_frame(
                    phrase, 
                    active_word_index=active_idx, 
                    font_size=font_size,
                    text_color=text_color, 
                    outline_color=outline_color
                )
                
                # Convert RGBA frame into ImageClip
                # moviepy handles RGBA numpy arrays as images with transparency automatically!
                sub_clip = ImageClip(rgba_frame)
                sub_clip = sub_clip.set_start(word_start).set_duration(word_duration)
                subtitle_clips.append(sub_clip)
                
        # 4. Handle Background Music
        music_path = user_music_path
        if not music_path:
            # Fallback to template downloading
            music_path = self._download_bg_music_placeholder(niche)
            
        final_audio_sources = [voiceover_audio]
        
        if music_path and Path(music_path).exists():
            try:
                bg_music = AudioFileClip(music_path)
                # Loop background music to match total duration
                bg_music = bg_music.loop(duration=total_duration)
                # Apply audio ducking: standard voiceover at volume 1.0, background music at ~0.08 - 0.12 (quiet)
                bg_music = bg_music.volumex(0.10)
                final_audio_sources.append(bg_music)
                logging.info(f"Integrated background music '{music_path}' with ducking.")
            except Exception as e:
                logging.error(f"Error integrating background music: {e}")
                
        composite_audio = CompositeAudioClip(final_audio_sources)
        
        # 5. Composite Final Video
        final_video = CompositeVideoClip([background_video, *subtitle_clips])
        final_video = final_video.set_audio(composite_audio)
        
        # 6. Render
        logging.info(f"Rendering final MP4 to: {output_video_path}...")
        final_video.write_videofile(
            output_video_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            remove_temp=True,
            threads=4,
            preset="medium"
        )
        
        # Close all clips to prevent file locking and memory leaks
        final_video.close()
        background_video.close()
        voiceover_audio.close()
        for c in video_clips:
            c.close()
        for s in subtitle_clips:
            s.close()
            
        logging.info("Video rendering complete!")
        return output_video_path

# Test block
if __name__ == "__main__":
    pass
