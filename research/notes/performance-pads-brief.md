# Performance pads brief (Fred again.. style)

Question: how does Fred again.. actually play pads live, and which part of that
can the console do honestly? Retrieved 2026-09-29. Tags: SOURCED (first-party
quote or a publication reporting what he said or did on camera), SECONDARY
(publication describing his setup in its own words), GUESS (no source found).

## What he does

| Claim | Tag | Source |
|---|---|---|
| He calls Maschine "like an MPC but a modern one... essentially it's 16 drum pads. You can put anything on it" | SOURCED | MusicTech, Ben Rogerson, 28 Oct 2022, https://musictech.com/news/fred-again-zane-lowe-native-instruments-maschine-live-set/ |
| "You can play anything on it, like, it's so infinitely powerful" (Maschine, Apple Music / Zane Lowe) | SOURCED | MusicRadar, Sam Willings, 27 Oct 2022, https://www.musicradar.com/news/fred-again-maschine-brian-eno |
| Boiler Room London (2022): Maschine+ next to three Pioneer CDJs and a DJM mixer, i.e. pads played over DJ decks | SECONDARY | MusicRadar (same article); SonicState, 11 Aug 2022, https://sonicstate.com/news/2022/08/11/fred-again-hybrid-set-for-boiler-room/ ("using a NI Maschine to play tracks live as well as playing some of his own remixes") |
| Voice memos / interview audio cut into short fragments and rhythmically reorganised | SECONDARY | gearnews, Marcus Schmahl, 12 Mar 2026, https://www.gearnews.com/fred-again-gear-sound-synths/ (author-written, no Fred quote) |
| Ableton Push 3 pads for samples, drum racks, melodic parts, "played like instruments" | SECONDARY | gearnews (same) |
| Beat building on an MPC for Zane Lowe | SECONDARY | Rolling Stone, https://www.rollingstone.com/music/music-news/fred-again-wows-zane-lowe-mpc-new-interview-1234618577/ (search snippet only) |
| Loops 2-bar vocal phrases, layering hats over repetition | SECONDARY | KB note DJ/13 Fred again.. Case Study (prior research, Tape Notes episodes) |
| Octatrack in his live rig | GUESS | no source found; not used as a design input |
| "USB" sets use pads the same way | GUESS | only the tour/series name surfaced; nothing on pad use |

## Machine translation (what ships)

- 16 pads, anything on them: 4x4 grid with three banks (user samples, slices
  cut from the playing deck's stems, the synth one-shots).
- Chops played over a DJ bed: slices come from the live deck's vocal and
  drum stems, quantised to the master beatgrid (1/16, 1/8, 1/4, off), key
  checked against the master and pitched at most 2 semitones, else refused.
- Short phrase looped live: per-pad-phrase loop record of 1/2/4 bars locked to
  the grid (beat positions, so it follows tempo changes).
- The bed stays in charge: pads duck ~6 dB while the deck's vocal sings, are
  high-passed at 120 Hz while a deck plays (one sub owner), and sit ~6 dB
  under the measured programme level.

## Not shipped and why

- AUTO PADS (AI plays a chop phrase): the gates that matter (transition in
  progress, merge hold, FX budget) live in dj-mind.js / autopilot.js state,
  which this work may not edit, and nothing exposes them as events. Without
  those gates it would fire over transitions. Needs a Host-port hook first.
- 909 + bass-synth jam layer: the beat grid (sampler-deck.js) already is the
  909-style drum layer; a bass synth under a playing deck breaks the single
  sub-owner rule by construction.
- Crowd reading: the app has no crowd signal (no camera, no mic of the room).
