# song_segmentation_using_openai

#!/usr/bin/env python3

"""
batch_song_segmentation.py
--------------------------
Processes a folder of audio files and generates JSON segmentation
(verse, chorus, bridge) for each song.

Usage:
    python batch_song_segmentation.py input_songs output_json
"""

import sys
import os
import json
from dotenv import load_dotenv
from openai import OpenAI


# -----------------------------------------------------------
# Helper: Remove code fence wrappers from GPT output
# -----------------------------------------------------------
def clean_json_output(text: str) -> str:
    return (
        text.replace("```json", "")
            .replace("```", "")
            .strip()
    )


# -----------------------------------------------------------
# Transcription step
# -----------------------------------------------------------
def transcribe_song(client, audio_path):
    print(f"🔊 Transcribing: {os.path.basename(audio_path)}")

    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"]
        )

    return result.model_dump()  # Convert to JSON-serializable dict


# -----------------------------------------------------------
# Structure Analysis step
# -----------------------------------------------------------
def analyze_structure(client, transcript_dict):
    prompt = f"""
You are an expert in music structure analysis.

Below is a transcription with timestamps:
{json.dumps(transcript_dict, indent=2)}

Identify these sections:
- verse
- chorus
- bridge

Return ONLY valid JSON (no explanations, no code fences):

{{
  "sections": [
    {{"label": "verse", "start": 0.0, "end": 20.0}},
    {{"label": "chorus", "start": 20.0, "end": 40.0}}
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You analyze song structure using timestamps."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    text = response.choices[0].message.content

    # Clean markdown fences
    cleaned = clean_json_output(text)

    try:
        data = json.loads(cleaned)
        return data

    except json.JSONDecodeError:
        print("⚠️ GPT returned invalid JSON for this song. Raw output:")
        print(text)
        return None


# -----------------------------------------------------------
# Main
# -----------------------------------------------------------
def main():
    # ------------------------- Arguments -------------------------
    if len(sys.argv) < 3:
        print("Usage: python batch_song_segmentation.py <input_folder> <output_folder>")
        sys.exit(1)

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    if not os.path.isdir(input_folder):
        print(f"❌ Input folder not found: {input_folder}")
        sys.exit(1)

    os.makedirs(output_folder, exist_ok=True)

    # ------------------------- Load API Key -------------------------
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ ERROR: Missing OPENAI_API_KEY in .env")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # ------------------------- Process songs -------------------------
    SUPPORTED = (".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg")

    for filename in os.listdir(input_folder):
        if not filename.lower().endswith(SUPPORTED):
            continue

        audio_path = os.path.join(input_folder, filename)
        print(f"\n🎵 Processing: {filename}")

        try:
            # Whisper transcription
            transcript = transcribe_song(client, audio_path)

            # GPT structure analysis
            structure = analyze_structure(client, transcript)

            if structure is None:
                print(f"❌ Failed to generate structure for: {filename}")
                continue

            # Save JSON
            base = os.path.splitext(filename)[0]
            out_path = os.path.join(output_folder, f"{base}.json")

            with open(out_path, "w") as f:
                json.dump(structure, f, indent=2)

            print(f"📁 Saved → {out_path}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")


# -----------------------------------------------------------
if __name__ == "__main__":
    main()
