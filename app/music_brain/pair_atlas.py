"""Compat shim, remove after 1.1: this module moved to app.music_brain.atlas.pair_atlas."""

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.music_brain.atlas.pair_atlas", run_name="__main__", alter_sys=True)
else:
    from app.music_brain.atlas.pair_atlas import *  # noqa: F401,F403
    from app.music_brain.atlas.pair_atlas import (  # noqa: F401
        _META_ONLY, _ID_RE, _stat_sig, _bar_rms, _W, _init_worker, _ta, _play_window, _score_a,
        _finish, _norm, _NameIndex, _read_jsonl, _root, _safe_id, _read_json, _dumps,
        _write_if_changed, _legacy, _meta, _load_file, _build, _short, _move_score, _studied_brief,
        _arc_ok, _INDEX, _fmt, _studied_cli, _import_set_cli,
    )
