#!/usr/bin/env python3
"""Regenerate the RIDDLE_ANSWERS custom slot type from lambda/data/quests.json.

Run this after adding or editing any `riddle` challenge so the interaction
model's answer/synonym list stays in sync with the quest content:

    python3 scripts/generate_interaction_model.py

Everything else in the interaction model (invocation name, built-in
intents, AnswerNumberIntent/DoneIntent/HintIntent samples) is hand-authored
and left untouched — only the RIDDLE_ANSWERS "types" entry is rewritten.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUESTS_PATH = ROOT / "lambda" / "data" / "quests.json"
MODEL_PATH = ROOT / "skill-package" / "interactionModels" / "custom" / "en-US.json"


def collect_riddle_values(quests_data: dict) -> list[dict]:
    seen = {}
    for quest in quests_data["quests"]:
        for stop in quest["stops"]:
            challenge = stop["challenge"]
            if challenge["type"] != "riddle":
                continue
            answer = challenge["answer"]
            synonyms = challenge.get("synonyms", [])
            seen[answer] = sorted(set(seen.get(answer, [])) | set(synonyms))

    return [
        {"id": answer, "name": {"value": answer, "synonyms": synonyms}}
        for answer, synonyms in sorted(seen.items())
    ]


def main() -> None:
    quests_data = json.loads(QUESTS_PATH.read_text(encoding="utf-8"))
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))

    riddle_values = collect_riddle_values(quests_data)

    types = model["interactionModel"]["languageModel"].setdefault("types", [])
    for type_entry in types:
        if type_entry["name"] == "RIDDLE_ANSWERS":
            type_entry["values"] = riddle_values
            break
    else:
        types.append({"name": "RIDDLE_ANSWERS", "values": riddle_values})

    MODEL_PATH.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(riddle_values)} RIDDLE_ANSWERS values to {MODEL_PATH}")


if __name__ == "__main__":
    main()
