"""
DJ Mixing Pipeline: Setlist Generation + Audio Analysis.
Handles MP3 scanning, OpenAI setlist parsing, BPM refinement, key/vocal/chorus analysis.
Chorus detection uses 5-method fusion (repetition, energy, spectral contrast, MFCC melody, self-similarity).
Updated with advanced segmentation inspired by mir-aidj/all-in-one: hierarchical clustering for boundaries,
feature-based scoring, and heuristic labeling for intro/verse/chorus/bridge/outro/break using position, energy,
repetition, and consecutive similarity.
Monkey-patches resampy for Numba compatibility. Outputs 'analyzed_setlist.json' with segments and first chorus times.
"""

import os
os.environ['NUMBA_DISABLE_JIT'] = '1'  # Disable Numba JIT to avoid resampy errors

import json
try:
    import openai
except Exception:
    # OpenAI client might not be installed in local dev/test environments. Only optional for analysis.
    openai = None
import re
import warnings
from dotenv import load_dotenv
warnings.filterwarnings("ignore", category=UserWarning, module="numba")
import librosa
from librosa.feature import chroma_stft, rms, mfcc, spectral_contrast
import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.signal import find_peaks
from scipy import signal

# Monkey patch librosa.resample to use scipy.signal.resample to avoid resampy Numba issues
def custom_resample(y, orig_sr, target_sr=None, scale=None, res_type='kaiser_best', **kwargs):
    """
    Custom resample using scipy to avoid resampy issues.
    """
    if scale is None:
        scale = target_sr / orig_sr if target_sr is not None else 1.0
    new_len = int(len(y) * scale)
    return signal.resample(y, new_len, axis=-1)

librosa.resample = custom_resample

# Load environment variables from the .env file to securely manage API keys.
load_dotenv()

# Configure the OpenAI client with the API key from environment.
if openai is not None:
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        client = None
else:
    client = None

# Define the directory path where local MP3 song files are stored.
SONGS_DIR = "./songs"


def get_available_songs():
    """
    Scans the specified songs directory (SONGS_DIR) for MP3 files and returns a list of dictionaries
    containing metadata for each available song (no BPM estimation).
    """
    available_songs = []
    for filename in os.listdir(SONGS_DIR):
        if filename.lower().endswith(".mp3"):
            clean_name = filename[:-4]
            if clean_name.startswith("[iSongs.info] "):
                clean_name = clean_name.split(" - ", 1)[-1] if " - " in clean_name else clean_name.split(" ", 2)[-1]
            parts = clean_name.split(" - ", 1)
            if len(parts) == 2:
                artist, title = parts
            else:
                artist = "Unknown"
                title = clean_name
            available_songs.append({"title": title, "artist": artist, "file": filename})
    return available_songs


def refine_bpm(title, artist):
    """
    Targeted OpenAI call to refine BPM if it defaulted to 120.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a music metadata expert. Respond ONLY with the exact integer BPM (e.g., 94) from reliable sources like Tunebat, SongBPM, or Musicstax. No units, no explanation, no extra text."},
                {"role": "user", "content": f"What is the precise BPM of '{title}' by '{artist}'?"}
            ],
            temperature=0.0,
            max_tokens=5
        )
        bpm_text = response.choices[0].message.content.strip()
        if bpm_text.isdigit():
            bpm = int(bpm_text)
            if 60 <= bpm <= 220:
                print(f"Refined BPM for '{title}' by '{artist}': {bpm}")
                return bpm
    except Exception as e:
        print(f"BPM refinement failed for '{title}' by '{artist}': {e}")
    return 120


def parse_time_segments_and_generate_setlist(user_input, available_songs):
    """
    Uses OpenAI to parse user input into setlist with BPMs, then refines defaults.
    """
    available_songs_str = json.dumps(available_songs, indent=2)
    system_prompt = "You are a DJ setlist generator. Analyze the user input and available songs, then output ONLY a valid JSON object in the exact format specified. Do not include any other text."
    user_prompt = f"""
    You are a professional DJ setlist generator.

    TASK SUMMARY:
        1. Parse the event description into:
        - Time segments (start, end, description)
        - Preferred genres
        - Specific songs mentioned by the user

        2. Using ONLY the available local songs list below, create an unordered setlist for each time segment.

        3. For every local song, recall or look up the BPM from trusted sources. Do not lie, do not guess, please return a value that you are 100% confident on
        - Use precise BPMs.
        - Avoid guesses.
        - If and ONLY IF truly unknown after trying to recall: use 120.

        4. For each time segment:
        - Select a pool of songs matching the vibe, genre, and description.
        - Prioritize exact matches of specific songs when available.
        - Only include tracks whose BPMs differ by <2 BPM within that segment.
        - Estimate number of songs based on duration (1 track ≈ 3–4 minutes).
        - DO NOT ORDER the tracks. Output an unordered list.

        5. For specific songs requested by the user but not found in the available local songs list:
        - Add them to "unavailable_songs" with reason "not found".

    AVAILABLE LOCAL SONGS:
    {available_songs_str}

    USER INPUT:
    \"\"\"{user_input}\"\"\"

    OUTPUT JSON FORMAT (STRICT — DO NOT ADD EXTRA TEXT):
    {{
      "time_segments": [
        {{"start": "HH:MM", "end": "HH:MM", "description": "string"}}
      ],
      "genres": ["genre1", "genre2"],
      "specific_songs": [
        {{"title": "string", "artist": "string"}}
      ],
      "unavailable_songs": [
        {{"title": "string", "artist": "string", "reason": "string"}}
      ],
      "setlist": [
        {{
          "time": "HH:MM–HH:MM",
          "tracks": [
            {{
              "title": "string",
              "artist": "string",
              "file": "filename.mp3",
              "bpm": integer
            }}
          ]
        }}
      ]
    }}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1
    )
    response_text = response.choices[0].message.content.strip()
    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    json_string = json_match.group(1) if json_match else response_text
    try:
        parsed_data = json.loads(json_string)
        for segment in parsed_data.get("setlist", []):
            for track in segment.get("tracks", []):
                if track.get("bpm") == 120:
                    track["bpm"] = refine_bpm(track["title"], track["artist"])
        return parsed_data
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to parse JSON. Raw response: '{response_text}'")
        raise ValueError("Failed to parse OpenAI response into JSON") from e


def estimate_key(chroma_mean):
    """
    Estimates key and scale using Krumhansl-Kessler profiles.
    """
    major_profile = np.array([6.35, 2.26, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    major_profile /= np.sum(major_profile)
    minor_profile /= np.sum(minor_profile)
    chroma_mean_norm = chroma_mean / np.sum(chroma_mean)
    major_corr_c = np.corrcoef(chroma_mean_norm, major_profile)[0, 1]
    minor_corr_c = np.corrcoef(chroma_mean_norm, minor_profile)[0, 1]
    if major_corr_c > minor_corr_c:
        corrs = [np.corrcoef(np.roll(chroma_mean_norm, -i), major_profile)[0, 1] for i in range(12)]
        key_idx = np.argmax(corrs)
        scale = 'major'
    else:
        corrs = [np.corrcoef(np.roll(chroma_mean_norm, -i), minor_profile)[0, 1] for i in range(12)]
        key_idx = np.argmax(corrs)
        scale = 'minor'
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key = keys[key_idx]
    return key, scale


def _key_to_semitone(key, scale):
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    idx = keys.index(key)
    if scale == 'minor':
        idx += 12
    return idx


def _detect_vocals(y, sr):
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    mid_idx = np.where((freqs > 200) & (freqs < 4000))[0]
    mid_energy = np.mean(S[mid_idx, :])
    return bool(mid_energy > 0.01)


def refine_chorus_end(y, sr, start_sec, end_sec):
    try:
        hop_length_vocal = 512
        n_fft = 2048
        mfccs = mfcc(y=y, sr=sr, n_mfcc=20, hop_length=hop_length_vocal, n_fft=n_fft)
        vocal_activity = np.mean(np.abs(mfccs[4:13, :]), axis=0)
        if np.max(vocal_activity) == 0:
            return end_sec
        vocal_activity = vocal_activity / (np.max(vocal_activity) + 1e-6)
        start_frame = librosa.time_to_frames(start_sec, sr=sr, hop_length=hop_length_vocal)
        end_frame = librosa.time_to_frames(end_sec, sr=sr, hop_length=hop_length_vocal)
        vocal_search_segment = vocal_activity[int(start_frame):int(end_frame)]
        buffer_sec = 6.0
        buffer_frames = int(buffer_sec * sr / hop_length_vocal)
        vocal_threshold = 0.6
        vocal_end_rel = len(vocal_search_segment) - buffer_frames
        for i in range(len(vocal_search_segment) - buffer_frames, 0, -1):
            if np.mean(vocal_search_segment[i - buffer_frames:i]) < vocal_threshold:
                vocal_end_rel = i - buffer_frames
                break
        instrumental_start = librosa.frames_to_time(start_frame + vocal_end_rel, sr=sr, hop_length=hop_length_vocal)
        refined_end = np.clip(instrumental_start, start_sec + 10.0, end_sec)
        return refined_end
    except Exception as e:
        print(f"Chorus end refinement failed: {e}")
        return end_sec


def _analyze_structure(y, sr):
    """
    Advanced structure analysis inspired by mir-aidj/all-in-one.
    Uses feature fusion + clustering for boundaries, then heuristic labeling (position, energy, repetition, consecutive similarity)
    for intro/verse/chorus/bridge/outro/break.
    Returns list of segments with start/end/label/energy/repetition/combined.
    """
    duration = len(y) / sr
    hop_length = 512

    try:
        # Define section params early
        min_sections = 6
        max_sections = 15
        # Harmonic source for chroma (better for melody)
        y_harmonic, _ = librosa.effects.hpss(y)
        chroma = chroma_stft(y=y_harmonic, sr=sr, hop_length=hop_length, n_chroma=12)
        chroma = librosa.util.normalize(chroma, norm=2, axis=0)

        # Features
        mfcc_feat = mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop_length)
        rms_feat = rms(y=y, hop_length=hop_length)[0]
        contrast = spectral_contrast(y=y, sr=sr, hop_length=hop_length)
        
        # Normalize everything properly
        def normalize_row(row):
            row = np.nan_to_num(row, nan=0.0, posinf=0.0, neginf=0.0)  # Clamp extremes
            if np.std(row) > 1e-6:  # Tighter threshold
                return (row - np.mean(row)) / np.std(row)
            return np.zeros_like(row)

        chroma_norm = np.apply_along_axis(normalize_row, 0, chroma)
        mfcc_norm = np.apply_along_axis(normalize_row, 0, mfcc_feat)
        contrast_norm = np.apply_along_axis(normalize_row, 0, contrast)

        rms_norm = normalize_row(rms_feat)
        rms_norm = rms_norm.reshape(1, -1)

        # Stack features
        # features = np.vstack([chroma_norm, mfcc_norm[1:, :], contrast_norm, rms_norm])  # drop first MFCC (energy)
        valid_features = []
        for feat in [chroma_norm, mfcc_norm[1:, :], contrast_norm, rms_norm]:
            if feat.size > 0 and not np.all(feat == 0):
                valid_features.append(feat)
        if not valid_features:
            raise ValueError("All features empty")
        features = np.vstack(valid_features)
        if features.size == 0:
            raise ValueError("Empty features - audio too short/silent")
        n_frames = features.shape[1]
        if n_frames == 0:
            raise ValueError("No frames after feature extraction")
        n_sections = min(max_sections, max(min_sections, int(duration // 20)))  # Lenient divisor
        if n_frames < n_sections:
            n_sections = max(3, n_frames // 4)  # Always assign, lower floor
        print(f"Debug: n_frames={n_frames}, n_sections={n_sections}")

        # ——— Robust segmentation ———
        n_frames = features.shape[1]
        if n_frames == 0:
            raise ValueError("Empty features - skipping")
        min_sections = 6
        max_sections = 15
        n_sections = min(max_sections, max(min_sections, int(duration // 20)))  # More lenient for subtle changes

        if n_frames < n_sections:
            n_sections = max(3, n_frames // 4)

        from sklearn.cluster import AgglomerativeClustering
        if n_sections < 2:
            raise ValueError("Insufficient sections for clustering")
        clustering = AgglomerativeClustering(n_clusters=n_sections, linkage='ward')
        labels = clustering.fit_predict(features.T)
        change_points = np.where(np.diff(labels) != 0)[0] + 1
        boundary_frames = np.unique(np.concatenate([[0], change_points, [n_frames]]))
        if len(boundary_frames) < 3:
            # Fallback to even division
            step = n_frames // 5
            boundary_frames = np.array([0] + [i*step for i in range(1,5)] + [n_frames])
        sections_frames = list(zip(boundary_frames[:-1], boundary_frames[1:]))
        # Compute a minimum section duration in frames (protect against short splits)
        min_section_sec = max(2.0, duration / 20)  # Adaptive: ~7-10s min
        min_frames = int(min_section_sec * sr / hop_length)
        print(f"Debug: Raw boundaries len={len(sections_frames)}, min_frames={min_frames}")

        # Merge if too many shorts
        merged_frames = [0, n_frames]
        for start, end in sections_frames:
            if end - start >= min_frames:
                merged_frames.append(start)
                merged_frames.append(end)
        if len(merged_frames) > 2:
            boundary_frames = np.unique(np.array(merged_frames))
        else:
            # Even split fallback early
            step = n_frames // 5
            boundary_frames = np.array([0] + [i*step for i in range(1,6)] + [n_frames])
        sections_frames = list(zip(boundary_frames[:-1], boundary_frames[1:]))

        # ——— Score each section ———
        def get_repetition_score(start_frame, end_frame):
            if end_frame - start_frame < 50:  # too short
                return 0.0, 0.0
            this_chroma = np.mean(chroma[:, start_frame:end_frame], axis=1)
            sims = []
            for s_start, s_end in sections_frames:
                if s_start == start_frame or s_end - s_start < 50:
                    continue
                other = np.mean(chroma[:, s_start:s_end], axis=1)
                corr = np.corrcoef(this_chroma, other)[0, 1]
                if np.isnan(corr):
                    corr = 0.0
                sims.append(corr)
            if not sims:
                return 0.0, 0.0
            avg_sim = np.mean(sims)
            high_sim_fraction = np.mean(np.array(sims) > 0.75)
            return max(avg_sim, high_sim_fraction), high_sim_fraction

        sections = []
        mean_chromas = []
        min_section_sec = max(2.0, duration / 20)  # Adaptive: ~7-10s min
        min_frames = int(min_section_sec * sr / hop_length)

        for start_frame, end_frame in sections_frames:
            if end_frame - start_frame < min_frames:
                continue

            start_t = librosa.frames_to_time(start_frame, sr=sr, hop_length=hop_length)
            end_t = librosa.frames_to_time(end_frame, sr=sr, hop_length=hop_length)

            # Scores
            energy = np.mean(rms_norm[0, start_frame:end_frame])
            contrast_score = np.mean(contrast_norm[:, start_frame:end_frame])
            melody_var = np.mean(np.var(mfcc_feat[1:10], axis=0)[start_frame:end_frame])  # melodic movement
            melody_var = (melody_var - np.mean(melody_var)) / (np.std(melody_var) + 1e-6)
            melody_score = np.clip(melody_var, 0, 2)

            repetition_score, match_fraction = get_repetition_score(start_frame, end_frame)
            repetition_score = max(repetition_score, match_fraction)

            # Final combined score
            combined = (
                0.35 * repetition_score +
                0.25 * energy +
                0.20 * contrast_score +
                0.15 * melody_score +
                0.05 * min(1.0, (end_t - start_t) / 30.0)  # slight bias toward 15–30s sections
            )

            # Temp label
            temp_label = "verse"
            if start_t < 15:
                temp_label = "intro"
            elif end_t > duration - 30:
                temp_label = "outro"
            elif energy < -0.5:
                temp_label = "break"
            elif combined > 0.40:  # lowered threshold
                temp_label = "chorus"

            this_mean_ch = np.mean(chroma[:, start_frame:end_frame], axis=1)
            mean_chromas.append(this_mean_ch)

            sections.append({
                "label": temp_label,
                "start": round(start_t, 2),
                "end": round(end_t, 2),
                "energy": float(energy),
                "repetition": float(repetition_score),
                "combined": float(combined)
            })

        if not sections:
            raise ValueError("No valid sections detected")

        # ——— Improved labeling inspired by functional segment prediction ———
        sections.sort(key=lambda x: x['start'])  # Ensure chronological order

        # Normalize energies
        energies = [s['energy'] for s in sections]
        min_e, max_e = min(energies), max(energies)
        e_range = max_e - min_e + 1e-6

        # Compute consecutive similarities
        consec_sims = []
        for j in range(1, len(mean_chromas)):
            a = mean_chromas[j-1]
            b = mean_chromas[j]
            if len(a) == 0 or len(b) == 0 or np.all(a == 0) or np.all(b == 0):
                sim = 0.0
            else:
                sim_m = np.corrcoef(a, b)
                sim = sim_m[0, 1] if not np.isnan(sim_m[0, 1]) else 0.0
            consec_sims.append(sim)

        # Re-label sequentially
        for i, s in enumerate(sections):
            if i == 0:
                s['label'] = 'intro'
                continue
            if i == len(sections) - 1:
                s['label'] = 'outro'
                continue

            energy_norm = (s['energy'] - min_e) / e_range
            repet_norm = np.clip(s['repetition'], 0, 1)
            sim_to_prev = consec_sims[i-1] if i > 0 else 1.0
            prev_label = sections[i-1]['label']

            if energy_norm > 0.6 and repet_norm > 0.5:
                s['label'] = 'chorus'
            elif energy_norm > 0.3 and repet_norm < 0.4 and prev_label != 'chorus':
                s['label'] = 'verse'
            elif sim_to_prev < 0.3 and energy_norm < 0.5 and prev_label == 'chorus':
                s['label'] = 'bridge'
            elif energy_norm < 0.2:
                s['label'] = 'break'
            else:
                s['label'] = 'verse'

        # Force at least one chorus if none found
        chorus_sections = [s for s in sections if s['label'] == 'chorus']
        if not chorus_sections and sections:
            max_idx = np.argmax([s['combined'] for s in sections])
            sections[max_idx]['label'] = 'chorus'
            chorus_sections = [sections[max_idx]]

        return sections

    except Exception as e:
        print(f"Structure analysis failed for this track: {e}")
        # Fallback: energy-based segments with heuristic labels
        try:
            rms_feat = rms(y=y, hop_length=hop_length)[0]
            frame_times = librosa.frames_to_time(np.arange(len(rms_feat)), sr=sr, hop_length=hop_length)
            window_sec = duration / 5
            window_frames = int(window_sec * sr / hop_length)
            scores = []
            for i in range(0, len(rms_feat) - window_frames, window_frames // 2):
                seg_rms = rms_feat[i:i + window_frames]
                scores.append(np.mean(seg_rms) if len(seg_rms) > 0 else 0)
            
            # Create 5 fallback segments
            num_segs = 5
            seg_dur = duration / num_segs
            segments = []
            for i in range(num_segs):
                start_t = i * seg_dur
                end_t = (i + 1) * seg_dur
                energy = scores[i] if i < len(scores) else 0
                repetition = 0.5  # neutral
                combined = 0.3 + 0.1 * i  # increasing
                label = 'verse'
                if i == 0: label = 'intro'
                elif i == 2: label = 'chorus'
                elif i == 3 and num_segs > 4: label = 'bridge'
                elif i == num_segs - 1: label = 'outro'
                segments.append({
                    "label": label,
                    "start": round(start_t, 2),
                    "end": round(min(end_t, duration), 2),
                    "energy": float(energy),
                    "repetition": float(repetition),
                    "combined": float(combined)
                })
            return segments
        except:
            # Hard fallback
            seg_dur = duration / 3
            return [
                {"label": "intro", "start": 0.0, "end": round(seg_dur, 2), "energy": -0.5, "repetition": 0.0, "combined": 0.2},
                {"label": "chorus", "start": round(seg_dur, 2), "end": round(2 * seg_dur, 2), "energy": 0.8, "repetition": 0.8, "combined": 0.7},
                {"label": "outro", "start": round(2 * seg_dur, 2), "end": round(duration, 2), "energy": 0.0, "repetition": 0.0, "combined": 0.1}
            ]


def analyze_track(title, artist, filename, bpm):
    """
    Analyzes MP3 for key, vocals, structure (segments), choruses, first_chorus_start/end.
    """
    file_path = os.path.join(SONGS_DIR, filename)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}. Returning fallback data.")
        duration = 180.0  # assume 3 min
        fallback_segments = [
            {"label": "intro", "start": 0.0, "end": 30.0, "energy": -0.5, "repetition": 0.0, "combined": 0.2},
            {"label": "chorus", "start": 60.0, "end": 90.0, "energy": 0.8, "repetition": 0.8, "combined": 0.7},
            {"label": "outro", "start": 150.0, "end": duration, "energy": 0.0, "repetition": 0.0, "combined": 0.1}
        ]
        return {
            "title": title, "artist": artist, "file": filename,
            "bpm": bpm, "key": "N/A", "key_semitone": 0, "scale": "N/A",
            "has_vocals": False, "segments": fallback_segments,
            "choruses": [{"start": 60.0, "end": 90.0, "label": "Chorus 1"}],
            "first_chorus_start": 60.0, "first_chorus_end": 90.0,
            "genre": "File Missing"
        }
    try:
        try:
            y, sr = librosa.load(file_path, sr=None)
            if len(y) == 0:
                raise ValueError("Empty audio after load")
        except Exception as load_e:
            print(f"Load failed for {file_path}: {load_e}")
            y = np.zeros(44100 * 180)  # Dummy 3min mono at 44.1kHz
            sr = 44100
        
        duration = len(y) / sr
        if duration < 10:  # Too short for clustering
            print(f"Warning: Short track {title} ({duration}s)")
            # Jump to fallback code here
        print(f"Loaded: len(y)={len(y)}, sr={sr}, duration={duration}")

        # Beat tracking (for potential future use)
        try:
            _, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=float(bpm), tightness=100)
            beats = beats.astype(int)
        except Exception as e:
            print(f"Beat tracking failed: {e}. Using empty beats.")
            beats = np.array([])

        # Key estimation
        chroma_mat = chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma_mat, axis=1)
        key, scale = estimate_key(chroma_mean)
        key_name = f"{key}m" if scale == 'minor' else key
        key_semitone = _key_to_semitone(key, scale)
        # Vocals
        has_vocals = _detect_vocals(y, sr)
        # Structure analysis (replaces old segmentation and chorus detection)
        segments = _analyze_structure(y, sr)
        print(f"Detected segments for {title} by {artist}: {[s['label'] for s in segments]}")
        chorus_sections = [s for s in segments if s['label'] == 'chorus']
        print(f"  Choruses at: {[(c['start'], c['end']) for c in chorus_sections]}")
        # First chorus logic
        valid = [c for c in chorus_sections if c['start'] > 15.0 and (c['end'] - c['start']) > 15.0]
        if valid:
            first_chorus = min(valid, key=lambda x: x['start'])
        elif chorus_sections:
            first_chorus = chorus_sections[0]
        else:
            first_chorus = None
        first_chorus_start = first_chorus['start'] if first_chorus else None
        first_chorus_end = None
        if first_chorus:
            refined_end = refine_chorus_end(y, sr, first_chorus['start'], first_chorus['end'])
            first_chorus_end = refined_end
            # Update all matching choruses
            for s in segments:
                if s['label'] == 'chorus' and abs(s['start'] - first_chorus['start']) < 3.0:
                    s['end'] = refined_end
        # Prepare choruses list for compatibility
        choruses = []
        for i, cs in enumerate([s for s in segments if s['label'] == 'chorus'][:3], 1):
            choruses.append({
                "start": cs["start"],
                "end": cs["end"],
                "label": f"Chorus {i}"
            })
        return {
            "title": title, "artist": artist, "file": filename,
            "bpm": bpm,
            "key": key_name, "key_semitone": key_semitone, "scale": scale, "genre": "Unknown",
            "has_vocals": has_vocals,
            "segments": segments,
            "choruses": choruses,
            "first_chorus_start": first_chorus_start,
            "first_chorus_end": first_chorus_end
        }
    except Exception as e:
        print(f"Error analyzing '{title}' by '{artist}': {e}")
        duration = 180.0  # fallback duration
        fallback_segments = [
            {"label": "intro", "start": 0.0, "end": 30.0, "energy": -0.5, "repetition": 0.0, "combined": 0.2},
            {"label": "chorus", "start": 60.0, "end": 90.0, "energy": 0.8, "repetition": 0.8, "combined": 0.7},
            {"label": "outro", "start": 150.0, "end": duration, "energy": 0.0, "repetition": 0.0, "combined": 0.1}
        ]
        return {
            "title": title, "artist": artist, "file": filename,
            "bpm": bpm, "key": "C", "key_semitone": 0, "scale": "major",
            "has_vocals": False, "segments": fallback_segments,
            "choruses": [{"start": 60.0, "end": 90.0, "label": "Chorus 1"}],
            "first_chorus_start": 60.0,
            "first_chorus_end": 90.0,
            "genre": "Analysis Failed"
        }


def analyze_tracks_in_setlist(data):
    """
    Enriches setlist with analysis and saves to JSON.
    """
    try:
        analyzed_setlist = []
        for segment in data["setlist"]:
            time_range = segment["time"]
            tracks = segment["tracks"]
            analyzed_tracks = []
            for track in tracks:
                title = track["title"]
                artist = track["artist"]
                filename = track["file"]
                bpm = track["bpm"]
                metadata = analyze_track(title, artist, filename, bpm)
                analyzed_tracks.append(metadata)
            analyzed_setlist.append({
                "time": time_range,
                "analyzed_tracks": analyzed_tracks
            })
        output = {"analyzed_setlist": analyzed_setlist}
        with open("analyzed_setlist.json", "w") as f:
            json.dump(output, f, indent=2)
        print("Analyzed setlist saved to 'analyzed_setlist.json'")
        return output
    except Exception as e:
        print(f"Error in Track Analysis Engine: {str(e)}")
        raise


def combined_engine(user_input):
    """
    Main entry point.
    """
    try:
        available_songs = get_available_songs()
        data = parse_time_segments_and_generate_setlist(user_input, available_songs)
        analyze_tracks_in_setlist(data)
    except Exception as e:
        print(f"Error in Combined Engine: {str(e)}")
        raise


if __name__ == "__main__":
    user_input = (
        "I need a mix between 7pm and 10pm for a Casino. At 8pm there will be dinner, "
        "then dancing starts at 9pm. Most of our customers prefer R&B, Bollywood, Afrobeats "
        "and these songs specifically: [{'title': 'Tum Hi Ho', 'artist': 'Arijit Singh'}, "
        "{'title': 'Ye', 'artist': 'Burna Boy'}]."
    )
    combined_engine(user_input)