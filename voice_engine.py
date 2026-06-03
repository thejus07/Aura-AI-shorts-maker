import asyncio
import os
import re
import logging
from pathlib import Path
import edge_tts

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class VoiceEngine:
    def __init__(self):
        pass

    async def _generate_voiceover_async(self, text: str, voice: str, output_audio_path: str) -> list:
        """
        Internal async method to call edge-tts, save audio, and capture precise word boundary timestamps.
        """
        # Clean text slightly to avoid speech issues (e.g., removing multiple symbols, ensuring correct punctuation spacing)
        clean_text = re.sub(r'\s+', ' ', text).strip()
        
        communicate = edge_tts.Communicate(clean_text, voice)
        
        words_data = []
        audio_file = open(output_audio_path, "wb")
        
        try:
            # We iterate through the stream of audio and metadata chunks
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # Offset and duration are in ticks (100 nanoseconds units). 
                    # Convert to seconds: divide by 10,000,000 (1e7)
                    start_seconds = chunk["offset"] / 10000000.0
                    duration_seconds = chunk["duration"] / 10000000.0
                    end_seconds = start_seconds + duration_seconds
                    
                    word_text = chunk["text"]
                    
                    words_data.append({
                        "word": word_text,
                        "start": start_seconds,
                        "end": end_seconds
                    })
        finally:
            audio_file.close()

        logging.info(f"Generated TTS audio saved to {output_audio_path}")
        logging.info(f"Captured {len(words_data)} word boundaries with timestamps.")
        return words_data

    def generate_voiceover(self, text: str, voice: str, output_audio_path: str) -> list:
        """
        Synchronous wrapper to run the async audio generator.
        Returns a list of dictionaries: [{"word": "Hello", "start": 0.0, "end": 0.4}, ...]
        """
        # Create parent directories if they do not exist
        Path(output_audio_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Run async event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            words_data = loop.run_until_complete(
                self._generate_voiceover_async(text, voice, output_audio_path)
            )
            return words_data
        except Exception as e:
            logging.error(f"Error in edge-tts audio generation: {e}")
            raise RuntimeError(f"Voice generation failed: {str(e)}")
        finally:
            loop.close()

# Test code block (only runs if executed directly)
if __name__ == "__main__":
    import json
    from config import TEMP_DIR, VOICES
    
    engine = VoiceEngine()
    test_text = "This is a quick test of the AI Youtube Shorts voiceover engine. Space is massive!"
    test_voice = VOICES["Male (Andrew - Professional)"]
    test_output = str(TEMP_DIR / "test_voiceover.mp3")
    
    print(f"Testing TTS with voice: '{test_voice}'...")
    try:
        timestamps = engine.generate_voiceover(test_text, test_voice, test_output)
        print(f"Audio generated successfully at {test_output}")
        print("First few timestamps:")
        print(json.dumps(timestamps[:5], indent=2))
    except Exception as e:
        print(f"Error: {e}")
