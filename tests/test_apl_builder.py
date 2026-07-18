import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lambda"))

import apl_builder  # noqa: E402
import engine  # noqa: E402


def test_build_scene_datasource_marks_filled_pieces():
    quest = engine.get_quest(engine.load_quests(), "golden_acorn")
    stop = quest["stops"][0]
    datasource = apl_builder.build_scene_datasource(stop, earned_count=2, total_pieces=6)
    pieces = datasource["sceneData"]["properties"]["pieces"]
    assert len(pieces) == 6
    assert [p["filled"] for p in pieces] == [True, True, False, False, False, False]


def test_build_render_document_directive_embeds_scene_and_stop_data():
    quest = engine.get_quest(engine.load_quests(), "golden_acorn")
    stop = quest["stops"][0]
    directive = apl_builder.build_render_document_directive(stop, earned_count=0, total_pieces=6)
    assert directive["type"] == "Alexa.Presentation.APL.RenderDocument"
    assert directive["document"]["type"] == "APL"
    props = directive["datasources"]["sceneData"]["properties"]
    assert props["emoji"] == stop["apl"]["emoji"]
    assert props["title"] == stop["apl"]["title"]
    assert props["background"]["colorRange"] == stop["apl"]["bg"]
