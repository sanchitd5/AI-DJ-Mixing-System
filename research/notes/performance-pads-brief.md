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

## Machine translation (design; nothing shipped yet)

Planned for a 4x4 pad grid (a draft `pads.js` exists outside the branch; see
Status):
- 16 pads, anything on them: three banks (user samples from /api/samples,
  vocal chops and drum hits cut from the clock deck's stems, 16 synthesized
  one-shots rendered once to buffers, so no bundled audio).
- Chops over a DJ bed: hits snap to the master beatgrid (1/16, 1/8, 1/4, or
  off); a tonal slice plays only if it is compatible with the master key, or
  becomes compatible with a shift of at most 2 semitones, else it is refused
  and the reason is shown.
- Live loops: record a 1, 2 or 4 bar pad phrase from a bar line and loop it
  in beat units, so it follows the grid.
- The bed stays in charge: pads sit ~6 dB under the measured deck level, duck
  (-9 dB tonal, -3 dB drums) while the deck's vocal sings, and are high-passed
  at 120 Hz while a deck owns the low end.

## Status: not shipped, and why

- PADS (item 1): stopped at the owner's wrap-up call. The pure core was
  drafted (grid and quantise math, key shift, gain / duck / sub rules, choke,
  note repeat, loop record, slicing, one-shot synthesis). Still missing: the
  index.html panel, pads.css, the node check, and a smoke load in the sim.
  Nobody has played it in a browser or listened to it. It misses the quality
  bar, so it stays off the branch.
- AUTO PADS (item 2): depends on item 1. The gates can be read through the
  Host port without touching the owned files: `autopilotState.active`,
  `.activeDeck`, `.fireAt` (the booked transition, in track time) and
  `.layering`, plus "both decks audible" and recent `ai-activity`. No FX
  budget exists in the app today.
- 909 + bass-synth jam layer (item 3): the BEAT GRID (sampler-deck.js) is
  already a 909-style drum layer. A bass synth under a playing deck breaks
  the one-sub-owner rule by design.
- Crowd reading: the app has no crowd signal (no camera, no room mic), so
  there is nothing to read.
