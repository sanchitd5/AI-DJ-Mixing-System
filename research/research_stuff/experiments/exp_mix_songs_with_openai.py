import librosa
import soundfile as sf
import numpy as np
import os
import json
import re
from dotenv import load_dotenv
from openai import OpenAI
import argparse  # Added for configurable paths

# -----------------------------
# Load environment and OpenAI
# -----------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# Helper: Extract beat times (upgraded from spikes)
# -----------------------------
def extract_beat_times(audio, sr, target_beats=500):
    """
    Extract actual beat timestamps using librosa.beat.beat_track.
    Downsample if too many for analysis.
    """
    tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
    beat_times = librosa.frames_to_time(beats, sr=sr)
    # Downsample to target_beats if needed
    if len(beat_times) > target_beats:
        indices = np.linspace(0, len(beat_times) - 1, target_beats, dtype=int)
        beat_times = beat_times[indices]
    return beat_times, tempo

# -----------------------------
# Helper: Whisper transcription (with duration limit for efficiency)
# -----------------------------
def whisper_transcribe(path, duration=120):
    with open(path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            file=f,
            model="whisper-1"
        )
    return transcript.text

# -----------------------------
# Helper: Parse JSON safely (with better error handling)
# -----------------------------
def parse_json_from_gpt(out):
    out = out.strip()
    # Try to extract JSON block more robustly
    start = out.find('{')
    end = out.rfind('}') + 1
    if start != -1 and end != 0:
        json_str = out[start:end]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in GPT output: {e}\nRaw: {json_str}")
    else:
        raise ValueError(f"No JSON found in GPT output:\n{out}")

# -----------------------------
# Helper: Ask GPT-4o to detect chorus (fixed API, pass beats as string)
# -----------------------------
def ask_gpt4o_for_chorus(lyrics_short, beats1_str, beats2_str, sr1):
    prompt = f"""
You are a music analyst.

Task:
- Detect chorus_start_sec and chorus_end_sec for Song1.
- Chorus must be inside 30–100 seconds.
- Chorus is high-energy, loud, main part of song.
- Chorus often contains the main line or the song's title.
- Whisper transcription of Song1 lyrics:
\"\"\"
{lyrics_short}
\"\"\"

Beat times for Song1 (seconds): {beats1_str}
Beat times for Song2 (seconds): {beats2_str}

Rules:
1. If main line appears in 30–100 sec, that is the fixed chorus_start.
2. The waveform spike pattern can only adjust chorus_start within ±8 beats from this point (use beat times to estimate beats).
3. Second song should start at the first beat of the spike set to align with Song1's chorus end beat.
4. Return ONLY JSON:
{{
  "chorus_start_sec": number,
  "chorus_end_sec": number
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return parse_json_from_gpt(response.choices[0].message.content)

# -----------------------------
# Detect chorus points (upgraded with beat alignment)
# -----------------------------
def detect_chorus_points(song1_path, song2_path):
    print("→ Loading up to 120 seconds of audio for analysis...")
    y1, sr1 = librosa.load(song1_path, sr=None, offset=0, duration=120)
    y2, sr2 = librosa.load(song2_path, sr=None, offset=0, duration=120)

    print("→ Extracting beat times...")
    beats1, tempo1 = extract_beat_times(y1, sr1)
    beats2, tempo2 = extract_beat_times(y2, sr2)

    # Serialize beats for GPT prompt
    beats1_str = ", ".join(f"{t:.3f}" for t in beats1)
    beats2_str = ", ".join(f"{t:.3f}" for t in beats2)

    print("→ Transcribing lyrics with Whisper...")
    lyrics = whisper_transcribe(song1_path)
    lyrics_short = " ".join(lyrics.split()[:500])  # Truncate to first 500 words

    print("→ Asking GPT-4o to detect chorus boundaries...")
    result = ask_gpt4o_for_chorus(lyrics_short, beats1_str, beats2_str, sr1)

    chorus_start = float(result["chorus_start_sec"])
    chorus_end = float(result["chorus_end_sec"])

    # Align chorus_start to nearest beat in Song1
    if len(beats1) > 0:
        nearest_beat_idx = np.argmin(np.abs(beats1 - chorus_start))
        chorus_start_aligned = beats1[nearest_beat_idx]
    else:
        chorus_start_aligned = chorus_start  # Fallback

    # Align chorus_end to next phrase (e.g., 8 beats after start)
    if len(beats1) > nearest_beat_idx + 8:
        chorus_end_aligned = beats1[nearest_beat_idx + 8]  # Rough 8-beat phrase
    else:
        chorus_end_aligned = chorus_end

    # Validate bounds
    full_len1 = librosa.get_duration(filename=song1_path)
    chorus_start = max(30, min(chorus_start_aligned, full_len1 - 10))
    chorus_end = max(chorus_start + 5, min(chorus_end_aligned, full_len1))

    return chorus_start, chorus_end

# -----------------------------
# Detect BPM (with full track for accuracy)
# -----------------------------
def detect_bpm(path):
    y, sr = librosa.load(path, sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo

# -----------------------------
# Time-stretch helper
# -----------------------------
def time_stretch(audio, rate):
    return librosa.effects.time_stretch(audio, rate)

# -----------------------------
# Progressive pitch ramp for transition (new: simulates gradual BPM increase)
# -----------------------------
def apply_tempo_ramp(audio_segment, sr, start_rate=1.0, end_rate=1.0, num_segments=10):
    """
    Gradually stretches segments of audio to ramp tempo from start_rate to end_rate.
    Preserves pitch; shortens/lengthens overall duration.
    """
    segment_len = len(audio_segment) // num_segments
    ramped_segments = []
    for i in range(num_segments):
        seg = audio_segment[i * segment_len:(i + 1) * segment_len]
        if len(seg) == 0:
            break
        # Linear rate interpolation
        seg_rate = start_rate + (end_rate - start_rate) * (i / (num_segments - 1))
        seg_stretched = time_stretch(seg, seg_rate)
        ramped_segments.append(seg_stretched)
    return np.concatenate(ramped_segments)

# -----------------------------
# Mix songs (upgraded: proper crossfade, normalization, optional ramp)
# -----------------------------
def mix_songs(song1_path, song2_path, chorus_start, chorus_end, fade_duration=3.0, use_ramp=True):
    y1, sr1 = librosa.load(song1_path, sr=None)
    y2, sr2 = librosa.load(song2_path, sr=None)
    sr = sr1  # Assume same SR; resample if needed

    # BPM detection
    bpm1 = detect_bpm(song1_path)
    bpm2 = detect_bpm(song2_path)
    print(f"BPM1 = {bpm1:.2f}")
    print(f"BPM2 = {bpm2:.2f}")

    # Global stretch for base alignment (ramp will adjust transition)
    rate1_to_2 = bpm2 / bpm1 if bpm1 != 0 else 1.0
    if abs(rate1_to_2 - 1.0) > 0.01:  # Only if different
        if bpm1 < bpm2:
            # Stretch song1 tail for ramp; full song2
            y1_stretched = y1
            y2_stretched = y2
            print(f"Preparing ramp: Song1 will accelerate to {bpm2:.2f} BPM during transition")
        else:
            # Stretch song2 to match (reverse case)
            y1_stretched = y1
            y2_stretched = time_stretch(y2, 1 / rate1_to_2)
            print(f"Song2 stretched to match Song1 BPM ({bpm1:.2f})")
    else:
        y1_stretched = y1
        y2_stretched = y2
        print("Both songs have same BPM — no stretching needed.")

    # Convert timing → samples
    chorus_start_s = int(chorus_start * sr)
    chorus_end_s = int(chorus_end * sr)
    fade_samples = int(fade_duration * sr)

    # Safety checks
    full_len1 = len(y1_stretched)
    if chorus_end_s <= chorus_start_s:
        raise ValueError("chorus_end must be greater than chorus_start.")
    if chorus_end_s + fade_samples > full_len1:
        fade_samples = full_len1 - chorus_end_s
    overlap_samples = chorus_end_s - chorus_start_s + fade_samples  # Full overlap window

    # Prepare Song1 with optional ramp on transition segment
    if use_ramp and bpm1 < bpm2:
        # Extract transition segment (from chorus_start to end)
        trans_start_s = chorus_start_s
        trans_audio = y1_stretched[trans_start_s:]
        # Apply ramp: start at 1.0, end at rate1_to_2
        ramped_trans = apply_tempo_ramp(trans_audio, sr, 1.0, rate1_to_2)
        # Reassemble: pre-transition + ramped (note: ramp shortens, so pad if needed)
        pre_trans = y1_stretched[:trans_start_s]
        y1_stretched = np.concatenate([pre_trans, ramped_trans])
        # Adjust indices (ramped is shorter, so shift end)
        ramp_shorten = len(trans_audio) - len(ramped_trans)
        chorus_end_s -= ramp_shorten  # Approximate
        fade_samples = min(fade_samples, len(y1_stretched) - chorus_end_s)
        print(f"Ramp applied: Transition shortened by ~{ramp_shorten/sr:.2f}s")

    # Pad Song2 to start at chorus_start
    y2_padded = np.pad(y2_stretched, (int(chorus_start * sr), 0))

    # Extend both to max length
    max_len = max(len(y1_stretched), len(y2_padded))
    y1_ext = np.pad(y1_stretched, (0, max_len - len(y1_stretched)), mode='constant')
    y2_ext = np.pad(y2_padded, (0, max_len - len(y2_padded)), mode='constant')

    # Apply crossfade in overlap: fade out y1, fade in y2
    overlap_start_s = chorus_start_s
    overlap_end_s = min(chorus_start_s + overlap_samples, min(len(y1_ext), len(y2_ext)))
    overlap_len = overlap_end_s - overlap_start_s

    if overlap_len > 0:
        # Fade curves
        fade_out = np.linspace(1.0, 0.0, overlap_len)
        fade_in = np.linspace(0.0, 1.0, overlap_len)

        # Apply to y1 and y2 in overlap
        y1_ext[overlap_start_s:overlap_end_s] *= fade_out
        y2_ext[overlap_start_s:overlap_end_s] *= fade_in

        # Zero y1 after overlap (cut remainder)
        y1_ext[overlap_end_s:] = 0.0

    # Mix and normalize to prevent clipping
    final_audio = y1_ext + y2_ext
    max_amp = np.max(np.abs(final_audio))
    if max_amp > 0:
        final_audio /= max_amp * 1.1  # -0.83 dB headroom

    # Export with timestamp to avoid overwrite
    timestamp = librosa.get_duration(y=y1)  # Approx
    output_name = f"final_mix_{int(timestamp):.0f}s.wav"
    sf.write(output_name, final_audio, sr)
    print(f"Exported → {output_name}")

# -----------------------------
# MAIN RUN (with argparse for flexibility)
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI DJ Mixer")
    parser.add_argument("--song1", default="songs/song1.mp3", help="Path to Song 1")
    parser.add_argument("--song2", default="songs/song2.mp3", help="Path to Song 2")
    parser.add_argument("--fade", type=float, default=3.0, help="Fade duration (seconds)")
    parser.add_argument("--no-ramp", action="store_true", help="Disable tempo ramp")
    args = parser.parse_args()

    print("\n-------------------------------------------")
    print(" DETECTING CHORUS START & END AUTOMATICALLY ")
    print("-------------------------------------------")

    if not os.path.exists(args.song1) or not os.path.exists(args.song2):
        raise FileNotFoundError(f"Song files not found: {args.song1}, {args.song2}")

    chorus_start, chorus_end = detect_chorus_points(args.song1, args.song2)

    print(f"\nDetected chorus_start = {chorus_start:.2f} sec")
    print(f"Detected chorus_end   = {chorus_end:.2f} sec\n")

    mix_songs(args.song1, args.song2, chorus_start, chorus_end, args.fade, not args.no_ramp)