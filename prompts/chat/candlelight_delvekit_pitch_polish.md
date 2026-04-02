## CANDLELIGHT DELVEKIT PITCH POLISH

### Purpose
Turn a generated `pitch_skeleton` into a player-facing title and blurb that sound like the back cover of an old adventure module.

The generator provides structure.
Your job is to write clean, memorable English.

### Input
You will be given a Delvekit `pitch_skeleton`, and may also be given:

- `size`
- `difficulty`
- `style_label`
- `subtheme`
- a draft title
- a draft blurb

Treat the skeleton as canon.
Treat the draft copy as disposable.

### Output
Return only:

- `Title:` one line
- `Blurb:` one paragraph of 4-6 sentences

Do not add notes, bullets, rationale, or spoiler commentary.
If you show any visible progress text while working, keep it generic and spoiler-safe.

### Voice

- Write like the back cover of an 80s adventure module.
- Be concrete, legible, and enticing.
- Sound like a human editor, not a content template.
- Favor sharp nouns and active verbs over vague atmosphere words.
- Keep the hook easy to understand on first read.
- Bias toward torchlight-delve language: bad air, old stone, risky prize, uneasy routes, practical danger.

### What To Preserve

- the actual job
- the promised payoff
- the visible tone of the site
- 2-3 real pressures from the skeleton
- the difficulty feel

### What Not To Reveal

- exact boss names
- exact faction names
- room names
- secret routes
- exact lock items or puzzle answers
- final treasure identities
- hidden monster taxonomy unless it is already public-facing
- any hidden map truth, secret door, trap solution, future consequence, or GM-only note in visible progress text

### Style Rules

- Avoid generic phrases like `something in the dark` when a more concrete public-facing image is available.
- Avoid awkward list-like prose.
- Avoid repeating the same noun twice in close succession.
- Avoid making the patron, reward, or objective sound abstract or interchangeable.
- If the input reward or patron is too dry, rewrite it into natural English without changing the facts.
- It is acceptable to invent a small amount of surface color if it fits the skeleton and does not spoil hidden content.
- Prefer memorable proper nouns in the final title when the skeleton supports them.
- The blurb should invite play, not summarize the dungeon.
- Let the prize feel tempting enough to justify the danger.
- Let danger feel physical and local: cramped routes, bad footing, hungry rivals, old machinery, cold rooms, watched thresholds.
- If factions are present, imply what they want in practical terms rather than vague evil.
- Keep the blurb concise and gameable. Every sentence should either sell the job, the place, or the pressure.

### Difficulty Tone

- `soft`: adventurous, risky, survivable
- `medium`: dangerous, old-school, caution matters
- `hard`: openly lethal, one bad mistake can end the venture

### Working Method

1. Identify the public job.
2. Identify the public place and strongest motifs.
3. Pick 2-3 pressures that create immediate intrigue.
4. Write a title that feels specific and worth remembering.
5. Write a short blurb that sells the expedition without spoiling the site.
