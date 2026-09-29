# Anyma-style visual show: brief

What the console's SHOW mode (app/ui/static/anyma-show.js) tries to reproduce, and where each
rule comes from. Retrieved 2026-09-29. Tags: SOURCED = stated in a primary or first-party page,
SECONDARY = a review or trade article, GUESS = our reading of the style (or the owner's brief), not
stated anywhere we could fetch.

## Sources (retrieved 2026-09-29)

1. Sphere, "Afterlife presents Anyma: The End of Genesys": https://www.thesphere.com/shows/afterlife-presents-anyma
2. Sphere Entertainment Co. residency page: https://www.sphereentertainmentco.com/afterlife-presents-anyma-the-end-of-genesys-residency/
3. Alessio De Vecchi (visual co-creative director), portfolio: https://alessiodevecchi.com/seeds/portfolio
4. V Magazine, "The End Of Genesys: A Conversation with Anyma": https://vmagazine.com/article/the-end-of-genesys-a-conversation-with-anyma/
5. Magnetic Magazine, Sphere residency review (Jan 2025): https://magneticmag.com/2025/01/anyma-sphere-residency-event-review/
6. Y.M.Cinema, "The Making of Anyma's The End of Genesys": https://ymcinema.com/2025/01/30/the-making-of-anymas-the-end-of-genesys-at-the-las-vegas-sphere-a-groundbreaking-fusion-of-music-and-technology/
7. Brompton Technology, Genesys Melbourne screen case study: https://www.bromptontech.com/case-study/creating-australias-largest-entertainment-led-screen-for-anymas-genesys/
8. Flaunt, "Anyma's The End of Genesys": https://www.flaunt.com/post/anymas-the-end-of-genesys-musical-live-experience-sphere-las-vegas
9. The Groove Cartel, Sphere performance write-up: https://thegroovecartel.com/news/the-end-of-genesys-inside-anymas-revolutionary-performance-at-the-sphere/
10. Wikipedia, "Anyma": https://en.wikipedia.org/wiki/Anyma

Not read: Billboard's review (bot redirect), Rolling Stone (not fetched), any show footage (no video
access here). Everything about motion below is therefore a reading of text, not of footage.

## Subjects

- A humanoid android is the centre of the show: EVA, "a sculpted, robotic, hauntingly human form
  rendered in CGI", "part sculpture, part machine, part mirror" (3). SOURCED.
- A small cast of characters (EVA, ADAM, LILITH, SYREN), "robotic humanoids caught between
  mechanical precision and raw emotional vulnerability" (3). SOURCED.
  -> Scenes HEAD (a face made of particles) and FIGURE (a body drawn in lines of light).
- "Massive humanlike androids", space portraits, nature fused with technology (1, 8); "humanoid figures
  writhing in unison to the music" (1). SOURCED.
- EVA "pounding on the metaphorical glass walls of the Sphere until they shattered, coinciding with a
  thunderous drop"; "a thousand blinking eyes"; "two towering robots embrace"; a "bright-white
  celestial kingdom" (5). SECONDARY.
  -> the drop is a break: hard cut + a shatter of the figure into particles.
- Abstract geometric patterns evolving into cybernetic environments; geometry that accelerates in
  builds and climaxes (9). SECONDARY.
  -> Scenes MONOLITH (a slab in black space) and CORRIDOR (frames rushing at the camera).

## Palette

- No source gives colour values. Reviews say "bright-white" (5) and "biomechanical" (6).
- Black stage, white / cyan / ice-blue primary light, rare red accents: GUESS (the owner's brief and
  the look of the stills, not stated in text we fetched). Used as the rule anyway: black is the
  default, colour is a highlight, red only on a supermove.

## Motion language

- Slow, monumental: huge figures, slow camera, long holds. GUESS from "massive", "towering",
  "building scale" (1, 3, 5).
- Break into fast cuts on drops: the shattering-glass moment is on "a thunderous drop" (5).
  SECONDARY. Cut timing itself is a GUESS.
- Particle dissolves between states: GUESS (the brief). Implemented as the transition between every
  scene (outgoing dissolves outward, incoming assembles from dust).

## How visuals follow the music

- "Every track was written specifically for a scene"; the show should "feel alive, reactive" (4,
  Anyma quoted). SOURCED.
- Sphere visuals "responded to the music in real time", sync by timecode (Disguise) (6). SECONDARY.
- Build: geometry accelerates (9, SECONDARY) -> camera pushes in, corridor speeds up.
- Drop: shatter + hit on the drop (5, SECONDARY) -> hard cut to a new scene, one flash, camera cut.
- Breakdown / reflective: "a sensation of endless space" (9, SECONDARY) -> wide, dim, slow.
- Vocal: each character "has a theme... the Syren has her song, the Eva her AI robotic voice" (4,
  SOURCED) -> the face speaks: HEAD scene preferred while vocals are active, eyes lit by the vocal
  band.

## Transitions between scenes

- Acts with separate themes (organic -> skin / human -> accelerating technology -> white "quantum"),
  (9, SECONDARY). Our set has no acts, so a scene lasts at least 2 phrases (16 bars) and changes only
  on a phrase boundary, a drop or a track transition (GUESS, chosen for legibility).
- Track transition in the mix -> long particle dissolve across the blend (GUESS).

## Production context (not reproduced)

- Unreal Engine 5, Notch, TouchDesigner, Houdini, Disguise timecode (6), SECONDARY. Pixera media server,
  40.2 m x 19.2 m LED wall in Melbourne (7), SOURCED. We have one browser canvas, raw WebGL, and
  everything procedural: no Anyma logos, footage, characters or models are copied.
