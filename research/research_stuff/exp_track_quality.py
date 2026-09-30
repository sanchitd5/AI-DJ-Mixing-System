import os
import numpy as np
from pydub import AudioSegment
from pydub.utils import which
import librosa
from mutagen.mp3 import MP3  # For precise bitrate

SONGS_DIR = "./songs"

def check_track_quality(filepath):
    filename = os.path.basename(filepath)
    try:
        # Basic file info with mutagen
        audio_file = MP3(filepath)
        duration = audio_file.info.length
        sample_rate = audio_file.info.sample_rate
        channels = audio_file.info.channels
        bitrate = audio_file.info.bitrate

        # Load with pydub for corruption check
        pydub_audio = AudioSegment.from_file(filepath)
        pydub_duration = len(pydub_audio) / 1000.0

        # Librosa load + energy check (mimics pipeline)
        y, sr = librosa.load(filepath, sr=None)
        rms = librosa.feature.rms(y=y)
        has_energy = np.mean(rms) > 0.01  # Threshold for "audible"

        # Quality flags
        is_short = duration < 30
        is_low_bitrate = bitrate < 128000  # <128 kbps
        is_corrupt = abs(duration - pydub_duration) > 1 or sr != sample_rate  # Mismatch = issues
        librosa_ok = True

        return {
            'file': filename,
            'duration_sec': round(duration, 1),
            'sample_rate_hz': sample_rate,
            'channels': channels,
            'bitrate_bps': bitrate,
            'pydub_load_ok': True,
            'librosa_load_ok': True,
            'has_audio_energy': has_energy,
            'issues': [
                f"Short (<30s)" if is_short else "",
                f"Low bitrate (<128kbps)" if is_low_bitrate else "",
                "Possible corruption (load mismatch)" if is_corrupt else "",
            ]
        }
    except Exception as e:
        return {
            'file': filename,
            'error': str(e),
            'pydub_load_ok': False,
            'librosa_load_ok': False
        }

# Scan all MP3s
mp3_files = [os.path.join(SONGS_DIR, f) for f in os.listdir(SONGS_DIR) if f.lower().endswith('.mp3')]
results = [check_track_quality(f) for f in mp3_files]

# Print summary
print("Track Quality Audit:\n")
for res in results:
    print(f"File: {res['file']}")
    if 'error' in res:
        print(f"  ERROR: {res['error']}")
    else:
        print(f"  Duration: {res['duration_sec']}s | Sample Rate: {res['sample_rate_hz']}Hz | Channels: {res['channels']} | Bitrate: {res['bitrate_bps']/1000:.0f}kbps")
        print(f"  Loads OK: Pydub={res['pydub_load_ok']}, Librosa={res['librosa_load_ok']}, Energy={res['has_audio_energy']}")
        issues = [i for i in res['issues'] if i]
        if issues:
            print(f"  Potential Issues: {', '.join(issues)}")
    print()

# Overall stats
num_files = len(results)
num_ok = sum(1 for r in results if 'error' not in r and r['librosa_load_ok'])
print(f"Summary: {num_ok}/{num_files} tracks load cleanly in Librosa. If low, check for corruption/low quality.")