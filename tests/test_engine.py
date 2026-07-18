import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "lambda"))

import engine  # noqa: E402


@pytest.fixture()
def quests():
    return engine.load_quests()


@pytest.fixture()
def quest(quests):
    return engine.get_quest(quests, "golden_acorn")


def test_load_quests_has_golden_acorn(quests):
    assert "golden_acorn" in quests


def test_quest_has_six_stops(quest):
    assert engine.total_stops(quest) == 6
    stop_ids = [s["id"] for s in quest["stops"]]
    assert stop_ids == [
        "village_square",
        "bakery",
        "old_bridge",
        "whispering_woods",
        "sunny_beach",
        "treasure_cave",
    ]


def test_new_state_starts_at_first_stop(quest):
    state = engine.new_state("golden_acorn")
    assert state.stop_index == 0
    assert state.misses == 0
    assert state.earned_pieces == []
    assert not state.completed
    stop = engine.current_stop(quest, state)
    assert stop["id"] == "village_square"


def test_correct_math_answer_advances_and_earns_piece(quest):
    state = engine.new_state("golden_acorn")
    result = engine.submit_answer(quest, state, 5)
    assert result.correct
    assert not result.revealed
    assert result.stop_complete
    assert result.earned_piece_count == 1
    assert state.stop_index == 1
    assert state.earned_pieces == ["village_square"]
    assert state.misses == 0


def test_wrong_math_answer_gives_first_hint_without_advancing(quest):
    state = engine.new_state("golden_acorn")
    result = engine.submit_answer(quest, state, 99)
    assert not result.correct
    assert not result.revealed
    assert not result.stop_complete
    assert state.stop_index == 0
    assert state.misses == 1
    assert result.hint == quest["stops"][0]["challenge"]["hints"][0]


def test_second_wrong_answer_gives_second_hint(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 99)
    result = engine.submit_answer(quest, state, 99)
    assert state.misses == 2
    assert not result.stop_complete
    assert result.hint == quest["stops"][0]["challenge"]["hints"][1]


def test_third_wrong_answer_reveals_and_advances(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 99)
    engine.submit_answer(quest, state, 99)
    result = engine.submit_answer(quest, state, 99)
    assert not result.correct
    assert result.revealed
    assert result.stop_complete
    assert state.stop_index == 1
    assert state.misses == 0
    assert state.earned_pieces == ["village_square"]


def test_riddle_answer_case_insensitive_and_trims_whitespace(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 5)  # clear village_square first
    result = engine.submit_answer(quest, state, "  ChIcKeN  ")
    assert result.correct
    assert state.earned_pieces[-1] == "bakery"


def test_riddle_answer_accepts_synonym(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 5)
    result = engine.submit_answer(quest, state, "hen")
    assert result.correct


def test_riddle_answer_rejects_unrelated_word(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 5)
    result = engine.submit_answer(quest, state, "dog")
    assert not result.correct
    assert state.misses == 1


def test_non_numeric_speech_on_math_stop_is_a_miss_not_an_error(quest):
    state = engine.new_state("golden_acorn")
    result = engine.submit_answer(quest, state, "banana")
    assert not result.correct
    assert state.misses == 1


def test_submit_answer_rejects_move_stop(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 5)
    engine.submit_answer(quest, state, "chicken")
    assert engine.current_stop(quest, state)["id"] == "old_bridge"
    with pytest.raises(ValueError):
        engine.submit_answer(quest, state, "anything")


def test_complete_move_stop_advances(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 5)
    engine.submit_answer(quest, state, "chicken")
    assert engine.current_stop(quest, state)["id"] == "old_bridge"
    result = engine.complete_move_stop(quest, state)
    assert result.correct
    assert result.stop_complete
    assert state.earned_pieces[-1] == "old_bridge"
    assert engine.current_stop(quest, state)["id"] == "whispering_woods"


def test_complete_move_stop_rejects_non_move_stop(quest):
    state = engine.new_state("golden_acorn")
    with pytest.raises(ValueError):
        engine.complete_move_stop(quest, state)


def test_full_quest_completion(quest):
    state = engine.new_state("golden_acorn")
    answers = [5, "chicken", None, 7, "octopus", None]
    for stop_index, answer in enumerate(answers):
        stop = engine.current_stop(quest, state)
        assert stop is not None
        if stop["challenge"]["type"] == "move":
            result = engine.complete_move_stop(quest, state)
        else:
            result = engine.submit_answer(quest, state, answer)
        assert result.correct
    assert state.completed
    assert len(state.earned_pieces) == 6
    assert engine.current_stop(quest, state) is None


def test_submit_answer_after_completion_raises(quest):
    state = engine.new_state("golden_acorn")
    for answer in [5, "chicken", None, 7, "octopus", None]:
        stop = engine.current_stop(quest, state)
        if stop["challenge"]["type"] == "move":
            engine.complete_move_stop(quest, state)
        else:
            engine.submit_answer(quest, state, answer)
    with pytest.raises(ValueError):
        engine.submit_answer(quest, state, 1)


def test_state_round_trips_through_dict_for_persistence(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 99)  # one miss, for good measure
    saved = state.to_dict()
    restored = engine.QuestState.from_dict(saved)
    assert restored == state


def test_resume_stop_title_matches_current_stop(quest):
    state = engine.new_state("golden_acorn")
    assert engine.resume_stop_title(quest, state) == "Village Square"
    engine.submit_answer(quest, state, 5)
    assert engine.resume_stop_title(quest, state) == "The Bakery"


def test_hint_for_current_stop_returns_first_hint_before_any_miss(quest):
    state = engine.new_state("golden_acorn")
    assert engine.hint_for_current_stop(quest, state) == quest["stops"][0]["challenge"]["hints"][0]


def test_hint_for_current_stop_tracks_miss_count(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 99)
    assert engine.hint_for_current_stop(quest, state) == quest["stops"][0]["challenge"]["hints"][1]


def test_hint_for_current_stop_returns_waiting_prompt_on_move_stop(quest):
    state = engine.new_state("golden_acorn")
    engine.submit_answer(quest, state, 5)
    engine.submit_answer(quest, state, "chicken")
    stop = engine.current_stop(quest, state)
    assert stop["id"] == "old_bridge"
    assert engine.hint_for_current_stop(quest, state) == stop["challenge"]["waiting_prompt"]


def test_resume_stop_title_none_when_quest_complete(quest):
    state = engine.new_state("golden_acorn")
    for answer in [5, "chicken", None, 7, "octopus", None]:
        stop = engine.current_stop(quest, state)
        if stop["challenge"]["type"] == "move":
            engine.complete_move_stop(quest, state)
        else:
            engine.submit_answer(quest, state, answer)
    assert engine.resume_stop_title(quest, state) is None
