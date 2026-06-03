import json
import logging
import google.generativeai as genai
from config import NICHE_TEMPLATES

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ScriptAgent:
    def __init__(self, api_key: str = None):
        """
        Initializes the ScriptAgent.
        If api_key is provided, configures the genai client.
        """
        self.api_key = api_key
        if api_key:
            genai.configure(api_key=api_key)
        
    def set_api_key(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)

    def generate_short_data(self, topic: str, niche: str) -> dict:
        """
        Generates structured Script, Visual Prompts, Search Keywords, and YouTube SEO metadata.
        Uses structured JSON response from Gemini for 100% reliable parsing.
        """
        if not self.api_key:
            raise ValueError("Gemini API Key is not set. Please set it in Settings.")

        # Get niche specifications
        niche_details = NICHE_TEMPLATES.get(niche, NICHE_TEMPLATES["Motivational & Growth"])
        niche_prompt = niche_details["system_prompt_niche"]
        
        # Build strict system instruction
        system_instruction = (
            "You are an elite, viral YouTube Shorts creator and scriptwriter. Your channel focuses on producing high-retention, "
            "addictively watchable 9:16 vertical videos. You understand that the first 3 seconds require an irresistible hook, "
            "sentences must be short and impactful for easy dynamic caption overlay, and the video must end with a natural loop "
            "or a high-impact call to action. The total spoken script must take 30 to 45 seconds to read (roughly 100 to 140 words total)."
        )

        prompt = f"""
Write a complete YouTube Short about the topic: "{topic}".
The niche of the channel is: "{niche}", which means: {niche_prompt}

Generate a fully structured JSON response. The JSON must exactly match this schema:
{{
  "metadata": {{
    "title": "A highly clickable, catchy, viral YouTube Shorts title (under 55 characters, must include #shorts)",
    "description": "An engaging description that summarizes the video, includes a hook, and 3-5 relevant hashtags",
    "tags": ["list", "of", "10-15", "highly", "searched", "seo", "tags", "for", "discoverability"]
  }},
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "The exact spoken words for this scene. Keep it highly catchy, short, and impactful.",
      "visual_prompt": "A vivid description of the vertical stock video that matches this sentence (e.g. 'A slow motion shot of a man climbing a steep mountain peak, sunrise, golden lighting, cinematic')",
      "search_keyword": "A single extremely accurate English search keyword or short phrase to find this stock video on Pexels (e.g. 'climbing mountain sunrise')"
    }}
  ]
}}

Guidelines for "scenes":
- Break the video into 4 to 7 scenes.
- Total narration across all scenes should be 100-140 words.
- Each scene's narration MUST be a single, short sentence or clause.
- Ensure the "search_keyword" is simple, clean, and highly relevant, suitable for a standard stock video site query (avoid complex phrasing, use literal search terms like "galaxy space", "clock ticking", "rain storm").

Return ONLY valid raw JSON conforming to this schema. Do not enclose it in markdown code blocks like ```json ... ```. Just return the JSON object.
"""

        model_names = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        last_error = None
        
        for m_name in model_names:
            try:
                logging.info(f"Generating script using model: '{m_name}'...")
                model = genai.GenerativeModel(
                    model_name=m_name,
                    system_instruction=system_instruction
                )
                
                # Request JSON output
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # Parse response
                raw_text = response.text.strip()
                # In case the model wrapped it in markdown code blocks anyway
                if raw_text.startswith("```json"):
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()
                    
                data = json.loads(raw_text)
                
                logging.info(f"Successfully generated script with {len(data.get('scenes', []))} scenes using '{m_name}'.")
                return data
                
            except Exception as e:
                logging.warning(f"Model '{m_name}' failed: {e}")
                last_error = e
                continue
                
        # If we reached here, all models failed
        logging.error(f"All generative models failed. Last error: {last_error}")
        raise RuntimeError(f"Failed to generate script using Gemini API: {str(last_error)}")

# Test code block (only runs if executed directly)
if __name__ == "__main__":
    import os
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        agent = ScriptAgent(api_key)
        try:
            result = agent.generate_short_data("3 Terrifying Facts About The Ocean", "Immersive Storytelling & Horror")
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("GEMINI_API_KEY environment variable not set, skipping direct script test.")
