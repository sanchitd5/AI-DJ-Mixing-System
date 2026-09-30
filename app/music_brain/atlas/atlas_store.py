"""Pair atlas STORAGE: the SQLite tables (CACHE_DIR/app.db) behind pair_atlas's load / pairs_for /
track / load_for / load_meta / write_atlas / migrate. Kept apart from pair_atlas.py on purpose:
pair_atlas.py is one of the atlas RULE_FILES (rules_hash), so a storage-only change here never
invalidates the scored pairs.

Tables: atlas_meta (the atlas dict's own keys as JSON, plus _rev bumped by every write that
changes something; cached_index keys on it), atlas_tracks (id, sig, name, artist, bpm, camelot,
duration, level, light = the track_index fields, features = the full entry JSON), atlas_pairs
(a, b, works, recipe, best, moves_ok bitmask over MOVES, merge_ok, combo, studied, played, seed,
data = the full pair JSON) with indexes on (a, works DESC), combo and studied.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Sequence


class _Rules:
    """pair_atlas's constants / move_of, looked up at call time (pair_atlas imports this module
    part way through its own import, and may itself run as __main__)."""

    def __getattr__(self, name):
        from app.music_brain.atlas import pair_atlas

        return getattr(pair_atlas, name)


_pa = _Rules()


def atlas_path(cache_dir: Path) -> Path:
    """The atlas path, CACHE_DIR/pair_atlas: its parent holds the DB; the path itself is the
    old segmented folder (migration source only)."""
    return Path(cache_dir) / _pa.ATLAS_NAME


def _root(cache_dir: Optional[Path], path: Optional[Path]) -> Path:
    from app.music_brain.config import CACHE_DIR

    return Path(path) if path else atlas_path(Path(cache_dir) if cache_dir else CACHE_DIR)


def _safe_id(tid: str) -> bool:
    return isinstance(tid, str) and bool(_pa._ID_RE.fullmatch(tid))


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _dumps(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _write_if_changed(p: Path, data: bytes) -> bool:
    """Atomic per-process tmp + replace; False (nothing written) when the file already holds these bytes."""
    try:
        if p.read_bytes() == data:
            return False
    except OSError:
        pass
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f"{p.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_bytes(data)
    tmp.replace(p)
    return True


def _legacy(root: Path) -> Path:
    return root.with_name(root.name + ".json")          # pair_atlas/ -> the old single file pair_atlas.json


def _meta(root: Path) -> Optional[dict]:
    """meta.json of an old segmented folder (the migration source)."""
    d = _read_json(root / _pa.META)
    return d if isinstance(d, dict) and d.get("schema") == _pa.SCHEMA else None


def _load_file(p: Path) -> Optional[dict]:
    d = _read_json(p)
    return d if isinstance(d, dict) and d.get("schema") == _pa.SCHEMA else None


def _load_folder(root: Path) -> Optional[dict]:
    """The whole atlas from an old segmented folder (meta.json, tracks/, pairs/)."""
    meta = _meta(root)
    if meta is None:
        return None
    doc = {k: v for k, v in meta.items() if k not in _pa._META_ONLY}
    doc["tracks"] = {}
    for t in meta.get("track_index") or {}:
        f = _read_json(root / "tracks" / f"{t}.json") if _safe_id(t) else None
        if isinstance(f, dict):
            doc["tracks"][t] = f
    doc["pairs"] = {}
    for a in meta.get("shards") or []:
        d = _read_json(root / "pairs" / f"{a}.json") if _safe_id(a) else None
        if isinstance(d, dict):
            doc["pairs"].update(d)
    return doc


# ------------------------------------------------------------------ the SQLite store
# Tables in CACHE_DIR/app.db (app.music_brain.db): the atlas of folder R lives in
# R.parent / app.db, so a cache dir holds one atlas. atlas_meta: the atlas dict's own keys
# (schema, rules, built_at, cache_dir, stats, ...) as JSON, plus _rev (bumped by every write that
# changes something; cached_index keys on it). Each row's `features` / `data` is the exact JSON
# the old shard held; the other columns are copies for indexed queries.
_REV = "_rev"
ATLAS_STEPS = (
    """CREATE TABLE atlas_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE atlas_tracks (id TEXT PRIMARY KEY, sig TEXT, name TEXT, artist TEXT, bpm REAL,
        camelot TEXT, duration REAL, level INTEGER, light TEXT NOT NULL, features TEXT NOT NULL);
    CREATE TABLE atlas_pairs (a TEXT NOT NULL, b TEXT NOT NULL, works REAL, recipe TEXT, best TEXT,
        moves_ok INTEGER NOT NULL DEFAULT 0, merge_ok INTEGER NOT NULL DEFAULT 0, combo TEXT,
        studied INTEGER NOT NULL DEFAULT 0, played INTEGER NOT NULL DEFAULT 0,
        seed INTEGER NOT NULL DEFAULT 0, data TEXT NOT NULL, PRIMARY KEY (a, b));
    CREATE INDEX atlas_pairs_works ON atlas_pairs (a, works DESC);
    CREATE INDEX atlas_pairs_combo ON atlas_pairs (works DESC) WHERE combo IS NOT NULL;
    CREATE INDEX atlas_pairs_studied ON atlas_pairs (works DESC) WHERE studied = 1""",
)
_PAIR_COLS = ("a", "b", "works", "recipe", "best", "moves_ok", "merge_ok", "combo", "studied",
              "played", "seed", "data")
_TRACK_COLS = ("id", "sig", "name", "artist", "bpm", "camelot", "duration", "level", "light",
               "features")


def _db(root: Path):
    """The connection to the database the atlas of folder `root` lives in (schema ensured)."""
    from app.music_brain import db

    conn = db.connect(Path(root).parent / db.APP_DB)
    db.ensure(conn, "pair_atlas", ATLAS_STEPS)
    return conn


def _scalar(v):
    return v if v is None or isinstance(v, (str, int, float)) else json.dumps(v, sort_keys=True)


def _track_row(t: str, f: dict, features: str) -> tuple:
    light = json.dumps({k: f[k] for k in _pa.LIGHT_FIELDS if k in f}, sort_keys=True)
    return (t, _scalar(f.get("sig")), _scalar(f.get("name")), _scalar(f.get("artist")),
            _scalar(f.get("bpm")), _scalar(f.get("key")), _scalar(f.get("duration")),
            _scalar(f.get("level")), light, features)


def _pair_row(p: dict, data: str) -> tuple:
    moves_ok = sum(1 << i for i, m in enumerate(_pa.MOVES) if _pa.move_of(p, m).get("ok"))
    merge = p.get("merge") if isinstance(p.get("merge"), dict) else {}
    combo = p.get("combo")
    return (p["a"], p["b"], _scalar(p.get("works")), _scalar(p.get("recipe")), _scalar(p.get("best")),
            moves_ok, int(bool(merge.get("ok"))), _scalar(combo) if combo else None,
            int(bool(p.get("studied"))), int(bool(p.get("played"))), int(bool(p.get("seed"))), data)


def _has_atlas(conn) -> bool:
    return conn.execute("SELECT 1 FROM atlas_meta WHERE key = 'schema'").fetchone() is not None


def _db_meta(conn) -> Optional[dict]:
    d = {k: json.loads(v) for k, v in conn.execute("SELECT key, value FROM atlas_meta WHERE key != ?", (_REV,))}
    return d if d.get("schema") == _pa.SCHEMA else None


def migrate(root: Path, log=lambda m: None) -> bool:
    """First open with no atlas in the database: import the old segmented folder (or, before
    that, the single pair_atlas.json) once, then rename it <name>.migrated (kept, never deleted;
    older checkouts then see "no atlas" and rebuild their own). True when it migrated."""
    root = Path(root)
    if root.is_file():
        return False
    folder, single = (root / _pa.META).is_file(), _legacy(root).is_file()
    if not (folder or single) or _has_atlas(_db(root)):
        return False
    from app.music_brain import db
    from app.music_brain.learning.set_import import _atlas_lock

    with _atlas_lock(root.parent):
        conn = _db(root)
        if _has_atlas(conn):                                 # another process migrated first
            return False
        src = root if folder else _legacy(root)
        old = _load_folder(root) if folder else _load_file(src)
        if old is None:
            return False                                     # unreadable / other schema: left alone
        t0 = time.time()
        write_atlas(old, root)
        db.checkpoint(conn)                                  # the one big write: WAL back to 0 bytes
        dest = db.retire(src)
        log(f"atlas migrated: {src.name} -> {db.APP_DB} in {time.time() - t0:.1f} s "
            f"(old copy kept as {dest.name})")
    return True


def load(cache_dir: Optional[Path] = None, path: Optional[Path] = None) -> Optional[dict]:
    """The whole atlas as ONE dict (schema, rules, built_at, cache_dir, stats, tracks, pairs), the
    same shape the old single file had. Reads every row: request paths use pairs_for / track /
    load_for / cached_index."""
    root = _root(cache_dir, path)
    if root.is_file():
        return _load_file(root)                          # an explicit old-style single file
    migrate(root)
    from app.music_brain import db

    conn = _db(root)
    with db.read(conn):
        doc = _db_meta(conn)
        if doc is None:
            return None
        doc["tracks"] = _objects(conn.execute("SELECT id, features FROM atlas_tracks ORDER BY id"))
        doc["pairs"] = _objects(conn.execute("SELECT a || '>' || b, data FROM atlas_pairs ORDER BY a, b"))
    return doc


def _objects(rows) -> Dict[str, dict]:
    """{key: json} rows -> dict with ONE json.loads over the joined text (~30 % faster than one
    per row on 306k pairs). Keys are _safe_id-checked ids, so they need no escaping."""
    return json.loads("{" + ",".join(f'"{k}":{v}' for k, v in rows) + "}")


def load_meta(cache_dir: Optional[Path] = None, path: Optional[Path] = None) -> Optional[dict]:
    """The atlas keys without tracks / pairs: rules, built_at, stats, track_index {id: name,
    artist, bpm, key, ...} and shards (the ids that have A -> * pairs)."""
    root = _root(cache_dir, path)
    if root.is_file():
        return None
    migrate(root)
    from app.music_brain import db

    conn = _db(root)
    with db.read(conn):
        meta = _db_meta(conn)
        if meta is None:
            return None
        meta["track_index"] = {t: json.loads(v) for t, v in
                               conn.execute("SELECT id, light FROM atlas_tracks ORDER BY id")}
        meta["shards"] = [a for (a,) in conn.execute("SELECT DISTINCT a FROM atlas_pairs ORDER BY a")]
    return meta


def pairs_for(a: str, cache_dir: Optional[Path] = None, path: Optional[Path] = None) -> Dict[str, dict]:
    """Every A -> * pair of one track ({"a>b": pair}); {} when unknown."""
    root = _root(cache_dir, path)
    if not _safe_id(a) or root.is_file():
        return {}
    migrate(root)
    rows = _db(root).execute("SELECT b, data FROM atlas_pairs WHERE a = ? ORDER BY b", (a,))
    return {f"{a}>{b}": json.loads(d) for b, d in rows}


def track(tid: str, cache_dir: Optional[Path] = None, path: Optional[Path] = None) -> Optional[dict]:
    """One track's full per-track entry (features included); None when unknown."""
    root = _root(cache_dir, path)
    if not _safe_id(tid) or root.is_file():
        return None
    migrate(root)
    row = _db(root).execute("SELECT features FROM atlas_tracks WHERE id = ?", (tid,)).fetchone()
    return json.loads(row[0]) if row else None


def load_for(ids: Sequence[str], cache_dir: Optional[Path] = None, path: Optional[Path] = None) -> Optional[dict]:
    """A partial atlas for a set of picks: meta fields, the light track_index as tracks (name,
    artist, bpm, key, duration, level, stems) and only the A -> * pairs of `ids`. Enough for
    order_picks / macros.from_picks without reading every row."""
    root = _root(cache_dir, path)
    if root.is_file():
        return _load_file(root)
    meta = load_meta(path=root)
    if meta is None:
        return None
    doc = {k: v for k, v in meta.items() if k not in _pa._META_ONLY}
    doc["tracks"] = dict(meta.get("track_index") or {})
    doc["pairs"] = {}
    for a in dict.fromkeys(ids):
        doc["pairs"].update(pairs_for(a, path=root))
    return doc


def write_atlas(doc: dict, root: Path) -> dict:
    """Write an atlas dict into the database of folder `root` in ONE transaction: only rows whose
    JSON changed are upserted, rows no longer in `doc` are deleted, the meta keys replaced (so a
    no-change build writes no row). Callers hold _atlas_lock for a build. Returns row counts."""
    from app.music_brain import db

    root = Path(root)
    tracks, pairs = doc.get("tracks") or {}, doc.get("pairs") or {}
    by_a: Dict[str, Dict[str, dict]] = {}
    for p in pairs.values():
        by_a.setdefault(p["a"], {})[p["b"]] = p
    bad = [t for t in list(tracks) + list(by_a) if not _safe_id(t)]
    if bad:
        raise ValueError(f"atlas track id not usable: {bad[0]!r}")
    rep = {"tracks": 0, "pairs": 0, "removed": 0}
    conn = _db(root)
    put_t = f"INSERT OR REPLACE INTO atlas_tracks ({', '.join(_TRACK_COLS)}) VALUES ({', '.join('?' * len(_TRACK_COLS))})"
    put_p = f"INSERT OR REPLACE INTO atlas_pairs ({', '.join(_PAIR_COLS)}) VALUES ({', '.join('?' * len(_PAIR_COLS))})"
    # serialise before taking the write lock (seconds of CPU on a full library): the transaction
    # itself only compares strings and writes the rows that differ
    enc = json.JSONEncoder(sort_keys=True, separators=(",", ":")).encode     # = _dumps, one encoder
    new_t = {t: enc(f) for t, f in tracks.items()}
    new_p = {(a, b): enc(p) for a, ps in by_a.items() for b, p in ps.items()}
    with db.tx(conn):
        old = dict(conn.execute("SELECT id, features FROM atlas_tracks"))
        for t, s in new_t.items():
            if old.pop(t, None) != s:
                conn.execute(put_t, _track_row(t, tracks[t], s))
                rep["tracks"] += 1
        for t in old:
            conn.execute("DELETE FROM atlas_tracks WHERE id = ?", (t,))
            rep["removed"] += 1
        old = {(a, b): d for a, b, d in conn.execute("SELECT a, b, data FROM atlas_pairs")}
        for k, s in new_p.items():
            if old.pop(k, None) != s:
                conn.execute(put_p, _pair_row(by_a[k[0]][k[1]], s))
                rep["pairs"] += 1
        for a, b in old:
            conn.execute("DELETE FROM atlas_pairs WHERE a = ? AND b = ?", (a, b))
            rep["removed"] += 1
        meta = {k: json.dumps(v, sort_keys=True) for k, v in doc.items()
                if k not in ("tracks", "pairs", "seeded", "written") + _pa._META_ONLY}
        oldm = dict(conn.execute("SELECT key, value FROM atlas_meta WHERE key != ?", (_REV,)))
        changed = any(rep.values())
        for k, v in meta.items():
            if oldm.pop(k, None) != v:
                conn.execute("INSERT OR REPLACE INTO atlas_meta (key, value) VALUES (?, ?)", (k, v))
                changed = True
        for k in oldm:
            conn.execute("DELETE FROM atlas_meta WHERE key = ?", (k,))
            changed = True
        if changed:
            conn.execute("INSERT INTO atlas_meta (key, value) VALUES (?, '1') ON CONFLICT(key) "
                         "DO UPDATE SET value = CAST(value AS INTEGER) + 1", (_REV,))
    return rep
