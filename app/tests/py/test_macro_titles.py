"""Macro titles: owner "macros should have proper names". The slug stays the id."""
import json

from app.music_brain.atlas import macros as mc

A, B, C = "a" * 16, "b" * 16, "c" * 16


def _m(name, steps, source="console", **kw):
    return dict(name=name, source=source, steps=steps, **kw)


def _st(a, b, an, bn, **kw):
    return dict(a=a, b=b, a_name=an, b_name=bn, **kw)


def test_song_label_strips_upload_noise():
    assert mc.song_label("Artbat - Horizon (Official Audio)") == "Artbat - Horizon"


def test_chain_title_first_last_artist_and_count():
    m = mc.normalize(_m("chain-1-x", [_st(A, B, "Jon Hopkins - Open Eye Signal", "YOTTO - Hyperfall"),
                                       _st(B, C, "YOTTO - Hyperfall", "Chemicals - Galvanize")],
                        source="atlas:chain"))
    assert m["name"] == "chain-1-x"
    assert m["title"] == "Jon Hopkins → Chemicals · 3 songs"
    assert mc.kind_of(m) == "chain"


def test_combo_title_names_the_move():
    m = mc.normalize(_m("combo-x", [_st(A, B, "Seven Lions - Days To Come", "Lane 8 - Stay Still", combo="merge")],
                        source="atlas:combo"))
    assert m["title"] == "Seven Lions - Days To Come → Lane 8 - Stay Still (Merge-Hold)"


def test_seed_title():
    m = mc.normalize(_m("combo-seed-x", [_st(A, B, "X - One", "Y - Two")], source="atlas:seed"))
    assert m["title"].startswith("Seed combo: X - One → Y - Two")


def test_studied_set_title_from_note():
    m = mc.normalize(_m("studied-set-orb", [_st(A, B, "A - 1", "B - 2"), _st(B, C, "B - 2", "C - 3")],
                        source="atlas:studied", note="studied set Anyma | Live from Atomium in set order: 3 of 3 songs"))
    assert m["title"] == "Anyma @ Live from Atomium (studied set, 3 songs)"
    assert mc.kind_of(m) == "studied"


def test_given_title_wins_and_user_kind():
    m = mc.normalize(_m("friday", [_st(A, B, "A - 1", "B - 2")], title="  My   Friday "))
    assert m["title"] == "My Friday"
    assert mc.kind_of(m) == "yours"


def test_backfill_writes_only_missing_titles(tmp_path):
    d = tmp_path / "macros"
    d.mkdir()
    old = mc.normalize(_m("old", [_st(A, B, "A - 1", "B - 2")]))
    del old["title"]
    (d / "old.json").write_text(json.dumps(old), encoding="utf-8")
    (d / "kept.json").write_text(json.dumps(mc.normalize(_m("kept", [_st(A, B, "A - 1", "B - 2")], title="Keep"))),
                                 encoding="utf-8")
    assert mc.backfill_titles(tmp_path) == ["old"]
    assert mc.stored(tmp_path)["old"]["title"] == "A - 1 → B - 2"
    assert mc.stored(tmp_path)["old"]["name"] == "old"
    assert mc.main(["titles", "--cache-dir", str(tmp_path)]) == 0  # the CLI command
    rows = {r["name"]: r for r in mc.list_macros(tmp_path)}
    assert rows["kept"]["title"] == "Keep" and rows["old"]["kind"] == "yours"
