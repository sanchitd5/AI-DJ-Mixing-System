"""OWNER VETO store (app/music_brain/atlas/vetoes.py): the tracked seed, atomic round trip, the CLI, and the
PLAYED_BAD evidence the atlas build mines from it (pair_atlas.mine_history)."""
import json

import pytest

from app.music_brain.atlas import pair_atlas as pa
from app.music_brain.atlas import vetoes as vt

SEED = vt.load(None)          # the tracked seed (the conftest keeps the cache file private and empty)
BODYROCK, WORK = "TH;EN - Bodyrock", "Masters At Work - Work (Skytech Remix)"
HACKNEY, SANTI = "Sammy Virji - Hackney Pigeon", "Santigold - You\u2019ll Find a Way (Official Audio)"


def test_seed_holds_the_two_pairs():
    pairs = {(e["a_key"], e["b_key"]) for e in SEED if e["kind"] == "pair"}
    assert (vt.song_key(BODYROCK), vt.song_key(WORK)) in pairs
    assert (vt.song_key(HACKNEY), vt.song_key(SANTI)) in pairs
    assert vt.song_key(SANTI) == vt.song_key("Santigold - You'll Find a Way"), "curly and straight quotes, upload suffix"


def test_round_trip_atomic_and_idempotent(tmp_path, monkeypatch):
    p = tmp_path / "vetoes.json"
    monkeypatch.setattr(vt, "path", lambda cache_dir=None: p)
    e = vt.make("pair", "B - Song", "A - Song", note="bad")
    assert vt.add(e) is True and vt.add(e) is False
    rows = json.loads(p.read_text())["vetoes"]
    assert len(rows) == 1 and rows[0]["b_key"] == "b song"
    assert not list(tmp_path.glob(".vetoes.*")), "no temp file left behind"
    got = vt.load(seed=None)
    assert vt.blocked(got, "A - Song (Official Video)", "B - Song") and not vt.blocked(got, "C - x", "B - Song")
    s = vt.make("song", "D - Tune", scene="house")
    vt.add(s)
    got = vt.load(seed=None)
    assert vt.blocked(got, "Z - q", "D - Tune", a_genre="deep house")
    assert vt.blocked(got, "Z - q", "D - Tune", a_genre="punjabi") is None, "a song veto holds in its scene only"
    p.write_text("not json")
    assert vt.load(seed=None) == [], "a broken file never stops a set"
    with pytest.raises(ValueError):
        vt.make("pair", "B - Song")
    with pytest.raises(ValueError):
        vt.make("pair", "A - Song", "A - Song")


def test_cli_adds(tmp_path, monkeypatch, capsys):
    p = tmp_path / "vetoes.json"
    monkeypatch.setattr(vt, "path", lambda cache_dir=None: p)
    assert vt.main(["add", "A - one", "B - two"]) == 0
    assert json.loads(capsys.readouterr().out)["added"] is True
    assert vt.blocked(vt.load(seed=None), "A - one", "B - two")


def test_mined_as_played_bad_evidence(tmp_path, monkeypatch):
    p = tmp_path / "vetoes.json"
    monkeypatch.setattr(vt, "path", lambda cache_dir=None: p)
    vt.add(vt.make("pair", "B - two", "A - one"))
    names = {"ida": "A - one (Official Audio)", "idb": "B - two", "idc": "C - three"}
    ev = pa.mine_history(tmp_path, names)
    e = ev["ida>idb"]
    assert e["bad"] >= pa.OWNER_VETO_BAD and e["sources"]["owner_veto"] == 1
    assert pa.played_adjust(e) <= -30 + 0, "the veto takes the full played-bad penalty"
    assert "ida>idc" not in ev
