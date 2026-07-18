"""Quest state machine for Treasure Village.

Pure Python only — no Alexa/ask-sdk imports here, so this module can be
unit tested without any Alexa request/response scaffolding.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

DEFAULT_QUESTS_PATH = Path(__file__).parent / "data" / "quests.json"

MAX_MISSES_BEFORE_REVEAL = 3
CHALLENGE_TYPES = {"math", "riddle", "move"}


def load_quests(path: Path | str = DEFAULT_QUESTS_PATH) -> dict[str, dict[str, Any]]:
    """Load quests.json into a dict keyed by quest id."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {quest["id"]: quest for quest in data["quests"]}


def get_quest(quests: dict[str, dict[str, Any]], quest_id: str) -> dict[str, Any]:
    return quests[quest_id]


def total_stops(quest: dict[str, Any]) -> int:
    return len(quest["stops"])


def current_stop(quest: dict[str, Any], state: "QuestState") -> Optional[dict[str, Any]]:
    stops = quest["stops"]
    if state.stop_index >= len(stops):
        return None
    return stops[state.stop_index]


@dataclass
class QuestState:
    """Serializable progress for one player within one quest."""

    quest_id: str
    stop_index: int = 0
    misses: int = 0
    earned_pieces: list[str] = field(default_factory=list)
    completed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuestState":
        return cls(
            quest_id=data["quest_id"],
            stop_index=data.get("stop_index", 0),
            misses=data.get("misses", 0),
            earned_pieces=list(data.get("earned_pieces", [])),
            completed=data.get("completed", False),
        )


def new_state(quest_id: str) -> QuestState:
    return QuestState(quest_id=quest_id)


@dataclass
class AttemptResult:
    correct: bool
    revealed: bool
    hint: Optional[str]
    stop_complete: bool
    quest_complete: bool
    earned_piece_count: int
    total_pieces: int


def _normalize(text: str) -> str:
    return text.strip().lower()


def check_answer(stop: dict[str, Any], spoken: Any) -> bool:
    """Return True if `spoken` satisfies the stop's challenge.

    `move` challenges have no wrong answer — completion is signalled by
    calling `complete_move_stop` (driven by DoneIntent), not this function.
    """
    challenge = stop["challenge"]
    ctype = challenge["type"]

    if ctype == "math":
        try:
            return int(spoken) == int(challenge["answer"])
        except (TypeError, ValueError):
            return False

    if ctype == "riddle":
        if spoken is None:
            return False
        spoken_norm = _normalize(str(spoken))
        accepted = {_normalize(challenge["answer"])}
        accepted.update(_normalize(s) for s in challenge.get("synonyms", []))
        return spoken_norm in accepted

    if ctype == "move":
        return False

    raise ValueError(f"Unknown challenge type: {ctype!r}")


def _advance(quest: dict[str, Any], state: QuestState, stop: dict[str, Any]) -> None:
    state.earned_pieces.append(stop["id"])
    state.misses = 0
    state.stop_index += 1
    if state.stop_index >= total_stops(quest):
        state.completed = True


def _result(state: QuestState, quest: dict[str, Any], *, correct: bool, revealed: bool, hint: Optional[str]) -> AttemptResult:
    return AttemptResult(
        correct=correct,
        revealed=revealed,
        hint=hint,
        stop_complete=correct or revealed,
        quest_complete=state.completed,
        earned_piece_count=len(state.earned_pieces),
        total_pieces=total_stops(quest),
    )


def submit_answer(quest: dict[str, Any], state: QuestState, spoken: Any) -> AttemptResult:
    """Apply a spoken math/riddle answer against the current stop.

    Implements the failure ladder: 1st and 2nd misses return an
    increasingly direct hint without advancing; the 3rd miss reveals the
    answer and advances anyway, so progress is never blocked.
    """
    stop = current_stop(quest, state)
    if stop is None:
        raise ValueError("No current stop; quest already complete")
    if stop["challenge"]["type"] not in ("math", "riddle"):
        raise ValueError("current stop is not a math/riddle challenge")

    if check_answer(stop, spoken):
        _advance(quest, state, stop)
        return _result(state, quest, correct=True, revealed=False, hint=None)

    state.misses += 1
    if state.misses >= MAX_MISSES_BEFORE_REVEAL:
        _advance(quest, state, stop)
        return _result(state, quest, correct=False, revealed=True, hint=None)

    hints = stop["challenge"].get("hints", [])
    hint = hints[min(state.misses - 1, len(hints) - 1)] if hints else None
    return _result(state, quest, correct=False, revealed=False, hint=hint)


def complete_move_stop(quest: dict[str, Any], state: QuestState) -> AttemptResult:
    """Advance past a `move` challenge (triggered by DoneIntent)."""
    stop = current_stop(quest, state)
    if stop is None:
        raise ValueError("No current stop; quest already complete")
    if stop["challenge"]["type"] != "move":
        raise ValueError("current stop is not a move challenge")

    _advance(quest, state, stop)
    return _result(state, quest, correct=True, revealed=False, hint=None)


def hint_for_current_stop(quest: dict[str, Any], state: QuestState) -> Optional[str]:
    """A hint/reprompt for the current stop without mutating any counters.

    Used by HintIntent (asking for help isn't a missed attempt) and by
    reprompts on `move` stops, which return their waiting prompt instead.
    """
    stop = current_stop(quest, state)
    if stop is None:
        return None
    challenge = stop["challenge"]
    if challenge["type"] == "move":
        return challenge.get("waiting_prompt")
    hints = challenge.get("hints", [])
    if not hints:
        return None
    return hints[min(state.misses, len(hints) - 1)]


def resume_stop_title(quest: dict[str, Any], state: QuestState) -> Optional[str]:
    """Human-friendly title of the stop the player was on, for a resume greeting."""
    stop = current_stop(quest, state)
    if stop is None:
        return None
    return stop["apl"]["title"]
