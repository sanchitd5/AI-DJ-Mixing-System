import librosa
import soundfile as sf  # For saving temp WAV; pip install soundfile if needed
import tempfile
import os
from pychorus import find_and_output_chorus

def detect_first_chorus_window(mp3_path, window_start=30, window_end=120, output_path=None, min_clip=15, max_clip=45):
    """
    Detects the first chorus by analyzing a specific time window (e.g., 30-120s).
    Auto-estimates clip_length based on tempo (8-16 bars) or scans a range if needed.
    
    Args:
    - mp3_path (str): Path to the local MP3 file.
    - window_start (int): Start of analysis window in seconds (default 30s).
    - window_end (int): End of analysis window in seconds (default 120s).
    - output_path (str, optional): Path to save the extracted chorus clip as WAV.
    - min_clip (int): Min clip length for scanning (default 15s).
    - max_clip (int): Max clip length for scanning (default 45s).
    
    Returns:
    - tuple: (start_time_sec, end_time_sec) of the first chorus in the full song.
    """
    if output_path is None:
        output_path = mp3_path.replace('.mp3', '_chorus.wav')
    
    # Load full audio
    y_full, sr = librosa.load(mp3_path)
    duration_full = librosa.get_duration(y=y_full, sr=sr)
    
    # Adjust window if song is shorter
    actual_window_end = min(window_end, duration_full)
    window_length = actual_window_end - window_start
    
    if window_length <= 0:
        raise ValueError(f"Song duration ({duration_full:.2f}s) is shorter than window start ({window_start}s).")
    
    # Trim to window
    start_samples = int(window_start * sr)
    end_samples = int(actual_window_end * sr)
    y_window = y_full[start_samples:end_samples]
    
    # Save window as temp WAV
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_path = temp_file.name
        sf.write(temp_path, y_window, sr)
    
    start_time_relative = None
    used_clip_length = None
    method_used = "heuristic"
    
    try:
        # Step 1: Auto-estimate clip_length via tempo
        tempo, _ = librosa.beat.beat_track(y=y_window, sr=sr)
        bar_length = 60.0 / tempo  # Seconds per bar
        estimated_short = int(8 * bar_length)  # 8 bars (short chorus)
        estimated_long = int(16 * bar_length)  # 16 bars (long chorus)
        
        print(f"Estimated tempo: {tempo:.1f} BPM → clip_lengths: {estimated_short}s or {estimated_long}s")
        
        # Try estimated lengths first
        for clip_try in [estimated_short, estimated_long]:
            if min_clip <= clip_try <= max_clip:
                print(f"Trying auto-estimated clip_length={clip_try}s...")
                temp_output = output_path.replace('.wav', f'_auto{clip_try}s.wav')
                start_time_relative = find_and_output_chorus(temp_path, temp_output, clip_try)
                if start_time_relative is not None:
                    used_clip_length = clip_try
                    output_path = temp_output
                    method_used = "auto-tempo"
                    break
        
        # Step 2: If tempo fails, scan range in 5s steps (bias to shorter for quick hooks)
        if start_time_relative is None:
            print("Tempo estimate failed; scanning range...")
            for clip_try in range(min_clip, max_clip + 1, 5):
                print(f"Trying scan clip_length={clip_try}s...")
                temp_output = output_path.replace('.wav', f'_scan{clip_try}s.wav')
                start_time_relative = find_and_output_chorus(temp_path, temp_output, clip_try)
                if start_time_relative is not None:
                    used_clip_length = clip_try
                    output_path = temp_output
                    method_used = "scan"
                    break  # Take the shortest successful (earliest bias)
        
        # Step 3: Final fallback to heuristic
        if start_time_relative is None:
            print("All pychorus attempts failed; falling back to basic onset-based heuristic.")
            start_time_relative, used_clip_length = basic_chorus_heuristic(y_window, sr)
    
    finally:
        # Clean up temp file
        os.unlink(temp_path)
    
    # Convert relative to absolute
    absolute_start = window_start + start_time_relative
    end_time = absolute_start + used_clip_length
    end_time = min(end_time, duration_full)
    
    print(f"Full song duration: {duration_full:.2f}s")
    print(f"Analyzed window: {window_start}s to {actual_window_end:.2f}s")
    print(f"Detection method: {method_used}")
    print(f"First chorus (using {used_clip_length}s clip): {absolute_start:.2f}s to {end_time:.2f}s")
    
    return absolute_start, end_time

def basic_chorus_heuristic(y, sr, hop_length=512):
    """
    Simple fallback: Estimate chorus start after ~4 onsets (post-intro) with fixed length.
    """
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop_length)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)
    
    if len(onset_times) > 4:
        chorus_start_rel = onset_times[3]  # Rough: after intro/verse onsets
    else:
        chorus_start_rel = min(20.0, len(y)/sr - 20)  # Shorter fallback, avoid end
    
    chorus_length = 25  # Slightly shorter default for variety
    print(f"Heuristic estimate: chorus at ~{chorus_start_rel:.2f}s relative to window (fixed {chorus_length}s length)")
    return chorus_start_rel, chorus_length

# Example usage:
if __name__ == "__main__":
    mp3_file = "input3.mp3"  # Replace with your MP3 path
    start, end = detect_first_chorus_window(mp3_file, window_start=30, window_end=120)