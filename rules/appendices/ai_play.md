# AI Play Notes

This appendix is not a tool manual.

The previous chapter makes the case: an AI can act as Custodian, and Sinew & Steel is deliberately legible enough for that to work. These notes explain what the repository harness adds for readers who want the repo path, without requiring anyone to play that way.

You can play S&S perfectly well with paper, dice, and people at a table. The harness exists for a different case: solo play, GM-less play, or long-running AI-assisted campaigns where memory, secrecy, and consequence tracking matter.

## The problem the harness solves

![](../../assets/art/ss_public_private_notes.png){.wrap-right width=1.6in}

A plain chat window can run a scene. It can describe a torchlit door, voice a suspicious hunter, and put choices on the table. What it does less reliably is remember everything that should matter three sessions later.

That is the first thing the harness does: it gives the AI a spine.

- Character sheets live in structured files.
- Pressure, clocks, and campaign state can be updated explicitly.
- Public narration and private Custodian notes stay separate.
- The last Custodian response can be checkpointed for clean resumes.
- Prompt builders can reload the right rules, skin, scenario, and current state.

The harness is not automation for its own sake. It is continuity with teeth.

## Two modes, one game

There are two broad ways to use an AI Custodian.

**In simple chat play**, you give the AI the relevant rules and tell it to act as Custodian. You roll dice yourself, keep a light note of current Stamina and Luck, and correct drift when it appears. This is fast, loose, and good for one-shots, experiments, and casual solo play.

**In harness play**, the AI works inside the repository. The rules, skins, sheets, trackers, and campaign memory are files. The agent can build prompts, update sheets, tick clocks, record logs, and resume from a checkpoint. This is slower to set up, but much better for campaigns where consequences should accumulate.

Both are Sinew & Steel. The difference is not rules; it is how much memory the table wants the machinery to carry.

## Secrets need a private place

There is one practical truth that matters more than any prompt trick: if players can see everything the AI says, secrets cannot live in that same channel.

This is not special to AI. A human Custodian also keeps notes behind the screen. The harness simply makes that boundary explicit. Hidden scenario notes, unseen clocks, and private consequences belong in files or a private Custodian channel. Player-facing narration should contain only what the characters could plausibly perceive.

If you want fair surprises, protect the information flow.

## The play loop that keeps pressure real

![](../../assets/art/ss_when_to_roll.png){.wrap-right width=1.6in}

AI Custodians behave better when the table insists on the same loop a good human Custodian would use:

1. Ask what the character is trying to do.
2. Clarify the method if it matters.
3. State the stakes before the roll.
4. Roll only if the outcome is uncertain and matters.
5. Apply the consequence immediately.
6. Record what changed.

That last step is where the harness earns its keep. A spent Luck token, a ticked Shadow track, a broken spear, a suspicious NPC, or a sealed passage must not evaporate because the context window moved on. It belongs in the next beat.

## Dice and trust

Dice should sit outside whatever the AI thinks would make a satisfying story.

Use physical dice, a trusted roller, or a local tool. Surface the roll, the margin, and any Luck-spend offer plainly. Once the result is known, let the fiction answer it. Do not ask the AI to rescue every bad roll with a softer twist.

S&S works because consequence is light enough to track and sharp enough to matter.

## What the harness feels like in play

At its best, harness-assisted play disappears.

The player sees a scene, makes a choice, rolls when it matters, and watches the world respond. Behind the screen, the AI has more to lean on than a bare chat: the current character sheet, the private scenario notes, the pressure clocks, the last checkpoint, and the campaign log.

That gives AI play a different texture from an oracle table. The world can surprise you, but it can also remember you.

## Where the tool details live

This book draws the line here: AI is optional, supported, and playable without turning Sinew & Steel into a prompt product.

If you are using the repository harness, the exact commands and workflow live in the repo documentation, not here. Start with:

`docs/ai_play_harness.md`

If you are not using the repository, keep the core advice and ignore the machinery: preserve secrets, roll only when it matters, state stakes, and record what changed.
