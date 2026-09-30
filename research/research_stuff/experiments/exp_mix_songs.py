import librosa
import soundfile as sf
import numpy as np

def detect_bpm(path):
    y, sr = librosa.load(path, sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo

def time_stretch(audio, rate):
    return librosa.effects.time_stretch(audio, rate)

def mix_songs(song1_path, song2_path, chorus_start, chorus_end, fade_duration=3.0):

    # Load audio
    y1, sr1 = librosa.load(song1_path, sr=None)
    y2, sr2 = librosa.load(song2_path, sr=None)

    # BPM detection
    bpm1 = detect_bpm(song1_path)
    bpm2 = detect_bpm(song2_path)

    print(f"BPM1 = {bpm1:.2f}")
    print(f"BPM2 = {bpm2:.2f}")

    # Stretch entire first song to match BPM2
    rate = bpm2 / bpm1
    y1_stretched = time_stretch(y1, rate)
    print("Song1 stretched from the beginning to match BPM2.")

    # Convert timing → samples
    chorus_start_s = int(chorus_start * sr1)
    chorus_end_s = int(chorus_end * sr1)
    fade_samples = int(fade_duration * sr1)

    # Safety checks
    if chorus_end_s <= chorus_start_s:
        raise ValueError("chorus_end must be greater than chorus_start.")
    if chorus_end_s + fade_samples > len(y1_stretched):
        fade_samples = len(y1_stretched) - chorus_end_s

    # Song1 segments
    y1_A = y1_stretched[:chorus_start_s]               # Before chorus
    y1_B = y1_stretched[chorus_start_s:chorus_end_s]   # During overlap (normal)
    y1_C = y1_stretched[chorus_end_s:chorus_end_s+fade_samples]  # Fade-out zone
    y1_D = y1_stretched[chorus_end_s+fade_samples:]    # After fade-out

    # Fade-out applied to y1_C
    fade_curve = np.linspace(1, 0, fade_samples)
    y1_C_faded = y1_C * fade_curve

    # Song2 must start exactly at chorus_start
    y2_padded_start = np.zeros(chorus_start_s)
    y2_full = np.concatenate([y2_padded_start, y2])

    # Ensure both arrays are same length before mixing
    max_len = max(len(y1_stretched), len(y2_full))
    y1_extended = np.pad(y1_stretched, (0, max_len - len(y1_stretched)))
    y2_extended = np.pad(y2_full, (0, max_len - len(y2_full)))

    # Apply fade-out inside y1_extended
    y1_extended[chorus_end_s:chorus_end_s+fade_samples] = y1_C_faded
    y1_extended[chorus_end_s+fade_samples:] = 0  # Song1 ends after fade-out

    # Final mix = song1 (with fade-out) + song2 (overlap)
    final_audio = y1_extended + y2_extended

    # Export
    sf.write("final_mix.wav", final_audio, sr1)
    print("Exported -> final_mix.wav")
    print("Chorus overlap and fade-out applied successfully.")


# -------------------------
# RUN
# -------------------------
song1 = "songs/song1.mp3"
song2 = "songs/song2.mp3"

chorus_start = float(input("Enter chorus start point (seconds): "))
chorus_end = float(input("Enter chorus end point (seconds): "))

mix_songs(song1, song2, chorus_start, chorus_end)
