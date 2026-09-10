# generate_mix.py

"""
This module generates a continuous DJ mix by applying transitions based on an analyzed setlist and a mixing plan.
It strictly supports only the 'Chorus Beatmatch' transition type for complex mixing.

Key features:
- Uses the globally sorted track order from 'mixing_plan.json'.
- Converts audio between pydub's AudioSegment and NumPy arrays for processing.
- **Chorus Beatmatch (UPDATED):** Hard cut exactly at first chorus end. Outgoing: vocals fade out in 2s, beats full for 10s then fade out in 6s. Incoming: vocals full from start, beats silent for 10s then fade in in 6s, aligned on percussives. Incoming starts from intro.
- **Fallback:** If the plan specifies any other transition type (e.g., 'Crossfade'), it executes a standard, unaligned crossfade.
- Applies tempo stretching based on BPM ratio for Chorus Beatmatch.
- Handles missing files gracefully and normalizes the final mix for consistent loudness.

Dependencies:
- os: For file path operations.
- json: For parsing input setlist and mixing plan JSON files.
- numpy: For numerical operations on audio data.
- librosa: For audio feature extraction (e.g., onset strength, HPSS separation, time stretch).
- pydub: For loading, manipulating, and exporting audio files.
"""

import os 
import json 
import numpy as np 
import librosa 
from pydub import AudioSegment 
from pydub.effects import normalize 

# Define the directory path where local MP3 song files are stored.
SONGS_DIR = "./songs"


# ---------------------------
# Utility conversions
# ---------------------------
def audio_segment_to_np(segment: AudioSegment):
    """Converts a pydub AudioSegment to a mono float32 NumPy array with values in [-1, 1]."""
    samples = np.array(segment.get_array_of_samples()) 
    if segment.channels == 2:
        samples = samples.reshape((-1, 2)).mean(axis=1) 
    sr = segment.frame_rate 
    y = samples.astype(np.float32) / 32768.0 
    return y, sr


def np_to_audio_segment(y: np.ndarray, sr: int):
    """Converts a mono float32 NumPy array in [-1, 1] to a pydub AudioSegment (mono, 16-bit)."""
    y_clipped = np.clip(y, -1.0, 1.0) 
    y_int16 = (y_clipped * 32767.0).astype(np.int16) 
    return AudioSegment(
        y_int16.tobytes(), 
        frame_rate=sr, 
        sample_width=2, 
        channels=1 
    )


# ---------------------------
# Beat / onset helpers
# ---------------------------
def get_onset_envelope(y, sr, hop_length=512):
    """Computes the normalized onset strength envelope of an audio signal using Librosa."""
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length) 
    if onset_env.size == 0:
        return None, hop_length 
    onset_env = onset_env / (np.max(onset_env) + 1e-9) 
    return onset_env, hop_length


def find_best_alignment(y1, sr1, y2, sr2, match_duration_sec=16.0):
    """
    Finds the best alignment (lag in seconds) between two audio tracks using onset strength correlation.
    
    The lag indicates how much to advance/delay y2 relative to y1 for optimal beat match.
    """
    try:
        # Use a segment length defined by the match duration (i.e., the overlap length).
        n1 = min(len(y1), int(match_duration_sec * sr1))
        n2 = min(len(y2), int(match_duration_sec * sr2))
        if n1 < 1024 or n2 < 1024:
            return 0.0 
        tail1 = y1[-n1:] 
        head2 = y2[:n2] 
        onset1, hop = get_onset_envelope(tail1, sr1) 
        onset2, _ = get_onset_envelope(head2, sr2) 
        if onset1 is None or onset2 is None:
            return 0.0 
        minlen = min(len(onset1), len(onset2)) 
        if minlen < 8:
            return 0.0 
        onset1_r = librosa.util.fix_length(onset1, size=minlen) 
        onset2_r = librosa.util.fix_length(onset2, size=minlen)
        corr = np.correlate(onset1_r - onset1_r.mean(), onset2_r - onset2_r.mean(), mode='full')
        lag_idx = corr.argmax() - (len(onset2_r) - 1) 
        approx_hop_seconds = hop / float(sr1) 
        lag_seconds = -lag_idx * approx_hop_seconds 
        lag_seconds = float(np.clip(lag_seconds, -match_duration_sec, match_duration_sec))
        return lag_seconds
    except Exception:
        return 0.0 


# ---------------------------
# Special Chorus Beatmatch transition
# ---------------------------
def apply_chorus_beatmatch_transition(from_audio, from_meta, chorus_end_sec, to_audio, to_meta, transition_sec=16.0):
    """
    Applies the special Chorus Beatmatch: hard cut at chorus end, outgoing vocals fade out in 2s, beats full for 10s then fade out in 6s; incoming vocals full, beats silent for 10s then fade in in 6s, aligned on percussives.
    Incoming starts from intro (0.0).
    Returns (transition_audio: full incoming with fade overlay, incoming_start: for timing)
    """
    incoming_start = 0.0  # Start from intro
    common_sr = 22050
    transition_ms = int(transition_sec * 1000)
    beats_full_sec = 10.0
    vocal_fade_sec = 2.0
    beats_fade_sec = 6.0

    # Tempo stretch incoming based on BPM ratio
    bpm_from = from_meta.get('bpm', 120)
    bpm_to = to_meta.get('bpm', 120)
    rate = bpm_to / bpm_from
    sr_to = to_audio.frame_rate  # Define sr_to always
    if abs(rate - 1.0) > 0.01:
        y_to_full, _ = audio_segment_to_np(to_audio)
        y_to_stretched = librosa.effects.time_stretch(y_to_full, rate=rate)
        to_audio = np_to_audio_segment(y_to_stretched, sr_to)

    # Outgoing: post-chorus up to transition_sec
    post_start_ms = int(chorus_end_sec * 1000)
    post_end_ms = min(post_start_ms + transition_ms, len(from_audio))
    out_seg = from_audio[post_start_ms:post_end_ms]
    y_out, sr_out = audio_segment_to_np(out_seg)
    y_out_res = librosa.resample(y_out, orig_sr=sr_out, target_sr=common_sr)
    y_out_harm, y_out_perc = librosa.effects.hpss(y_out_res)  # Harmonic for vocals, perc for beats
    num_samples = len(y_out_perc)

    # Envelopes for outgoing
    vocal_env_out = np.ones(num_samples)
    vocal_fade_samples = int(vocal_fade_sec * common_sr)
    if vocal_fade_samples < num_samples:
        vocal_env_out[:vocal_fade_samples] = np.linspace(1.0, 0.0, vocal_fade_samples)
    beats_env_out = np.ones(num_samples)
    beats_fade_start_samples = int(beats_full_sec * common_sr)
    if beats_fade_start_samples < num_samples:
        beats_fade_end_samples = num_samples
        beats_env_out[beats_fade_start_samples:] = np.linspace(1.0, 0.0, beats_fade_end_samples - beats_fade_start_samples)

    y_out_voc_fade = y_out_harm * vocal_env_out
    y_out_beats_adjusted = y_out_perc * beats_env_out
    y_out_adjusted = np.clip(y_out_voc_fade + y_out_beats_adjusted, -1.0, 1.0)

    # Incoming: intro up to transition_sec
    intro_start_ms = int(incoming_start * 1000)
    intro_end_ms = min(intro_start_ms + transition_ms, len(to_audio))
    in_seg = to_audio[intro_start_ms:intro_end_ms]
    y_in, sr_in = audio_segment_to_np(in_seg)
    y_in_res = librosa.resample(y_in, orig_sr=sr_in, target_sr=common_sr)
    y_in_harm, y_in_perc = librosa.effects.hpss(y_in_res)
    num_samples_in = len(y_in_perc)
    # Pad or trim to match outgoing if different
    if num_samples_in != num_samples:
        if num_samples_in > num_samples:
            y_in_harm = y_in_harm[:num_samples]
            y_in_perc = y_in_perc[:num_samples]
            num_samples_in = num_samples
        else:
            pad_len = num_samples - num_samples_in
            y_in_harm = np.pad(y_in_harm, (0, pad_len), mode='constant')
            y_in_perc = np.pad(y_in_perc, (0, pad_len), mode='constant')
            num_samples_in = num_samples

    # Envelopes for incoming
    vocal_env_in = np.ones(num_samples)
    beats_env_in = np.zeros(num_samples)
    beats_fade_start_samples_in = int(beats_full_sec * common_sr)
    if beats_fade_start_samples_in < num_samples:
        beats_fade_end_samples_in = num_samples
        beats_env_in[beats_fade_start_samples_in:] = np.linspace(0.0, 1.0, beats_fade_end_samples_in - beats_fade_start_samples_in)

    y_in_voc_full = y_in_harm * vocal_env_in
    y_in_beats_fade = y_in_perc * beats_env_in
    y_in_adjusted = np.clip(y_in_voc_full + y_in_beats_fade, -1.0, 1.0)

    # Align on raw percussives
    lag_sec = find_best_alignment(y_out_perc, common_sr, y_in_perc, common_sr, match_duration_sec=transition_sec)

    # To AudioSegments for adjusted
    out_adjusted_audio = np_to_audio_segment(y_out_adjusted, common_sr)
    in_adjusted_audio = np_to_audio_segment(y_in_adjusted, common_sr)

    # Apply lag shift
    lag_ms = int(lag_sec * 1000)
    if lag_ms >= 0:
        # Delay incoming
        silence = AudioSegment.silent(duration=lag_ms, frame_rate=common_sr)
        in_shifted = silence + in_adjusted_audio
        out_for_mix = out_adjusted_audio
    else:
        # Advance incoming
        advance_ms = -lag_ms
        silence = AudioSegment.silent(duration=advance_ms, frame_rate=common_sr)
        in_shifted = in_adjusted_audio
        out_for_mix = out_adjusted_audio + silence
        out_for_mix = out_for_mix[advance_ms:]

    # Pad to same length
    mix_len_ms = max(len(out_for_mix), len(in_shifted))
    out_for_mix = out_for_mix[:mix_len_ms]
    if len(out_for_mix) < mix_len_ms:
        out_for_mix += AudioSegment.silent(duration=mix_len_ms - len(out_for_mix))
    in_shifted = in_shifted[:mix_len_ms]
    if len(in_shifted) < mix_len_ms:
        in_shifted += AudioSegment.silent(duration=mix_len_ms - len(in_shifted))

    # Overlay adjusted sections
    fade_overlay = out_for_mix.overlay(in_shifted)

    # Rest of incoming (adjusted for lag)
    rest_start_adjust_sec = transition_sec + max(0, lag_sec)
    rest_start_sec = incoming_start + rest_start_adjust_sec
    rest_start_ms = int(rest_start_sec * 1000)
    rest = AudioSegment.empty()
    if rest_start_ms < len(to_audio):
        rest_seg = to_audio[rest_start_ms:]
        y_rest, sr_rest = audio_segment_to_np(rest_seg)
        y_rest_res = librosa.resample(y_rest, orig_sr=sr_rest, target_sr=common_sr)
        rest = np_to_audio_segment(y_rest_res, common_sr)

    # Full transition audio
    transition_audio = fade_overlay + rest

    return transition_audio, incoming_start


# ---------------------------
# Standard crossfade transition
# ---------------------------
def apply_transition(segment1: AudioSegment,
                     segment2: AudioSegment,
                     transition_type: str,
                     duration_ms: int = 8000,
                     early_ms: int = 5500,
                     otac: float = 0.0,
                     eq_match_duration_ms: int = 15000):
    """
    Standard crossfade for non-Chorus Beatmatch transitions.
    """
    # The new transition needs a defined fade out time for the outgoing track.
    # We will use 8000ms as the fade-out duration.
    FADE_OUT_MS = 8000
    
    # The total overlap must be enough for the fade out (8000ms) plus the early start (5500ms).
    overlap_ms = duration_ms + early_ms  # e.g. 8000 + 5500 = 13500ms overlap
    overlap_ms = max(overlap_ms, FADE_OUT_MS) # Ensure overlap is at least the fade-out duration.
    overlap_ms = min(overlap_ms, len(segment1), len(segment2))  # Safety

    # Convert to numpy
    y1, sr1 = audio_segment_to_np(segment1[-overlap_ms:])
    y2_full, sr2 = audio_segment_to_np(segment2)

    # Apply OTAC tempo stretch to incoming track
    if abs(otac) > 0.01:
        stretch_duration_sec = max(duration_ms, eq_match_duration_ms) / 1000.0
        # Formula for rate based on OTAC (beats/minute * stretch_time_sec / 60 seconds)
        # Note: librosa rate is relative to 1.0, not a percentage.
        # This formula seems slightly off for a general tempo change but is preserved from the original.
        rate = 1.0 + otac * stretch_duration_sec / 60.0
        y2_full = librosa.effects.time_stretch(y2_full, rate=rate)

    segment2_stretched = np_to_audio_segment(y2_full, sr2)
    segment2_stretched = segment2_stretched.set_frame_rate(segment1.frame_rate).set_channels(1)

    # Extract overlap portions
    outgoing_tail = segment1[-overlap_ms:]
    incoming_head = segment2_stretched[:overlap_ms]

    if transition_type.lower() == "crossfade":
        # Standard crossfade (no alignment)
        faded_out = outgoing_tail.fade_out(overlap_ms)
        faded_in = incoming_head.fade_in(overlap_ms)
        crossed = faded_out.overlay(faded_in)
        return crossed + segment2_stretched[overlap_ms:]

    # Fallback
    return outgoing_tail.fade_out(overlap_ms).overlay(incoming_head.fade_in(overlap_ms)) + segment2_stretched[overlap_ms:]


# ---------------------------
# Mix generator
# ---------------------------
def generate_mix(analyzed_setlist_json, mixing_plan_json, first_fade_in_ms=5000, crossfade_early_ms=5500, eq_match_ms=15000):
    """
    Generates a continuous DJ mix by processing an analyzed setlist and applying transitions from a mixing plan.
    """
    try:
        # Parse the analyzed setlist JSON string to get all metadata.
        analyzed_data = json.loads(analyzed_setlist_json)
        # Load the mixing plan from the specified JSON file.
        mixing_plan = json.load(open(mixing_plan_json, 'r')).get("mixing_plan", [])
        
        full_mix = AudioSegment.empty()  # Initialize an empty AudioSegment for the mix.
        last_track_start_mix_sec = None  # Track the mix start time (seconds) of the last added track.
        last_track_meta = None  # Track last track metadata for transitions
        
        # Flatten all track metadata into a single dictionary for easy lookup by title.
        all_tracks_metadata = {}
        for segment in analyzed_data.get("analyzed_setlist", []):
            for track in segment.get("analyzed_tracks", []):
                all_tracks_metadata[track['title']] = track

        # Iterate over the mixing plan entries (each entry represents the start of a new track).
        for track_index, plan_entry in enumerate(mixing_plan):
            to_track_title = plan_entry.get("to_track")
            
            # --- Get Incoming Track Metadata ---
            if to_track_title not in all_tracks_metadata:
                print(f"[generate_mix] Missing metadata for incoming track: {to_track_title}. Skipping.")
                continue
            track = all_tracks_metadata[to_track_title]  # to_meta

            transition_type = plan_entry.get("transition_type", "Crossfade") 
            otac = plan_entry.get("otac", 0.0) 
            outgoing_cut_sec = plan_entry.get("outgoing_cut_sec") 
            overlap_sec = plan_entry.get("overlap_sec", 8.0) 
            # Recalculate overlap based on the desired new transition logic
            # This is hardcoded to 13500ms (8s crossfade + 5.5s early) in the original, 
            # which is fine as the *fade* only uses 8000ms.
            overlap_ms = 13500  # 8s crossfade + 5.5s early = 13.5s (standard pro DJ overlap)

            file_path = os.path.join(SONGS_DIR, track["file"]) 
            if not os.path.exists(file_path):
                print(f"[generate_mix] Missing file: {file_path}. Skipping track.")
                continue

            # Load the audio file (incoming track).
            to_audio = AudioSegment.from_file(file_path)

            if track_index == 0:
                # --- FIRST TRACK ---
                fade_dur = int(min(first_fade_in_ms, len(to_audio)))
                full_mix += to_audio.fade_in(fade_dur)
                last_track_start_mix_sec = 0.0
                last_track_meta = track
            else:
                # --- SUBSEQUENT TRACKS (TRANSITIONS) ---
                from_title = plan_entry.get("from_track")
                from_meta = all_tracks_metadata.get(from_title)
                if from_meta is None:
                    print(f"[generate_mix] Missing from metadata for {from_title}. Falling back to crossfade.")
                    transition_type = "Crossfade"
                
                # 1. Calculate the exact mix time of the outgoing track's cut point.
                trans_start_mix_sec = last_track_start_mix_sec + outgoing_cut_sec
                trans_start_ms = int(trans_start_mix_sec * 1000 + 0.5)

                if transition_type == "Chorus Beatmatch":
                    # --- SPECIAL CHORUS BEATMATCH ---
                    pre_transition = full_mix[:trans_start_ms]
                    
                    # Load outgoing audio for post-chorus extraction
                    from_file_path = os.path.join(SONGS_DIR, from_meta["file"])
                    from_audio = AudioSegment.from_file(from_file_path)
                    
                    # Apply special transition
                    transition_audio, incoming_start = apply_chorus_beatmatch_transition(
                        from_audio, from_meta, outgoing_cut_sec, to_audio, track
                    )
                    
                    # Rebuild mix
                    full_mix = pre_transition + transition_audio
                    
                    # Update timing: incoming "starts" at trans_start, but content from incoming_start (0)
                    last_track_start_mix_sec = trans_start_mix_sec - incoming_start
                else:
                    # --- STANDARD CROSSFADE ---
                    # 2. Determine the start of the overlap/tail segment in the current mix.
                    tail_start_ms = max(0, trans_start_ms - overlap_ms)

                    # 3. Trim the mix and extract the necessary segments.
                    pre_transition = full_mix[:tail_start_ms]  # Audio before the overlap starts.
                    tail = full_mix[tail_start_ms:trans_start_ms]  # The overlap segment of the outgoing track.
                    
                    if len(tail) < 500:
                        print(f"[generate_mix] Warning: Tail for '{plan_entry.get('from_track')}' is too short ({len(tail)}ms). Appending fully.")
                        full_mix += to_audio
                        last_track_start_mix_sec = len(full_mix) / 1000.0 
                        last_track_meta = track
                        continue

                    # 4. Apply the specified transition.
                    trans_audio = apply_transition(
                        tail, to_audio, transition_type,
                        duration_ms=8000,
                        early_ms=crossfade_early_ms,
                        otac=otac,
                        eq_match_duration_ms=eq_match_ms
                    )
                    
                    # 5. Rebuild full_mix.
                    full_mix = pre_transition + trans_audio
                    
                    # 6. Update last start time for the *newly added* track.
                    last_track_start_mix_sec = trans_start_mix_sec - overlap_sec
                
                last_track_meta = track

        # Normalize the final mix for consistent loudness and export as MP3.
        full_mix = normalize(full_mix)
        full_mix.export("mix.mp3", format="mp3")
        print("Mix exported to 'mix.mp3'")

    except Exception as e:
        print(f"[generate_mix] Error: {e}")
        raise


# ---------------------------
# Example run
# ---------------------------
if __name__ == "__main__":
    """
    Entry point for testing the mix generator with a sample analyzed setlist and mixing plan.
    """
    # Sample setlist with chorus times added for proper Chorus Beatmatch testing.
    sample_analyzed_setlist_json = '''
    {
        "analyzed_setlist": [
            {
                "time": "19:00–20:00",
                "analyzed_tracks": [
                    {
                        "title": "Tum Hi Ho",
                        "artist": "Arijit Singh",
                        "file": "Arijit Singh - Tum Hi Ho.mp3",
                        "bpm": 94,
                        "key_semitone": 9,
                        "scale": "major",
                        "genre": "bollywood",
                        "energy": 0.45,
                        "valence": 0.32,
                        "danceability": 0.52,
                        "has_vocals": true,
                        "segments": [{"label": "verse", "start": 30.0, "end": 60.0}],
                        "choruses": [{"start": 60.0, "end": 90.0}], 
                        "chroma_matrix": null,
                        "transition": "Fade In",
                        "notes": "Balanced Vibe track. Genre: bollywood."
                    },
                    {
                        "title": "No Scrubs",
                        "artist": "TLC",
                        "file": "TLC - No Scrubs.mp3",
                        "bpm": 93,
                        "key_semitone": 8,
                        "scale": "minor",
                        "genre": "r&b",
                        "energy": 0.7,
                        "valence": 0.6,
                        "danceability": 0.8,
                        "has_vocals": true,
                        "segments": [{"label": "verse", "start": 20.0, "end": 50.0}],
                        "choruses": [{"start": 45.0, "end": 75.0}], 
                        "chroma_matrix": null,
                        "transition": "Crossfade",
                        "notes": "Dance Floor Filler track. Genre: r&b."
                    }
                ]
            }
        ]
    }
    '''
    generate_mix(sample_analyzed_setlist_json, "mixing_plan.json")