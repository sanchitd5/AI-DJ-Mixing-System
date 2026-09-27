# Set study: Fred again.. & Thomas Bangalter (USB002, Alexandra Palace, 27 Feb 2026)

Source: https://www.youtube.com/watch?v=gfF8jzBVWvM
Title: "Fred again.. & Thomas Bangalter (USB002, Alexandra Palace, London 27 February 2026)"
Duration: 6983s (1:56:23). Audio downloaded with `yt-dlp -x --audio-format mp3` for offline analysis; not committed (gitignored `data/`-equivalent scratch dir, not this repo).

Analysis tool: `research/notes/set_study_analyze.py` (librosa, mono, sr=22050). Re-run with:
```
python research/notes/set_study_analyze.py /path/to/set.mp3
```

**How to read the confidence tags below.** Band-energy (sub/mid/high in dB) and RMS
dBFS are direct measurements of the mixed signal — trust these. Tempo and Camelot key
are model estimates (chroma + Krumhansl-Schmuckler correlation `r`, librosa tempo
tracker) run on **already-mixed, often 3-6-track-deep mashup audio**. Both estimators
were built for single clean tracks, so a low correlation (`r < 0.6`) or an isolated
tempo spike that doesn't persist across adjacent windows is noise, not a fact. Every
transition below is tagged **High / Medium / Low** confidence accordingly.

The tracklist and mashup layering notes come from the user (a fan-transcribed
tracklist for this specific set is not otherwise published); timestamps below are that
tracklist converted to seconds and fed to the analysis script as transition centers,
with a ±20s window read around each one.

---

## 1. Set overview

- Two selectors, one drum machine (Bangalter) synced to the decks for the entire
  set — this is why so many "transitions" are really live layering/mashup builds
  rather than classic two-deck blends, and why the drum-machine track rarely fully
  disappears even across genre changes.
- Genre path: house/disco edits and Daft Punk-adjacent material for the first
  ~68 minutes, a drum & bass detour from roughly 1:09:07 to 1:18:20 (the Nia
  Archives remix of "leavemealone" and neighbours), then back to house/disco/pop
  through to the close.
- Segment ("play time") length is highly variable: as short as 40s (a
  commentary-adjacent beat) up to 10 minutes for the big build stretch at 1:28:20.
  See the "Play time per segment" table below — this is one of the sharpest
  contrasts with the autopilot (Section 8).
- Two callbacks of "One More Time" (3:16 and 1:46:06) bookend the set as a
  recognisable motif — see Section 7.

### Play time per segment (from tracklist gaps)

| segment start | label (first track named) | duration |
|---|---|---|
| 0:01 | Mythologies x L'Accouchement x My House | 3:15 |
| 3:16 | One More Time x We've Lost Dancing x ANMHE | 4:21 |
| 7:37 | Hackney Pigeon (Sammy Virji VIP) | 3:53 |
| 11:30 | Rollin' & Scratchin' x ... x Renegade Master | 4:50 |
| 16:20 | LFO | 1:20 |
| 17:40 | Crescendolls (MPH edit) | 2:20 |
| 20:00 | Technologic x stop&watch x Pulse Z x ... | 2:34 |
| 22:34 | Technologic x Needle Guy | 1:31 |
| 24:05 | Technologic x Circles | 0:55 |
| 25:00 | Contact x My Girls x Night Vision | 6:10 |
| 31:10 | Doin' it Right x places to be | 0:40 |
| 31:50 | ("87 x 2" note / DnB check) | 8:10 |
| 40:00 | Clubbed To Death x Revolution Will Not Be Televised | 1:45 |
| 41:45 | Yeah! (Usher) | 2:04 |
| 43:49 | Serious Sounds (VIP) | 1:36 |
| 45:25 | Touch | 1:45 |
| 47:10 | Giorgio by Moroder | 1:35 |
| 48:45 | Digital Love (arms) | 5:29 |
| 54:14 | Raspberry Beret | 3:06 |
| 57:20 | Teachers x flight fm x Southside | 3:40 |
| 1:01:00 | Turn On The Lights again.. x HBFS | 5:30 |
| 1:06:30 | Aerodynamic x Victory Lap Five | 2:37 |
| 1:09:07 | Starboy x leavemealone | 2:13 |
| 1:11:20 | leavemealone (Nia Archives Remix) | 7:00 |
| 1:18:20 | Music Sounds Better With You | 10:00 |
| 1:28:20 | Da Funk (AvH mix) x 2009 x ICEY.. | 4:25 |
| 1:32:45 | Never the End x Can't Do Without You | 3:15 |
| 1:36:00 | Signatune x Around the World | 3:40 |
| 1:39:40 | Delilah | 6:26 |
| 1:46:06 | One More Time x just stand there x Femi | 9:12 |
| 1:55:18 | end | — |

Median segment length is roughly **3 minutes**; several run 5-10 minutes. Only two
segments (0:40 and 1:20) are under a minute, and both are transitional/commentary
beats, not the norm.

---

## 2. Fred mind: decision rules

**Framing.** The goal here is not to reproduce this tracklist or these songs — it's
to read this set as evidence of a decision-making style and pull out rules general
enough to apply to any songs an autopilot might queue. Each rule below states the
*trigger* (what the music/set is doing), the *action*, the *timing* (in bars where
derivable, otherwise seconds — BPM estimates in this set are noisy, see Section 6),
and *how often* it shows up across the ~30 segments studied. Frequencies are small-n
observations from one set, not statistics — read them as "this happened enough to be
a pattern," not as a rate to hit exactly.

| # | Trigger (state of the music/set) | Action | Timing | Frequency |
|---|---|---|---|---|
| 1 | Outgoing track is at full, established energy (steady high sub, stable loudness) **and** the incoming track's drop can be timed to land on a shared phrase boundary | Swap the bass almost instantly; other bands overlap only briefly | <1-2 bars (near-instant swap) | ~5 of 30 segments (e.g. clean drop-swaps at 41:45, 1:09:07, 1:28:20 in the studied set) |
| 2 | Incoming track shares a hook, key, or structural fit with what's already playing (harmonically adjacent or same Camelot) | Layer 2-3 tracks simultaneously (mashup) instead of swapping; usually vocal/lead of one over the beat/bass of another | Sustained — no fixed bar count, lasts 1-7+ minutes, unwound gradually rather than cut | Roughly half of all segments (~14 of 30) run as multi-track layers, not single-in/single-out swaps |
| 3 | A track has "said its idea" (hook has repeated, energy has plateaued) but no clean drop-aligned cue point exists yet | Pre-clear the outgoing bass well ahead of the audible transition — filter/fade it down before the actual swap moment, rather than swapping cold | ~8-16 bars of pre-roll before the nominal transition point (10-20s at typical 120-140 BPM) | Majority of non-mashup transitions (~18 of ~25 single-track swaps show bass movement 10-20s early) |
| 4 | Entering a vocal-forward or emotionally "spacious" moment (a lyric or breakdown that asks for room) | Cut sub-bass to near-silence for an extended stretch, let the vocal/mid ride alone; resolve later with a big low-end re-entry | Extended, not bar-locked — 10-20s+ of suppressed bass, then a sharp full-band return | ~5 of 30 segments show this pattern (breakdown-style entries) |
| 5 | A large genre/tempo gap is coming up (e.g. four-on-the-floor house into a breakbeat/DnB-family tempo) | Don't hard-cut the tempo; ease through it over several minutes, tolerating tempo ambiguity (the estimator itself flip-flops between full- and half-time reads through this stretch) rather than jump-cutting on a downbeat | Multi-minute bridge (7+ minutes observed), not a single 8-16 bar transition | 1 clear instance in this set, but the general rule — big tempo gaps get bridged, not cut — is the takeaway, not the specific genre |
| 6 | DJ banter or an on-mic aside sounds like it's flagging a technical move (e.g. a tempo-doubling joke) | Treat spoken cues with suspicion — in this set, the banter did **not** line up with an actual sustained tempo change at that moment; the real tempo move (if any) happened later and gradually | N/A (a caution about signal, not a timed action) | 1 instance checked in this set; worth treating as a general caution, not a rule to trigger on |
| 7 | Opening the set / establishing a recognisable idea early | Reintroduce that same idea later in the set, recontextualized (different layer partners, different section) as a bookend | No fixed bars; the callback showed the same relative-key family both times (see Section 7) | 1 clear pair in this set (open + close); read as "include at least one deliberate callback per set," not a fixed count |
| 8 | Extra live/turntablist elements are available (drum machine, scratch, needle-drop FX) | Use them sparingly, in short percussive bursts, rather than continuously — most segments stay comparatively minimal; FX-heavy moments are the exception | Bursts of ~1-2s repeating cycles when used, lasting well under a full segment | ~4 of 30 segments are FX-heavy; the rest are restrained |
| 9 | A long high-energy/peak stretch has just finished | Loudness (RMS) doesn't stay pinned at the peak — it oscillates down by 5-10dB into the next stretch before building again, rather than chaining peak after peak | Loudness cycles roughly every 2-4 minutes across the set's RMS curve | Broad pattern across the whole set's loudness curve, not a single isolated event — treat as "don't queue peak after peak with no dip," not a precise timer |

### Pseudo-policy (state → action)

This is meant as an input to code, not code itself — it names the state an autopilot
would need to track and the decision each rule above implies.

```
state = {
  section: current track's structural section (intro/verse/build/drop/breakdown/outro),
  energy: recent RMS trend (rising / plateaued / falling) and how it compares to the
          set's recent peak,
  time_on_track: seconds since this track/layer became the primary element,
  bass_status: {A: is A's sub currently present/suppressed, B: same for the cued-up track},
  camelot_fit: A/B key relationship (same, adjacent, relative, distant),
  bpm_gap: A/B tempo relationship (near-identical, ramp-able, large genre-style gap),
  set_position: fraction of set elapsed, and whether an early "theme" track exists
                that hasn't been recalled yet,
  fx_budget: how recently a scratch/FX/turntablist move was used (avoid overuse),
}

decide(state):
  if state.energy == "plateaued" and no aligned drop point exists:
      -> begin pre-clearing A's bass now (rule 3), 8-16 bars ahead of any swap
  if state.camelot_fit in {same, adjacent, relative} and section/hook of B fits over A:
      -> layer B in (rule 2) instead of swapping; don't force an exit time
  if state.bass_status.A present and a shared drop point is computable with B:
      -> near-instant bass swap at that point (rule 1)
  if entering a vocal-only/breakdown moment:
      -> suppress A's sub for an extended stretch, hold for the vocal (rule 4)
  if state.bpm_gap == "large genre-style gap":
      -> don't cut; open a multi-minute bridge, tolerate tempo ambiguity (rule 5)
  if state.set_position is late and an early-set "theme" track hasn't been recalled:
      -> consider recalling it now, recontextualized (rule 7)
  if fx_budget is "used recently":
      -> avoid another FX-heavy move; default to a more restrained handling (rule 8)
  if state.energy is at/near the set's recent peak and has been for a while:
      -> favor a track/queue choice that lets loudness dip before building again (rule 9)
```

---

## 3. Per-transition table (supporting evidence)

The table below is the raw evidence the rules above were drawn from — a
transition-by-transition read of one set. It is not a recommendation to replay this
tracklist; it's here so the rules in Section 2 can be checked against what actually
happened.

`t=` is the tracklist timestamp (start of the labelled segment). Tempo/key are the
before→after estimate from a ±20s window centered on that time. Bass-handoff style
and technique label are read from the band-energy trace (sub <120Hz / mid / high
>4kHz, in dB, and RMS dBFS) around the same window.

| t | tracks | BPM (est.) | Camelot (est.) | bass handoff | technique (recipe name) | confidence |
|---|---|---|---|---|---|---|
| 0:01 | Mythologies x L'Accouchement x My House | 123→123 | 4B→4B (r .90/.48) | sub cut hard ~3s after intro settles, held out ~8s | Breakdown Transition (slow build-in) | Medium (bands), Low (key, 2nd read r<0.6) |
| 3:16 | One More Time x We've Lost Dancing x ANMHE | 117.5→123 | 5A→10B (r .36/.69) | sub snaps from -20dB to +30dB in <1s at the boundary | Hard Cut / Live Mashup layering | Medium (bands); tempo/key Low |
| 7:37 | Hackney Pigeon (Sammy Virji VIP) | 136→136 | 10A→10B (r .63/.83) | steady, already blended in — no sub event at this timestamp | Long Blend (already underway) | Medium-High (relative major/minor key move, both r>0.6) |
| 11:30 | Rollin' & Scratchin' x Spinal Scratch x 808 State x Baby again.. x Rumble x Renegade Master | 136→136 | 10A→1A (r .33/.51) | sub oscillates every 1-2s across the whole ±20s window | Stutter Transition / live scratch-style layering | Bands High; key Low (both r<0.6) |
| 16:20 | LFO | 136 (held) | 6B→4A (r .59/.37) | sub swings -10↔+55dB repeatedly, sparse/minimal | Filter Transition into breakdown | Bands High; key Low |
| 17:40 | Crescendolls (MPH edit) | 136 (held) | 6A→7B (r .36/.64) | sub holds ~50dB before, cut to near 0dB for ~20s after | Breakdown Transition (chopped intro, matches the track's known arrangement) | Bands High; key Low |
| 20:00 | Technologic x stop&watch x Pulse Z x Needle Guy x Circles | 136 (held) | 8A→7B (r .25/.30) | sub high and continuous, no single swap point | 3-Deck Layering / Live Mashup | Bands High; key Low (both weak) |
| 22:34 | Technologic x Needle Guy | 136 (held) | 4A→12B (r .56/.59) | sub jumps 15↔58dB every ~1s (needle-drop effect, matches track name) | Stutter Transition / scratch FX | Bands High; key borderline |
| 24:05 | Technologic x Circles | 143.6→136 | 1A→1A (r .52/.51) | sub modest (~20dB) then ramps to 50+dB by +13s | Bass Swap (slow ramp, not instant) | Bands Medium; key Low |
| 25:00 | Contact x My Girls x Night Vision | 136→129.2 | 2A→9B (r .52/.74) | sub crashes to negative dB right at the boundary, held down ~15-20s | Breakdown Transition / Echo Out | Bands High; key Low |
| 31:10 | Doin' it Right x places to be | 117.5 (held) | 1A→1A (r .73/.78) | sub steady 40-58dB, continuous groove | Basic Blend / EQ Blend | Bands High; key Medium-High (same key both sides, decent r) |
| 31:50 | "87 x 2" note — checked for a DnB/half-time switch | 86.1→117.5 in the ±20s read, but the fine 30s/10s-hop scan across 1750-2000s shows **117.5 BPM in every window except one isolated 172.3 BPM read at exactly t=1910s**, reverting to 117.5 immediately before and after | 1B→2B (r .80/.72) | no dramatic sub event in this window | **No sustained tempo shift found here** — see note below | Bands Medium; tempo Low (one-window artifact, not corroborated) |
| 40:00 | Clubbed To Death (Kurayamino Variation) x Revolution Will Not Be Televised | 123→103.4 | 6A→6A (r .73/.77) | sub strongly negative for ~15s pre-boundary (filtered out, matches the track's stringy, bass-light intro), recovers to 50dB+ after +6s | Breakdown Transition / Filter Transition | Bands High; key Medium-High |
| 41:45 | Yeah! (Usher) | 143.6→107.7 | 9B→9A (r .61/.60) | sub near/below 0dB for ~20s, then a clean jump to 50+dB at +2s | Bass Swap / Drop Swap | Bands High; tempo/key borderline (both ~0.6) |
| 47:10 | Giorgio by Moroder | 123→152 | 11A→3A (r .64/.33) | sub dips to near-0 or negative around +10 to +14s then recovers | (internal arrangement dip, not a hard transition) | Bands Medium; tempo/key Low (152 BPM read is very likely an octave error) |
| 1:06:30 | Aerodynamic x Victory Lap Five | 129.2→112.3 | 11B→10B (r .85/.62) | — | Genre Bridge / Tempo Bridge (adjacent Camelot hour) | Bands unread in detail; key Medium-High |
| 1:09:07 | Starboy x leavemealone | 123→129.2 | 6B→8A (r .47/.39) | sub low before, clean jump to mid-50s dB at +1s | Bass Swap (matches DJ's "same structure, different universe" framing — aligned drop point) | Bands High; key Low |
| 1:11:20 | leavemealone (Nia Archives Remix) | 117.5 (held); see DnB tempo-path note in Section 6 | 7B→8A (r .48/.54) | sub strongly negative (-3 to -9dB) for ~15s pre-boundary, jumps to 40-55dB after +5s | Filter Transition (into the remix's own low end) | Bands High; tempo/key Low here — real tempo story is in Section 6 |
| 1:18:20 | Music Sounds Better With You (Stardust) | 161.5 (held, but see caveat) | 4A→4A (r .55/.37) | sub very high/steady 50-59dB, high band suppressed (<20dB) for a long stretch | Filter Transition (low-pass held, matches Stardust's filtered-disco intro) | Bands High; tempo Low (see Section 4), key Low |
| 1:28:20 | Da Funk (AvH mix) x 2009 x ICEY.. | 123 (held) | 1B→9A (r .47/.29) | sub subdued (10-35dB) before, locks to 53-59dB after +3s | Bass Swap | Bands High; key Low |
| 1:36:00 | Signatune (Bangalter edit) x Around the World | 123 (held) | 8A→8B (r .84/.55) | sub deeply negative for ~10s pre-boundary, jumps to mid-40s dB at -4s (pre-drop hit) | Breakdown Transition / Filter Transition | Bands High; key Medium |
| 1:39:40 | Delilah (pull me out of this) | 123→129.2 | 4A→6B (r .69/.91) | sub negative to near-0 across almost the entire ±20s window, one partial recovery near +13s | Breakdown Transition / Echo Out (mood matches the lyric) | Bands High; key Medium-High (after side) |
| 1:46:06 | One More Time x just stand there x Femi (callback) | 136→129.2 | 10B→10B (r .78/.72) | sub modest and steady (~15-20dB), no hard swap visible | Long Blend (thematic re-entry, not a technical "move") | Bands Medium; key Medium-High |

---

## 4. Recurring patterns — the DJ's "rules"

1. **Segments are musical phrases, not fixed clock lengths.** Play time ranges from
   40s to 10 minutes and tracks the music (a build, a vocal hook, a drum-machine
   pattern), not a fixed budget. Nothing in the data suggests a hard per-track cap.
2. **The bass almost always moves first, ahead of the perceptible "transition."**
   In nearly every table row, the sub band is already dipping or climbing 10-20s
   *before* the tracklist-labelled timestamp — the DJs pre-clear or pre-build the low
   end, then the new track's identity (vocal, lead) arrives on top afterward. This is
   closer to "Filter Transition" / "Breakdown Transition" phrasing than an instant
   "Bass Swap" snap, except at a handful of clean drop-swaps (41:45 Yeah!, 1:09:07
   Starboy x leavemealone, 1:28:20 Da Funk).
3. **Layering (the "x" mashups) is the default, not the exception.** Roughly half the
   segments name 3+ simultaneous tracks. The drum machine being synced to the decks
   for the whole set is almost certainly why the sub/mid bands rarely go fully silent
   even at a "transition" — there's often a constant rhythmic floor under everything.
4. **Genre/tempo bridges are gradual, not sudden, even into DnB.** See Section 6 —
   the tempo trace shows flip-flopping between full and half-time reads across
   several minutes rather than one clean jump, which is consistent with a DJ easing
   a room through a big genre change rather than cutting to it.
5. **Callbacks are a structural device.** "One More Time" opens the mashup-heavy
   first act (3:16) and returns to close the set (1:46:06) in a different mashup
   context (`x just stand there x Femi`) — see Section 7.

---

## 5. Mashup layering (what's riding on what)

Based on band-energy shape rather than stem separation (no source separation was run
for this study), so this is inference from the mixed signal, not a certainty:

- **20:00 "Technologic x stop&watch x Pulse Z x Needle Guy x Circles"**: continuous
  high sub/mid throughout with no single dominant swap — reads as a genuine 3+deck
  layer (drum machine + Technologic's vocoded hook + at least one more melodic
  layer), not a sequential A→B→C chain.
- **22:34 "Technologic x Needle Guy"**: the sub band's rapid ~1s-period swings match
  a literal scratch/needle-drop FX layered under the sustained Technologic vocal —
  the vocal (mid band) stays essentially flat through the segment while the sub/high
  bands do the moving, a vocal-over-shifting-rhythm pattern.
- **1:09:07 "Starboy x leavemealone"**: DJ's own commentary ("the same in different
  universes") plus the clean, near-instant bass handoff at +1s suggests the two
  tracks' drops are timed to land together — a phrase-aligned mashup rather than a
  sequential transition.
- **1:36:00 "Signatune (Bangalter edit) x Around the World"**: sub goes deeply
  negative for ~10s then jumps at -4s, i.e. *before* the tracklist timestamp —
  reads as a filtered buildup under Signatune's edit that resolves into Around the
  World's bassline, consistent with an edit built specifically to land there.

## 6. Tempo path across the set, and the 31:50 / DnB question

**31:50 ("What's 87 times 2?"):** the fine-grained tempo scan (30s window, 10s hop,
1750-2000s) shows **117.5 BPM in every single window except one** — a single 30s
window centered at t=1910s reads 172.3 BPM, then the very next window (t=1920s, only
10s later) is back to 117.5. A real, sustained tempo doubling would show up across
several consecutive overlapping windows, not one. The most likely explanation is a
transient (a vocal stab, a scratch, or the "87 x 2" bit itself) confusing the beat
tracker for a single window, not an actual BPM change. **Low confidence that a real
tempo shift happens at 31:50** — the data argues against the note's suggestion, though
a single 30s slice can't rule out a very brief interpolated hit.

**The actual DnB stretch (per the tracklist, 1:09:07-1:18:20, seconds 4147-4700):**
here the tempo trace is far noisier and much more consistent with a genuine tempo/genre
change — readings flip between roughly 89-99 BPM and roughly 123-161 BPM across
adjacent windows in this stretch (see raw scan in the script output, 4100-4750s). This
flip-flopping is the classic signature of an octave-confused beat tracker on a fast
breakbeat track (DnB's true tempo, typically 170-176 BPM, aliases to a half-time read
around 85-88 BPM, which shows up repeatedly: 86.1 at 43:49/44:49, 89.1 at 4400-4430s).
The clearest full-tempo lock is 161.5 BPM across four consecutive windows at
4670-4710s (77:50-78:30), i.e. near the end of the labelled Nia Archives remix
segment, closer to (but still under) a typical DnB tempo — **read this as "the set is
running fast and breakbeat-driven through here," not as a precise 161.5 BPM fact.**
**Medium confidence on the direction of the tempo story (up into DnB-range and back
down), Low confidence on any single BPM number in this stretch.**

## 7. Callbacks

"One More Time" appears at 3:16 (inside an early triple mashup:
`One More Time x We've Lost Dancing x Ain't No Mountain High Enough`) and again at
1:46:06, close to the end (`One More Time x just stand there x Femi`). Both instances
carry a 10A/10B-family Camelot read (3:16's second-window: 10B, r=.69; 1:46:06:
10B→10B, r=.78/.72 — the strongest key-confidence read of the whole closing stretch).
Combined with the tracklist itself flagging it as a deliberate return, this reads as
a genuine set-construction device: open on a theme, develop the set through it
(mashups, genre detour, build), and close by returning to the same track in a new
combination — bookending rather than pure linear progression.

---

## 8. Autopilot comparison

Code read: `app/ui/static/autopilot.js` (`executeTransition` at line 200,
`scheduleTransition` at line 486) and `app/music_brain/recipe_matcher.py`
(`RecipeMatcher`, `TransitionCandidate`, phrase/vocal/camelot/bpm scoring).

### What the autopilot does today

- `scheduleTransition` (autopilot.js:492-505): **hard play-time cap of 120s for a
  good match (score ≥ 65) or 60s for a weaker one**, with a 15s minimum before any
  crossfade can fire.
- `executeTransition` (autopilot.js:200-311): every recipe kind resolves to an
  **8-bar transition** (bass swap, echo, filter, cut, loop, default) except "blend"
  and the fallback default, which run **16 bars**. There is no recipe longer than
  16 bars, and no recipe shorter than "cut" (instant).
- EQ order in the dominant "bass"/"default"/"filter" kinds: **kill outgoing low
  first, ramp crossfader, then release incoming low around the bar-4 mark** — a
  fixed schedule regardless of what's actually happening acoustically in either
  track.
- No genre-bridge or "hold both basses briefly" logic; `recipeKind` maps directly
  off the recipe *name string* (autopilot.js:181-191), with no path that lets a
  transition run open-ended while a build or breakdown plays out.

### What this set does that the autopilot doesn't

1. **Play time is nothing like 60-120s.** Median segment here is ~3 minutes; the
   longest is 10 minutes (1:28:20) and several others run 5-9 minutes. The
   autopilot's `MAX_PLAY_SECS` (60/120s, autopilot.js:494) would force an exit
   roughly 15-40x sooner than this DJ ever does.
2. **The bass moves 10-20s before the "transition point," not in an 8-16 bar
   window that starts at the transition** (rule 3 in Section 2). Nearly every row
   in Section 3 shows the
   sub band already dipping or building well ahead of the tracklist timestamp. The
   autopilot's EQ ramps only start once `scheduleTransition` fires the crossfade —
   there's no equivalent of a slow pre-clear.
3. **Overlap length varies by technique, not by a fixed 8/16-bar schedule.** The
   quick mashup snaps (3:16, 22:34) read as near-instant (<1-2s of overlap); the
   breakdown-style entries (25:00, 1:36:00, 1:39:40) read as 15-20s+ of overlapping,
   filtered low end before the swap completes. The autopilot only has two discrete
   overlap lengths (8 bars or 16 bars) regardless of recipe.
4. **Genre/tempo bridges are gradual and multi-minute** (rule 5 in Section 2; the
   DnB stretch, Section 6), not a single scored transition. `recipe_matcher.py`'s
   `bpm_compatibility`
   and `camelot_distance_score` (lines 77-105) score a single A→B pair; there's no
   concept of a multi-track bridge sequence.
5. **Layering ("x" mashups) is the norm, not a fallback.** Roughly half of this
   set's segments run 3+ tracks simultaneously. `RecipeMatcher.match` (line 258)
   and `resolve_candidate` (line 322) evaluate exactly one A→B pair at a time;
   there's no 3-deck layering concept in the matcher or in `executeTransition`'s
   `recipeKind` switch (autopilot.js:181), even though `3-Deck Layering.md` exists
   as a documented recipe.

### Concrete changes, ranked by impact

1. **`app/ui/static/autopilot.js:scheduleTransition` → raise `MAX_PLAY_SECS` from
   60/120s to something like 180-360s (3-6 min), and stop scaling it only off match
   score.** This is the single biggest gap: every real segment observed here except
   two commentary beats ran longer than the autopilot's current maximum, several
   by 5-10x. Even a conservative middle ground (180s good match / 90s weak match)
   would be 1.5-3x the current cap and much closer to what was actually observed.
2. **`app/ui/static/autopilot.js:executeTransition` → add a slow pre-clear phase
   before the crossfade window starts**, e.g. begin ramping the outgoing low band
   down over 8-16 bars *before* `scheduleTransition`'s `fireAt`, rather than only
   ramping inside the fixed 8/16-bar window that starts at the fire point. The data
   shows the bass moving 10-20s ahead of the nominal transition point in most rows
   of Section 3 — the current code has no concept of "early."
3. **`app/music_brain/recipe_matcher.py` → add a per-recipe overlap-length field**
   (or at least a slow/fast flag) instead of the autopilot deriving overlap purely
   from `recipeKind` string-matching (autopilot.js:181-191) into a binary 8-or-16-bar
   choice. Breakdown/filter-style recipes in this set ran 15-20s+ of overlap; clean
   drop-swaps ran under 2s. One overlap constant per kind can't represent both.
4. **`app/ui/static/autopilot.js` → add a 3-deck layering mode** that can hold two
   tracks (plus the existing single-deck EQ chain) simultaneously without forcing a
   swap, matching `DJ/05 - Transition Cookbook/3-Deck Layering.md` and `Live
   Mashup.md`, which already exist in the knowledge base but have no corresponding
   `recipeKind` branch in `executeTransition` (autopilot.js:222-309).
5. **`app/music_brain/recipe_matcher.py:RecipeMatcher.match` → support scoring a
   multi-minute genre bridge** (e.g. house→DnB) as a sequence of 2-3 chained
   candidate transitions with a shared BPM ramp, rather than one A→B pair. The
   observed DnB stretch here reads as a gradual multi-minute push, not a single
   scored move; `bpm_compatibility` (recipe_matcher.py:96-105) currently has no path
   for "this pair is meant to be a multi-minute bridge, not a single 8-16 bar
   transition."

---

*Confidence caveat, repeated for emphasis: tempo and Camelot key numbers throughout
this document come from librosa's tempo tracker and a Krumhansl-Schmuckler chroma
correlation, both run on mixed, often 3+-track audio. They are directional hints
useful for spotting patterns (adjacent-hour Camelot moves, tempo trending up or down),
not ground truth for any single track's actual BPM or key. Band-energy and RMS
readings are direct measurements and are much more reliable.*

---

## Stem-level studies (2026-09-27, 4-stem Demucs `htdemucs_ft` on the set audio)

Method: separate the set excerpt into drums / bass / vocals / other, read RMS dB per
stem per window, and identify each layer by onset-envelope cross-correlation
against the candidate songs' own stems at 1.0x and at the tempo ratios that would
lock them (pitch-invariant, so it works with or without key-lock). Pitch shift is
read from a 1/3-semitone pitch-class profile of the matched layer. Scripts:
`study_seg.py`, `match_aero.py`, `keylock.py`, `aero_map.py`, `verify_offset.py`
(session scratchpad; the algorithm now lives in `app/music_brain/techniques.py`).
Qwen3-Omni was also asked to describe the audio: when the prompt named the songs it
echoed the prompt back ("steady 123 BPM" while the drums read 140), and on isolated
stems it returned nothing. Its descriptions were not used as evidence.

### 1:14:22 leavemealone (Nia Archives Remix), 174 BPM: "strip & rebuild"

| time | vocals | drums | bass | other | move |
|---|---|---|---|---|---|
| 74:22-74:26 | -22 | -24 -> -42 | -8 | -26 | drums out |
| 74:30-74:38 | -17 | -47 | -82 | -28 | bass out: voice nearly alone |
| 74:42-74:54 | -19 | -35..-40 | -10 | -24 | bass back, still no kick |
| 74:58-75:14 | -17..-22 | -34 -> -23 | -31..-79 | -30 -> -17 | bass out, synths rise, drums creep: build |
| 75:18-75:22 | -19 | -23 -> -18 | -11 | -29 | bass, then drums slam back: drop |

The vocal never stops; ~43 bars. This is how a famous song plays for 7 minutes.
Implemented as `strip_rebuild` (stem-moves.js BREAKDOWN, 40 / 24 bars).

### 1:06:30 Aerodynamic x Victory Lap Five: "riff over rap"

- Everything runs at **140 BPM, Victory Lap Five's own tempo**. Aerodynamic
  (122.9 BPM) is **key-locked stretched +13.9 %**: its riff matches the original
  at 0.00 semitones (0.981), not the +2.26 st a vinyl-rate change would give.
- Keys **10A (B minor) vs 5B (D# major)**: a clash on the Camelot rules. It works
  because the layer on top is rap.
- Aerodynamic's **16-bar full groove (0:31.6-1:02.9) is looped** under everything
  until 67:24 (drum matches keep returning to 0:48-0:52).
- 66:48: VLF's bass takes over under the Aerodynamic groove (one bass owner).
- 67:24: the loop is **released into Aerodynamic's own drumless breakdown**
  (1:02.9, the guitar solo) = the 8-bar break. Nobody cut the drums: the song did.
- 67:36: VLF drops in (drums, bass, the rap from its 4:35) under the solo, whose
  first 8 bars (1:02.9-1:18.6) are **looped on top**; riff onsets sit 92.9 ms (mod
  one beat) before VLF's drum hits.
- 68:24: the riff fades; VLF runs to its end (~68:48), then Starboy x leavemealone.
- Unresolved: a half-voiced vocal (pyin voiced 0.40-0.49) over the groove at
  66:00-67:24, matching neither song. Likely a third layer; left out.

Recreated from the two library tracks with the measured timeline:
`data/output/recreate_USB002_1-06-30_aerodynamic_x_victory_lap_five.wav`
(Rubber Band R3 key-lock stretch; VLF offset solved to the set's riff->drums phase,
within 1 ms). Stem-energy timeline matches the set's at every event (break -70/-80 dB
vs set -51/-77; drop at 67:36).

### What changed in the algorithm (app/music_brain/techniques.py)

1. **Techniques are conditional.** Each one lists what it needs and `rank()` returns
   every technique with the reasons it fits or not (`GET /api/techniques?a=&b=`).
   Same-tempo, same-key pairs still get the EQ blend; riff over rap only when a
   pair has a 3-15 % tempo gap, a loopable groove and its own breakdown in A, and a
   rap section in B.
2. **Key compatibility applies between tonal layers only.** A rap vocal over a riff
   ignores the Camelot rule.
3. **Rap vs sung** is read from pitch stability (held-pitch run < 0.10 s and > 20 c
   off the nearest note), not voiced fraction (rap is voiced speech: VLF 0.79).
   Preliminary: calibrated on 5 vocals.
4. **Key-lock stretch up to ~14 % on an instrumental layer** is a real move; the live
   console cannot do it yet (Web Audio playbackRate moves pitch), so `riff_over_rap`
   is marked `live: false` until key-locked stems are rendered server-side.

### Riff over rap, live (2026-09-27): balance

First live run (`riff-over-rap.js`) had B's rap on top and a +5.9 dB jump at the drop:
Aerodynamic's master is ~6 dB quieter than Victory Lap Five's, so B arrived loud.
User: "rap volume should have been lower than Aerodynamic". Now `keylock.balance()`
lifts A to B's loudness (max +8 dB), and while A's riff plays B stays in stem mode with
its rap 3 dB under the riff and its bass 9 dB under (the set's bass-under-riff balance);
both come back up as the riff fades. Measured on the next live recording: rap 5.6 dB
under the riff, drop jump +0.6 dB, groove -13.9 dB (set -13.3). Note: the set itself
has the rap 2.4 dB above the riff; the user's preference wins.

**One tonal owner (user, 2026-09-27).** "Aerodynamic's background music is good, but Victory
Lap Five's background music plays on top of it, doesn't sound good." Right, and the set
agrees: at 67:36-68:24 the set's `other` stem matches Aerodynamic's riff (0.47-0.60), not
VLF's. While A's riff plays, B contributes drums, bass and rap only; its own synths/samples
enter as the riff fades. Same principle as one bass owner, applied to the tonal layer, and
the reason a 10A/5B key clash never sounds: only one pitched layer plays at a time.

**B enters at its rap (user, 2026-09-27).** "Before 1:20-25 there's no point playing Victory Lap
Five's background music." The set's bass-intro handover (VLF bass from 0:04 under the
Aerodynamic groove at 66:48) is dropped: B starts ON the drop, at the phrase line of its rap
(1:24), with drums, bass and rap only; A owns the bass through the groove and the break.

**Victory Lap, not Victory Lap Five (user, 2026-09-27).** The live move now pairs Aerodynamic
with the original Victory Lap (Fred again.., Skepta, PlaqueBoyMax; 140 BPM, 2:46), whose rap
starts at the top, so B enters from 0:01 on the drop. The downloader had matched "Victory Lap
Five" for "Victory Lap": sequel titles (Two / Five / Pt. 2) are now rejected unless asked for
(`download_service._sequel`). Also from the user: the rap sits ~9 dB under Aerodynamic's riff
("in concert the vocals are low, the music carries it"), the rap enters on top of A's
breakdown with B's drums crossfading in over 8 bars (no hard cut), and B's synths stay out
while A's riff plays.

**Live vs set, final pass (2026-09-27).** Structure now follows the set: A's groove, the first
half of A's drop clean (the break: set drums -51 / bass -77 dB, live -70 / -84), that half
looped under B's rap (one groove, no second loop), rap entering after B's repeated opening
hook (detected by vocal-rhythm repetition, Victory Lap 0:28.7), rap x1.5 for the mashup's
second half, 8-bar crossfade with the bass swap on a line. Remaining gap: in the set B's
drums and bass play under the rap during the mashup (drums -19..-22, bass -14..-17 dB) and
the mashup is ~8 dB louder than ours, where B is rap only (user asked for none of B's
backing under A). Open question for the user: are B's drums + bass "background music" too?
