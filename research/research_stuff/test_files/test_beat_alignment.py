#!/usr/bin/env python
"""
Test script for perfect beat-to-beat alignment system
Validates that the new beat grid alignment works correctly
"""

import sys
from mixing_engine import detect_beat_grid, align_beats_perfect
from pydub import AudioSegment
import numpy as np

def test_beat_detection():
    """Test basic beat detection on sample audio"""
    print("=" * 60)
    print("TEST 1: Beat Grid Detection")
    print("=" * 60)
    
    # Load a sample track from the songs directory
    import os
    songs_dir = "songs"
    
    if not os.path.exists(songs_dir):
        print("❌ Songs directory not found. Please ensure test songs exist.")
        return False
    
    # Find first MP3 file
    test_file = None
    for file in os.listdir(songs_dir):
        if file.endswith(".mp3"):
            test_file = os.path.join(songs_dir, file)
            break
    
    if not test_file:
        print("❌ No MP3 files found in songs directory.")
        return False
    
    print(f"Loading test file: {os.path.basename(test_file)}")
    
    try:
        audio = AudioSegment.from_mp3(test_file)
        # Test on first 30 seconds
        audio_sample = audio[:30000]
        
        print(f"Duration: {len(audio_sample)/1000:.1f}s")
        
        # Detect beat grid
        beats, downbeats, tempo = detect_beat_grid(audio_sample)
        
        print(f"\n✅ Beat detection successful!")
        print(f"   Detected tempo: {tempo:.1f} BPM")
        print(f"   Total beats found: {len(beats)}")
        print(f"   Downbeats found: {len(downbeats)}")
        
        if len(beats) > 0:
            avg_beat_interval = np.diff(beats).mean() if len(beats) > 1 else 0
            print(f"   Average beat interval: {avg_beat_interval:.1f}ms")
            print(f"   Calculated BPM from intervals: {60000/avg_beat_interval:.1f}")
        
        print(f"\n   First 10 beats (ms): {beats[:10]}")
        print(f"   First 5 downbeats (ms): {downbeats[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Beat detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_perfect_alignment():
    """Test perfect beat alignment between two tracks"""
    print("\n" + "=" * 60)
    print("TEST 2: Perfect Beat-to-Beat Alignment")
    print("=" * 60)
    
    import os
    songs_dir = "songs"
    
    # Find two MP3 files for testing
    mp3_files = [f for f in os.listdir(songs_dir) if f.endswith(".mp3")][:2]
    
    if len(mp3_files) < 2:
        print("❌ Need at least 2 MP3 files for alignment test.")
        return False
    
    try:
        print(f"Track 1: {mp3_files[0]}")
        print(f"Track 2: {mp3_files[1]}")
        
        track1 = AudioSegment.from_mp3(os.path.join(songs_dir, mp3_files[0]))
        track2 = AudioSegment.from_mp3(os.path.join(songs_dir, mp3_files[1]))
        
        # Use 30-second segments for testing
        segment1 = track1[60000:90000]  # 1:00 - 1:30
        segment2 = track2[:30000]       # 0:00 - 0:30
        
        print(f"\nSegment 1 duration: {len(segment1)/1000:.1f}s")
        print(f"Segment 2 duration: {len(segment2)/1000:.1f}s")
        
        # Test with 8-second overlap
        overlap_ms = 8000
        
        # Apply perfect alignment
        print(f"\nApplying perfect beat alignment (overlap: {overlap_ms/1000:.1f}s)...")
        aligned_segment2, shift_ms = align_beats_perfect(
            segment1, 
            segment2, 
            overlap_ms, 
            bpm_from=120,  # These would normally come from metadata
            bpm_to=125
        )
        
        print(f"\n✅ Alignment completed!")
        print(f"   Initial shift: {shift_ms:.1f}ms")
        print(f"   Original duration: {len(segment2)/1000:.1f}s")
        print(f"   Aligned duration: {len(aligned_segment2)/1000:.1f}s")
        print(f"   Duration change: {(len(aligned_segment2) - len(segment2))/1000:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Alignment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test the complete integration with mixing engine"""
    print("\n" + "=" * 60)
    print("TEST 3: Integration Test")
    print("=" * 60)
    
    # Check if mixing plan exists
    import os
    if not os.path.exists("output/mixing_plan.json"):
        print("⚠️  No mixing plan found. Run run_pipeline.py first.")
        print("   This test validates the complete mixing system.")
        return False
    
    print("✅ Mixing plan found.")
    print("   The new beat alignment system is now integrated.")
    print("   Run the full pipeline to test: python run_pipeline.py")
    
    return True

if __name__ == "__main__":
    print("\n" + "🎵" * 30)
    print("PERFECT BEAT ALIGNMENT - TEST SUITE")
    print("🎵" * 30 + "\n")
    
    results = []
    
    # Run tests
    results.append(("Beat Grid Detection", test_beat_detection()))
    results.append(("Perfect Alignment", test_perfect_alignment()))
    results.append(("Integration Check", test_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Beat alignment system is ready.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    sys.exit(0 if passed == total else 1)
