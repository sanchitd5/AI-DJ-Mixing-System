"""Compat shim, remove after 1.1: this module moved to app.music_brain.atlas.studied_combos."""

if __name__ == "__main__":
    import runpy

    runpy.run_module("app.music_brain.atlas.studied_combos", run_name="__main__", alter_sys=True)
else:
    from app.music_brain.atlas.studied_combos import *  # noqa: F401,F403
    from app.music_brain.atlas.studied_combos import (  # noqa: F401
        _SPLIT, _fold, _read, _heard, _ID_ONLY, _step,
    )
