"""Alexa handler registry for Treasure Village.

Thin wiring layer: request/intent handlers translate Alexa requests into
calls on `engine` (the pure quest state machine), format speech with
`speech`, and build the on-screen scene with `apl_builder`. All game
logic lives in `engine.py`, which has no dependency on this module.
"""
import logging
import os

from ask_sdk_core.dispatch_components import AbstractExceptionHandler, AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.utils import get_slot_value, is_intent_name, is_request_type
from ask_sdk_model import Response
from ask_sdk_model.interfaces.alexa.presentation.apl import RenderDocumentDirective
from ask_sdk_model.ui import SimpleCard
from ask_sdk_s3.adapter import S3Adapter

import apl_builder
import engine
import speech

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_QUEST_ID = "golden_acorn"
QUESTS = engine.load_quests()

SKILL_NAME = "Treasure Village"


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _load_state(handler_input: HandlerInput) -> engine.QuestState:
    attrs = handler_input.attributes_manager.persistent_attributes
    saved = attrs.get("quest_state")
    if saved:
        return engine.QuestState.from_dict(saved)
    return engine.new_state(DEFAULT_QUEST_ID)


def _save_state(handler_input: HandlerInput, state: engine.QuestState) -> None:
    handler_input.attributes_manager.persistent_attributes = {"quest_state": state.to_dict()}
    handler_input.attributes_manager.save_persistent_attributes()


def _current_quest(state: engine.QuestState) -> dict:
    return engine.get_quest(QUESTS, state.quest_id)


def _respond(handler_input: HandlerInput, speech_text: str, reprompt_text: str = None,
             apl_directive: dict = None, should_end_session: bool = None) -> Response:
    session_attrs = handler_input.attributes_manager.session_attributes
    session_attrs["last_speech"] = speech_text
    session_attrs["last_reprompt"] = reprompt_text
    handler_input.attributes_manager.session_attributes = session_attrs

    builder = handler_input.response_builder
    builder.speak(speech_text)
    builder.set_card(SimpleCard(SKILL_NAME, speech_text))
    if reprompt_text:
        builder.ask(reprompt_text)
    if apl_directive is not None:
        builder.add_directive(apl_directive)
    if should_end_session is not None:
        builder.set_should_end_session(should_end_session)
    return builder.response


def _stop_speech(quest: dict, stop: dict, state: engine.QuestState, intro: str = "") -> str:
    challenge = stop["challenge"]
    parts = [intro, stop["scene"], challenge["prompt"]]
    return speech.wrap_ssml(*parts)


def _stop_reprompt(stop: dict) -> str:
    challenge = stop["challenge"]
    if challenge["type"] == "move":
        return speech.wrap_ssml(challenge.get("waiting_prompt", challenge["prompt"]))
    return speech.wrap_ssml(challenge["prompt"])


def _apl_directive_for(handler_input: HandlerInput, stop: dict, state: engine.QuestState, quest: dict) -> RenderDocumentDirective | None:
    if not apl_builder.supports_apl(handler_input):
        return None
    directive = apl_builder.build_render_document_directive(
        stop, earned_count=len(state.earned_pieces), total_pieces=engine.total_stops(quest)
    )
    return RenderDocumentDirective(
        token=directive["token"], document=directive["document"], datasources=directive["datasources"]
    )


def _enter_stop_response(handler_input: HandlerInput, quest: dict, state: engine.QuestState, intro: str = "") -> Response:
    stop = engine.current_stop(quest, state)
    speech_text = _stop_speech(quest, stop, state, intro)
    reprompt_text = _stop_reprompt(stop)
    apl_directive = _apl_directive_for(handler_input, stop, state, quest)
    _save_state(handler_input, state)
    return _respond(handler_input, speech_text, reprompt_text, apl_directive)


def _finale_response(handler_input: HandlerInput, quest: dict, state: engine.QuestState) -> Response:
    speech_text = speech.wrap_ssml(
        speech.sound_tag("fanfare"),
        f"You found {quest['title']}! You solved every challenge across Treasure Village and earned all "
        f"{engine.total_stops(quest)} map pieces. What an adventure! Want to play again?",
    )
    reprompt_text = speech.wrap_ssml("Want to play again? You can say yes or no.")
    session_attrs = handler_input.attributes_manager.session_attributes
    session_attrs["awaiting_play_again"] = True
    handler_input.attributes_manager.session_attributes = session_attrs
    _save_state(handler_input, state)
    return _respond(handler_input, speech_text, reprompt_text)


# ---------------------------------------------------------------------------
# Launch / resume
# ---------------------------------------------------------------------------

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        state = _load_state(handler_input)
        quest = _current_quest(state)

        if state.completed:
            return _finale_response(handler_input, quest, state)

        if state.stop_index == 0 and state.misses == 0 and not state.earned_pieces:
            intro = speech.welcome_intro()
        else:
            title = engine.resume_stop_title(quest, state)
            intro = speech.join_fragments(speech.welcome_back_intro(), f"You were at {title}.")

        return _enter_stop_response(handler_input, quest, state, intro)


# ---------------------------------------------------------------------------
# Answer intents
# ---------------------------------------------------------------------------

def _handle_attempt(handler_input: HandlerInput, spoken) -> Response:
    state = _load_state(handler_input)
    quest = _current_quest(state)
    stop = engine.current_stop(quest, state)

    if stop is None:
        return _finale_response(handler_input, quest, state)

    if stop["challenge"]["type"] not in ("math", "riddle"):
        # A spoken answer during a move challenge isn't a miss; just nudge them along.
        reprompt_text = _stop_reprompt(stop)
        speech_text = speech.wrap_ssml(speech.move_waiting_line())
        return _respond(handler_input, speech_text, reprompt_text)

    result = engine.submit_answer(quest, state, spoken)

    if result.correct:
        intro = speech.join_fragments(speech.sound_tag("chime"), speech.praise(), speech.map_piece_cue(
            result.earned_piece_count, result.total_pieces))
    elif result.revealed:
        answer = stop["challenge"]["answer"]
        intro = speech.join_fragments(
            speech.reveal_intro(), f"The answer was {answer}.",
            speech.map_piece_cue(result.earned_piece_count, result.total_pieces),
        )
    else:
        _save_state(handler_input, state)
        speech_text = speech.wrap_ssml(speech.encouragement(), result.hint)
        reprompt_text = _stop_reprompt(stop)
        return _respond(handler_input, speech_text, reprompt_text)

    if result.quest_complete:
        return _finale_response(handler_input, quest, state)

    return _enter_stop_response(handler_input, quest, state, intro)


class AnswerNumberIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AnswerNumberIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        spoken = get_slot_value(handler_input=handler_input, slot_name="number")
        return _handle_attempt(handler_input, spoken)


class AnswerWordIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AnswerWordIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        spoken = get_slot_value(handler_input=handler_input, slot_name="answer")
        return _handle_attempt(handler_input, spoken)


class DoneIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("DoneIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        state = _load_state(handler_input)
        quest = _current_quest(state)
        stop = engine.current_stop(quest, state)

        if stop is None:
            return _finale_response(handler_input, quest, state)

        if stop["challenge"]["type"] != "move":
            # "Done" on a math/riddle stop: gently redirect them to answer instead.
            speech_text = speech.wrap_ssml("Ooh, almost! First, tell me your answer.")
            return _respond(handler_input, speech_text, _stop_reprompt(stop))

        result = engine.complete_move_stop(quest, state)
        intro = speech.join_fragments(
            speech.sound_tag("chime"), speech.praise(),
            speech.map_piece_cue(result.earned_piece_count, result.total_pieces),
        )
        if result.quest_complete:
            return _finale_response(handler_input, quest, state)
        return _enter_stop_response(handler_input, quest, state, intro)


class HintIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("HintIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        state = _load_state(handler_input)
        quest = _current_quest(state)
        stop = engine.current_stop(quest, state)

        if stop is None:
            return _finale_response(handler_input, quest, state)

        hint = engine.hint_for_current_stop(quest, state)
        speech_text = speech.wrap_ssml(speech.encouragement(), hint) if hint else _stop_reprompt(stop)
        return _respond(handler_input, speech_text, _stop_reprompt(stop))


# ---------------------------------------------------------------------------
# Built-in intents
# ---------------------------------------------------------------------------

class RepeatIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.RepeatIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        session_attrs = handler_input.attributes_manager.session_attributes
        speech_text = session_attrs.get("last_speech") or speech.wrap_ssml(speech.welcome_back_intro())
        reprompt_text = session_attrs.get("last_reprompt")
        return _respond(handler_input, speech_text, reprompt_text)


class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        session_attrs = handler_input.attributes_manager.session_attributes
        if not session_attrs.get("awaiting_play_again"):
            return _respond(handler_input, speech.wrap_ssml("Okay!"), speech.wrap_ssml("What would you like to do?"))

        session_attrs["awaiting_play_again"] = False
        handler_input.attributes_manager.session_attributes = session_attrs

        state = engine.new_state(DEFAULT_QUEST_ID)
        quest = _current_quest(state)
        intro = speech.join_fragments(speech.sound_tag("drumroll"), "Yay, let's go on another adventure!")
        return _enter_stop_response(handler_input, quest, state, intro)


class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.NoIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        session_attrs = handler_input.attributes_manager.session_attributes
        if not session_attrs.get("awaiting_play_again"):
            return _respond(handler_input, speech.wrap_ssml("Okay!"), speech.wrap_ssml("What would you like to do?"))

        session_attrs["awaiting_play_again"] = False
        handler_input.attributes_manager.session_attributes = session_attrs

        speech_text = speech.wrap_ssml("Okay, thanks for playing Treasure Village! See you next time!")
        return _respond(handler_input, speech_text, should_end_session=True)


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        state = _load_state(handler_input)
        quest = _current_quest(state)
        stop = engine.current_stop(quest, state)
        speech_text = speech.wrap_ssml(
            "This is Treasure Village! Just say your answer out loud, or say 'hint' if you need help, "
            "or 'done' when you finish a move like stomping or spinning.",
            stop["challenge"]["prompt"] if stop else "",
        )
        reprompt_text = _stop_reprompt(stop) if stop else speech.wrap_ssml("What would you like to do?")
        return _respond(handler_input, speech_text, reprompt_text)


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.CancelIntent")(handler_input) or is_intent_name("AMAZON.StopIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        state = _load_state(handler_input)
        _save_state(handler_input, state)
        speech_text = speech.wrap_ssml("Bye for now, adventurer! Your map is saved, come back anytime!")
        return _respond(handler_input, speech_text, should_end_session=True)


class StartOverIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.StartOverIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        state = engine.new_state(DEFAULT_QUEST_ID)
        quest = _current_quest(state)
        intro = "Okay, starting a brand new adventure!"
        return _enter_stop_response(handler_input, quest, state, intro)


class FallbackIntentHandler(AbstractRequestHandler):
    """FallbackIntent is treated as an answer attempt, never a rebuff (see CLAUDE.md)."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return _handle_attempt(handler_input, None)


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        logger.exception("Unhandled exception in Treasure Village skill")
        speech_text = speech.wrap_ssml("Oops, a little magic hiccup! Let's try that again.")
        return _respond(handler_input, speech_text, speech_text)


# ---------------------------------------------------------------------------
# Skill builder
# ---------------------------------------------------------------------------

sb = CustomSkillBuilder(
    persistence_adapter=S3Adapter(bucket_name=os.environ.get("S3_PERSISTENCE_BUCKET"))
)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(AnswerNumberIntentHandler())
sb.add_request_handler(AnswerWordIntentHandler())
sb.add_request_handler(DoneIntentHandler())
sb.add_request_handler(HintIntentHandler())
sb.add_request_handler(RepeatIntentHandler())
sb.add_request_handler(YesIntentHandler())
sb.add_request_handler(NoIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(StartOverIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()
