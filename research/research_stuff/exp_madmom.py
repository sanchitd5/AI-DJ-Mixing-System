import numpy as np
import madmom.features.beats
import madmom.features.tempo

# -------------------------------------------------------------------------
# Define the Path to your Audio File
# NOTE: Replace 'path/to/your/song.wav' with the actual path to your file
# Madmom works best with WAV files, but can often handle MP3/FLAC if you
# have 'ffmpeg' installed on your system and in your PATH.
# -------------------------------------------------------------------------
audio_file_path = r'D:\brdge\AI DJ Mixing System\songs\OneRepublic - I Ain’t Worried (Lyrics) - 7clouds.mp3'

# --- 1. Beat Activation Generation ---
# RNNBeatProcessor uses a recurrent neural network to generate a beat activation function.
# The default frame rate (fps=100) is standard for madmom.
try:
    print("-> 1. Generating Beat Activations (this may take a few seconds)...")
    act_proc = madmom.features.beats.RNNBeatProcessor()
    
    # Process the audio file to get the beat activation function (a time series)
    beat_activations = act_proc(audio_file_path)

except Exception as e:
    print(f"\nFATAL ERROR during Madmom Activation: {e}")
    print("Madmom could not load or process the file. Check the path and file format.")
    # Exit or handle the error gracefully
    exit()

# --- 2. Tempo Estimation ---
# TempoEstimationProcessor takes the activations and calculates the most dominant tempi.
# 'comb' method uses a comb-filter bank and is a high-performing default.
print("-> 2. Estimating Tempo...")
tempo_proc = madmom.features.tempo.TempoEstimationProcessor(
    method='comb',  # Use comb filter bank method
    min_bpm=40.0,
    max_bpm=250.0,
    fps=100.0
)

# Process the activations to get the BPM results
tempi_data = tempo_proc(beat_activations)

# --- 3. Extract and Format Results ---
# The result is a NumPy array where each row is [BPM, Strength]
if tempi_data.size > 0:
    # Get the most dominant tempo (first row, first column)
    dominant_bpm = tempi_data[0][0]
    dominant_strength = tempi_data[0][1]

    print("\n" + "="*40)
    print(f"✅ Dominant Tempo (BPM): {dominant_bpm:.2f}")
    print(f"Confidence (Strength): {dominant_strength:.3f}")
    
    # Display secondary tempos
    if len(tempi_data) > 1:
        print("\nSecondary Tempo Candidates:")
        # List other top tempos (excluding the first)
        for bpm, strength in tempi_data[1:]:
            print(f"- {bpm:.2f} BPM (Strength: {strength:.3f})")
    print("="*40)
else:
    print("⚠️ Could not detect a reliable tempo.")