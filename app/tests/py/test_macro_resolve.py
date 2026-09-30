"""Macro steps resolve to LIBRARY track ids (the dedup alias map), so the console plays
the library copy of each song, never a removed duplicate or a set clip. tmp cache only."""
import json

from app.music_brain import macros as mc

LIB_A, LIB_B, DUP_B, C = "1111111111111111", "2222222222222222", "3333333333333333", "4444444444444444"


def _macro():
    return {"name": "studied-set-x", "steps": [
        {"a": LIB_A, "b": DUP_B, "recipe": "Stem Merge", "a_time": 61.0, "b_time": 45.2, "merge": {"hold_bars": 14}},
        {"a": DUP_B, "b": C, "recipe": "Echo Out", "a_time": 241.3, "b_time": 18.0}]}


def test_resolve_ids_maps_duplicates_to_the_library_copy():
    m = mc.normalize(_macro())
    r = mc.resolve_ids(m, lambda t: {DUP_B: LIB_B}.get(t, t))
    assert [(s["a"], s["b"]) for s in r["steps"]] == [(LIB_A, LIB_B), (LIB_B, C)]
    assert r["steps"][0]["resolved"] == {"b": DUP_B} and "resolved" not in m["steps"][0]
    assert r["tracks"] == [LIB_A, LIB_B, C]
    # the stored move is untouched: recipe and points
    assert (r["steps"][0]["recipe"], r["steps"][0]["a_time"], r["steps"][0]["b_time"]) == ("Stem Merge", 61.0, 45.2)


def test_get_macro_endpoint_resolves_through_the_alias_file(tmp_path, monkeypatch):
    from fastapi import FastAPI

    from app.tests.py.testclient_compat import TestClient
    from app.ui.services import atlas_api

    (tmp_path / "track_aliases.json").write_text(json.dumps({DUP_B: LIB_B}))
    mc.save(_macro(), tmp_path)
    monkeypatch.setattr(atlas_api, "ATLAS_CACHE_DIR", tmp_path)
    app = FastAPI()
    app.include_router(atlas_api.router)
    got = TestClient(app).get("/api/macros/studied-set-x").json()["macro"]
    assert [(s["a"], s["b"]) for s in got["steps"]] == [(LIB_A, LIB_B), (LIB_B, C)]
    # on disk the macro keeps what it was saved with
    assert mc.load("studied-set-x", tmp_path)["steps"][0]["b"] == DUP_B
