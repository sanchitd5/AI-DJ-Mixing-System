"""Transition-level acoustic analysis for a studied DJ set.

Re-run with:
    python research/notes/set_study_analyze.py /path/to/set.mp3

Written for the Fred again.. & Thomas Bangalter USB002 set study
(research/notes/set-study-gfF8jzBVWvM.md). Not part of the app; a research
tool only. Takes an audio file (mp3/m4a/wav) and a hand-supplied list of
segment-start timestamps (seconds), and for each transition prints:

  - tempo estimate before/after (30s windows, librosa.beat.tempo)
  - chroma + Krumhansl-Schmuckler key estimate before/after, as Camelot
  - band energy (sub <120Hz, mid 120Hz-4kHz, high >4kHz) in 1s frames
    across a +/-20s window around the transition, so the ORDER the bands
    move in is visible in the printed table
  - RMS dBFS curve across the same window (dips / echo tails / builds)

Notes on reliability (read before trusting any single number):
  - Tempo/key estimates are computed on the *mixed* (already-blended) audio,
    with two or more tracks/stems often playing at once. Librosa's tempo
    and Krumhansl-Schmuckler key estimators were built for single, clean
    tracks. Treat every BPM/Camelot value here as a rough hint, not a fact,
    especially inside long mashup segments where 3-6 songs overlap.
  - Band-energy and RMS curves are far more trustworthy: they're direct
    measurements of the mixed signal, not model inferences.
"""

from __future__ import annotations

import sys
import numpy as np
import librosa
import librosa.feature.rhythm

SR = 22050
LOW_HZ = 120.0
HIGH_HZ = 4000.0

# Krumhansl-Schmuckler major/minor key profiles
KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Camelot wheel: (pitch_class_of_tonic, mode) -> Camelot code
# Standard mapping, major = "B", minor = "A"
CAMELOT_MAJOR = {
    "B": "1B", "F#": "2B", "Db": "3B", "C#": "3B", "Ab": "4B", "G#": "4B",
    "Eb": "5B", "D#": "5B", "Bb": "6B", "A#": "6B", "F": "7B", "C": "8B",
    "G": "9B", "D": "10B", "A": "11B", "E": "12B",
}
CAMELOT_MINOR = {
    "Ab": "1A", "G#": "1A", "Eb": "2A", "D#": "2A", "Bb": "3A", "A#": "3A",
    "F": "4A", "C": "5A", "G": "6A", "D": "7A", "A": "8A", "E": "9A",
    "B": "10A", "F#": "11A", "Db": "12A", "C#": "12A",
}


def estimate_key(y: np.ndarray, sr: int) -> tuple[str, str, float]:
    """Returns (pitch_class, mode, correlation) best-fit via KS profiles."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    profile = chroma.mean(axis=1)
    best = ("C", "major", -2.0)
    for shift in range(12):
        maj = np.roll(KS_MAJOR, shift)
        minr = np.roll(KS_MINOR, shift)
        cmaj = np.corrcoef(profile, maj)[0, 1]
        cmin = np.corrcoef(profile, minr)[0, 1]
        pc = PITCH_CLASSES[shift]
        if cmaj > best[2]:
            best = (pc, "major", cmaj)
        if cmin > best[2]:
            best = (pc, "minor", cmin)
    return best


def to_camelot(pc: str, mode: str) -> str:
    table = CAMELOT_MAJOR if mode == "major" else CAMELOT_MINOR
    return table.get(pc, "?")


def band_energy_db(y: np.ndarray, sr: int, hop_s: float = 1.0) -> dict:
    """Frame-wise energy (dBFS) in sub/mid/high bands via STFT."""
    n_fft = 4096
    hop_length = int(sr * hop_s)
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    low_mask = freqs < LOW_HZ
    mid_mask = (freqs >= LOW_HZ) & (freqs < HIGH_HZ)
    high_mask = freqs >= HIGH_HZ

    def band_db(mask):
        e = S[mask, :].sum(axis=0)
        return 10 * np.log10(np.maximum(e, 1e-12))

    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop_length)
    return {
        "times": times,
        "low": band_db(low_mask),
        "mid": band_db(mid_mask),
        "high": band_db(high_mask),
    }


def rms_dbfs(y: np.ndarray, sr: int, hop_s: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    hop_length = int(sr * hop_s)
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    return times, 20 * np.log10(np.maximum(rms, 1e-8))


def analyze_window(y_full: np.ndarray, sr: int, center_s: float, half_window_s: float = 20.0):
    lo = max(0, int((center_s - half_window_s) * sr))
    hi = min(len(y_full), int((center_s + half_window_s) * sr))
    y = y_full[lo:hi]
    if len(y) < sr * 2:
        return None
    bands = band_energy_db(y, sr, hop_s=1.0)
    times, rms = rms_dbfs(y, sr, hop_s=1.0)
    tempo_before = None
    tempo_after = None
    key_before = None
    key_after = None
    try:
        half = len(y) // 2
        if half > sr * 3:
            tb = librosa.feature.rhythm.tempo(y=y[:half], sr=sr, aggregate=np.median)
            ta = librosa.feature.rhythm.tempo(y=y[half:], sr=sr, aggregate=np.median)
            tempo_before, tempo_after = float(tb[0]), float(ta[0])
            pc_b, mode_b, corr_b = estimate_key(y[:half], sr)
            pc_a, mode_a, corr_a = estimate_key(y[half:], sr)
            key_before = (to_camelot(pc_b, mode_b), corr_b)
            key_after = (to_camelot(pc_a, mode_a), corr_a)
    except Exception:
        pass
    return {
        "bands": bands,
        "rms_times": times,
        "rms": rms,
        "tempo_before": tempo_before,
        "tempo_after": tempo_after,
        "key_before": key_before,
        "key_after": key_after,
    }


def print_window_report(label: str, center_s: float, result: dict):
    print(f"\n=== {label} (center t={center_s:.0f}s) ===")
    if result["tempo_before"] is not None:
        print(f"  tempo before->after: {result['tempo_before']:.1f} -> {result['tempo_after']:.1f} BPM (noisy on mixed audio)")
    if result.get("key_before") is not None:
        kb, cb = result["key_before"]
        ka, ca = result["key_after"]
        print(f"  key (Camelot, KS-correlation) before->after: {kb} (r={cb:.2f}) -> {ka} (r={ca:.2f}) (noisy, low confidence if r<0.6)")
    bands = result["bands"]
    times = bands["times"]
    print("  t(rel_s)  low_dB  mid_dB  high_dB   rms_dB")
    rms = dict(zip(np.round(result["rms_times"], 1), result["rms"]))
    for i, t in enumerate(times):
        rel = t - (times[-1] / 2)
        rms_v = rms.get(round(t, 1), float("nan"))
        print(f"  {rel:+7.1f}  {bands['low'][i]:6.1f}  {bands['mid'][i]:6.1f}  {bands['high'][i]:6.1f}   {rms_v:6.1f}")


def scan_tempo_curve(y_full: np.ndarray, sr: int, start_s: float, end_s: float,
                      window_s: float = 30.0, hop_s: float = 10.0):
    """Windowed tempo estimate (30s window / 10s hop by default) over a span."""
    t = start_s
    while t + window_s <= end_s:
        lo = int(t * sr)
        hi = int((t + window_s) * sr)
        seg = y_full[lo:hi]
        try:
            bpm = librosa.feature.rhythm.tempo(y=seg, sr=sr, aggregate=np.median)[0]
            print(f"  t={t:6.0f}s  window=[{t:.0f},{t + window_s:.0f}]  tempo~{bpm:6.1f} BPM")
        except Exception as e:
            print(f"  t={t:6.0f}s  tempo estimate failed: {e}")
        t += hop_s


def main():
    if len(sys.argv) < 2:
        print("usage: python set_study_analyze.py <audio_path> [timestamps_csv_seconds]")
        sys.exit(1)
    path = sys.argv[1]

    # Default: transition timestamps from the pasted tracklist, in seconds.
    default_marks = [1, 196, 457, 690, 980, 1060, 1200, 1354, 1445, 1500,
                      1870, 1910, 2400, 2505, 2629, 2725, 2830, 2925,
                      3254, 3440, 3660, 3990, 4147, 4280, 4700, 4760,
                      5300, 5565, 5760, 5980, 6366]
    marks = default_marks
    if len(sys.argv) > 2:
        marks = [float(x) for x in sys.argv[2].split(",")]

    print(f"Loading {path} (mono, sr={SR})...")
    y_full, sr = librosa.load(path, sr=SR, mono=True)
    dur = len(y_full) / sr
    print(f"Loaded {dur:.1f}s of audio")

    for m in marks:
        if m >= dur:
            continue
        res = analyze_window(y_full, sr, m, half_window_s=20.0)
        if res:
            print_window_report(f"t={m:.0f}s", m, res)

    # Tempo-over-time curve, fine resolution, for the windows the report needs
    # to speak precisely to: the 31:50 "87 x 2" possible half-time/DnB switch,
    # and the Nia Archives DnB stretch (roughly 1:09-1:18).
    print("\n=== Tempo over time, 30s window / 10s hop (1750s-2000s: 31:50 switch) ===")
    scan_tempo_curve(y_full, sr, 1750, 2000)
    print("\n=== Tempo over time, 30s window / 10s hop (4100s-4750s: DnB / Nia Archives section) ===")
    scan_tempo_curve(y_full, sr, 4100, 4750)

    # Whole-set RMS curve at coarse resolution for the loudness/build overview.
    print("\n=== Whole-set RMS dBFS (30s hop) ===")
    times, rms = rms_dbfs(y_full, sr, hop_s=30.0)
    for t, r in zip(times, rms):
        mins = int(t // 60)
        secs = int(t % 60)
        print(f"  {mins:3d}:{secs:02d}  {r:6.1f} dBFS")


if __name__ == "__main__":
    main()
