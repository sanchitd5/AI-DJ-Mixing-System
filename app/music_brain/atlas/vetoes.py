"""OWNER VETO: pairs (or a song in a context) the owner marked as a vibe killer. Never booked again.

    CACHE_DIR/user.db, marks of kind "veto" (app.music_brain.user_marks)   (console "bad pair")
    app/music_brain/atlas/vetoes_seed.json                                 (tracked seed, always loaded)

USER-side data (private, never written into the knowledge/ export). Everything goes through this one
module (load / add / check). The pre-DB CACHE_DIR/vetoes.json migrates once, kept as .migrated.

entry: {"kind": "pair", "a": "<A name>", "b": "<B name>", "a_key", "b_key", "at", "source", "note"}
       {"kind": "song", "b": "<name>", "b_key", "scene": "<scene term>" | "", ...}
         a song veto holds after any song whose genre shares `scene` (genre.genre_scenes), or always when "".

Keys are the clean "artist title" identity (track_identity.clean_identity, then pair_atlas-style
normalisation), so a re-download or an "(Official Audio)" upload is the same song.

Who reads it: the server's booking vet (every candidate the console tries: picks, FOLLOW SET, macro
steps, studied / atlas combos, the atlas backup, deadline and library fallbacks), the atlas rows it
serves (vetoed rows are marked), and pair_atlas.mine_history, which turns each vetoed pair into
PLAYED_BAD evidence at build so the learning uses it.

CLI (the seeding path besides the tracked seed file):
    python3 -m app.music_brain.atlas.vetoes list
    python3 -m app.music_brain.atlas.vetoes add "Artist - A" "Artist - B" [--note ...]
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, List, Optional

FILE = "vetoes.json"                 # the pre-DB file (migration source); its folder holds user.db
MARK = "veto"
VERSION = 1
SEED = Path(__file__).resolve().parent / "vetoes_seed.json"   # tracked seed; never the knowledge/ export
MAX_VETOES = 2000
MAX_FIELD = 200
KINDS = ("pair", "song")


def path(cache_dir: Optional[Path] = None) -> Path:
    from app.music_brain.config import CACHE_DIR

    return Path(cache_dir or CACHE_DIR) / FILE


def _norm(s: str) -> str:
    return " ".join("".join(c if c.isalnum() else " " for c in (s or "").lower()).split())


def song_key(name: str) -> str:
    """ "Santigold - You'll Find a Way (Official Audio)" -> "santigold you ll find a way"."""
    from app.ui.services.track_identity import clean_identity

    name = str(name or "").strip()
    if not name:
        return ""
    artist, title = clean_identity(name)
    artist = "" if artist == "Unknown" else artist
    return _norm(f"{artist} {title}")


def _clean(v) -> str:
    return str(v or "").strip()[:MAX_FIELD]


def make(kind: str, b: str, a: str = "", scene: str = "", source: str = "console", note: str = "") -> dict:
    """A validated entry. ValueError when it cannot be a veto."""
    kind = str(kind or "pair").strip().lower()
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    a, b = _clean(a), _clean(b)
    bk = song_key(b)
    if not bk:
        raise ValueError("the vetoed song (b) needs a name")
    e = {"kind": kind, "b": b, "b_key": bk, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "source": _clean(source) or "console", "note": _clean(note)}
    if kind == "pair":
        ak = song_key(a)
        if not ak:
            raise ValueError("a pair veto needs the song before it (a)")
        if ak == bk:
            raise ValueError("a pair needs two different songs")
        e.update(a=a, a_key=ak)
    else:
        e["scene"] = _clean(scene).lower()
    return e


def _ident(e: dict) -> tuple:
    return (e.get("kind"), e.get("a_key", ""), e.get("b_key", ""), e.get("scene", ""))


def _parse(p: Path) -> Optional[List[dict]]:
    """Rows of a vetoes JSON file (the tracked seed, or the pre-DB cache file); None: unreadable."""
    try:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    rows = d.get("vetoes") if isinstance(d, dict) else None
    out = []
    for r in rows or []:
        if not isinstance(r, dict) or r.get("kind") not in KINDS:
            continue
        try:   # re-keyed on read: a hand-edited or seed row only needs names
            e = make(r["kind"], r.get("b", ""), r.get("a", ""), r.get("scene", ""), r.get("source") or "file", r.get("note", ""))
        except (ValueError, KeyError):
            continue
        if r.get("at"):
            e["at"] = _clean(r["at"])
        out.append(e)
    return out


def _read(p: Path) -> List[dict]:
    return _parse(p) or []


def _subject(e: dict) -> str:
    return "|".join(str(x) for x in _ident(e))


def _stored(cache_dir: Optional[Path] = None) -> List[dict]:
    """The owner's vetoes in the user DB beside path(cache_dir); the old vetoes.json there
    migrates once (kept as vetoes.json.migrated). [] when the DB cannot be read."""
    import sqlite3

    from app.music_brain import user_marks as um

    p = path(cache_dir)
    try:
        um.migrate_json(MARK, p, lambda f: None if (rows := _parse(f)) is None else
                        [(_subject(e), e) for e in rows[-MAX_VETOES:]])
        return [e for _, e in um.rows(MARK, p.parent)]
    except (sqlite3.Error, OSError):
        return []


def load(cache_dir: Optional[Path] = None, seed: Optional[Path] = SEED) -> List[dict]:
    """Seed + the owner's stored vetoes, one row per (kind, a, b, scene); the stored row wins."""
    seen, out = {}, []
    for e in (_read(seed) if seed else []) + _stored(cache_dir):
        k = _ident(e)
        if k in seen:
            out[seen[k]] = e
        else:
            seen[k] = len(out)
            out.append(e)
    return out


def stamp(cache_dir: Optional[Path] = None) -> tuple:
    """Changes whenever a veto is stored (the server's memo key)."""
    from app.music_brain import user_marks as um

    p = path(cache_dir)
    _stored(cache_dir)
    return (str(p), um.stamp(MARK, p.parent))


def add(entry: dict, cache_dir: Optional[Path] = None) -> bool:
    """Store one veto (one transaction; the newest MAX_VETOES are kept). False when it was
    already there."""
    from app.music_brain import user_marks as um

    p = path(cache_dir)
    _stored(cache_dir)                                 # migrate an old vetoes.json first
    return um.add_new(MARK, _subject(entry), entry, p.parent, keep=MAX_VETOES)


def blocked(vetoes: Iterable[dict], a_name: str, b_name: str, a_genre: Optional[str] = None) -> Optional[str]:
    """The veto that forbids A -> B, as a reason string, else None."""
    from app.music_brain.analysis.genre import genre_scenes

    ak, bk = song_key(a_name), song_key(b_name)
    if not bk:
        return None
    scenes = None
    for e in vetoes or []:
        if e.get("b_key") != bk:
            continue
        if e.get("kind") == "pair" and ak and e.get("a_key") == ak:
            return f"owner veto: {e.get('a')} -> {e.get('b')} is a vibe killer"
        if e.get("kind") == "song":
            sc = e.get("scene") or ""
            if scenes is None:
                scenes = genre_scenes(a_genre)
            if not sc or sc in scenes:
                return f"owner veto: {e.get('b')}{f' after {sc}' if sc else ''} is a vibe killer"
    return None


check = blocked   # the store's read API: load / add / check


def bad_pairs(vetoes: Iterable[dict]) -> List[tuple]:
    """(A name, B name) of every pair veto: pair_atlas.mine_history's PLAYED_BAD evidence."""
    return [(e["a"], e["b"]) for e in vetoes or [] if e.get("kind") == "pair" and e.get("a") and e.get("b")]


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="python3 -m app.music_brain.atlas.vetoes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    ad = sub.add_parser("add")
    ad.add_argument("a", help="the song before (Artist - Title)")
    ad.add_argument("b", help="the vetoed next song (Artist - Title)")
    ad.add_argument("--note", default="")
    args = ap.parse_args(argv)
    if args.cmd == "list":
        for e in load():
            print(json.dumps(e, ensure_ascii=False))
        return 0
    try:
        e = make("pair", args.b, args.a, source="cli", note=args.note)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps({"added": add(e), "veto": e}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
