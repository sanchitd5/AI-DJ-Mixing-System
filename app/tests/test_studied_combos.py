"""Studied combos: transitions of the famous studied sets (study.json) -> library pairs ->
atlas evidence, macros and the `pair_atlas studied` CLI. Synthetic tmp_path caches only."""
import json
from pathlib import Path

import pytest

from app.music_brain import macros as mc, pair_atlas as pa, studied_combos as sc

A, B, C, D, DUP = "aaaaaaaaaaaaaaaa", "bbbbbbbbbbbbbbbb", "cccccccccccccccc", "dddddddddddddddd", "eeeeeeeeeeeeeeee"
NAMES = {A: "Anyma & Chris Avantgarde - Eternity (Official Audio)", B: "Cassian - SOS",
         C: "Argy & Omiki - WIND", D: "GENESI - Hyper", DUP: "Cassian - SOS [Extended Mix]"}


def _obs(kind, a, b, at, **kw):
    return {"kind": kind, "set_id": "oRb_81stwy8", "at": at, "track_a": a, "track_b": b,
            "tempo_gap": kw.get("gap", 0.0), "key_score": kw.get("key", 1.0), "detail": {}}


def _study(tmp_path: Path) -> Path:
    cache = tmp_path
    (cache / "uploads").mkdir()
    (cache / "uploads" / "_names.json").write_text(json.dumps(NAMES))
    (cache / "track_aliases.json").write_text(json.dumps({DUP: B}))           # a second upload of Cassian - SOS
    s = cache / "sets" / "oRb_81stwy8"
    s.mkdir(parents=True)
    (cache / "sets" / "oRb_81stwy8.info.json").write_text(json.dumps({"title": "Anyma | Live from Atomium - Brussels, Belgium"}))
    tracks = [{"start": 0.0, "title": "Anyma & Chris Avantgarde - Eternity", "path": None, "heard_share": 0.8, "likely_wrong_song": False},
              {"start": 200.0, "title": "SOS - Cassian", "path": None, "heard_share": 0.7, "likely_wrong_song": False},   # "Title - Artist"
              {"start": 400.0, "title": "Argy & Omiki - WIND", "path": None, "heard_share": 0.6, "likely_wrong_song": False},
              {"start": 600.0, "title": "GENESI - Hyper", "path": None, "heard_share": 0.05, "likely_wrong_song": True},
              {"start": 800.0, "title": "Mau P - People Talk People Sing", "path": None, "heard_share": 0.5, "likely_wrong_song": False}]
    timeline = [{"t": t, "stem": "drums", "db": -10.0, "owners": [{"track": 0}] + ([{"track": 1}] if t >= 190 else [])}
                for t in (180.0, 190.0, 200.0, 210.0)]
    study = {"set_id": "oRb_81stwy8", "tracks": tracks, "timeline": timeline, "ai": "reviewed",
             "observations": [_obs("stem_intro", tracks[0]["title"], tracks[1]["title"], 195.0, gap=0.01, key=0.9),
                              _obs("hard_cut", tracks[1]["title"], tracks[2]["title"], 399.0),
                              _obs("bass_swap", tracks[2]["title"], tracks[3]["title"], 600.0)],
             "ai_rejected": [_obs("loop_extend", tracks[0]["title"], tracks[1]["title"], 190.0)]}
    (s / "study.json").write_text(json.dumps(study))
    return cache


def test_extraction_resolution_and_skips(tmp_path):
    cache = _study(tmp_path)
    rows = sc.load(cache)
    assert [r["position"] for r in rows] == [2, 3, 4, 5]
    first = rows[0]
    assert first["dj"] == "Anyma" and first["set_title"].startswith("Anyma | Live")
    assert first["techniques"] == [("stem_intro", 1)]
    assert first["rejected"] == ["loop_extend"], "the AI-rejected sighting is kept apart, never a technique"
    assert first["tempo_gap"] == 0.01 and first["key_score"] == 0.9
    assert first["overlap_s"] == 30.0, "both heard in 3 windows of 10 s"
    assert (first["a_id"], first["b_id"]) == (A, B), "the swapped 'Title - Artist' name resolves"
    # probably the wrong download: skipped, both transitions touching it
    assert rows[2]["skip"] and rows[3]["skip"]
    ev = sc.evidence(rows)
    assert set(ev) == {f"{A}>{B}", f"{B}>{C}"}
    assert ev[f"{B}>{C}"]["techniques"] == {"hard_cut": 1}
    st = sc.status(rows)
    assert st["sets"][0] == {"set_id": "oRb_81stwy8", "dj": "Anyma", "title": "Anyma | Live from Atomium - Brussels, Belgium",
                             "transitions": 4, "resolved": 2, "missing": 0, "skipped": 2}
    miss = {m["name"]: m for m in st["missing_songs"]}
    assert set(miss) == {"Mau P - People Talk People Sing", "GENESI - Hyper"}, "a skipped chain still lists what to download"
    assert miss["GENESI - Hyper"]["wrong_download"]


def test_alias_map_resolves_to_the_canonical_upload(tmp_path):
    cache = _study(tmp_path)
    names = {A: NAMES[A], DUP: "Cassian - SOS", C: NAMES[C]}      # only the duplicate upload of SOS is named
    rows = sc.resolve(sc.extract(cache), names, {DUP: B})
    assert rows[0]["b_id"] == B


def _pair(a, b, **kw):
    p = {"a": a, "b": b, "works": kw.get("works", 40), "best": "Echo Out", "recipe": kw.get("recipe", "Echo Out"),
         "combo": kw.get("combo"), "key": 0.9, "gap": 0.01, "lock": "none", "exit": 150.0, "entry": 8.0,
         "merge": {"ok": kw.get("merge_ok", False), "gate": "tempo", "hold_bars": 16 if kw.get("merge_ok") else None},
         "moves": {"stem_intro": [1, 70, None], "bass_swap": [1, 60, None]}, "energy": {}, "played": None}
    return p


def _atlas(pairs):
    return {"tracks": {t: {"name": n} for t, n in NAMES.items()}, "pairs": {f"{p['a']}>{p['b']}": p for p in pairs}}


def test_attach_ranks_studied_first_and_never_plays_a_cut(tmp_path):
    cache = _study(tmp_path)
    rows = sc.load(cache)
    rule = _pair(A, C, works=95, combo="merge", merge_ok=True, recipe="Stem Merge")      # a rule-only combo
    ab, bc = _pair(A, B, works=40), _pair(B, C, works=30, recipe="Hard Cut")
    atlas = _atlas([rule, ab, bc])
    assert sc.attach(atlas["pairs"], sc.evidence(rows)) == 2
    assert ab["combo"] == "studied" and ab["studied"]["djs"] == ["Anyma"]
    assert ab["studied"]["recipe"] == "Long Blend" and ab["studied"]["move"] == "stem_intro", "stem intro -> the console's learned recipe"
    assert pa.plan_of(ab)["recipe"] == "Long Blend"
    # hard cut sighting: studied only, and the atlas's own cut is rewritten too
    assert bc["studied"]["move"] is None and bc["studied"]["recipe"] == "Echo Out"
    assert "hard_cut" in bc["studied"]["why"] and pa.plan_of(bc)["recipe"] == "Echo Out"
    idx = pa.Index(atlas)
    assert [r["b"] for r in idx.partners(A)] == [B, C], "the studied partner ranks above the works-95 rule-only combo"
    assert idx.pair(A, B)["studied"]["sets"] == ["oRb_81stwy8"]
    assert idx.pair(A, C)["studied"] is None
    # a rebuild clears the old evidence
    sc.attach(atlas["pairs"], {})
    assert "studied" not in ab and ab["combo"] is None and rule["combo"] == "merge"


def test_macros_written_and_stale_ones_removed(tmp_path):
    cache = _study(tmp_path)
    rows = sc.load(cache)
    atlas = _atlas([_pair(A, B), _pair(B, C)])
    sc.attach(atlas["pairs"], sc.evidence(rows))
    (cache / "macros").mkdir()
    (cache / "macros" / "studied-old-1.json").write_text(json.dumps({"source": sc.MACRO_SOURCE}))
    (cache / "macros" / "studied-mine.json").write_text(json.dumps({"source": "console"}))     # the user's: untouched
    out = sc.write_macros(atlas, rows, cache)
    names = sorted(m["name"] for m in out)
    assert names == ["studied-orb_81stwy8-2", "studied-orb_81stwy8-3", "studied-set-orb_81stwy8"]
    chain = mc.load("studied-set-orb_81stwy8", cache)
    assert chain["tracks"] == [A, B, C] and chain["source"] == sc.MACRO_SOURCE
    assert chain["steps"][0]["recipe"] == "Long Blend" and chain["steps"][1]["recipe"] == "Echo Out"
    assert "Anyma #2" in chain["steps"][0]["why"]
    assert not (cache / "macros" / "studied-old-1.json").exists()
    assert (cache / "macros" / "studied-mine.json").exists()


def test_cli_lists_and_missing(tmp_path, capsys):
    cache = _study(tmp_path)
    assert pa.main(["studied", "--cache-dir", str(cache)]) == 0
    out = capsys.readouterr().out
    assert "ok   oRb_81stwy8" in out and "skip oRb_81stwy8" in out and "[stem_intro]" in out
    assert pa.main(["studied", "--missing", "--json", "--cache-dir", str(cache)]) == 0
    d = json.loads(capsys.readouterr().out)
    assert "transitions" not in d and len(d["missing_songs"]) == 2


@pytest.mark.parametrize("title,dj", [("Anyma | Live from Atomium", "Anyma"), ("Fred again.. & Thomas Bangalter (USB002)", "Fred again.. & Thomas Bangalter")])
def test_set_meta_dj(tmp_path, title, dj):
    (tmp_path / "sets").mkdir()
    (tmp_path / "sets" / "x.info.json").write_text(json.dumps({"title": title}))
    assert sc.set_meta(tmp_path, "x")["dj"] == dj
