"""Builds the APL RenderDocument directive + datasource for a quest stop.

Pure Python — no ask-sdk imports. `lambda_function.py` only calls this
after checking `Alexa.Presentation.APL` is in the request's
`supportedInterfaces`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCENE_DOCUMENT_PATH = Path(__file__).parent / "apl" / "scene.json"
GRADIENT_ANGLE = 135

_scene_document: dict[str, Any] | None = None


def _load_scene_document() -> dict[str, Any]:
    global _scene_document
    if _scene_document is None:
        with open(SCENE_DOCUMENT_PATH, "r", encoding="utf-8") as f:
            _scene_document = json.load(f)
    return _scene_document


def build_scene_datasource(stop: dict[str, Any], earned_count: int, total_pieces: int) -> dict[str, Any]:
    apl = stop["apl"]
    pieces = [{"filled": i < earned_count} for i in range(total_pieces)]
    return {
        "sceneData": {
            "type": "object",
            "objectId": "sceneData",
            "properties": {
                "background": {
                    "type": "linear",
                    "colorRange": apl["bg"],
                    "angle": GRADIENT_ANGLE,
                },
                "emoji": apl["emoji"],
                "title": apl["title"],
                "pieces": pieces,
            },
        }
    }


def build_render_document_directive(stop: dict[str, Any], earned_count: int, total_pieces: int) -> dict[str, Any]:
    return {
        "type": "Alexa.Presentation.APL.RenderDocument",
        "token": "treasureVillageScene",
        "document": _load_scene_document(),
        "datasources": build_scene_datasource(stop, earned_count, total_pieces),
    }


def supports_apl(handler_input: Any) -> bool:
    from ask_sdk_core.utils import get_supported_interfaces

    return get_supported_interfaces(handler_input).alexa_presentation_apl is not None
