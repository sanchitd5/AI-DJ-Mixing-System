"""Pair atlas + macros: console-rule parity, incremental rebuild, schema, chains, history
mining, macros save/load/validate/versioning, seed macros and the REST surface. All on a
synthetic tmp cache dir (never the real data/)."""
import json
import os
import shutil
import time
from pathlib import Path

import numpy as np
import pytest

from app.music_brain import energy, macros as mc, pair_atlas as pa, techniques

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed: the atlas runs the console's JS rules")

IDS = ["6e3ee890fbf3d9bc", "9f7060c991aeb80b", "0123456789abcdef"]
NAMES = ["Seven Lions - Days To Come (feat. Fiora)", "Lane 8, Jyll - Stay Still, A Little While", "Skrillex - Rise ft. Krewella"]
KEYS = ["5B", "5B", "11A"]
BPMS = [112.0, 112.5, 150.0]


def _write_track(cache: Path, tid: str, name: str, key, bpm: float, dur: float = 200.0, sr: int = 11025):
    import soundfile as sf

    digest = (tid * 4)[:64]
    (cache / "uploads" / f"{tid}.flac").write_bytes(b"x")
    bar = 240.0 / bpm
    beats = list(np.arange(0.0, dur, 60.0 / bpm))
    phrases = list(np.arange(0.0, dur - 1, 8 * bar))
    times = list(np.arange(0.0, dur, 1.0))
    curve = [0.3 + 0.6 * ((t // (32 * bar)) % 2) for t in times]      # 32-bar energy steps: drops
    a = {"path": name, "duration": dur, "bpm": bpm, "beat_times": beats, "downbeat_times": beats[::4],
         "phrase_boundaries_8bar": phrases, "phrase_boundaries_16bar": phrases[::2],
         "key": key, "energy_curve": curve, "energy_times": times, "sections": [], "vocal_active_regions": []}
    (cache / "analysis" / f"{digest}.v5.json").write_text(json.dumps(a))
    st = cache / "stems" / f"{digest}_htdemucs"
    st.mkdir(parents=True)
    rng = np.random.default_rng(int(tid[:6], 16))
    n = int(dur * sr)
    t = np.arange(n) / sr
    man = {}
    for stem in ("drums", "bass", "vocals", "other"):
        y = 0.1 * rng.standard_normal(n).astype("float32") if stem != "vocals" else np.zeros(n, "float32")
        if stem == "vocals":        # sings from bar 16 for 32 bars, then silent
            on = (t >= 16 * bar) & (t < 48 * bar)
            y[on] = 0.2 * np.sin(2 * np.pi * 220 * t[on]).astype("float32")
        p = st / f"{stem}.wav"
        sf.write(p, y, sr)
        man[stem] = str(p)
    (st / "manifest.json").write_text(json.dumps(man))
    return digest


@pytest.fixture()
def cache(tmp_path):
    for d in ("uploads", "analysis", "stems", "sessions"):
        (tmp_path / d).mkdir()
    (tmp_path / "uploads" / "_names.json").write_text(json.dumps(dict(zip(IDS, NAMES))))
    for i, tid in enumerate(IDS):
        key = {"camelot": KEYS[i], "key_name": KEYS[i], "is_major": KEYS[i].endswith("B"), "confidence": 0.8} if i != 2 else KEYS[i]
        _write_track(tmp_path, tid, NAMES[i], key, BPMS[i])
    return tmp_path


def _build(cache, **kw):
    return pa.build(cache, log=lambda m: None, workers=1, **kw)


def test_console_rule_parity_on_fixed_vectors():
    """The atlas's Python pieces agree with the console's JS copies (run in node) on fixed vectors."""
    keys = ["1A", "1B", "2A", "3A", "12A", "11B", "5B", "8A", "", "7A"]
    tempos = [(128, 128), (128, 124), (128, 64), (170, 85), (112, 112.5), (120, 150), (140, 131)]
    jobs = [{"kind": "camelot", "a": a, "b": b} for a in keys for b in keys]
    jobs += [{"kind": "lock", "aEff": a, "bBpm": b} for a, b in tempos]
    jobs += [{"kind": "keysafe", "recipe": r, "keyScore": k} for r in ("Long Blend", "Bass Swap", "Echo Out") for k in (None, 0.3, 0.6, 1)]
    jobs += [{"kind": "energy", "cur": c, "nxt": x} for c in range(1, 11) for x in range(1, 11)]
    res = pa.node_run({}, jobs)

    def console_table(a, b):     # CLAUDE.md s4 "Live console gate" (dj-mind.js camelotScore)
        import re
        pa_, pb_ = re.match(r"^(\d{1,2})([AB])$", a), re.match(r"^(\d{1,2})([AB])$", b)
        if not pa_ or not pb_:
            return 0
        up = (int(pb_[1]) - int(pa_[1])) % 12
        d = min(up, 12 - up)
        if pa_[2] != pb_[2]:
            return {0: 0.85, 1: 0.75, 2: 0.3}.get(d, 0)
        return 1 if d == 0 else 0.9 if d == 1 else 0.8 if up == 2 else 0.6 if up == 10 else 0

    i = 0
    for a in keys:
        for b in keys:
            assert res[i] == console_table(a, b), (a, b)
            i += 1
    for a, b in tempos:
        assert abs(res[i] - pa.fold_gap(a, b)[1]) < 1e-12, (a, b)
        i += 1
    for r in ("Long Blend", "Bass Swap", "Echo Out"):
        for k in (None, 0.3, 0.6, 1):
            expect = r if k is None or k >= pa.KEY_SAFE_MIN or r == "Echo Out" else "Echo Out"
            assert res[i] == expect, (r, k)
            i += 1
    for c in range(1, 11):
        for x in range(1, 11):
            got = energy.next_ok(c, x)
            assert {"ok": res[i]["ok"], "step": res[i]["step"], "why": res[i]["why"]} == got, (c, x)
            i += 1


def test_build_scores_every_ordered_pair_and_the_live_test_pair_is_a_merge_combo(cache):
    doc = _build(cache)
    assert doc["stats"]["pairs"] == 6 and doc["schema"] == pa.SCHEMA
    p = doc["pairs"][f"{IDS[0]}>{IDS[1]}"]
    assert p["key"] == 1.0 and p["gap"] < 0.01
    # the key the atlas stores is the console's (node) answer, not a Python copy
    assert doc["pairs"][f"{IDS[0]}>{IDS[2]}"]["key"] == pa.node_run({}, [{"kind": "camelot", "a": "5B", "b": "11A"}])[0]
    assert p["merge"]["ok"], p["merge"]
    assert p["combo"] == "merge" and p["best"] == "Merge → Hold"
    assert p["merge"]["hold_bars"] and p["merge"]["phases"]
    rise = doc["pairs"][f"{IDS[0]}>{IDS[2]}"]
    assert not rise["merge"]["ok"] and rise["merge"]["gate"] in ("tempo", "key")
    assert rise["works"] < p["works"]
    assert pa.move_of(rise, "echo_out")["ok"] is True
    assert pa.move_of(rise, "hook_drop")["ok"] is None and "live" in pa.move_of(rise, "hook_drop")["gate"]
    # the string key record was handled
    assert doc["tracks"][IDS[2]]["key"] == "11A"
    # queries
    top = pa.partners(doc, IDS[0], n=2)
    assert top[0]["b"] == IDS[1]
    assert [r["b"] for r in pa.partners(doc, IDS[0], move="merge")] == [IDS[1]]
    assert pa.best_pairs(doc, move="supermove")[0]["merge_ok"]
    with pytest.raises(ValueError):
        pa.normalize_move("teleport")


def test_incremental_rebuild_and_rules_versioning(cache, monkeypatch):
    first = _build(cache)
    assert first["stats"]["scored"] == 6
    again = _build(cache)
    assert again["stats"]["scored"] == 0 and again["stats"]["unchanged"] == 6 and again["stats"]["feature_tracks"] == 0
    # one track's analysis changes: only its pairs are rescored (2 per other track)
    ap = next((cache / "analysis").glob(f"{IDS[2] * 4}"[:64] + "*.v5.json"))
    d = json.loads(ap.read_text())
    d["bpm"] = 151.0
    ap.write_text(json.dumps(d))
    os.utime(ap, (time.time() + 5, time.time() + 5))
    inc = _build(cache)
    assert inc["stats"]["scored"] == 4 and inc["stats"]["feature_tracks"] == 1
    # a rule file change invalidates everything
    monkeypatch.setattr(pa, "rules_hash", lambda: "different")
    full = _build(cache)
    assert full["stats"]["scored"] == 6
    # a schema bump is not read
    p = pa.atlas_path(cache) / pa.META
    doc = json.loads(p.read_text())
    doc["schema"] = 999
    p.write_text(json.dumps(doc))
    assert pa.load(cache) is None


def test_segmented_layout_round_trips_and_migrates(cache):
    doc = {k: v for k, v in _build(cache).items() if k not in ("seeded", "written")}
    root = pa.atlas_path(cache)
    assert pa.load(cache) == doc, "load() of the folder is the old single-file dict"
    assert sorted(p.stem for p in (root / "pairs").glob("*.json")) == sorted(IDS)
    a = IDS[0]
    assert pa.pairs_for(a, cache) == {k: v for k, v in doc["pairs"].items() if v["a"] == a}
    assert pa.track(a, cache) == doc["tracks"][a] and pa.track("../x", cache) is None and pa.pairs_for("..", cache) == {}
    part = pa.load_for([IDS[0], IDS[1]], cache)
    assert set(part["pairs"]) == {k for k, v in doc["pairs"].items() if v["a"] in IDS[:2]}
    assert part["tracks"][IDS[2]]["name"] == NAMES[2] and "bars" not in part["tracks"][IDS[2]]
    # an old checkout's single file, no folder: migrated once, old file kept renamed
    shutil.rmtree(root)
    (cache / "pair_atlas.json").write_text(json.dumps(doc, separators=(",", ":")))
    assert pa.load(cache) == doc
    assert (root / pa.META).is_file() and not (cache / "pair_atlas.json").exists()
    assert json.loads((cache / "pair_atlas.json.migrated").read_text()) == doc
    # the folder wins from now on: a stale single file written again by old code is ignored
    (cache / "pair_atlas.json").write_text(json.dumps(dict(doc, pairs={})))
    assert pa.load(cache) == doc and pa.migrate(root) is False


def test_incremental_build_writes_only_changed_shards(cache):
    first = _build(cache, only=IDS[:2])
    assert first["written"] == {"tracks": 2, "pairs": 2, "removed": 0}
    root = pa.atlas_path(cache)
    stamp = {p.name: p.stat().st_mtime_ns for p in root.rglob("*.json")}
    again = _build(cache, only=IDS[:2])
    assert again["written"] == {"tracks": 0, "pairs": 0, "removed": 0}, "0 rescored: no shard written"
    assert {p.name: p.stat().st_mtime_ns for p in root.rglob("*.json") if p.name != pa.META} == \
        {k: v for k, v in stamp.items() if k != pa.META}
    # one new song: its own track + pairs shard, plus A -> new appended to each old A's shard
    one = _build(cache)
    assert one["stats"]["scored"] == 4 and one["written"] == {"tracks": 1, "pairs": 3, "removed": 0}
    # a song leaves the library (only=): its shards go
    gone = _build(cache, only=IDS[:2])
    assert gone["written"]["removed"] == 2 and not (root / "tracks" / f"{IDS[2]}.json").exists()


def test_build_takes_the_lock_and_nests(cache):
    import threading
    from app.music_brain.set_import import _atlas_lock

    with _atlas_lock(cache):
        _build(cache, only=IDS[:2])                      # re-entrant: a caller already holding it
        t = threading.Thread(target=_build, args=(cache,), kwargs={"only": IDS[:2]})
        t.start()
        t.join(0.5)
        assert t.is_alive(), "another thread's build waits for the lock"
    t.join(60)
    assert not t.is_alive() and pa.load(cache)["stats"]["tracks"] == 2


def test_index_is_lazy_per_track(cache, monkeypatch):
    doc = _build(cache)
    full = pa.Index(pa.load(cache))
    reads = []
    real = pa.pairs_for
    monkeypatch.setattr(pa, "pairs_for", lambda a, *x, **k: reads.append(a) or real(a, *x, **k))
    pa._INDEX.clear()
    idx = pa.cached_index(cache)
    assert reads == [] and idx.names == full.names and idx.rules == doc["rules"]
    assert idx.partners(IDS[0]) == full.partners(IDS[0]) and reads == [IDS[0]]
    assert idx.pair(IDS[0], IDS[1]) == full.pair(IDS[0], IDS[1]) and reads == [IDS[0]]
    assert pa.cached_index(cache) is idx, "same meta.json: same Index"


def _atlas(tracks, pairs):
    return {"tracks": {t: {"name": n, "artist": pa.artist_of(n), "level": lv} for t, n, lv in tracks},
            "pairs": {f"{a}>{b}": {"a": a, "b": b, "works": w, "best": "Long Blend", "recipe": "Long Blend", "combo": None,
                                   "key": 1.0, "gap": 0.0, "lock": "pitched", "exit": 100.0, "entry": 0.0,
                                   "merge": {"ok": False}, "moves": {}, "energy": {}, "played": None} for a, b, w in pairs}}


def test_chain_search_respects_energy_arc_and_artist_spacing():
    T = [("t1", "Alpha - One", 5), ("t2", "Alpha - Two", 5), ("t3", "Beta - Three", 5), ("t4", "Gamma - Four", 9), ("t5", "Delta - Five", 5)]
    pairs = [("t1", "t2", 99), ("t1", "t3", 80), ("t3", "t2", 90), ("t3", "t4", 95), ("t3", "t5", 70), ("t5", "t2", 70), ("t2", "t5", 60)]
    doc = _atlas(T, pairs)
    for c in pa.chains(doc, length=4, k=3, min_works=0, spacing=3):
        arts = [doc["tracks"][t]["artist"] for t in c["tracks"]]
        for i in range(len(arts)):
            assert arts[i] not in arts[max(0, i - 3):i], c["tracks"]        # no artist within 3 songs
        assert "t4" not in c["tracks"][1:], "5 -> 9 breaks the energy arc (energy.next_ok)"
    # PLAN FROM PICKS keeps a locked order, else orders for flow
    assert pa.order_picks(doc, ["t2", "t1"], locked=True)["order"] == ["t2", "t1"]
    free = pa.order_picks(doc, ["t5", "t3", "t1"])
    assert free["order"][0] == "t1" and set(free["order"]) == {"t1", "t3", "t5"}


def test_history_mining_on_a_tmp_session(tmp_path):
    s = tmp_path / "sessions" / "2026-09-29_120000" / "songs"
    rows = [(1, IDS[0], "Seven Lions - Days To Come", None), (2, IDS[1], "Lane 8 - Stay Still", "Stem Merge"), (3, IDS[2], "Skrillex - Rise", "Long Blend")]
    for nn, tid, name, rin in rows:
        d = s / f"{nn:02d}-x"
        d.mkdir(parents=True)
        (d / "meta.json").write_text(json.dumps({"nn": nn, "track_id": tid, "name": name, "recipe_in": rin, "entry_t": 1000.0 * nn, "entry_song_s": 8.0}))
        steps = [{"t": 1000.0 * nn + 60, "kind": "transition_start", "phase": "planning", "decision": rin or "Long Blend"}]
        if nn == 3:
            steps.append({"t": 3005.0, "kind": "glitch", "phase": "transition-in", "decision": "silence"})
        if nn == 1:
            steps.append({"t": 1061.0, "kind": "recipe_executed", "phase": "transition-out", "decision": "Stem Merge"})
        (d / "steps.jsonl").write_text("\n".join(json.dumps(x) for x in steps))
    ev2 = tmp_path / "sessions" / "2026-09-28_100000"
    ev2.mkdir(parents=True)
    ev2.joinpath("events.jsonl").write_text("\n".join(json.dumps(x) for x in [
        {"kind": "track", "event": "transition_start", "from": NAMES[0], "to": NAMES[1], "recipe": "Stem Merge"},
        {"kind": "track", "event": "transition_end"}]))
    (tmp_path / "learned_techniques.json").write_text(json.dumps({"bass_swap": {"observations": [
        {"set_id": "s1", "at": 10.0, "track_a": NAMES[0], "track_b": NAMES[1]}]}}))
    ev = pa.mine_history(tmp_path, dict(zip(IDS, NAMES)))
    good = ev[f"{IDS[0]}>{IDS[1]}"]
    assert good["count"] == 2 and good["good"] == 2 and good["bad"] == 0
    assert good["executed"] == {"Stem Merge": 1} and good["learned"][0]["kind"] == "bass_swap"
    bad = ev[f"{IDS[1]}>{IDS[2]}"]
    assert bad["dead_air"] == 1 and bad["bad"] == 1
    assert pa.played_adjust(bad) < 0 < pa.played_adjust(good)
    # the session becomes a macro
    m = mc.from_session("2026-09-29_120000", tmp_path)
    assert m["tracks"] == IDS and [s["recipe"] for s in m["steps"]] == ["Stem Merge", "Long Blend"]
    assert m["steps"][0]["a_time"] == pytest.approx(68.0)


def test_macros_save_load_validate_versions(tmp_path):
    step = {"a": IDS[0], "b": IDS[1], "recipe": "Stem Merge", "a_time": 150.1, "b_time": 8.6, "merge": {"hold_bars": 16}}
    m = mc.save({"name": "Friday Night!", "steps": [step]}, tmp_path)
    assert m["name"] == "friday-night" and m["version"] == 1
    v2 = mc.save(dict(m, steps=[dict(step, recipe="Bass Swap")]), tmp_path)
    assert v2["name"] == "friday-night-v2" and v2["parent"] == "friday-night" and v2["version"] == 2
    with pytest.raises(ValueError):
        mc.save(m, tmp_path, new_version=False)
    assert mc.load("friday-night", tmp_path)["steps"][0]["recipe"] == "Stem Merge"
    assert {x["name"] for x in mc.list_macros(tmp_path)} == {"friday-night", "friday-night-v2"}
    with pytest.raises(ValueError):
        mc.normalize({"steps": [step, dict(step, a=IDS[2], b=IDS[0])]})       # not chained
    with pytest.raises(ValueError):
        mc.normalize({"steps": [dict(step, a="../../etc")]})
    val = mc.validate(m, known=lambda t: t != IDS[1], has_stems=lambda t: False)
    assert not val[0]["ok"] and any("not in the library" in i for i in val[0]["issues"]) and any("stems missing" in i for i in val[0]["issues"])
    assert mc.validate(m, known=lambda t: True, has_stems=lambda t: True)[0]["ok"]
    # seeds never overwrite the user's macro
    with pytest.raises(ValueError):
        mc.write_seed({"name": "friday-night", "source": "atlas:combo", "steps": [step]}, tmp_path)
    s1 = mc.write_seed({"name": "combo-x", "source": "atlas:combo", "steps": [step]}, tmp_path)
    s2 = mc.write_seed({"name": "combo-x", "source": "atlas:combo", "steps": [dict(step, recipe="Echo Out")]}, tmp_path)
    assert s1["name"] == s2["name"] and mc.load("combo-x", tmp_path)["steps"][0]["recipe"] == "Echo Out"


def test_seed_macros_and_plan_from_picks(cache, monkeypatch):
    seeds = cache / "seeds.json"
    seeds.write_text(json.dumps({"combos": [{"a": IDS[0], "b": IDS[1], "move": "merge"}, {"a": IDS[0], "b": IDS[2], "move": "merge"}]}))
    monkeypatch.setattr(pa, "SEED_FILE", seeds)
    monkeypatch.setattr(pa, "load_seeds", lambda path=seeds: json.loads(Path(path).read_text())["combos"])
    doc = _build(cache, seed_macros_to=cache)
    names = {m["name"]: m for m in doc["seeded"]}
    ok = next(m for n, m in names.items() if n.startswith("combo-seed-seven") and "lane" in n)
    assert "merge -> hold" in ok["note"] and ok["steps"][0]["merge"]["hold_bars"]
    refused = next(m for n, m in names.items() if n.startswith("combo-seed-seven") and "skrillex" in n)
    assert "refused" in refused["note"], refused["note"]
    assert any(n.startswith("combo-") and not n.startswith("combo-seed") for n in names)
    m = mc.from_picks([IDS[2], IDS[1], IDS[0]], doc, locked=True)
    assert m["tracks"] == [IDS[2], IDS[1], IDS[0]]
    assert mc.from_picks([IDS[1], IDS[0]], doc)["steps"][0]["recipe"]


def test_endpoints(cache, monkeypatch):
    from fastapi import FastAPI

    from app.tests.py.testclient_compat import TestClient
    from app.ui import atlas_api

    monkeypatch.setattr(atlas_api, "ATLAS_CACHE_DIR", cache)
    monkeypatch.setattr(pa, "load_seeds", lambda path=None: [{"a": IDS[2], "b": IDS[0], "move": "merge", "b_name": NAMES[0]}])
    app = FastAPI()
    app.include_router(atlas_api.router)
    c = TestClient(app)
    assert c.get("/api/atlas/status").json() == {"built": False}
    pre = c.get(f"/api/atlas/partners?a={IDS[2]}").json()
    assert pre["built"] is False and pre["partners"][0]["seed"] and pre["partners"][0]["combo"] == "merge"
    _build(cache)
    st = c.get("/api/atlas/status").json()
    assert st["built"] and st["stats"]["pairs"] == 6
    r = c.get(f"/api/atlas/partners?a={IDS[0]}&n=5").json()
    assert r["partners"][0]["b"] == IDS[1] and r["partners"][0]["plan"]["recipe"] == "Stem Merge"
    assert [x["b"] for x in c.get(f"/api/atlas/partners?a={IDS[0]}&move=merge").json()["partners"]] == [IDS[1]]
    assert c.get(f"/api/atlas/partners?a={IDS[0]}&combo=1").json()["partners"][0]["combo"] == "merge"
    assert c.get(f"/api/atlas/partners?a={IDS[0]}&move=nope").status_code == 400
    assert c.get(f"/api/atlas/pair?a={IDS[0]}&b={IDS[1]}").json()["pair"]["merge_ok"] is True
    step = {"a": IDS[0], "b": IDS[1], "recipe": "Stem Merge", "a_time": 150.0, "b_time": 8.0}
    saved = c.post("/api/macros", json={"macro": {"name": "fri", "steps": [step]}}).json()["macro"]
    assert saved["name"] == "fri"
    assert c.post("/api/macros", json={"macro": {"name": "bad", "steps": []}}).status_code == 400
    assert [m["name"] for m in c.get("/api/macros").json()["macros"]] == ["fri"]
    got = c.get("/api/macros/fri").json()
    assert got["macro"]["steps"][0]["recipe"] == "Stem Merge" and got["validation"][0]["n"] == 1
    assert c.get("/api/macros/nothing").status_code == 404
    picks = c.post("/api/macros/plan-from-picks", json={"ids": [IDS[0], IDS[1]], "name": "picks"}).json()["macro"]
    assert picks["tracks"][0] in IDS and picks["source"] == "picks"
    assert c.post("/api/macros/from-session/../../x").status_code in (400, 404)
