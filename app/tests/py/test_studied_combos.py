"""Studied combos: transitions of the famous studied sets (study.json) -> library pairs ->
atlas evidence, macros and the `pair_atlas studied` CLI. Synthetic tmp_path caches only."""
import json
from pathlib import Path

import pytest

from app.music_brain.atlas import macros as mc, pair_atlas as pa, studied_combos as sc

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
    kept = mc.stored(cache)                              # the old folder migrated into the app DB first
    assert "studied-old-1" not in kept and kept["studied-mine"] == {"source": "console"}


def test_set_chain_in_set_order_bridges_missing_songs(tmp_path):
    cache = _study(tmp_path)
    F = "ffffffffffffffff"
    rows = sc.resolve(sc.extract(cache), dict(NAMES, **{F: "Mau P - People Talk People Sing"}), {})
    atlas = _atlas([_pair(A, B), _pair(B, C), _pair(C, F, recipe="Hard Cut")])
    atlas["tracks"][F] = {"name": "Mau P - People Talk People Sing"}
    sc.attach(atlas["pairs"], sc.evidence(rows))
    steps, gaps = sc.set_chain(atlas, [r for r in rows if not r["layered"]])
    assert [(s["a"], s["b"]) for s in steps] == [(A, B), (B, C), (C, F)], "set order, the wrong download skipped"
    assert gaps == ["#4 GENESI - Hyper (wrong download)"]
    assert "gap: skipped GENESI - Hyper" in steps[2]["why"]
    assert steps[2]["recipe"] == "Echo Out", "a bridging step never books a cut"
    assert steps[1]["recipe"] == "Echo Out" and "hard_cut" in steps[1]["why"], "a studied hard cut maps to a blend"


def _import_cache(tmp_path):
    cache = tmp_path
    (cache / "uploads").mkdir()
    songs = cache / "sets" / "S1" / "songs"
    songs.mkdir(parents=True)
    files = {}
    for name, body in (("Argy_Omiki_-_WIND.mp3", b"wind"), ("Resonance_Melodic_Techno_WAV_Samples_Serum_Presets.mp3", b"pack"),
                       ("Anyma_HILLS_-_Dreams_Isolated_Vocals.mp3", b"vox"), ("PACS_No_Control_Extended_Mix.mp3", b"pacs"),
                       ("Cassian_-_SOS.mp3", b"sos"), ("Some_Set_Live_at_Awakenings_2020.mp3", b"live"), ("x.mp3", b"wrong")):
        (songs / name).write_bytes(body)
        files[name] = str(songs / name)
    from app.music_brain.learning import set_import as si
    sos_id = si.content_id(songs / "Cassian_-_SOS.mp3")
    (cache / "uploads" / f"{sos_id}.mp3").write_bytes(b"sos")                  # the same file is already a library track
    (cache / "uploads" / "1111111111111111.mp3").write_bytes(b"other upload")
    (cache / "uploads" / "_names.json").write_text(json.dumps({sos_id: "Cassian - SOS", "1111111111111111": "Argy & Omiki - WIND (Official)"}))
    tr = lambda title, f, **kw: dict({"start": 0.0, "title": title, "path": files.get(f), "heard_share": 0.9, "likely_wrong_song": False}, **kw)
    study = {"set_id": "S1", "tracks": [
        tr("Argy & Omiki - WIND", "Argy_Omiki_-_WIND.mp3"), tr("Bittermind - Resonance", "Resonance_Melodic_Techno_WAV_Samples_Serum_Presets.mp3"),
        tr("Anyma & HILLS - Dreams", "Anyma_HILLS_-_Dreams_Isolated_Vocals.mp3"), tr("PACS & Ruiz (BR) - No Control", "PACS_No_Control_Extended_Mix.mp3"),
        tr("Cassian - SOS", "Cassian_-_SOS.mp3"), tr("ID ID - Higher", None), tr("Adam Beyer - ID", "x.mp3"),
        tr("Some - Song", "Some_Set_Live_at_Awakenings_2020.mp3"), tr("Wrong - Download", "x.mp3", likely_wrong_song=True, heard_share=0.04),
        tr("Cherry - Puer", None)], "observations": [], "timeline": []}
    (cache / "sets" / "S1" / "study.json").write_text(json.dumps(study))
    return cache


def test_import_set_plan_skips_and_reuses(tmp_path):
    from app.music_brain.learning import set_import as si

    cache = _import_cache(tmp_path)
    rows = si.plan(cache, "S1")
    act = {r["title"]: (r["action"], r["why"]) for r in rows}
    assert act["Argy & Omiki - WIND"][0] == "reuse" and "same recording" in act["Argy & Omiki - WIND"][1], "dedup: the library copy by name"
    assert act["Cassian - SOS"] == ("reuse", "already in the library (same file)")
    assert act["PACS & Ruiz (BR) - No Control"][0] == "import", "an Extended Mix is a release, not a DJ mix"
    for t, why in (("Bittermind - Resonance", "not the song"), ("Anyma & HILLS - Dreams", "not the song"), ("ID ID - Higher", "ID"),
                   ("Adam Beyer - ID", "ID"), ("Some - Song", "live"), ("Wrong - Download", "wrong download"), ("Cherry - Puer", "not downloaded")):
        assert act[t][0] == "skip" and why in act[t][1], (t, act[t])
    assert [r["id"] for r in rows if r["action"] == "import"] == [si.content_id(Path(rows[3]["path"]))]


def test_import_set_apply_goes_through_the_upload_path(tmp_path, capsys):
    from app.music_brain.learning import set_import as si

    cache = _import_cache(tmp_path)
    calls = []

    def upload(path, name):        # stands in for POST /api/tracks
        calls.append((path.name, name))
        return {"track_id": si.content_id(path), "filename": name}

    rows = si.apply(si.plan(cache, "S1"), upload=upload)
    assert calls == [("PACS_No_Control_Extended_Mix.mp3", "PACS & Ruiz (BR) - No Control")], "only new songs, named from the tracklist"
    s = si.summary(rows)
    assert (s["entries"], s["playable"], s["imported"], s["reused"], len(s["skipped"])) == (10, 3, 1, 2, 7)
    bad = si.apply(si.plan(cache, "S1"), upload=lambda p, n: {"track_id": "0000000000000000"})
    assert si.summary(bad)["errors"], "an id that is not the content hash is an error"
    assert pa.main(["import-set", "S1", "--dry-run", "--cache-dir", str(cache)]) == 0
    assert "3 playable" in capsys.readouterr().out
    assert pa.main(["import-set", "nope", "--cache-dir", str(cache)]) == 1


@pytest.mark.skipif(__import__("shutil").which("ffmpeg") is None, reason="ffmpeg cuts the ID out of the set")
def test_import_set_cuts_ids_out_of_the_set_and_they_resolve(tmp_path):
    import numpy as np
    import soundfile as sf

    from app.music_brain.learning import set_import as si

    cache = _import_cache(tmp_path)
    sr = 22050
    sf.write(cache / "sets" / "S1.wav", (0.1 * np.sin(2 * np.pi * 220 * np.arange(sr * 400) / sr)).astype("float32"), sr)
    study = json.loads((cache / "sets" / "S1" / "study.json").read_text())
    for i, t in enumerate(study["tracks"]):
        t["start"] = 60.0 * i
    (cache / "sets" / "S1" / "study.json").write_text(json.dumps(study))
    rows = si.plan(cache, "S1")
    cuts = [r for r in rows if r["action"] == "cut"]
    assert [(r["position"], r["name"], r["t0"], r["t1"]) for r in cuts] == [
        (6, "ID ID - Higher [set cut S1 #6]", 300.0, 360.0), (7, "Adam Beyer - ID [set cut S1 #7]", 360.0, 420.0)]
    names = json.loads((cache / "uploads" / "_names.json").read_text())

    def upload(path, name):        # POST /api/tracks stand-in: the file lands under its content id
        tid = si.content_id(path)
        (cache / "uploads" / f"{tid}{path.suffix}").write_bytes(path.read_bytes())
        names[tid] = name
        (cache / "uploads" / "_names.json").write_text(json.dumps(names))
        return {"track_id": tid}

    out = si.apply(cuts, upload=upload, analysis=lambda tid: {"bpm": 124.0, "key": {"camelot": "8A"}, "duration": 60.0})
    assert all(r.get("info") == {"bpm": 124.0, "key": "8A", "duration": 60.0} for r in out), out
    assert si.summary(out)["cut"] == 2
    assert all((cache / "uploads" / f"{r['id']}.flac").is_file() for r in out), "ID cuts register as FLAC"
    recut = si.apply([dict(c) for c in cuts], upload=upload, analysis=lambda tid: {})
    assert [r["id"] for r in recut] == [r["id"] for r in out], "a re-cut hashes to the same track id"
    again = {r["position"]: r for r in si.plan(cache, "S1")}
    assert again[6]["action"] == "reuse" and again[6]["id"] == out[0]["id"], "a second run reuses the cut"
    # the studied chain sees the cut: the ID's slot resolves, its wrong-download flag no longer applies
    rows = sc.resolve(sc.extract(cache), sc.library_names(cache), {})
    t = next(r for r in rows if r["position"] == 7)
    assert t["a_id"] == out[0]["id"] and t["b_id"] == out[1]["id"] and not t["skip"]
    fs = {x["position"]: x for x in sc.set_songs(cache)[0]["songs"]}
    assert fs[6]["status"] == "library" and fs[6]["track_id"] == out[0]["id"]


def test_set_songs_for_follow_set_and_endpoint(tmp_path, monkeypatch):
    cache = _study(tmp_path)
    for tid in NAMES:
        (cache / "uploads" / f"{tid}.mp3").write_bytes(tid.encode())
    sets = sc.set_songs(cache)
    assert [s["set_id"] for s in sets] == ["oRb_81stwy8"] and sets[0]["dj"] == "Anyma"
    got = [(x["position"], x["track_id"], x["status"]) for x in sets[0]["songs"]]
    assert got == [(1, A, "library"), (2, B, "library"), (3, C, "library"), (4, D, "library"), (5, None, "download")]
    from app.ui.services import atlas_api

    monkeypatch.setattr(atlas_api, "ATLAS_CACHE_DIR", cache)
    atlas_api._SETS_MEMO.clear()
    assert atlas_api.studied_sets()["sets"][0]["songs"][1]["track_id"] == B


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
