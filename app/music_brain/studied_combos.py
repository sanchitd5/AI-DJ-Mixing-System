"""STUDIED COMBOS: the transitions real DJs played in the famous sets the set learner studied.

Owner: "known combos are one from the famous sets already studied". Every consecutive
(A -> B) of a studied set's tracklist (data/cache/sets/<set_id>/study.json) plus every
set_learner observation naming two songs is a studied transition: set, DJ, position, the
techniques the learner heard (bass_swap, stem_intro, acapella_over, loop_extend, ...), the
overlap both songs were heard for, tempo gap and key score. Entries on a "probably the wrong
download" song are skipped, and AI-rejected observations never count as a technique.

Both songs resolve to LIBRARY ids by name (dedup_songs.identity: same artist + title + remix
markers, or the same title when one side names no artist) and the dedup alias map. A resolved
pair becomes a separate evidence class `studied` on its atlas pair (pair_atlas.build) and a
combo the console tries FIRST (macro-mode.js comboCandidates), still behind an armed macro
step and still through every live gate. A studied technique maps to the console move it
would use; a hard cut sighting is never played as a cut: the pair gets the atlas's own plan.

Offline, no network: reads the study files and the upload names only.
"""
from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from app.music_brain.recipe_matcher import is_cut_recipe
from app.music_brain.techniques import LEARNED_RECIPE, NEVER_PLAY

# learner technique -> the atlas move column that judges it offline. The recipe is the console's
# own (techniques.LEARNED_RECIPE, the table the live learned pick uses); a loop extension is the
# console's merge -> hold (A's loop held under B). Every other kind (vocal re-cuts, chops, vocal
# loops) has no console move: studied only, the pair plays the atlas's own plan.
TECHNIQUE_MOVE: Dict[str, Tuple[str, str]] = {
    "bass_swap": ("bass_swap", LEARNED_RECIPE["learned:bass_swap"]),
    "stem_intro": ("stem_intro", LEARNED_RECIPE["learned:stem_intro"]),
    "acapella_over": ("mashup", LEARNED_RECIPE["learned:acapella_over"]),
    "acapella_drop": ("mashup", LEARNED_RECIPE["learned:acapella_over"]),
    "loop_extend": ("merge", "Stem Merge"),
}
STUDIED_ONLY = {k.split(":", 1)[1] for k in NEVER_PLAY}   # hard_cut: seen in the set, never played as a cut
MACRO_SOURCE = "atlas:studied"

_SPLIT = re.compile(r"\s+[-–—]\s+")


def _fold(s: str) -> str:
    return " ".join("".join(c if c.isalnum() else " " for c in (s or "").lower()).split())


def _read(p: Path, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------------------------------------- set metadata

def set_meta(cache_dir: Path, set_id: str, notes_dir: Optional[Path] = None) -> dict:
    """{title, dj}: the yt-dlp info.json title, else the research note heading, else the id.
    The DJ is the title's first segment ("Anyma | Live from Atomium" -> "Anyma")."""
    title = (_read(Path(cache_dir) / "sets" / f"{set_id}.info.json", {}) or {}).get("title")
    if not title and notes_dir is not None:
        try:
            head = (Path(notes_dir) / f"set-study-{set_id}.md").read_text(encoding="utf-8").splitlines()[0]
            title = re.sub(r"^#\s*(set study:\s*)?", "", head, flags=re.I).strip() or None
        except (OSError, IndexError):
            title = None
    title = title or set_id
    dj = re.split(r"\s+[|｜]\s+|\s+[-–—]\s+|\s+\(", title, maxsplit=1)[0].strip() or set_id
    return {"title": title, "dj": dj}


# ---------------------------------------------------------------------------------------------- extraction

def _heard(timeline: List[dict]) -> Tuple[Dict[int, set], float]:
    """{tracklist index: {window t heard in any stem}}, window hop (s)."""
    heard: Dict[int, set] = {}
    for r in timeline or []:
        for h in r.get("owners") or []:
            if isinstance(h, dict) and isinstance(h.get("track"), int):
                heard.setdefault(h["track"], set()).add(r.get("t"))
    ts = sorted({r.get("t") for r in timeline or [] if isinstance(r.get("t"), (int, float))})
    hop = statistics.median([b - a for a, b in zip(ts, ts[1:])]) if len(ts) > 1 else 0.0
    return heard, float(hop)


def extract_set(study: dict, set_id: str, meta: Optional[dict] = None, learned_obs: Iterable[dict] = ()) -> List[dict]:
    """Every studied transition of one set, in set order (skipped ones carry `skip`)."""
    meta = meta or {"title": set_id, "dj": set_id}
    tracks = [t for t in study.get("tracks") or [] if isinstance(t, dict) and t.get("title")]
    heard, hop = _heard(study.get("timeline"))
    kept = [o for o in study.get("observations") or [] if isinstance(o, dict)]
    seen = {(o.get("kind"), o.get("at"), o.get("track_a"), o.get("track_b")) for o in kept}
    for o in learned_obs:            # learned_techniques.json sightings of this set not in the study file
        if isinstance(o, dict) and o.get("set_id") == set_id and (o.get("kind"), o.get("at"), o.get("track_a"), o.get("track_b")) not in seen:
            kept.append(o)
    rejected = [o for o in study.get("ai_rejected") or [] if isinstance(o, dict)]

    def by_pair(obs):
        d: Dict[Tuple[str, str], List[dict]] = {}
        for o in obs:
            a, b = _fold(o.get("track_a")), _fold(o.get("track_b"))
            if a and b and a != b:
                d.setdefault((a, b), []).append(o)
        return d

    ok_obs, bad_obs = by_pair(kept), by_pair(rejected)
    first_idx = {}
    for i, t in enumerate(tracks):
        first_idx.setdefault(_fold(t["title"]), i)

    def rec(i: Optional[int], j: Optional[int], a_title: str, b_title: str, layered: bool) -> dict:
        A = tracks[i] if i is not None else {}
        B = tracks[j] if j is not None else {}
        key = (_fold(a_title), _fold(b_title))
        obs = sorted(ok_obs.get(key, []), key=lambda o: o.get("at") or 0)
        wrong = [x["title"] for x in (A, B) if x.get("likely_wrong_song")]
        first = next((o for o in obs if o.get("tempo_gap") is not None or o.get("key_score") is not None), {})
        overlap = len(heard.get(i, set()) & heard.get(j, set())) * hop if i is not None and j is not None else None
        return {"set_id": set_id, "set_title": meta["title"], "dj": meta["dj"],
                "position": (j if j is not None else i or 0) + 1, "a_title": a_title, "b_title": b_title,
                "at": obs[0].get("at") if obs else B.get("start"),
                "techniques": sorted(Counter(o.get("kind") for o in obs if o.get("kind")).items(), key=lambda x: (-x[1], x[0])),
                "rejected": sorted({o.get("kind") for o in bad_obs.get(key, []) if o.get("kind")}),
                "overlap_s": round(overlap, 1) if overlap is not None else None,
                "tempo_gap": first.get("tempo_gap"), "key_score": first.get("key_score"),
                "heard_a": A.get("heard_share"), "heard_b": B.get("heard_share"), "layered": layered, "wrong": wrong,
                "skip": f"probably the wrong download: {', '.join(wrong)}" if wrong else None}

    out, done = [], set()
    for i in range(len(tracks) - 1):
        a, b = tracks[i]["title"], tracks[i + 1]["title"]
        if _fold(a) == _fold(b):
            continue
        out.append(rec(i, i + 1, a, b, False))
        done.add((_fold(a), _fold(b)))
    for (fa, fb), obs in ok_obs.items():       # layered / non-adjacent pairs the learner heard together
        if (fa, fb) in done:
            continue
        o = obs[0]
        out.append(rec(first_idx.get(fa), first_idx.get(fb), o.get("track_a"), o.get("track_b"), True))
        done.add((fa, fb))
    out.sort(key=lambda r: (r["position"], r["layered"]))
    return out


def extract(cache_dir: Path, notes_dir: Optional[Path] = None) -> List[dict]:
    """Every studied transition of every set under CACHE_DIR/sets/*/study.json."""
    cache_dir = Path(cache_dir)
    if notes_dir is None:
        notes_dir = Path(__file__).resolve().parents[2] / "research" / "notes"
    lt = _read(cache_dir / "learned_techniques.json", {}) or {}
    learned = [o for e in (lt.values() if isinstance(lt, dict) else []) if isinstance(e, dict)
               for o in e.get("observations") or [] if isinstance(o, dict)]
    out = []
    for p in sorted((cache_dir / "sets").glob("*/study.json")):
        study = _read(p)
        if not isinstance(study, dict):
            continue
        sid = str(study.get("set_id") or p.parent.name)
        out += extract_set(study, sid, set_meta(cache_dir, sid, notes_dir), learned)
    return out


# ---------------------------------------------------------------------------------------------- resolution

class Resolver:
    """Studied song title -> library track id (canonical through the dedup alias map)."""

    def __init__(self, names: Dict[str, str], aliases: Optional[Dict[str, str]] = None):
        from app.ui.services import dedup_songs as ds

        self.ds, self.aliases = ds, aliases or {}
        self.items = [(tid, ds.identity(n), n) for tid, n in names.items() if isinstance(n, str)]
        self._memo: Dict[str, Optional[str]] = {}

    def _canon(self, tid: str) -> str:
        return self.ds.resolve_alias(tid, None, self.aliases)

    def find(self, title: str) -> Optional[str]:
        if title in self._memo:
            return self._memo[title]
        ds, hit = self.ds, None
        parts = _SPLIT.split(title or "", maxsplit=1)
        for cand in [title] + ([f"{parts[1]} - {parts[0]}"] if len(parts) == 2 else []):   # "Title - Artist" tracklists
            want = ds.identity(cand)
            if not want.title:
                continue
            strong, weak = [], set()
            for tid, ident, name in self.items:
                m = ds.name_match(want, ident)
                if m == "strong":
                    strong.append((-ds.source_rank(name)[0], self._canon(tid)))
                elif m == "weak":
                    weak.add(self._canon(tid))
            if strong:
                hit = sorted(strong)[0][1]
                break
            if len(weak) == 1:          # the same title with one artist unnamed: only when unambiguous
                hit = next(iter(weak))
                break
        self._memo[title] = hit
        return hit


def cut_name(title: str, set_id: str, position: int) -> str:
    """The library name of an unreleased "ID" cut out of the set recording (set_import): unique
    per set slot, so two "ID - ID" entries never read as one recording to the dedup."""
    return f"{title} [set cut {set_id} #{position}]"


def resolve(transitions: List[dict], names: Dict[str, str], aliases: Optional[Dict[str, str]] = None) -> List[dict]:
    """Adds a_id / b_id (None: not in the library) to every transition. An "ID" entry is the
    track cut out of the set at that slot (cut_name), never a name match."""
    r = Resolver(names, aliases)
    rev = {n: tid for tid, n in names.items()}

    def find(title: str, set_id: str, pos: int) -> Optional[str]:
        if _ID_ONLY.search(title or ""):
            return rev.get(cut_name(title, set_id, pos))
        return r.find(title)

    for t in transitions:
        t["a_id"] = find(t["a_title"], t["set_id"], t["position"] - 1)
        t["b_id"] = find(t["b_title"], t["set_id"], t["position"])
        # a cut out of the set IS the song the set played, whatever the learner's own download was
        cut = {x for x, tid in ((t["a_title"], t["a_id"]), (t["b_title"], t["b_id"])) if tid and _ID_ONLY.search(x or "")}
        if cut and t.get("wrong"):
            t["wrong"] = [w for w in t["wrong"] if w not in cut]
            t["skip"] = f"probably the wrong download: {', '.join(t['wrong'])}" if t["wrong"] else None
    return transitions


def library_names(cache_dir: Path) -> Dict[str, str]:
    d = _read(Path(cache_dir) / "uploads" / "_names.json", {})
    return {k: v for k, v in d.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(d, dict) else {}


def load(cache_dir: Path, names: Optional[Dict[str, str]] = None) -> List[dict]:
    """extract + resolve against the library names and the alias map."""
    from app.ui.services import dedup_songs as ds

    return resolve(extract(cache_dir), library_names(cache_dir) if names is None else names, ds.load_aliases(Path(cache_dir)))


# ---------------------------------------------------------------------------------------------- follow a set

# "ID", "ID - ID", "ID ID - Higher", "Adam Beyer - ID": an unreleased track, no song to find
_ID_ONLY = re.compile(r"^\s*id(\s*[-–—]?\s*id)?\s*([-–—]|$)|[-–—]\s*id\s*$", re.I)


def set_songs(cache_dir: Path, names: Optional[Dict[str, str]] = None) -> List[dict]:
    """Every studied set as its tracklist in set order, for FOLLOW SET (macro-mode.js):
    [{set_id, dj, title, songs: [{position, title, track_id, status}]}]; status: library (the
    library holds it), download (missing: offered through the normal suggest -> download
    path), id (an unreleased "ID": nothing to fetch). A wrong download of the learner is not
    used: the library copy, else the title to download."""
    from app.ui.services import dedup_songs as ds

    cache_dir = Path(cache_dir)
    names = library_names(cache_dir) if names is None else names
    up = cache_dir / "uploads"
    have = {p.stem for p in up.glob("*") if not p.name.startswith("_")} if up.is_dir() else None
    res = Resolver({k: v for k, v in names.items() if have is None or k in have}, ds.load_aliases(cache_dir))
    rev = {n: tid for tid, n in names.items() if have is None or tid in have}
    notes =Path(__file__).resolve().parents[2] / "research" / "notes"
    out = []
    for p in sorted((cache_dir / "sets").glob("*/study.json")):
        study = _read(p)
        if not isinstance(study, dict):
            continue
        sid = str(study.get("set_id") or p.parent.name)
        meta = set_meta(cache_dir, sid, notes)
        songs = []
        for i, t in enumerate(study.get("tracks") or []):
            title = str((t or {}).get("title") or "")
            if not title:
                continue
            if _ID_ONLY.search(title):          # an unreleased ID: only its cut out of the set (set_import)
                tid = rev.get(cut_name(title, sid, i + 1))
                status = "library" if tid else "id"
            else:
                tid = res.find(title)
                status = "library" if tid else "download"
            songs.append({"position": i + 1, "title": title, "track_id": tid, "status": status})
        out.append({"set_id": sid, "dj": meta["dj"], "title": meta["title"], "songs": songs})
    return out


# ---------------------------------------------------------------------------------------------- atlas evidence

def evidence(transitions: List[dict]) -> Dict[str, dict]:
    """{"A>B": {count, sets, djs, sources, techniques, rejected}} over the resolved, not skipped ones."""
    ev: Dict[str, dict] = {}
    for t in transitions:
        if t.get("skip") or not t.get("a_id") or not t.get("b_id") or t["a_id"] == t["b_id"]:
            continue
        e = ev.setdefault(f"{t['a_id']}>{t['b_id']}", {"count": 0, "sets": [], "djs": [], "sources": [], "techniques": Counter(), "rejected": []})
        e["count"] += 1
        if t["set_id"] not in e["sets"]:
            e["sets"].append(t["set_id"])
        if t["dj"] not in e["djs"]:
            e["djs"].append(t["dj"])
        e["sources"].append({"set_id": t["set_id"], "dj": t["dj"], "position": t["position"], "overlap_s": t.get("overlap_s")})
        for k, n in t.get("techniques") or []:
            e["techniques"][k] += n
        e["rejected"] = sorted(set(e["rejected"]) | set(t.get("rejected") or []))
    for e in ev.values():
        e["techniques"] = dict(sorted(e["techniques"].items(), key=lambda x: (-x[1], x[0])))
        e["sources"] = e["sources"][:8]
    return ev


def pick_move(p: dict) -> dict:
    """The console move a studied pair plays: the most seen technique the atlas does not refuse,
    mapped to its move; else (only cuts / unknown / refused) the atlas's own plan. -> {move, recipe, why}"""
    from app.music_brain import pair_atlas as pa

    st = p.get("studied") or {}
    for tech in st.get("techniques") or {}:
        if tech in STUDIED_ONLY or tech not in TECHNIQUE_MOVE:
            continue
        move, recipe = TECHNIQUE_MOVE[tech]
        if move == "merge":
            if not (p.get("merge") or {}).get("ok"):
                continue
        elif pa.move_of(p, move).get("ok") is False:        # the atlas's (console) rules refuse it offline
            continue
        return {"move": move, "recipe": recipe, "why": f"studied {tech} -> {recipe}"}
    other = [t for t in st.get("techniques") or {} if t not in TECHNIQUE_MOVE]
    base = "Stem Merge" if (p.get("merge") or {}).get("ok") else (p.get("recipe") or "Echo Out")
    if is_cut_recipe(base):                                # never a cut, whatever the atlas or the set did
        base = "Echo Out"
    return {"move": None, "recipe": base,
            "why": f"studied {', '.join(other)} (studied only): atlas plan {base}" if other else f"atlas plan {base}"}


def attach(pairs: Dict[str, dict], ev: Dict[str, dict]) -> int:
    """Put the studied evidence on the atlas pairs (every build: a pair's old evidence is cleared).
    A studied pair is a combo (`studied` unless a combo move already fits). -> pairs attached."""
    n = 0
    for k, p in pairs.items():
        p.pop("studied", None)
        if p.get("combo") == "studied":
            p["combo"] = None
        e = ev.get(k)
        if e is None:
            continue
        p["studied"] = dict(e)
        p["studied"].update(pick_move(p))
        if not p.get("combo"):
            p["combo"] = "studied"
        n += 1
    return n


# ---------------------------------------------------------------------------------------------- macros

def _step(atlas: dict, t: dict, why_prefix: str) -> Optional[dict]:
    from app.music_brain import pair_atlas as pa

    p = atlas["pairs"].get(f"{t['a_id']}>{t['b_id']}")
    if p is None:
        return None
    pl = pa.plan_of(p)
    if is_cut_recipe(pl["recipe"]):                 # a macro never books a cut
        pl["recipe"] = "Echo Out"
    st = p.get("studied") or {}
    tr = atlas["tracks"]
    return {"a": t["a_id"], "b": t["b_id"], "a_name": tr.get(t["a_id"], {}).get("name"), "b_name": tr.get(t["b_id"], {}).get("name"),
            "recipe": pl["recipe"], "a_time": pl["a_time"], "b_time": pl["b_time"],
            "merge": pl["merge"] if pl["recipe"] == "Stem Merge" else None, "tempo": {"lock": pl["lock"]},
            "combo": p.get("combo"), "works": p.get("works"),
            "why": f"{why_prefix}: {t['dj']} #{t['position']}, {st.get('why') or 'atlas plan'}"}


def set_chain(atlas: dict, ts: List[dict]) -> Tuple[List[dict], List[str]]:
    """The set in SET ORDER as macro steps over the songs the library holds. A studied
    transition keeps its technique (pick_move: a console move, never a cut); a song that is
    missing (or the wrong download) is skipped and the step bridging the gap says so.
    ts: the set's adjacent (not layered) transitions. -> (steps, skipped song notes)"""
    songs: Dict[int, Tuple[Optional[str], str, bool]] = {}         # tracklist position -> (id, title, wrong)
    for t in ts:
        wrong = set(t.get("wrong") or [])
        songs[t["position"] - 1] = (t.get("a_id"), t["a_title"], t["a_title"] in wrong)
        songs[t["position"]] = (t.get("b_id"), t["b_title"], t["b_title"] in wrong)
    by_pos = {t["position"]: t for t in ts}
    steps, gaps, skipped = [], [], []
    prev: Optional[Tuple[int, str]] = None
    for pos in sorted(songs):
        tid, title, wrong = songs[pos]
        if not tid or wrong:
            skipped.append(title)
            gaps.append(f"#{pos} {title} ({'wrong download' if wrong else 'not in the library'})")
            continue
        if prev is None:
            prev = (pos, tid)
            skipped = []
            continue
        if tid == prev[1]:                  # the same song again (a reprise): nothing to mix
            continue
        t = by_pos.get(pos) if pos == prev[0] + 1 else None
        step_t = t or {"a_id": prev[1], "b_id": tid, "dj": ts[0]["dj"], "position": pos}
        s = _step(atlas, step_t, "studied set")
        if s is None:                       # no atlas pair (unanalysed song): skip it, keep A
            gaps.append(f"#{pos} {title} (no atlas pair)")
            skipped.append(title)
            continue
        if skipped:
            s["why"] = (s["why"] + f"; gap: skipped {', '.join(skipped)}")[:300]
        steps.append(s)
        prev, skipped = (pos, tid), []
    return steps, gaps


def write_macros(atlas: dict, transitions: List[dict], cache_dir: Path) -> List[dict]:
    """studied-<set_id>-<n> per resolved pair and studied-set-<set_id> (the whole set in set
    order, missing songs skipped). Stale macros this function wrote before are removed; a user's
    macro of the same name is never touched (macros.write_seed)."""
    from app.music_brain import macros as mc

    out, by_set = [], {}
    for t in transitions:
        if not t.get("layered"):
            by_set.setdefault(t["set_id"], []).append(t)

    def write(m):
        try:
            out.append(mc.write_seed(dict(m, source=MACRO_SOURCE), cache_dir))
        except ValueError:
            pass

    for sid, ts in by_set.items():
        good = [t for t in ts if not t.get("skip") and t.get("a_id") and t.get("b_id") and t["a_id"] != t["b_id"]]
        for t in good:
            s = _step(atlas, t, "studied combo")
            if s is not None:
                write({"name": f"studied-{sid}-{t['position']}", "steps": [s],
                       "title": f"{mc.set_label(t['set_title'], t['dj'])} #{t['position']}: "
                                f"{mc.song_label(s['a_name'])} \u2192 {mc.song_label(s['b_name'])}",
                       "note": f"studied combo from {t['set_title']} (position {t['position']}), techniques "
                               f"{', '.join(k for k, _ in t['techniques']) or 'none heard'}"})
        chain, gaps = set_chain(atlas, ts)
        if len(chain) >= 2:
            write({"name": f"studied-set-{sid}", "steps": chain[:mc.MAX_STEPS],
                   "title": f"{mc.set_label(ts[0]['set_title'], ts[0]['dj'])} (studied set, "
                            f"{len(chain[:mc.MAX_STEPS]) + 1} songs)",
                   "note": f"studied set {ts[0]['set_title']} in set order: {len(chain) + 1} of {len(ts) + 1} songs"
                           + (f"; skipped {len(gaps)}: " + "; ".join(gaps) if gaps else "")})
    fresh = {m["name"] for m in out}
    d = mc.macros_dir(cache_dir)
    for p in d.glob("studied-*.json") if d.is_dir() else []:
        old = _read(p, {}) or {}
        # a macro seeded from the tracked knowledge/ studies a set this cache never studied: keep it
        if p.stem not in fresh and str(old.get("source", "")) == MACRO_SOURCE and not old.get("knowledge"):
            p.unlink()
    return out


# ---------------------------------------------------------------------------------------------- report

def status(transitions: List[dict]) -> dict:
    """Counts + the missing-song list (songs to download to complete the studied chains)."""
    per_set: Dict[str, dict] = {}
    missing: Dict[str, dict] = {}
    for t in transitions:
        s = per_set.setdefault(t["set_id"], {"set_id": t["set_id"], "dj": t["dj"], "title": t["set_title"],
                                             "transitions": 0, "resolved": 0, "missing": 0, "skipped": 0})
        s["transitions"] += 1
        wrong = set(t.get("wrong") or [])
        if t.get("skip"):
            s["skipped"] += 1
        elif t.get("a_id") and t.get("b_id"):
            s["resolved"] += 1
            continue
        else:
            s["missing"] += 1
        for side in ("a", "b"):
            name = t[f"{side}_title"]
            if name in wrong or not t.get(f"{side}_id"):
                m = missing.setdefault(_fold(name), {"name": name, "sets": [], "blocks": 0, "wrong_download": False})
                m["blocks"] += 1
                m["wrong_download"] |= name in wrong      # the set's download was another song: fetch the right one
                if t["set_id"] not in m["sets"]:
                    m["sets"].append(t["set_id"])
    return {"sets": list(per_set.values()),
            "missing_songs": sorted(missing.values(), key=lambda m: (-m["blocks"], m["name"].lower()))}


def row_line(t: dict) -> str:
    state = "skip" if t.get("skip") else "ok  " if t.get("a_id") and t.get("b_id") else "miss"
    tech = ",".join(k for k, _ in t.get("techniques") or []) or "-"
    return f"{state} {t['set_id']:<12} #{t['position']:<3} {t['a_title'][:34]:<34} -> {t['b_title'][:34]:<34} [{tech}]"
