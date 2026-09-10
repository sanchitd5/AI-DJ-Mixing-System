#!/usr/bin/env python3
"""
denis_chorus_v2.py

Usage:
    python denis_chorus_v2.py <mp3_file> --model_weights models/best_model_V3.h5 [--summary] [--threshold 0.5]

Notes:
 - This script will try tf.keras.models.load_model(...) first.
 - If that fails with the "Could not locate class 'Functional'" error, it will
   attempt to load with keras.saving.load_model(..., safe_mode=False) which
   restores legacy-saved Functional models.
"""
import os
import argparse
import numpy as np
import librosa
from sklearn.decomposition import NMF
import tensorflow as tf

# Prefer tf.keras load_model; fallback import for keras.saving if needed
from tensorflow.keras.models import load_model as tf_load_model

try:
    # Keras package import (may be available depending on your TF/Keras versions)
    from keras.saving import load_model as keras_saving_load_model  # type: ignore
    _HAS_KERAS_SAVING = True
except Exception:
    keras_saving_load_model = None
    _HAS_KERAS_SAVING = False

# --- Feature extraction (NMF reductions) ---
def extract_features(y, sr, hop_length=512):
    """
    Produces exactly 16 features (rows) across frames (columns).
    Components: RMS(1), Mel(4), Chroma(4), MFCC(3), Tempogram(3), Dummy(1) = 16
    Returns:
      features: np.ndarray, shape (16, n_frames)
      hop_length: int
      n_features: int (=16)
    """
    # RMS
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop_length)
    print(f"RMS shape: {rms.shape}")

    # Mel spectrogram
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, hop_length=hop_length)
    print(f"Mel shape: {mel.shape}")

    # Chroma (CQT)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    print(f"Chroma shape: {chroma.shape}")

    # MFCC
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20, hop_length=hop_length)
    mfcc = np.abs(mfcc) + 1e-8
    print(f"MFCC shape: {mfcc.shape}")

    # Onset-based tempogram
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    tempogram = librosa.feature.tempogram(onset_envelope=onset_env, sr=sr,
                                          hop_length=hop_length, win_length=384, norm=None)
    tempogram = np.maximum(tempogram, 0) + 1e-8
    print(f"Tempogram shape (onset-based): {tempogram.shape}")

    # NMF reductions (increase max_iter for stability)
    nmf_rms = NMF(n_components=1, random_state=0, max_iter=1000, init='random').fit_transform(rms.T).T
    nmf_mel = NMF(n_components=4, random_state=0, max_iter=1000, init='random').fit_transform(mel.T).T
    nmf_chroma = NMF(n_components=4, random_state=0, max_iter=1000, init='random').fit_transform(chroma.T).T
    nmf_mfcc = NMF(n_components=3, random_state=0, max_iter=1000, init='random').fit_transform(mfcc.T).T
    nmf_temp = NMF(n_components=3, random_state=0, max_iter=1000, init='random').fit_transform(tempogram.T).T

    features = np.concatenate([nmf_rms, nmf_mel, nmf_chroma, nmf_mfcc, nmf_temp], axis=0)

    # Add dummy zero feature to make 16
    dummy = np.zeros((1, features.shape[1]), dtype=features.dtype)
    features = np.concatenate([features, dummy], axis=0)

    n_features = features.shape[0]
    print(f"Final features shape (with dummy): {features.shape}")  # Expect (16, N_frames)
    return features, hop_length, n_features

# --- Segment into meters (bars) ---
def segment_into_meters(features, hop_length, sr, tempo):
    """
    Return input_data shaped (max_meters, max_frames_per_meter, n_features)
    and meter_starts, meter_durations arrays.
    """
    frame_duration = hop_length / sr
    beat_duration = 60.0 / tempo if tempo and tempo > 0 else 0.5
    frames_per_beat = beat_duration / frame_duration
    frames_per_meter = max(1, int(round(4 * frames_per_beat)))  # 4/4 assumed

    num_frames = features.shape[1]
    num_meters = int(np.ceil(num_frames / frames_per_meter)) if frames_per_meter > 0 else 0

    max_frames_per_meter = 32
    max_meters = 256

    input_data = np.zeros((max_meters, max_frames_per_meter, features.shape[0]), dtype=np.float32)
    meter_starts = np.zeros(max_meters, dtype=np.float32)
    meter_durations = np.full(max_meters, 4 * beat_duration, dtype=np.float32)

    for m in range(min(num_meters, max_meters)):
        start_frame = int(m * frames_per_meter)
        end_frame = min(start_frame + frames_per_meter, num_frames)

        meter_features = features[:, start_frame:end_frame]  # (n_features, frames_in_meter)

        # Pad/truncate to max_frames_per_meter
        if meter_features.shape[1] < max_frames_per_meter:
            pad_width = max_frames_per_meter - meter_features.shape[1]
            meter_features = np.pad(meter_features, ((0, 0), (0, pad_width)), mode='constant')
        else:
            meter_features = meter_features[:, :max_frames_per_meter]

        input_data[m, :, :] = meter_features.T  # (frames, n_features)
        meter_starts[m] = start_frame * frame_duration

    return input_data, meter_starts, meter_durations

# --- Robust model loader with fallback for legacy .h5 Functional models ---
def robust_load_model(model_path, print_summary=False):
    """
    Try tf.keras.models.load_model first. If it fails due to Functional/class registry
    issues, and if keras.saving.load_model is available, try it with safe_mode=False.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    print(f"Attempting to load model via tf.keras.models.load_model('{model_path}') ...")
    try:
        model = tf_load_model(model_path, compile=False)
        print("Loaded model using tf.keras.models.load_model.")
        if print_summary:
            print("\n=== model.summary() ===")
            model.summary()
            print("=======================\n")
        return model
    except Exception as e_tf:
        print("tf.keras.models.load_model failed with exception:")
        print(e_tf)

    # Fallback to keras.saving.load_model(..., safe_mode=False) if available
    if _HAS_KERAS_SAVING and keras_saving_load_model is not None:
        try:
            print("Attempting fallback: keras.saving.load_model(..., safe_mode=False) ...")
            model = keras_saving_load_model(model_path, safe_mode=False)
            print("Loaded model using keras.saving.load_model(safe_mode=False).")
            if print_summary:
                print("\n=== model.summary() ===")
                model.summary()
                print("=======================\n")
            return model
        except Exception as e_ks:
            print("keras.saving.load_model(..., safe_mode=False) also failed with exception:")
            print(e_ks)

    # If both attempts failed, raise the first error
    raise RuntimeError("Failed to load model with both tf.keras and keras.saving fallbacks.")

# --- Main detection pipeline ---
def run_detection(mp3_file, model_path, print_summary=False, threshold=0.5):
    sr = 22050
    hop_length = 512

    print(f"Loading audio: {mp3_file}")
    y, _ = librosa.load(mp3_file, sr=sr)
    print(f"Audio length: {y.shape[0] / sr:.2f}s, sr={sr}")

    features, hop_length, n_features = extract_features(y, sr, hop_length)

    print("Estimating tempo...")
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    print(f"Estimated tempo: {tempo:.2f} BPM")

    input_data, meter_starts, meter_durations = segment_into_meters(features, hop_length, sr, tempo)

    # Attempt robust model load
    try:
        model = robust_load_model(model_path, print_summary=print_summary)
    except Exception as e:
        print("ERROR: Could not load model. Details:")
        print(e)
        return

    # Show model expected input shape
    print(f"Model input shape: {model.input_shape}")

    # Prepare data for inference
    x = input_data.astype(np.float32)
    x = np.expand_dims(x, axis=0)  # (1, max_meters, max_frames_per_meter, n_features)
    print(f"Prepared input shape for inference: {x.shape}")

    # Run prediction
    preds = model.predict(x, verbose=0)
    preds = np.asarray(preds)
    # Reduce to 1D probabilities across meters
    if preds.ndim == 3:
        probs = preds[0, :, 0]
    elif preds.ndim == 2:
        probs = preds[0, :]
    else:
        probs = preds.flatten()

    chorus_mask = probs > threshold
    chorus_indices = np.where(chorus_mask)[0]

    if len(chorus_indices) > 0:
        first_idx = chorus_indices[0]
        start_time = meter_starts[first_idx]
        end_time = start_time + meter_durations[first_idx]
        print(f"First chorus start: {start_time:.2f}s")
        print(f"First chorus end:   {end_time:.2f}s")
    else:
        print(f"No chorus detected with probability > {threshold:.2f}")

# --- CLI ---
def parse_args():
    p = argparse.ArgumentParser(description="Chorus detection (robust loader) - denis_chorus_v2")
    p.add_argument("mp3_file", type=str, help="Path to MP3 file")
    p.add_argument("--model_weights", "-m", type=str, default="models/best_model_V3.h5",
                   help="Path to saved Keras model (.h5) created with model.save()")
    p.add_argument("--summary", action="store_true", help="Print model.summary() after loading")
    p.add_argument("--threshold", type=float, default=0.5, help="Probability threshold for chorus detection")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    # Reduce TF verbosity a bit (adjust as needed)
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "1")
    run_detection(args.mp3_file, args.model_weights, print_summary=args.summary, threshold=args.threshold)
