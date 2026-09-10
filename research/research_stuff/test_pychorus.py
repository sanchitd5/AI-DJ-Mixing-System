import argparse
import librosa
import numpy as np
import scipy.signal
from scipy.ndimage import gaussian_filter
from sklearn.metrics.pairwise import cosine_similarity
import soundfile as sf
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# ==================== CONFIGURATION ====================
N_FFT = 2048
SMOOTHING_SIZE_SEC = 0.5
LINE_THRESHOLD = 0.5
MIN_LINES = 3
NUM_ITERATIONS = 10
OVERLAP_PERCENT_MARGIN = 0.1
MAX_LAG = 1000  # Maximum lag in frames (controls speed vs accuracy)
# =======================================================

class Line:
    def __init__(self, start, end, lag):
        self.start = start    # frame index (time)
        self.end = end        # frame index (time)
        self.lag = lag        # frame lag (how far back this segment repeats)

    def __repr__(self):
        return f"Line(start={self.start}, end={self.end}, lag={self.lag})"


def extract_chroma(input_file, n_fft=N_FFT):
    y, sr = librosa.load(input_file, sr=None)
    song_length_sec = len(y) / sr

    # Compute power spectrogram and chroma
    S = np.abs(librosa.stft(y, n_fft=n_fft)) ** 2
    chroma = librosa.feature.chroma_stft(S=S, sr=sr)
    chroma = chroma.T  # Shape: (n_frames, 12)

    return chroma, y, sr, song_length_sec


def local_maxima_rows(denoised_time_lag):
    """Find rows (lags) that are locally prominent across time."""
    row_sums = np.sum(denoised_time_lag, axis=0)  # sum over time for each lag
    x = np.arange(len(row_sums))
    # Weight by distance from zero lag (favor reasonable repeat lengths)
    weights = 1.0 / (x + 1)
    normalized = row_sums * weights
    peaks = scipy.signal.argrelextrema(normalized, np.greater, order=15)[0]
    return peaks if len(peaks) > 0 else np.array([np.argmax(normalized)])


def detect_lines_helper(denoised_time_lag, rows, threshold, min_length_samples):
    num_frames = denoised_time_lag.shape[0]
    lines = []

    for lag_idx in rows:
        lag = lag_idx + 1  # because tl_sim[:,0] is lag=1
        col = denoised_time_lag[:, lag_idx]

        # Find contiguous segments above threshold
        above = col > threshold
        changes = np.diff(above.astype(int), prepend=0, append=0)
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]

        for s, e in zip(starts, ends):
            if e - s >= min_length_samples:
                lines.append(Line(s, e, lag))

    return lines


def detect_lines(denoised_time_lag, candidate_lags, min_length_samples):
    threshold = LINE_THRESHOLD
    for _ in range(NUM_ITERATIONS):
        lines = detect_lines_helper(denoised_time_lag, candidate_lags, threshold, min_length_samples)
        if len(lines) >= MIN_LINES:
            return lines
        threshold *= 0.95  # gradually lower threshold
    return lines


def count_overlapping_lines(lines, margin, min_lag_diff):
    scores = {line: 0 for line in lines}
    for i, l1 in enumerate(lines):
        for l2 in lines:
            if l1 is l2:
                continue
            if abs(l1.lag - l2.lag) <= min_lag_diff:
                continue

            # Vertical overlap: same time, different lag
            v_overlap = (l2.start < l1.end - margin) and (l2.end > l1.start + margin)
            # Diagonal alignment: l2 is a shifted version of l1
            d_overlap = (
                abs((l2.start - l2.lag) - (l1.start - l1.lag)) < margin and
                abs((l2.end - l2.lag) - (l1.end - l1.lag)) < margin
            )
            if v_overlap or d_overlap:
                scores[l1] += 1
    return scores


def select_first_chorus(line_scores, chroma_sr, min_score=3, min_start_sec=30):
    candidates = []
    for line, score in line_scores.items():
        duration = (line.end - line.start) / chroma_sr
        start_sec = line.start / chroma_sr
        if score >= min_score and start_sec >= min_start_sec and duration > 10:
            candidates.append((start_sec, score, duration, line))

    if candidates:
        candidates.sort(key=lambda x: (x[0], -x[1]))  # earliest + highest score
        return candidates[0][3]

    # Fallback: earliest high-scoring
    fallback = [(line.start / chroma_sr, line_scores[line], line) for line in line_scores]
    fallback.sort(key=lambda x: (x[1], x[0]), reverse=True)
    return fallback[0][2] if fallback else max(line_scores.keys(), key=lambda l: l.start)


def find_first_chorus(chroma, sr, song_length_sec, clip_length=18, min_start=30):
    num_frames = chroma.shape[0]
    chroma_sr = num_frames / song_length_sec

    print("Computing time-time similarity matrix...")
    tt_sim = cosine_similarity(chroma)

    # Pre-normalize chroma for fast cosine similarity
    chroma_norm = chroma / (np.linalg.norm(chroma, axis=1, keepdims=True) + 1e-12)

    max_lag = min(MAX_LAG, num_frames // 3)
    tl_sim = np.zeros((num_frames, max_lag))
    print(f"Computing time-lag similarity (diagonal only, max_lag={max_lag})...")

    for lag in range(1, max_lag + 1):
        if lag % 200 == 0 or lag == max_lag:
            print(f"  Processing lag {lag}/{max_lag}")
        sim = np.sum(chroma_norm[:-lag] * chroma_norm[lag:], axis=1)
        tl_sim[:-lag, lag - 1] = sim

    # Smooth the time-lag matrix
    print("Smoothing time-lag matrix...")
    denoised_tl = gaussian_filter(tl_sim, sigma=1.5)

    # Blend with time-time similarity (boost recurrence)
    blend_size = min(tt_sim.shape[0], denoised_tl.shape[0], denoised_tl.shape[1])
    denoised_tl[:blend_size, :blend_size] = np.maximum(
        denoised_tl[:blend_size, :blend_size],
        0.6 * tt_sim[:blend_size, :blend_size]
    )

    # Find strong repeating lags
    candidate_lags = local_maxima_rows(denoised_tl)

    clip_samples = int(clip_length * chroma_sr)
    lines = detect_lines(denoised_tl, candidate_lags, clip_samples)

    if not lines:
        print("No repeating segments found. Try lowering thresholds.")
        return None

    print(f"\nFound {len(lines)} candidate repeating segments:")
    line_scores = count_overlapping_lines(lines, margin=0.1 * clip_samples, min_lag_diff=chroma_sr * 5)
    for line in sorted(lines, key=lambda l: l.start):
        start_sec = line.start / chroma_sr
        dur_sec = (line.end - line.start) / chroma_sr
        print(f"  → {start_sec:6.2f}s → {start_sec + dur_sec:6.2f}s | dur={dur_sec:4.1f}s | lag={line.lag/chroma_sr:5.1f}s | score={line_scores[line]}")

    best_line = select_first_chorus(line_scores, chroma_sr, min_score=2, min_start_sec=min_start)
    start_sec = best_line.start / chroma_sr

    return start_sec


def detect_first_chorus_times(mp3_path: str, output_txt: str = None, clip_length: int = 18, min_start: int = 30):
    mp3_path = Path(mp3_path).resolve()
    if not mp3_path.exists():
        raise FileNotFoundError(f"File not found: {mp3_path}")

    print(f"Loading audio: {mp3_path.name}")
    chroma, _, sr, song_length_sec = extract_chroma(str(mp3_path))

    print(f"Song duration: {song_length_sec/60:.2f} minutes")
    print(f"Chroma frames: {chroma.shape[0]}, ~{chroma.shape[0]/song_length_sec:.1f} fps")

    start_sec = find_first_chorus(chroma, sr, song_length_sec, clip_length, min_start)

    if start_sec is None:
        raise ValueError("Could not detect first chorus.")

    end_sec = start_sec + clip_length

    print("\n" + "="*60)
    print(f" FIRST CHORUS DETECTED!")
    print(f" Start: {start_sec // 60:.0f}m {start_sec % 60:05.2f}s")
    print(f" End:   {end_sec // 60:.0f}m {end_sec % 60:05.2f}s")
    print(f" Duration: {clip_length} seconds")
    print("="*60)

    if output_txt:
        with open(output_txt, 'w') as f:
            f.write(f"{start_sec:.3f}\t{end_sec:.3f}\tchorus\n")
        print(f"Saved to: {output_txt}")

    return start_sec, end_sec


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Accurate First Chorus Detector (2025 Fixed Version)")
    parser.add_argument("mp3_path", type=str, help="Path to input MP3/WAV file")
    parser.add_argument("--output", type=str, default=None, help="Output .txt file (start end label)")
    parser.add_argument("--clip-length", type=int, default=18, help="Expected chorus length in seconds (default: 18)")
    parser.add_argument("--min-start", type=int, default=30, help="Ignore choruses before this time (seconds)")

    args = parser.parse_args()
    detect_first_chorus_times(args.mp3_path, args.output, args.clip_length, args.min_start)


# To run - python test_chorus_detection.py "input.mp3" --output chorus.txt --clip-length 20                     