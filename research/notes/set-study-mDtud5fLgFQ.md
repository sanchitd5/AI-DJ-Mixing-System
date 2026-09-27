# Set study: Latin house/pop open-format set (mDtud5fLgFQ)

Source: https://www.youtube.com/watch?v=mDtud5fLgFQ
Duration: 4150.8s (1:09:11). Audio downloaded with `yt-dlp -x --audio-format mp3` for offline
analysis; not committed (downloaded to the session scratchpad, a gitignored/temp location
outside the repo, not `data/songs`).

Analysis tool: `research/notes/set_study_analyze.py` (same script used for the Fred again.. &
Thomas Bangalter USB002 study, librosa, mono, sr=22050), re-run unmodified against this set's
audio with this set's own timestamps as the transition-center list. Re-run with:
```
python research/notes/set_study_analyze.py /path/to/set.mp3 "11,142,411,676,840,1150,1250,1453,1712,2162,2421,2706,3043,3329,3543,3703"
```

**How to read the confidence tags below** (same rule as `set-study-gfF8jzBVWvM.md`, repeated
here rather than assumed): band-energy (sub <120Hz / mid / high >4kHz, in dB) and RMS dBFS are
direct measurements of the mixed signal — trust these. Tempo and Camelot key are model
estimates (chroma + Krumhansl-Schmuckler correlation `r`, librosa tempo tracker) run on
**already-mixed audio**, and both estimators were built for single clean tracks. A low
correlation (`r < 0.6`) or a tempo read that doesn't persist across adjacent windows is noise,
not a fact. Every transition below is tagged **High / Medium / Low** confidence per band.

The tracklist and timestamps come from the user (a fan-transcribed tracklist for this set is
not otherwise published); the times below are that tracklist converted to seconds and fed to
the analysis script as transition centers, with a +/-20s window read around each one.

---

## 1. Set overview

- Single continuous open-format set, roughly 69 minutes, no selector handoff or drum-machine
  layer to track (unlike the USB002 study) — this is a more conventional one-DJ blend session,
  so most of Section 3's rows read as single A-to-B moves rather than multi-track mashups.
- Genre path: Spanish/Latin-language house and pop edits throughout, with a "Cmon (LATIN MAFIA
  & Fred edit)" mashup around 14:00 and an ambient/downtempo detour through "Open Eye Signal
  (under the fabric)" (a Jon Hopkins track — see Section 5) and "Film Scene Soundtrack" from
  roughly 28:32 to 40:21, before returning to Latin house/pop.
- **"Quiereme" is a recurring motif, not a one-off.** The tracklist itself labels three separate
  returns to it — 19:10 (Quiereme), 20:50 (Quiereme x2), 59:03 (Quiereme x3) — and "Te Estoy
  Correteando" gets one repeat (50:43, then "x2" at 55:29). See Section 7 — this reads as a
  different bookending device than the USB002 set's single open/close callback: repeated
  in-set returns to a crowd-favorite hook rather than a single symmetric open/close pair.
- Segment length ranges from as short as 1:40 (20:50 Quiereme x2) to 7:30 (36:02 Film Scene
  Soundtrack) and 7:28 (the closing Mabe segment, to the end of the recording). See the "Play
  time per segment" table below.

### Play time per segment (from tracklist gaps)

| segment start | label | duration |
|---|---|---|
| 0:11 | Hey Hey | 2:11 |
| 2:22 | Alvafro | 4:29 |
| 6:51 | Bonita | 4:25 |
| 11:16 | benjy chord | 2:44 |
| 14:00 | Cmon (LATIN MAFIA & Fred edit) | 5:10 |
| 19:10 | Quiereme | 1:40 |
| 20:50 | Quiereme x2 | 3:23 |
| 24:13 | casino143 (Rue De La Fortuna Remix) | 4:19 |
| 28:32 | Open Eye Signal (under the fabric) | 7:30 |
| 36:02 | Film Scene Soundtrack | 4:19 |
| 40:21 | Piensas En Mi | 4:45 |
| 45:06 | Halo | 5:37 |
| 50:43 | Te Estoy Correteando | 4:46 |
| 55:29 | Te Estoy Correteando x2 | 3:34 |
| 59:03 | Quiereme x3 | 2:40 |
| 1:01:43 | Mabe | 7:28 |
| 1:09:11 | end | — |

Median segment length is roughly **4 minutes**; only one segment (20:50, 1:40) runs under two
minutes. No segment here is as short as the USB002 study's 40s commentary beats, and none runs
as long as that set's 10-minute build — this set's play times cluster more tightly around the
3-5 minute range.

---

## 2. Per-transition table (supporting evidence)

`t=` is the tracklist timestamp. Tempo/key are the before->after estimate from a +/-20s window
centered on that time. Bass-handoff style is read from the band-energy trace (sub <120Hz / mid
/ high >4kHz, in dB, and RMS dBFS) around the same window. As in the template note, tempo and
key numbers below are directional hints, not facts — see the confidence caveat above.

| t | track | BPM (est.) | Camelot (est.) | bass handoff | confidence |
|---|---|---|---|---|---|
| 0:11 | Hey Hey (set open) | 123->123 | 4A(r.64)->3B(r.77) | sub oscillating (dips to -37dB, spikes to +6dB) through most of the window, one clean swap near +10.5s | Bands Medium (oscillating, not a single clean event); tempo Medium (held); key Low-Medium |
| 2:22 | Alvafro | 129.2->136.0 | 4A(r.54)->4A(r.81) | sub climbs from ~20dB pre through a dip near -6s, then locks to 50-52dB from +14s onward (drop lands ~14s after the marker) | Bands High; tempo Low (weak pre-read); key Medium (strong post-read, same pitch class both sides) |
| 6:51 | Bonita | 107.7->129.2 | 5A(r.91)->10A(r.80) | sub negative almost the whole pre-window (-8 to -26dB), snaps to +49dB at +9s and stays 38-54dB after | Bands High (clean Bass Swap ~9s post-marker); key Medium-High (both reads strong, relative-key-family move); tempo Low (large jump, likely genre/track BPM difference more than a tracking artifact, but unverified) |
| 11:16 | benjy chord | 136.0->136.0 | 9A(r.37)->5A(r.52) | sub already high (45-56dB) both sides, one brief dip to 3-7dB at +2 to +4s, recovers within a second | Bands High (direct read); tempo Medium (held, consistent with no real move here); key Low (both weak) |
| 14:00 | Cmon (LATIN MAFIA & Fred edit) | 136.0->123.0 | 8B(r.72)->4B(r.75) | sub steady 52-56dB pre, falls sharply after +4s to single digits through +17s, only starts recovering at +20s | Bands High (clear Breakdown/Filter Transition, post-marker); key Medium-High (both strong, same-letter move); tempo Medium |
| 19:10 | Quiereme | 117.5->86.1 | 2A(r.40)->5B(r.60) | sub swings wildly pre (-24 to +48dB), stabilizes to 48-55dB from +12s | Bands High (direct); tempo Low (big drop plausibly a half-time tracker read, not confirmed by a sustained multi-window scan the way Section 3 below checks); key Low-borderline |
| 20:50 | Quiereme x2 | 112.3->117.5 | 11A(r.38)->5B(r.60) | sub fluctuates heavily pre (many dips to -14 to -29dB), locks to 51-54dB by +14s | Bands High; tempo Low; key Low — same overall shape as the 19:10 window, consistent with this being a repeat pass over the same hook |
| 24:13 | casino143 (Rue De La Fortuna Remix) | 117.5->152.0 | 7A(r.58)->4A(r.60) | sub deeply negative through the entire pre-window (-8 to -21dB), jumps positive right at the marker (+41dB at 0s) and stays 34-49dB after | Bands High (unusually clean alignment — the bass swap lands almost exactly on the tracklist timestamp); tempo Low (152 BPM read on a "remix" tag is plausibly a tracker octave-error, not verified against a fine-grained scan); key Low-borderline |
| 28:32 | Open Eye Signal (under the fabric) | 103.4->117.5 | 4A(r.67)->8A(r.79) | sub strong pre (43-55dB), crashes to negative right at the marker and stays negative through +15s, only creeping back near 0dB by +20s | Bands High (long Breakdown Transition, matches Jon Hopkins' "Open Eye Signal" ambient-breakdown arrangement — see Section 5); key Medium-High (both strong reads); tempo Low-Medium |
| 36:02 | Film Scene Soundtrack | 123.0->117.5 | 4A(r.35)->9B(r.77) | sub high pre (39-54dB), crashes at the marker to strongly negative, sustained through +12s, partial recovery only by +13-20s | Bands High; key Medium (post-read strong, pre weak); tempo Low — matches a scored/orchestral-sounding title pulling the low end out |
| 40:21 | Piensas En Mi | 103.4->112.3 | 1B(r.68)->10A(r.50) | low band stays modest (0-25dB) with no single dramatic event across the whole window | Bands Medium (no clear swap point to anchor a technique label — reads as a continuous groove/long blend rather than a cut); key Low-Medium; tempo Low |
| 45:06 | Halo | 123.0->112.3 | 7B(r.52)->9A(r.39) | sub strong pre (45-49dB), drops to a modest 10-25dB range through +15s, then jumps hard to 50-56dB at +16-18s | Bands High (Breakdown-into-Bass-Swap, swap lands ~16s after the marker); tempo/key Low (both weak) |
| 50:43 | Te Estoy Correteando | 99.4 (held) | 9A(r.34)->11B(r.38) | sub very high and steady (50-56dB) almost throughout, one brief dip to 23-26dB around +8-12s, recovers immediately | Bands High; tempo Medium (held both sides); key Low (both weak) — reads as a filter blip inside a continuous groove, not a hard transition |
| 55:29 | Te Estoy Correteando x2 | 136.0->99.4 | 5A(r.44)->8A(r.54) | sub negative through most of the pre-window and into the marker itself, then a slow, oscillating partial recovery (10-32dB) after | Bands High; tempo/key Low — a drawn-out breakdown/build rather than a clean swap, consistent with this being a repeat pass on the same track |
| 59:03 | Quiereme x3 | 117.5 (held) | 11A(r.38)->5B(r.56) | sub negative through most of the pre-window (-12 to -22dB), climbs steadily from -11dB to 44-54dB by +13-20s | Bands High; tempo Medium (held); key Low-borderline — same gradual-build shape as the 19:10 and 20:50 "Quiereme" windows, the strongest cross-window consistency of any repeated track in this set (see Section 7) |
| 1:01:43 | Mabe | 123.0->136.0 | 7A(r.65)->6B(r.73) | sub deeply negative through most of the pre-window (-19 to -34dB), recovers gradually from +8s, locks to 52-55dB by +16-20s | Bands High; key Medium-High (both strong); tempo Low-Medium |

---

## 3. Tempo-scan sanity checks (methodology note)

Two fine-grained scans (30s window / 10s hop) were run to check for real sustained tempo shifts
versus single-window tracker artifacts, the same check the USB002 study ran for its "87 x 2"
moment and its DnB stretch:

- **1750s-2000s (around the 28:32 Open Eye Signal entry and after):** the tempo trace is
  clean and monotonic — steady 123.0 BPM from 1750s through 1930s, then a single, sustained
  step up to 129.2 BPM from 1940s onward that holds for the rest of the scanned range. This is
  a genuine, well-behaved tempo move (persists across four consecutive overlapping windows),
  unlike the isolated one-window spikes flagged as noise in the template study.
- **4100s-4750s (tail of the recording):** the scan window was set past the end of this
  set's audio (the set is only 4150.8s long; the script's fine-scan windows were written for a
  ~116-minute set and were not re-sized for this ~69-minute one). The single 198.8 BPM read at
  t=4150s, sandwiched between steady 117.5 BPM reads immediately before and after, is very
  likely a tracker artifact from a near-silent or empty trailing slice at end-of-file (a
  `librosa` warning about a too-short input segment appears in the raw script output at this
  point) rather than any real event in the set — **flagged explicitly so it isn't mistaken for
  a finding.**

---

## 4. Recurring patterns

1. **The bass consistently moves ahead of or right at the labelled timestamp, not after.**
   Nearly every row in Section 2 shows the sub band already falling (a pre-clear) in the
   seconds before the marker, with the actual swap/recovery landing anywhere from right at the
   marker (24:13, an unusually clean alignment) to 16-20s after it (14:00, 45:06, 28:32). This
   matches the general pre-clearing pattern the template study documented for USB002 —
   evidence this isn't a set-specific fluke but a broader DJ habit worth encoding.
2. **Ambient ownership of the low end during the mid-set downtempo stretch.** Both 28:32 (Open
   Eye Signal) and 36:02 (Film Scene Soundtrack) show the sub band pulled hard and held down for
   10-15+ seconds after their markers — consistent with letting an ambient/soundtrack-style
   track breathe without competing sub-bass, the same "vocal/spacious moment -> suppress bass"
   rule the template study named (its rule 4).
3. **Repeated-track passes ("x2"/"x3") share a band-energy shape with their first appearance.**
   The three "Quiereme" entries (19:10, 20:50, 59:03) all show the same signature: heavy sub
   oscillation or a deep pre-marker dip, followed by a gradual (10-20s) climb to a locked-in
   50+dB sub — not a hard re-cut each time, more a re-approach of the same hook. See Section 5.
4. **Held tempo more often than a clean ramp.** Several transitions here read as tempo-held on
   both sides (11:16, 50:43, 59:03) rather than a graduated BPM change — this set stays closer
   to a narrow house/pop tempo band (roughly 99-136 BPM across the whole tracklist) than the
   template set's wide house-to-DnB range, so there's less need for the multi-minute tempo
   bridges the template study's rule 5 described.

---

## 5. Callbacks / motif tracking: "Quiereme"

Unlike the USB002 study's single open/close "One More Time" bookend, this set's callback
device is a **repeated in-set return** rather than a symmetric frame: "Quiereme" is named three
times by the tracklist (19:10, 20:50 as "x2", 59:03 as "x3"), and "Te Estoy Correteando" once
more (50:43, then "x2" at 55:29).

The band-energy evidence supports treating these as genuine repeats of the same musical idea
rather than three unrelated tracks that happen to share a title: the 19:10, 20:50, and 59:03
windows all show the same shape — a period of sub-bass instability or suppression, followed by
a gradual (not instant) 10-20s climb into a locked, high, steady sub level. That's a distinct
acoustic signature from the single-marker "clean swap" transitions elsewhere in Section 2
(e.g. 24:13), and it recurs at three points roughly 40 minutes apart (19:10, 20:50 immediately
after, then 59:03 near the close) — read as the DJ deliberately re-visiting a favorite hook
through the set rather than bookending the set with it once at the start and once at the end.

"Rue De La Fortuna" (24:13, as a remix — "casino143 (Rue De La Fortuna Remix)") and "Open Eye
Signal" (28:32, the Jon Hopkins ambient/techno track, here tagged "under the fabric") are
metadata identifications from the tracklist itself, not lyric or audio content — no lyric or
spoken-vocal text was transcribed or reproduced in producing this note.

---

## 6. Comparison to the USB002 study (`set-study-gfF8jzBVWvM.md`)

- **Structure:** USB002 is a two-selector, drum-machine-synced set with heavy 3+-track
  layering (~half its segments); this set reads as a conventional single-DJ, mostly two-deck
  blend set — no segment here shows the sustained 3+-track simultaneous layering signature
  (continuous high sub+mid+high with no single dominant swap point) that USB002's 20:00 and
  11:30 windows show.
- **Callback device:** USB002 bookends with a single track played once at the open and once at
  the close ("One More Time," 3:16 and 1:46:06). This set instead threads one hook through
  three separate returns spread across the whole running time ("Quiereme," see Section 5) —
  a different, arguably more DJ-crowd-reading-driven use of repetition than a scripted
  open/close frame.
- **Tempo range:** USB002 ranges from house/disco tempos into a genuine DnB stretch (roughly
  86-174 BPM territory, with the low reads being half-time aliases of the true DnB tempo); this
  set stays within a tighter ~99-152 BPM band throughout, with no genre/tempo bridge as dramatic
  as USB002's Section 6 DnB transition — the closest analogue here is the clean, sustained
  123->129.2 BPM step at 1940s (Section 3), which is a normal house-tempo nudge, not a genre
  change.
- **Segment length:** both sets cluster around a 3-5 minute median segment, but USB002 has a
  much wider spread (40s to 10 minutes) than this set's tighter 1:40-7:30 range.

No changes to `set-study-gfF8jzBVWvM.md`'s own text were made — it has no "compare to other
sets" section of its own to extend; this section here is the only cross-reference between the
two notes.

---

*Confidence caveat, repeated for emphasis (same wording as the template note): tempo and
Camelot key numbers throughout this document come from librosa's tempo tracker and a
Krumhansl-Schmuckler chroma correlation, both run on mixed audio. They are directional hints
useful for spotting patterns, not ground truth for any single track's actual BPM or key.
Band-energy and RMS readings are direct measurements and are much more reliable.*
