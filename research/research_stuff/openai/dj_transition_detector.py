#!/usr/bin/env python3
"""
dj_transition_detector.py
--------------------------
Detects the “main part” / chorus of songs for DJ transitions.
Input: Folder of songs
Output: JSON file per song with main part start/end and transition point
"""

import sys
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------
# Helper: Strip code fences from GPT output
# ---------------------------------------------------
def clean_json_output(text: str) -> str:
    return text.replace("```json", "").replace("```", "").strip()

# ---------------------------------------------------
# Transcribe song using Whisper
# ---------------------------------------------------
def transcribe_song(client, audio_path):
    print(f"🔊 Transcribing: {os.path.basename(audio_path)}")
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"]
        )
    return result.model_dump()

# ---------------------------------------------------
# Analyze main part for DJ transition
# ---------------------------------------------------
def detect_main_part(client, transcript_dict):
    prompt = f"""
You are an expert music DJ assistant.

Using the following transcript with timestamps:
{json.dumps(transcript_dict, indent=2)}

Identify the most energetic and catchy part of the song that DJs should use for transition.
This main part is usually the first chorus and typically between 40-80 seconds into the track.

Return JSON only with:

{{
  "main_part_start": 0.0,
  "main_part_end": 0.0,
  "recommended_transition_time": 0.0,
  "description": "Brief note about why this is the best part"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You identify DJ transition points in songs."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    text = response.choices[0].message.content
    cleaned = clean_json_output(text)

    try:
        data = json.loads(cleaned)
        return data
    except json.JSONDecodeError:
        print("⚠️ GPT returned invalid JSON:")
        print(text)
        return None

# ---------------------------------------------------
# Main batch processing
# ---------------------------------------------------
def main():
    if len(sys.argv) < 3:
        print("Usage: python dj_transition_detector.py <input_folder> <output_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    os.makedirs(output_folder, exist_ok=True)

    # Load API key from .env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Missing OPENAI_API_KEY in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    SUPPORTED = (".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg")

    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(SUPPORTED):
            continue

        audio_path = os.path.join(input_folder, filename)
        print(f"\n🎵 Processing: {filename}")

        try:
            transcript = transcribe_song(client, audio_path)
            main_part = detect_main_part(client, transcript)

            if main_part is None:
                print(f"❌ Failed to detect main part for {filename}")
                continue

            # Save JSON output
            base = os.path.splitext(filename)[0]
            out_path = os.path.join(output_folder, f"{base}.json")
            with open(out_path, "w") as f:
                json.dump(main_part, f, indent=2)

            print(f"📁 Saved → {out_path}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")


if __name__ == "__main__":
    main()
