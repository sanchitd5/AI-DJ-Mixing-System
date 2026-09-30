"""GET /api/atlas/backup: A's served atlas partners (one shard read) with b_level / a_level for the
console's energy ranking (autopilot.js rankAtlasBackups) and earlier_set for songs heard in an
earlier set (hold-loop-preplan: a preplanned backup B so the deadline fallback never searches
from zero)."""
from app.music_brain import pair_atlas as pa
from app.tests.test_pair_atlas import IDS, NAMES, _build, cache  # noqa: F401  (pytest fixture)


def test_backup_endpoint_marks_earlier_sets_and_levels(cache, monkeypatch):  # noqa: F811
    from fastapi import FastAPI

    from app.tests.testclient_compat import TestClient
    from app.ui import atlas_api
    from app.ui import set_memory as sm

    monkeypatch.setattr(atlas_api, "ATLAS_CACHE_DIR", cache)
    monkeypatch.setattr(pa, "load_seeds", lambda path=None: [])
    app = FastAPI()
    app.include_router(atlas_api.router)
    c = TestClient(app)
    assert c.get(f"/api/atlas/backup?a={IDS[0]}").json() == {"a": IDS[0], "partners": [], "built": False}
    _build(cache)
    mem = sm.SetMemory(cache / "set_memory.json")
    mem.record([NAMES[1]], set_id="old-set")
    monkeypatch.setattr(atlas_api, "_earlier_set_keys",
                        lambda set_id: {sm._key(n) for n in mem.earlier_sets([], set_id=set_id)})
    r = c.get(f"/api/atlas/backup?a={IDS[0]}&set_id=now").json()
    assert r["built"] and {p["b"] for p in r["partners"]} == {IDS[1], IDS[2]}
    by = {p["b"]: p for p in r["partners"]}
    assert by[IDS[1]]["earlier_set"] is True and by[IDS[2]]["earlier_set"] is False
    assert all("b_level" in p for p in r["partners"]) and "a_level" in r


def test_earlier_set_keys_reads_the_set_memory(tmp_path, monkeypatch):
    from app.ui import atlas_api
    from app.ui import set_memory as sm

    monkeypatch.setattr(atlas_api, "ATLAS_CACHE_DIR", tmp_path)
    import app.ui.server as srv
    monkeypatch.setattr(srv, "_set_memory", sm.SetMemory(tmp_path / "set_memory.json"))
    srv._set_memory.record(["Shubh - Cheques"], set_id="earlier")
    assert sm._key("Shubh - Cheques") in atlas_api._earlier_set_keys("today")
    assert atlas_api._earlier_set_keys("earlier") == set()
