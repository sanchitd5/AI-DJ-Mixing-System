# generate_mixing_plan.py

"""
This module generates a DJ mixing plan based on an analyzed setlist, strictly enforcing 
the 'Chorus Beatmatch' transition type. The mix will prioritize a chain of tracks that 
are harmonically compatible, have choruses, and a BPM difference of 2 or less.

Key features:
- **STRICT ENFORCEMENT:** Only 'Chorus Beatmatch' is suggested if BPM difference <= 2 
  and both tracks have chorus data. Otherwise, a 'Crossfade' fallback is used (which 
  results in no complex transition in generate_mix for tracks that don't meet the rule).
- Prioritizes a chain of Chorus Beatmatch-ready tracks at the start of the mix.
- Estimates transition overlaps based on the Chorus Beatmatch type (16s for special fade) or standard crossfade.
- Computes OTAC (Optimal Tempo Adjustment Coefficient) for smooth tempo transitions.
- Prevents a track from transitioning to itself.
- Generates a mixing plan with start times, transition points, cut offsets, and comments for each track.

Dependencies:
- json: For parsing input setlist and serializing the mixing plan.
- os: For file path operations.
- numpy: For numerical computations (e.g., OTAC calculation).
- datetime, timedelta: For handling time calculations and formatting.
- pydub: For loading audio files to determine track durations.
"""

import os 
import json 
import numpy as np 
from datetime import datetime, timedelta 
from pydub import AudioSegment 

# Define the directory path where local MP3 song files are stored.
SONGS_DIR = "./songs"


# ---------------------------
# Estimated overlap for timing
# ---------------------------
def get_estimated_overlap(transition_type: str, crossfade_early_ms: int = 5500, duration_ms: int = 8000, eq_match_ms: int = 15000):
    """
    Estimates the overlap duration (in seconds) for a transition based on the transition type.
    """
    t = transition_type.lower() 
    if "fade in" in t:
        return 0.0 
    if "chorus beatmatch" in t:
        return 16.0  # Special 16s fade for vocal/instrumental separation
    # Use standard crossfade overlap for the required 'Chorus Beatmatch' transition.
    return (duration_ms + crossfade_early_ms) / 1000.0 


# ---------------------------
# Harmonic compatibility
# ---------------------------
def is_harmonic_key(from_key_semitone, to_key_semitone):
    """
    Determines if two tracks are harmonically compatible based on their key semitone indices.
    """
    compatible_shifts = [0, 1, 11, 7, 5] 
    if from_key_semitone is None or to_key_semitone is None:
        return True 
    key_diff = abs(int(from_key_semitone) - int(to_key_semitone)) % 12 
    return key_diff in compatible_shifts or (12 - key_diff) in compatible_shifts 


# ---------------------------
# OTAC (tempo adjust) helper
# ---------------------------
def compute_otac(song1_data, song2_data):
    """
    Computes the Optimal Tempo Adjustment Coefficient (OTAC) for transitioning between two tracks.
    """
    tempo1, tempo2 = song1_data.get('bpm', 0), song2_data.get('bpm', 0) 
    try:
        if tempo1 <= 0 or tempo2 <= 0:
            return 0.0 
        otac = np.log(float(tempo2) / float(tempo1)) / 60.0 
        return float(otac) 
    except Exception:
        return 0.0 


# ---------------------------
# Transition suggestion (STRICT)
# ---------------------------
def suggest_transition_type(from_track, to_track):
    """
    Strictly suggests 'Chorus Beatmatch' if BPM difference <= 2 and choruses are available.
    Falls back to 'Crossfade' if conditions are not met.
    """
    # 1. Prevent self-transition.
    if from_track.get('title') == to_track.get('title'):
        return "Crossfade" # Fallback

    bpm_diff = abs(float(from_track.get('bpm', 0)) - float(to_track.get('bpm', 0)))
    has_choruses_from = bool(from_track.get('choruses', [])) 
    has_choruses_to = bool(to_track.get('choruses', [])) 
    harmonic_compatible = is_harmonic_key(from_track.get('key_semitone'), to_track.get('key_semitone'))

    # 2. Condition for STRICT Chorus Beatmatch: BPM diff <= 2 and both tracks have choruses.
    if bpm_diff <= 2 and has_choruses_from and has_choruses_to and harmonic_compatible:
        return "Chorus Beatmatch"

    # 3. Fallback for all other cases (e.g., if BPM is too far, or no chorus).
    return "Crossfade" 


# ---------------------------
# Time formatting helper
# ---------------------------
def format_time(seconds: float) -> str:
    """
    Formats seconds into HH:MM:SS string.
    """
    delta = timedelta(seconds=seconds)
    return (datetime.min + delta).strftime("%H:%M:%S")

# ---------------------------
# Track selection and sorting
# ---------------------------

def select_and_sort_tracks_for_mixing(analyzed_data):
    """
    Selects and sorts all tracks, prioritizing a continuous chain of 
    Chorus Beatmatch-friendly tracks at the start, ensuring no song repeats 
    immediately after being played.
    """
    all_tracks = []
    for segment in analyzed_data.get("analyzed_setlist", []):
        for track in segment.get("analyzed_tracks", []):
            track_copy = track.copy()
            track_copy["original_segment_time"] = segment.get("time", "Unknown")
            all_tracks.append(track_copy)
    
    # 1. Sort all tracks globally by BPM ascending (low to high)
    all_tracks.sort(key=lambda x: x.get('bpm', 0))
    
    selected_chain = []
    remaining_tracks_pool = list(all_tracks)
    
    if not remaining_tracks_pool:
        return []

    # 2. Select the starting track: the first track that has a chorus.
    start_track_index = -1
    for i, track in enumerate(remaining_tracks_pool):
        if bool(track.get('choruses', [])):
            start_track_index = i
            break
    
    if start_track_index == -1:
        print("No tracks with choruses found. Cannot initiate Chorus Beatmatch chain. Using simple BPM sort.")
        return all_tracks

    current_track = remaining_tracks_pool.pop(start_track_index)
    selected_chain.append(current_track)
    
    available_tracks = remaining_tracks_pool 
    
    # 3. Greedily select the next best Chorus Beatmatch track using the strict rule.
    print(f"Starting with {current_track['title']} (BPM: {current_track.get('bpm', 'N/A')}). Searching for initial Chorus Beatmatch chain...")
    
    while available_tracks:
        best_next_track = None
        best_index = -1
        
        # Filter available tracks to exclude immediate repeats.
        next_candidates = [
            (i, t) for i, t in enumerate(available_tracks) 
            if t['title'] != current_track['title'] 
        ]
        
        # Look for the track with the closest BPM that satisfies the Chorus Beatmatch criteria.
        for i_original, next_track in next_candidates:
            if suggest_transition_type(current_track, next_track) == "Chorus Beatmatch":
                best_next_track = next_track
                # Find the index of the track in the *original* `available_tracks` list.
                original_index = available_tracks.index(best_next_track)
                best_index = original_index
                break 

        if best_next_track:
            print(f" -> Next track: {best_next_track['title']} (BPM: {best_next_track.get('bpm', 'N/A')}) via Chorus Beatmatch.")
            selected_chain.append(best_next_track)
            
            # Remove the track from the pool and update current_track.
            available_tracks.pop(best_index)
            current_track = best_next_track
        else:
            print("Chorus Beatmatch chain complete or no further compatible track available without repeating.")
            break
            
    # 4. Append the rest of the BPM-sorted tracks.
    final_mixing_order = selected_chain + available_tracks
    
    print(f"Total tracks in plan: {len(final_mixing_order)}. Tracks in initial Chorus Beatmatch chain: {len(selected_chain)}")
    print(f"Final track order (first 5): {[(t['title'], t['bpm']) for t in final_mixing_order[:5]]}...")

    return final_mixing_order


# ---------------------------
# Mixing plan generator
# ---------------------------
def generate_mixing_plan(analyzed_setlist_json=None, first_fade_in_ms=5000, crossfade_early_ms=5500, eq_match_ms=15000):
    """
    Generates a DJ mixing plan from an analyzed setlist, strictly enforcing Chorus Beatmatch transitions.
    """
    try:
        # Load analyzed setlist JSON.
        if analyzed_setlist_json is None:
            with open("analyzed_setlist.json", "r") as f:
                analyzed_setlist_json = f.read()
        analyzed_data = json.loads(analyzed_setlist_json)
        
        # Use the custom selection/sorting logic.
        all_tracks = select_and_sort_tracks_for_mixing(analyzed_data)

        mixing_plan = [] 
        last_track_meta = None 
        last_start_sec = None 
        last_full_duration_sec = 0.0 

        # Process sorted tracks (global order).
        for track in all_tracks:
            file_path = os.path.join(SONGS_DIR, track["file"])
            
            # Skip if the current track is the same as the last track (prevents self-transition)
            if last_track_meta and track.get("title") == last_track_meta.get("title"):
                print(f"Skipping track '{track.get('title')}' to prevent self-transition.")
                continue

            if not os.path.exists(file_path):
                print(f"[generate_mixing_plan] Missing file: {file_path}. Skipping track.")
                continue 

            # Load audio file to determine its duration.
            try:
                audio = AudioSegment.from_file(file_path)
                duration_sec = len(audio) / 1000.0 
            except Exception as e:
                print(f"[generate_mixing_plan] Error loading audio for {track['file']}: {e}. Skipping.")
                continue

            # --- Transition Calculation ---
            if last_track_meta is None:
                # First track uses a fade-in transition.
                start_sec = 0.0
                transition_type = "Fade In"
                outgoing_cut_sec = None 
                overlap_sec = 0.0
                from_track_title = None
                otac_val = 0.0
                transition_point = "downbeat align"
                comment = f"Start set with {track.get('title')} (BPM: {track.get('bpm', 'N/A')}, original segment: {track.get('original_segment_time', 'N/A')})." 
            else:
                # Suggest transition type (will be Chorus Beatmatch or Crossfade/Fallback).
                transition_type = suggest_transition_type(last_track_meta, track)
                otac_val = compute_otac(last_track_meta, track)
                overlap_sec = get_estimated_overlap(transition_type, crossfade_early_ms, 8000, eq_match_ms)
                
                # Default cut is the end of the outgoing track (full duration).
                outgoing_cut_sec = last_full_duration_sec 
                transition_point = "beat grid match"

                if transition_type == "Chorus Beatmatch":
                    # If Chorus Beatmatch is suggested, find the first valid chorus end for the cut point.
                    choruses = last_track_meta.get("choruses", []) 
                    min_cut_sec = 30.0 # Minimum seconds to play before cutting.
                    
                    if choruses and len(choruses) > 0:
                        first_chorus_end = choruses[0].get("end", last_full_duration_sec)
                        
                        if first_chorus_end > max(overlap_sec, min_cut_sec):
                            # Cut the outgoing track at the first chorus end.
                            outgoing_cut_sec = first_chorus_end
                            transition_point = "first chorus end beat align (hard cut to intro vocals + beats crossfade over 16s)"
                        else:
                            # Fallback if chorus is too short/early, but keep the suggested type for log/plan clarity.
                            print(f"[Warning] Chorus for {last_track_meta['title']} too short/early. Using full track duration as cut point.")
                            transition_point = "end of track (chorus invalid)"

                    else:
                        # Should not happen if `suggest_transition_type` worked, but is a safe fallback.
                        transition_type = "Crossfade" # Downgrade to simple crossfade on the plan
                        overlap_sec = get_estimated_overlap(transition_type, crossfade_early_ms, 8000, eq_match_ms)
                        transition_point = "end of track (chorus missing)"
                
                # Calculate start time for the track (when it begins playing in the mix).
                if transition_type == "Chorus Beatmatch":
                    start_sec = last_start_sec + outgoing_cut_sec  # Hard cut: incoming starts exactly at cut time
                else:
                    start_sec = last_start_sec + outgoing_cut_sec - overlap_sec  # Standard overlap
                from_track_title = last_track_meta.get('title')
                comment = f"Transition {from_track_title} (BPM {last_track_meta.get('bpm', 'N/A')}) -> {track.get('title')} (BPM {track.get('bpm', 'N/A')}, original segment: {track.get('original_segment_time', 'N/A')}). Suggested '{transition_type}' at {transition_point}. OTAC: {otac_val:.4f}" 

            # Format start time as string.
            start_str = format_time(start_sec)

            # Add the transition to the mixing plan.
            mixing_plan.append({
                "from_track": from_track_title,
                "to_track": track.get("title"),
                "start_time": start_str,
                "transition_point": transition_point,
                "transition_type": transition_type,
                "outgoing_cut_sec": outgoing_cut_sec,
                "overlap_sec": overlap_sec,
                "otac": float(otac_val),
                "comment": comment
            })

            # Update last track info for next iteration.
            last_start_sec = start_sec
            last_full_duration_sec = duration_sec
            last_track_meta = track

        # Save the mixing plan to a JSON file.
        with open("mixing_plan.json", "w") as f:
            json.dump({"mixing_plan": mixing_plan}, f, indent=2)
        print("Mixing plan saved to 'mixing_plan.json'")

    except Exception as e:
        print(f"[generate_mixing_plan] Error: {e}")
        raise


# ---------------------------
# Example run
# ---------------------------
if __name__ == "__main__":
    generate_mixing_plan()