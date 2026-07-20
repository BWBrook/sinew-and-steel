# AI Play Notes

This appendix sketches what the repository harness adds.

The previous chapter makes the case: an AI can act as Custodian, and Sinew & Steel is deliberately legible enough for that to work. These notes are for readers who want the repository path.

You can play S&S perfectly well with paper, dice, and people at a table. The harness exists for a different case: solo play, GM-less play, or long-running AI-assisted campaigns where memory, secrecy, and consequence tracking matter.

## The problem the harness solves

![](../../assets/art/ss_public_private_notes.png){.wrap-right width=1.6in}

A plain chat window can run a scene. It can describe a torchlit door, voice a suspicious hunter, and put choices on the table. Its memory becomes less reliable three sessions later.

The harness gives the AI a spine.

- Character sheets live in structured files.
- Pressure, clocks, and campaign state can be updated explicitly.
- Public narration and private Custodian notes stay separate.
- The last Custodian response can be checkpointed for clean resumes.
- Prompt builders can reload the right rules, skin, scenario, and current state.

That structure keeps consequences alive between sessions.

## Two modes, one game

There are two broad ways to use an AI Custodian.

**In simple chat play**, you give the AI the relevant rules and tell it to act as Custodian. You roll dice yourself, keep a light note of current Stamina and Luck, and correct drift when it appears. This is fast, loose, and good for one-shots, experiments, and casual solo play.

**In harness play**, the AI works inside the repository. The rules, skins, sheets, trackers, and campaign memory are files. The agent can build prompts, update sheets, tick clocks, record logs, and resume from a checkpoint. This is slower to set up, but much better for campaigns where consequences should accumulate.

Both are Sinew & Steel. They differ in how much memory the table wants the machinery to carry.

## Secrets need a private place

A shared channel makes every AI message public. This matters more than any prompt trick.

A human Custodian also keeps notes behind the screen. The harness makes that boundary explicit. Hidden scenario notes, unseen clocks, and private consequences belong in files or a private Custodian channel. Player-facing narration should contain only what the characters could plausibly perceive.

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

That last step is where the harness earns its keep. A spent Luck token, a ticked Shadow track, a broken spear, a suspicious NPC, or a sealed passage must carry into the next beat. The harness does the carrying.

## Dice and trust

Dice should sit outside whatever the AI thinks would make a satisfying story.

Use physical dice, a trusted roller, or a local tool. Surface the roll, the margin, and any Luck-spend offer plainly. Once the result is known, let the fiction answer it. Let bad rolls keep their edge.

S&S works because consequence is light enough to track and sharp enough to matter.

## What the harness feels like in play

During play, the harness should disappear.

The player sees a scene, makes a choice, rolls when it matters, and watches the world respond. Behind the screen, the AI has more to lean on than a bare chat: the current character sheet, the private scenario notes, the pressure clocks, the last checkpoint, and the campaign log.

That gives AI play a different texture from an oracle table. The world can surprise you, but it can also remember you.

## Where the tool details live

AI is an optional, supported mode. Sinew & Steel remains a tabletop game.

The repository documentation contains the exact commands and workflow. Start with:

`docs/ai_play_harness.md`

At a paper table, keep the core advice: preserve secrets, roll only when it matters, state stakes, and record what changed.
