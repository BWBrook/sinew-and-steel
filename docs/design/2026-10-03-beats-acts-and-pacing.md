# Beats, acts and pacing

A design note for Barry's decision, 3 October 2026, by Fable.

Barry raised the problem while ruling on the external review: "In tabletop its
clear: a night of gaming. In interactive AI Custodian or other harness play, it's
not: a player might dip in and out for one exchange, or 10, or 100. There is no
session." He framed the answer too: play "naturally break[s] into scenes and acts",
like a 43-minute TV episode, though with "no neat 'episode' or 'session', just an
arc of undefined length".

## Where the rules count in sessions

- **Abilities and effects.** Totem Mark and Heroic Act are once per session; so
  are Stout-Heart, Vision Glass and several boons. One Twilight crisis result
  expires with "this session".
- **Custodian guidance.** Call one or two Luck tests "per dozen beats", and
  reconsider after two "this session". Allow one lethal trap and one or two boons
  per session.
- **Harness and playtests.** Telemetry runs by session (`session-close`), and the
  Luck reopen trigger is measured "by mid-session".

At a table a session is a sitting. In interactive play nothing marks one, so each
of these needs a unit an AI Custodian can see in the story itself.

## Proposal: beats, acts, sessions and arcs

- **Exchange:** one player message and the Custodian's reply.
- **Beat (a scene):** one situation with one open question. It ends when the
  question is answered, dropped or changed, or the story cuts to another place or
  time. A beat must change something, so do not slice scenes thin. It is
  *perilous* when failure could cost Stamina, a life or the goal, as now.
- **Act:** four to six beats, ending at a turn (a reveal, a reversal, a hard
  choice) or at a pause (camp, port, a safe bed).
- **Session:** a sitting at the table. In interactive play, two acts (about ten
  beats), closed at an act break. Once-per-session limits refresh there.
- **Arc:** the story, as long as it needs to be. An adventure-sized problem
  usually takes three to six acts.

A television hour runs a teaser and four or five acts of a handful of scenes each.
On this scale an S&S session is about half an episode, and an arc is the thread
that runs across episodes.

**Why a session is two acts, not one.** The Almanac already treats a session as
about a dozen beats ("one or two per dozen beats ... two this session"). A
one-act session would make Heroic Act and the other once-per-session powers twice
as frequent as at a table.

## Numbers to pace by

These are guidance for a Custodian, not quotas; the fiction decides. They rest on
two existing sources:
- **the rules:** a milestone every 3–4 perilous beats, and one or two Luck tests
  per dozen beats;
- **the engine atlas's pacing model:** a roll in 60% of beats, a rest every six
  beats, one Pressure tick in three beats, and one crisis per twenty beats.

| Unit | Size | Pace |
|---|---|---|
| Beat | 3–12 exchanges. A fight is one beat of 2–5 rounds. | Outside a fight, 0–3 rolls, with about 6 beats in 10 having a roll. About half the beats are perilous. Pressure ticks in about one beat in three. |
| Act | 4–6 beats | A turn at its end. At most one or two fights. One pause, when the fiction allows a short rest (+1 Luck, +1 Stamina). One or two Pressure ticks. |
| Session | Two acts, about 10 beats | About one milestone. One or two Luck tests. Once-per-session powers refresh. A crisis about every second session. |
| Arc | 3–6 acts, about 15–30 beats | Ends when its question is answered. Two to four milestones, one or two crises. |

What the numbers imply:

- **Milestones.** With half the beats perilous, a milestone every 3–4 perilous
  beats comes every 6–8 beats, so about once a session. Slicing scenes thin would
  speed advancement, which is why a beat must change something.
- **Luck.** In the atlas, a Luck-8 character who rolls in 60% of beats, rests
  every six beats and rescues misses by up to 3 still holds about 6 tokens after
  16 beats; the chance of being down to 1 is 3%. Measured at the end of the first act, the Luck trigger
  ("1 or fewer by mid-session") should rarely fire in ordinary play. If it fires
  routinely, that is a real signal.
- **Pressure.** At one tick in three beats, a crisis comes every 15–20 beats,
  about every second session. A bigger party ticks faster; the Almanac already
  says how to slow it.
- **The red line.** At that rate a window at step 4 lasts about three beats.
  Measure it in beats as well as rolls: a fixed roll count covers less of the
  story for four characters than for one.

## Interactive play: guidance for an AI Custodian

- **Coming back is not a boundary.** Time away does not end a beat, refresh a
  limit or grant a rest. Recap from the checkpoint in a line or two, then
  continue the beat.
- **Follow the story, not the message count.** One beat may span several returns,
  and one long return may cover ten beats. Mark beats and act breaks as the story
  makes them.
- **Check at each beat's end:**
  - Did the question move?
  - How many rolls did this beat take? More than three outside a fight is a
    stall: cut, escalate or resolve.
  - How many perilous beats since the last milestone?
  - How much Pressure has moved this act?
  - When did the last pause come?
- **One roll per exchange,** rarely more.
- **Close a session at the first act break after about ten beats.** Award any
  milestone first; in the harness, roster changes wait for that boundary.

## What would change if adopted

- **Rules.**
  - A short pacing section in the Almanac, with the definitions and the table.
  - One sentence where the rules mention sessions: "Without sittings, a session
    is two acts, about ten beats."
  - A paragraph on interactive pacing in AI as Custodian.
  - The Quickstart's "perilous beats (dangerous scenes)" stays, and the skins'
    "per session" wording stays.
- **Prompts.** A five-line pacing card in both prompt profiles.
- **Harness.**
  - Merge `scene` into `beat`: ending a beat starts the next scene and resets
    once-per-scene limits.
  - Add `beat --act-end`.
  - The summary reports by act, and can take the end of a session's first act as
    its midpoint. That would replace the current midpoint of half the last beat
    number.
  - Remind the agent to close the session after two acts.
- **Playtests.** A standard run is one session: two acts, 10–12 beats. Report
  red-line windows in beats and in rolls.

## Decisions for Barry

1. Adopt beat, act, session and arc as defined above?
2. A session in interactive play is two acts, about ten beats? The alternatives:
   - one act, which is simpler but doubles once-per-session powers;
   - a fixed beat count, which is mechanical but ignores the story's shape.
3. Accept the pacing table as Custodian guidance, not quotas?
4. Harness:
   - merge `scene` into `beat`;
   - record act breaks;
   - measure the playtest midpoint at the first act break instead of at half the
     last beat number?
5. Put the definitions and the table in the Almanac and the AI chapter, leaving
   the Quickstart unchanged?
