"""Golden: the owner-liked transitions (app/tests/fixtures/owner_liked_pairs.json) pass every live-fixes gate.

Adapter - Catchaman -> PACS & Ruiz (BR) - No Control (Long Blend); PACS & Ruiz (BR) - No Control -> Anyma & Baset -
Neverland (From Japan) (HNTR Remix) (merge -> hold / supermove); Anyma & Baset - Neverland -> Adam Sellouk & Doriann -
Nocturnal (Echo Out, key 0, the artist vocal throw). None of the new gates (drop line, mashup scene, booking vet,
owner veto) may refuse them; merges / holds are not drop-line gated at all (the liked PACS & Ruiz -> Neverland
hold sings B's voice over PACS's drop at 197 s). The analysis inputs the gates read are copied read-only in owner_liked_tracks.json.
"""
import json
from pathlib import Path

from app.music_brain.atlas import vetoes as vt
from app.music_brain.render import drop_line, mashup
from app.ui.services import booking_vet as bv

ROOT = Path(__file__).resolve().parents[3]
PAIRS = json.loads((ROOT / "app/tests/fixtures/owner_liked_pairs.json").read_text())["pairs"]
TRACKS = json.loads((ROOT / "app/tests/fixtures/owner_liked_tracks.json").read_text())["tracks"]
def _seed():
    """The tracked veto seed, loaded when a test runs (the conftest keeps the cache private), never at import."""
    return vt.load(None)


def test_no_vet_gate_refuses_them():
    for k, p in PAIRS.items():
        a, b = TRACKS[p["a"]], TRACKS[p["b"]]
        for stored in (False, True):
            r = bv.vet_one(a["name"], b["name"], a_genre=a["genre"], b_genre=b["genre"], a_era=a["era"], b_era=b["era"],
                           history=[a["name"]], vetoes=_seed(), stored=stored)
            assert r is None, (k, stored, r)
        assert mashup.scene_gate(a["genre"], b["genre"]) is None, k


def test_the_blends_keep_their_vocal_handoff():
    """autopilot.js stemHandoff: A's voice rides B's beat through the blend; the drop-line gate may not refuse
    the liked Long Blend (B's window from its entry, 16 bars, A's measured voice mapped from its exit). The liked
    Bass Swap (PACS & Ruiz -> Neverland) ran a STEM BLEND B -> A in session 2026-09-29_235413, not a handoff: the
    stem blend is not gated."""
    for k, p in PAIRS.items():
        if p["recipe"] != "Long Blend" or p["a"] != "dd3f0c201c0c0f03":
            continue
        a, b = TRACKS[p["a"]], TRACKS[p["b"]]
        bar_b = 240.0 / b["bpm"]
        sings = drop_line.mapped_sings(a["vocal_active_regions"], p["entry"], p["exit"], b["bpm"] / a["bpm"])
        assert drop_line.song_busy(b, p["entry"], p["entry"] + 16 * bar_b, sings=sings) is None, k


def test_the_echo_out_vocal_throw_stays_allowed():
    p = next(p for p in PAIRS.values() if p["recipe"] == "Echo Out")
    b = TRACKS[p["b"]]
    bar = 240.0 / b["bpm"]
    # the throw's echo tail rides B's first bars from its entry: B's drop window is not there
    assert drop_line.song_busy(b, p["entry"], p["entry"] + 8 * bar) is None
    assert p["key"] == 0
