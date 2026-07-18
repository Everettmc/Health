"""SSML and voice-line builders for Treasure Village.

Pure Python — no ask-sdk imports. Keeps every spoken line in one place so
tone stays warm and silly, and the failure ladder never says "wrong" or
"no" anywhere in the skill.
"""
from __future__ import annotations

import random

PRAISE_LINES = [
    "Wow, you got it!",
    "Yes! High five!",
    "You're a treasure-hunting superstar!",
    "Amazing job!",
    "Woo-hoo, nailed it!",
]

ENCOURAGEMENT_LINES = [
    "Ooh, so close! Let's try again.",
    "Good try! Here's a little help.",
    "Almost! You can totally do this.",
    "Nice thinking! One more try.",
]

REVEAL_INTROS = [
    "That's okay, adventurers help each other out!",
    "No worries, let's peek at the answer together!",
    "Here, I'll share a secret with you!",
]

WELCOME_INTROS = [
    "Hooray, an adventurer!",
    "Welcome to Treasure Village!",
]

WELCOME_BACK_INTROS = [
    "Welcome back, adventurer!",
    "Yay, you're back!",
    "Ready to keep exploring?",
]

MOVE_WAITING_LINES = [
    "Take your time, I'll wait right here!",
    "You've got this, keep going!",
    "I'm cheering you on!",
]

# Sound Library tokens are best-effort placeholders. Alexa validates
# soundbank:// paths against its live catalog, so verify each token in the
# Developer Console's Sound Library browser (or with `ask dialog`) during
# the deploy smoke test before shipping — an unverified token can make an
# otherwise-correct response fail. Swap any that don't resolve.
SOUND_EFFECTS = {
    "chime": "soundbank://soundlibrary/musical/amzn_sfx_movie_bell_02",
    "drumroll": "soundbank://soundlibrary/musical/amzn_sfx_drum_roll_01",
    "fanfare": "soundbank://soundlibrary/musical/amzn_sfx_trumpet_fanfare_01",
}

# Flip on only after verifying the tokens above against the live Sound
# Library — keeps the skill safe to deploy out of the box.
SOUND_EFFECTS_ENABLED = False


def praise() -> str:
    return random.choice(PRAISE_LINES)


def encouragement() -> str:
    return random.choice(ENCOURAGEMENT_LINES)


def reveal_intro() -> str:
    return random.choice(REVEAL_INTROS)


def welcome_intro() -> str:
    return random.choice(WELCOME_INTROS)


def welcome_back_intro() -> str:
    return random.choice(WELCOME_BACK_INTROS)


def move_waiting_line() -> str:
    return random.choice(MOVE_WAITING_LINES)


def map_piece_cue(earned: int, total: int) -> str:
    return f"You earned a map piece! That's {earned} of {total}!"


def sound_tag(name: str) -> str:
    """SSML <audio> tag for a named effect, or "" if effects are disabled."""
    if not SOUND_EFFECTS_ENABLED:
        return ""
    token = SOUND_EFFECTS.get(name)
    return f'<audio src="{token}"/>' if token else ""


def join_fragments(*parts: str) -> str:
    """Join speech fragments with a space, dropping empty ones.

    Use this (not `wrap_ssml`) when building a piece of speech that will
    be combined with more text later — only the final assembly should add
    the outer <speak> tag, since SSML doesn't allow nesting it.
    """
    return " ".join(p.strip() for p in parts if p and p.strip())


def wrap_ssml(*parts: str) -> str:
    return f"<speak>{join_fragments(*parts)}</speak>"
