import os
import re
import hashlib
import logging
import requests
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
from moviepy.editor import VideoClip
from config import VIDEOS_DIR, TEMP_DIR

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class AssetManager:
    def __init__(self, pexels_api_key: str = None):
        """
        Initializes the AssetManager with a Pexels API Key.
        """
        self.api_key = pexels_api_key

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def _sanitize_filename(self, text: str) -> str:
        """
        Cleans text to make it a safe filename.
        """
        return re.sub(r'[^a-zA-Z0-9_\-]', '', text.replace(' ', '_'))

    def search_and_download_video(self, keyword: str) -> str:
        """
        Searches Pexels for a portrait stock video based on the keyword,
        downloads it, and returns the absolute local path.
        If the download fails or the API key is not present, generates
        a stunning procedural aesthetic gradient background video.
        """
        sanitized = self._sanitize_filename(keyword)
        # Create a unique filename hash to prevent keyword collisions
        keyword_hash = hashlib.md5(keyword.lower().encode('utf-8')).hexdigest()[:8]
        filename = f"pexels_{sanitized}_{keyword_hash}.mp4"
        local_path = VIDEOS_DIR / filename
        
        # Check cache first
        if local_path.exists() and local_path.stat().st_size > 100000:
            logging.info(f"Using cached stock video for '{keyword}' at: {local_path}")
            return str(local_path)

        # Attempt to download from Pexels if API key is provided
        if self.api_key and self.api_key.strip():
            try:
                headers = {"Authorization": self.api_key.strip()}
                # Request vertical (portrait) orientation videos
                url = "https://api.pexels.com/videos/search"
                params = {
                    "query": keyword,
                    "orientation": "portrait",
                    "per_page": 5,
                    "size": "medium" # Saves bandwidth and speeds up downloads
                }
                
                logging.info(f"Searching Pexels for video matching: '{keyword}'...")
                response = requests.get(url, headers=headers, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get("videos", [])
                    if videos:
                        # Find a suitable vertical video file link
                        for video in videos:
                            video_files = video.get("video_files", [])
                            # Sort video files to find appropriate resolution (preferring 720p or 1080p, portrait)
                            best_link = None
                            for f in video_files:
                                w = f.get("width", 0)
                                h = f.get("height", 0)
                                # Check if it's vertical (height > width)
                                if h > w:
                                    # Prefer HD quality (720x1280 or similar) over 4K or ultra-small SD
                                    if 720 <= w <= 1080:
                                        best_link = f.get("link")
                                        break
                                    # Secondary fallback: any vertical video
                                    best_link = f.get("link")
                            
                            if best_link:
                                logging.info(f"Downloading video from Pexels: {best_link}")
                                vid_res = requests.get(best_link, stream=True, timeout=30)
                                if vid_res.status_code == 200:
                                    with open(local_path, "wb") as f:
                                        for chunk in vid_res.iter_content(chunk_size=8192):
                                            if chunk:
                                                f.write(chunk)
                                    logging.info(f"Saved Pexels video to {local_path}")
                                    return str(local_path)
                    else:
                        logging.warning(f"No vertical stock videos found for keyword: '{keyword}'")
                else:
                    logging.error(f"Pexels API search failed with status code {response.status_code}: {response.text}")
            except Exception as e:
                logging.error(f"Error downloading Pexels video: {e}")

        # If Pexels fails or key is missing, build/generate a beautiful fallback gradient video!
        logging.info(f"Generating aesthetic shifting gradient fallback video for keyword: '{keyword}'...")
        fallback_filename = f"fallback_gradient_{keyword_hash}.mp4"
        fallback_path = VIDEOS_DIR / fallback_filename
        
        if fallback_path.exists():
            return str(fallback_path)
            
        return self._generate_aesthetic_gradient_video(str(fallback_path), duration=15)

    def _generate_aesthetic_gradient_video(self, output_path: str, duration: int = 15) -> str:
        """
        Generates a gorgeous high-speed shifting abstract gradient background video.
        Uses PIL to draw low-res gradient and upscale it via linear interpolation for ultra-high speed.
        """
        # Random seed based on output path to make each visual clip unique
        hash_val = int(hashlib.md5(output_path.encode()).hexdigest()[:6], 16)
        np.random.seed(hash_val)
        
        # Select vibrant, complementary preset hues
        hue_offset1 = np.random.uniform(0, 2*np.pi)
        hue_offset2 = np.random.uniform(0, 2*np.pi)
        
        def make_frame(t):
            # Time-varying colors
            c1_r = int(120 + 100 * np.sin(t * 0.4 + hue_offset1))
            c1_g = int(60 + 50 * np.cos(t * 0.3))
            c1_b = int(180 + 75 * np.sin(t * 0.5 + hue_offset1))
            
            c2_r = int(30 + 30 * np.sin(t * 0.3 + hue_offset2))
            c2_g = int(100 + 80 * np.sin(t * 0.5))
            c2_b = int(220 + 35 * np.cos(t * 0.2 + hue_offset2))
            
            w_small, h_small = 10, 20
            img = Image.new("RGB", (w_small, h_small))
            draw = ImageDraw.Draw(img)
            
            for y in range(h_small):
                r = y / (h_small - 1)
                color = (
                    int((1.0 - r) * c1_r + r * c2_r),
                    int((1.0 - r) * c1_g + r * c2_g),
                    int((1.0 - r) * c1_b + r * c2_b)
                )
                draw.line([(0, y), (w_small - 1, y)], fill=color)
            
            # High-speed upscale using bilinear scaling to get smooth gradients in HD
            img_large = img.resize((1080, 1920), Image.Resampling.BILINEAR)
            return np.array(img_large)

        try:
            # Create video clip from generator
            clip = VideoClip(make_frame, duration=duration)
            # Render using moderate FPS to save CPU and compile quickly
            clip.write_videofile(
                output_path, 
                fps=24, 
                codec="libx264", 
                audio=False, 
                logger=None,
                preset="ultrafast" # Speed optimization
            )
            clip.close()
            logging.info(f"Successfully rendered fallback gradient video at: {output_path}")
            return output_path
        except Exception as e:
            logging.error(f"Error generating fallback gradient video: {e}")
            raise RuntimeError(f"Fallback visual generation failed: {str(e)}")

# Test code block (only runs if executed directly)
if __name__ == "__main__":
    from config import TEMP_DIR
    manager = AssetManager()
    test_path = str(TEMP_DIR / "test_gradient.mp4")
    print("Testing programmatic gradient background generator...")
    try:
        res = manager._generate_aesthetic_gradient_video(test_path, duration=5)
        print(f"Gradient video generated successfully at {res}!")
    except Exception as e:
        print(f"Error: {e}")
