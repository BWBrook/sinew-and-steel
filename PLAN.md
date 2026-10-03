# Plan

The living plan for Sinew & Steel, set by Barry on 1 October 2026 and recorded on the project board (thread 46, message 787). Finished work is in `CHANGELOG.md`. The old snapshot file is archived at `docs/archive/HANDOVER_2026-09-30.md` and is no longer maintained.

## Stages

1. **Cross-examine the prose-pass revision.** Done: Astra's review is `docs/reviews/2026-10-01-stage1-review.md`.
2. **Decide and implement engine changes with Barry.** Closed on 1 October 2026; decisions below. The evidence is the independent engine review (`docs/independent_engine/`), the engine atlas (`docs/engine_atlas.md`), and the Stage 1 review and Stage 2 engine check (`docs/reviews/`).
3. **Align the rules and chapters with those changes,** keeping the narrative voice the prose pass established. Fable implemented it on 1 October 2026; Astra reviewed and signed off the changes at `14b6544` on the same day. The changes are listed below.
4. **Overhaul the AI Custodian harness and supporting tools.** Done on 2 October 2026: Astra's implementation (`7f595b9`, handoff `docs/reviews/2026-10-01-stage4-harness.md`) and Fable's review and fixes (`79d4d38`, `docs/reviews/2026-10-02-stage4-review.md`), committed and pushed at Barry's direction.

Before the playtests, Barry commissioned an independent external review of the whole repository from GPT-6 Pro (brief: `docs/reviews/2026-10-02-external-review-brief.md`; report: `docs/reviews/2026-10-02-external-review.md`). It was triaged with Barry on 2 October 2026 and its repairs are done (below). Then come simulated playtests: AI-run sessions across several skins and party sizes, logged well enough to test the reopen triggers below. Barry's human sessions will add an indicative trickle ("more vibes than distributional probabilities"). Then the rules and writing are declared GOLD, and only then comes layout. Until then, every text change must still keep the Quickstart on exactly two facing pages.

## Stage 2 decisions

The engine numbers stay: damage, soak, margin steps, natural results, Luck, and the Twilight stance values. The atlas's older stance-tuning recommendation is superseded by the Stage 2 engine check. The decisions, all made on 1 October 2026:

- **Pressure steps add up,** as exhaustion does: everything at or below the current step applies while the track stays there. A one-test penalty fires once when the track first reaches or passes its step, and re-arms only after a crisis resets the track. If the track falls below that step, discard any unused penalty from it (Barry: "Discard the unused penalty"). Manual 8, Almanac 4.
- **Twilight combat positions** are declared at the start of each round and held for every attack and defence that round; the bonus and the drawback come as a bundle. Twilight skin.
- **Initiative:** unless the fiction settles who acts first, each side rolls a d20 once, at the start of the fight, and that order holds for the whole fight; each side chooses its own members' order every round. Manual 6, Emberfall.
- **Refund cap:** lowering scores below baseline pays back at most 8 build points in total. In Barry's words, it works "to further de-emphasise min-maxxing… Initial specialisation can only go so far, after that, milestones are required to get more extremes out of the characters, and the Custodian can ultimately overrule anything." A 16 with Stamina 9 now needs the pulp budget, and no attribute starts above 14 on the grim budget. The Almanac's Iron Brute was rebuilt to fit; every other sample build already did. Manual 2.2 and 2.4, Quickstart, Almanac Part I and the tone dial, Customisation; the ledger, generator and tests enforce it.
- **Pressure and party size:** Barry: "real play will sit somewhere in between, and can be 'tuned' [by] the Custodian if required." The Almanac now tells Custodians that a bigger party fills the fuse faster, and how to slow it: charge shared hazards once per beat for the whole party, or purge more generously.
- **Tolls fall on choices** (2 October 2026, during the Stage 4 review): Pressure tolls and step costs apply only to tests a character attempts, never to a defence or Deflection roll; step penalties still apply to those rolls. Barry: "It was never intended to be involuntarily sapped like that!" Manual 8, Almanac 4, the six skins with tolls, the manifest labels and the harness (the defender and Deflection toll flags are gone).

### Reopen triggers for the simulated playtests

- **Luck:** if characters routinely drop to 1 token or fewer by mid-session, revisit rest recovery.
- **Red line:** if step-4 windows routinely last more than a few rolls, revisit the step-4 effects.
- **Reading the triggers** (agreed with Barry, 2 October 2026): "routinely" means at least half of the eligible observations in a group of runs declared in advance; "a few" means more than 3 rolls made at step 4. Both flag a cause to investigate with Barry, not an automatic rule change. "Mid-session" means the end of a session's first act (adopted 3 October 2026, below), and red-line windows report the scenes they touch as well as their rolls. Censored windows are handled explicitly: one already past 3 rolls is a confirmed exceedance, and one still open below that is unresolved. Sparse flags call for more matched runs, not a rules change.

The playtest logs should record the attribute and method behind each roll, Pressure gains by source, Luck spent and recovered, and each crisis with its target.

## Stage 3 changes, signed off

Implemented by Fable on 1 October 2026, from the Stage 1 tally. Items marked "choice" took one reading where two were possible; Astra's review accepted these readings.

- **Emberfall teaching round:** states the round essentials (each able combatant acts once per round; defending uses no action). Choice: a lost intimidation contest lets the wolf hold its ground, with no extra action; on its turn it attacks Tarra or snatches the meat. Choice: the wolf's drag hook needs an attack won by a margin of 4 or more, not a successful dodge.
- **Emberfall and Custodian Notes:** the closing question applies only if play has not answered it; otherwise close on the question play created.
- **Quickstart:** "perilous beats (dangerous scenes)"; checked in both the full book and the standalone PDF.
- **The Custodian:** choice: the failure consequence is chosen before the roll, as part of the stated stakes. When two fit, name both, and if the roll fails let a d6 pick between them; the failure adds detail, not new costs.
- **The Adventurer:** thinking aloud is fine and only stalling costs time; a roll-free outcome needs no real chance of failure, or no interesting cost.
- **Almanac:** power creep is "kept in check", not stopped, and the d20 step is "on an ordinary roll"; 10 + stat is a rough character translation for 2d6 games, not a probability match.
- **Tipper rule (Manual 8, Almanac 4):** when no single action tipped the track, the Custodian names the character the fiction points to. A worked example in Almanac 4 (Free Traders' Strain) covers group gains, per-character next-test penalties (spent even when Advantage cancels them), discarding on recovery, no re-firing, crisis effects outlasting the reset, and Pressure gained during a crisis being wiped by it.
- **Free Traders:** a ship's drive fails when its own Hull Damage clock fills, so larger clocks work.
- **Twilight travel:** choice: a failed role test takes the role's own failure instead of the general travel Fatigue.
- **Twilight knacks:** Hope comes from your own pool and Dread lands on the company's track; neither comes from Companionship.
- **Twilight Healing Rest:** the undertakings table now clears Injury too.

Astra's closeout check passed all 31 tests and repository validation. Independent pricing checked 2,600 generated characters across all ten skins and four budgets, plus every published sample. The saved book and Quickstart assemblies match the current sources; PDF inspection confirms two standalone Quickstart pages and full-book pages 6-7. The older uncapped analyses are explicitly labelled historical pending Stage 4 refresh.

## Stage 4 implementation and review

Implemented on 1–2 October 2026. Detailed contracts, verification and remaining
Custodian judgments are in `docs/reviews/2026-10-01-stage4-harness.md`.

- Shared rules code, with executable book examples and automatic pricing of all
  20 skin samples. The Quickstart's two-page spread is a release check.
- Schema-2 Pressure state: party scope except personal Insanity in Mournful Shores;
  fired thresholds, per-character pending penalties, discard without re-arming,
  atomic crisis reset, and separate lasting effects.
- Immutable creation snapshots and replayable advancement entries. The pulp
  `[16,6,6,6,8]`, Stamina 9 example now retains its 1-point advancement charge
  when a 6 becomes 7 even though the capped creation price remains 12.
- Atomic campaign actions and receipts, deferred Luck decisions, attack/damage
  resolution, fixed side initiative, Twilight positions and optional Injury,
  manifest-defined resource bookkeeping, and explicit backed-up migration.
- Structured session logs and a descriptive summariser for the reopen triggers.
  Completed sessions are kept separate from unfinished or migrated partial
  histories; roster changes occur between logged sessions.
- Compact prompts, on-demand rules sections, stale-prompt checks, safe public
  exports, and updated CLI documentation/skills. Private campaigns remain in
  their existing format until explicitly migrated.
- Historical creation-economy scripts and outputs are labelled as uncapped;
  the expensive analyses have not been rerun.

Fable's review (2 October 2026, `docs/reviews/2026-10-02-stage4-review.md`) found
the core sound and fixed the defects at its edges. Defence and Deflection no longer
pay tolls (author ruling above), and Iron & Ruin's missing step 4 is restored as a
Custodian lever. Edge may exceed +2, top-tier magic can be marked `--no-nudge`, and
an opposed test uses a combatant's action. A session cannot close mid-combat, and a
new session carries open threads, NPCs and secrets. Read-only tools refuse torn
state until `play.py status` recovers it. Event IDs are case-insensitive and
session-bound. A milestone Luck raise leaves a full pool, and the playtest midpoint
no longer counts the scene after its beat. The documentation was audited command by
command. 158 tests pass. Follow-ups that were noted but not fixed are listed in the
review.

## External review (GPT-6 Pro), triaged 2 October 2026

The reviewer recommended keeping the numbers and repairing procedural gaps. Its
own enumerations against the rules code (1,127,357 creation allocations, 99,550
damage cases, 41,680 resolution and nudge cases, 23 sample prices) found no
discrepancy. Fable checked every finding against the code and text; all eleven
reproduced.

**Barry's decisions**
- **DriveThruRPG is out.** Its policy refuses products that include AI-generated
  text and products meant to elicit AI output. Barry: "I think it's pointless to
  ask them: they'll say no on principle." The aim is to reach players who want an
  AI-forward game, free and openly licensed, through channels such as GitHub
  releases, itch.io and his own site. The distribution strategy is parked for
  later; the licences (CC BY 4.0 text, MIT code) already fit it.
- **Names.** Sinew & Steel stays. The Whispers in the Fog skin shared its title
  with a horror video game, so on 3 October 2026 Barry renamed it Mournful Shores
  (no game, RPG or book by that title was found). Its internal ID and file name,
  `whispers_in_the_fog`, are unchanged so existing campaigns still load.
- **Rulings.** Unnudgeable magic: no one moves the caster's die, and the caster pays
  for no nudge on either die; a resister may nudge their own (Manual 3). A
  Free Traders misjump ticks Fuel +2 instead of +1. A pilot contest tie or double
  failure gives no one Advantage. A test a crisis demands pays no toll, and on
  3 October Barry extended that to a Luck test the Custodian calls for (Manual 8,
  Almanac 4; `check --crisis-test`, `check --luck-test`). The release package is to be decided after the text and harness
  are locked.
- All four nits accepted, and the README overhauled.

**Repairs done** (with tests; 169 pass)
- A failed Arcanum or Unspeakable rite records its crisis below 5
  (`pressure --crisis --forced`); summaries count forced and threshold crises.
- A test a pending crisis demands (Service Duct Blues' nanite alarm) rolls with
  `check --crisis-test`.
- Beast Bond beads pay for nudges (`settle --fund beast_bond`, which also carries
  Companionship), and a milestone reminds the Custodian to refill a bonded beast.
- A check that is a combatant's action (`--combat-action`) and `pass` get the
  turn-order, already-acted and 0-Stamina guards.
- Chat prompts default to both full books; a compact chat prompt tells the model
  not to invent missing procedures.
- Success-only Luck costs are set aside before nudging (`--success-luck-cost`).
- Every advancement change to Luck is logged.
- Read-only tools share the writers' lock.
- The hidden-notes chat template no longer promises secrecy.
- Defence rolls no longer carry the attacker's method; the summary reports Pressure
  gains by source and category.
- A dead or departed character retires between sessions (`play.py retire`).

**Playtest programme** (adopted, with Fable's two changes)
- Five sample skins (Clanfire, Rust & Domes, Candlelight Dungeons, Mournful
  Shores, Twilight of the Northlands) at party sizes 1, 2 and 4, two runs each
  (30 runs). The other five skins at sizes 1 and 4, one run each (10 runs).
- A pilot of three or four runs first, to test the procedure.
- A standard run is one session: two acts, 10-12 beats. At least one campaign
  continues across two or three sessions, to exercise carried Pressure,
  once-per-session refreshes and resuming (Astra, 3 October 2026).
- The Almanac 9 pacing numbers are illustrations, not targets: the Custodians are
  not steered towards them, and agreement with them is not validation.
- Each run records its conditions: rules commit, model, skin, roster, policies
  for Luck, rest and Pressure, and any manual interventions. A different model
  audits a sample of rulings. Ordinary and adversarial runs are kept apart.

**Sessions in interactive play** (adopted 3 October 2026). Barry: "In tabletop its
clear: a night of gaming. In interactive AI Custodian or other harness play, it's
not: a player might dip in and out for one exchange, or 10, or 100. There is no
session." Rules and metrics that count per session (limits, "mid-session", the
playtest triggers) need a beat-based definition, with a clear definition of a
beat and quantitative guidance for an AI Custodian who plays whenever the player
returns. Barry added that play breaks into scenes and acts like a TV episode, but
with "no neat 'episode' or 'session', just an arc of undefined length". Fable's
design note, `docs/design/2026-10-03-beats-acts-and-pacing.md`, was accepted with
all five decisions as proposed (Barry: "Your proposal for beats, acts, sessions
and arcs is accepted. It's excellent."):
- A beat is a scene; an act is four to six beats ending at a turn or a pause;
  without sittings, a session is two acts, about ten beats; an arc is the story.
- The pacing table is Custodian guidance, not quotas. It is Almanac 9, and AI as
  Custodian has a section on pacing without sessions; the Quickstart is unchanged.
- The harness merges `scene` into `beat` (ending a beat begins the next scene),
  records act breaks (`beat --act-end`) and reminds the agent to close a session
  after two acts. The summary reports by act, takes the end of the first act as
  the midpoint, and reports the scenes each red-line window touches. Both
  prompt templates carry a five-line pacing card.

**Later:** the distribution strategy, to keep ideating on but not start yet.
Barry: "It's going to be hugely important to get this strategy right." A start: GitHub Releases, a
free itch.io page and a small site as the hub, all at no or little cost; then
deeper and wider, including the RPG Discord communities Barry belongs to, where
links with a cover message are welcome if not spammy. Also later: a possible
browser-based client in which players connect their own model access (Barry
flagged ChatGPT sign-in changes from Dev Day 2026).

**The game's name** (3 October 2026). Barry: "I came up with Sinew & Steel a long
time ago when it was only a base game with a few of the earlier skins. But I'm not
sure how descriptive it is of the overall game anymore." The name is also in use
elsewhere: "Bloody Basic (Sinew & Steel Edition)" is a published fantasy RPG,
"Steel And Sinew" an unreleased Steam game, and "Sinew and Steel and What They
Told" a short story by Carrie Vaughn.

Barry's choice is **Hazardry**, an old word for playing at dice and taking risks.
Barry: "Hazardry: I'm really liking it. We can think of Sinew & Steel as the
alpha-development codename." No game uses the title, though "Hazard" names are
common in RPGs. The tagline is "Hazardry: a lean roleplaying game for the table,
and for any AI in the Custodian's chair." The book will quote Chaucer in his own
spelling; two candidate lines from the Pardoner's Tale (Harvard's Chaucer edition)
are "Now wol I yow deffenden hasardrye." and "Hasard is verray mooder of
lesynges,". Astra and Fable both prefer the first, which contains the title's
ancestor ("deffenden" means forbid), attributed to the Pardoner in Chaucer's tale.

Astra's review (board 837) supports Hazardry over both Sinew & Steel and Fuse &
Fortune and keeps the tagline. It adds that onboarding should state which models
the game needs, rather than imply that "any AI" has been tested.

Clearance check (Fable, 3 October 2026), with no conflict found:
- **The word:** only dictionaries use it (Merriam-Webster: obsolete, gambling;
  rashness).
- **Games:** no product called Hazardry on Steam, itch.io, DriveThruRPG or
  BoardGameGeek, though many titles begin "Hazard".
- **US trademarks:** the USPTO register returns no results for "hazardry". The
  IP Australia and EU searches need their search forms and were not run.
- **Domains:** hazardry.com has been registered since 2017 and shows a parking
  page, so it is probably for sale. hazardry.net, .org, .io and .games, and
  hazardryrpg.com, are unregistered.
- **GitHub:** a personal account "hazardry" exists, so the repository would become
  BWBrook/hazardry.

Social handles were not checked. Still to do: Barry's go-ahead, then the rename in
one pass. In the text it
is mechanical (about 90 mentions in 54 files, plus "S&S" shorthand, release file
names and the repository). The cover and logo need new lettering in the GOLD art
pass, and GitHub redirects a renamed repository.

Next: the clearance check and the rename to Hazardry, then the pilot and the
programme. Astra's review of the recent work (board 837) found three bounded
defects, now fixed: a retired name could be reused and overwrite its archived
sheet; an older receipt without a session could replay in a later session; and
red-line windows counted scene boundaries rather than the scenes they touched. Harness tests do
not replace those playtests or authorize GOLD and layout.
