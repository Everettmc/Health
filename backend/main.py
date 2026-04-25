import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import date
from typing import Any, Dict, List, Optional

import anthropic
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ai_engine import HEALTH_COACH_SYSTEM, calculate_trends, generate_daily_suggestions
from ai_engine import _format_sleep_table, _format_metrics_table
from apple_health import parse_apple_health_export
from database import (
    batch_upsert_metrics,
    get_health_metrics,
    get_latest_suggestion,
    get_setting,
    get_sleep_sessions,
    get_suggestions,
    init_db,
    save_suggestions,
    set_setting,
    upsert_health_metric,
    upsert_sleep_session,
)
from eight_sleep import EightSleepClient

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Health Dashboard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ──────────────────────────────────────────────────────────────────


class EightSleepCredentials(BaseModel):
    email: str
    password: str


class ManualMetric(BaseModel):
    date: str
    metric_type: str
    value: float
    unit: Optional[str] = ""
    source: Optional[str] = "manual"


class SettingUpdate(BaseModel):
    value: str


class SuggestionsRequest(BaseModel):
    user_context: Optional[str] = None


# ── Background helpers ───────────────────────────────────────────────────────


async def _sync_eight_sleep_bg(email: str, password: str):
    client = EightSleepClient(email, password)
    try:
        sessions = await client.get_sleep_sessions(days=30)
        for s in sessions:
            await upsert_sleep_session(s)
        logger.info(f"Synced {len(sessions)} Eight Sleep sessions")
    finally:
        await client.close()


# ── Routes ───────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# Eight Sleep sync
@app.post("/api/sync/eight-sleep")
async def sync_eight_sleep(
    credentials: Optional[EightSleepCredentials] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    email = (credentials.email if credentials else None) or await get_setting("eight_sleep_email") or os.getenv("EIGHT_SLEEP_EMAIL")
    password = (credentials.password if credentials else None) or await get_setting("eight_sleep_password") or os.getenv("EIGHT_SLEEP_PASSWORD")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Eight Sleep credentials not configured")

    # Save credentials for future use
    await set_setting("eight_sleep_email", email)
    await set_setting("eight_sleep_password", password)

    background_tasks.add_task(_sync_eight_sleep_bg, email, password)
    return {"status": "sync started", "message": "Eight Sleep data syncing in background"}


# Apple Health import
@app.post("/api/sync/apple-health")
async def sync_apple_health(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_ext = {".xml", ".zip"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail="File must be .xml or .zip")

    content = await file.read()
    metrics = parse_apple_health_export(content, file.filename)

    if not metrics:
        raise HTTPException(status_code=422, detail="No health data found in file")

    await batch_upsert_metrics(metrics)
    return {"status": "success", "imported": len(metrics), "message": f"Imported {len(metrics)} metrics from Apple Health"}


# Sleep data
@app.get("/api/sleep")
async def get_sleep(days: int = 30) -> List[Dict]:
    return await get_sleep_sessions(days=days)


# Health metrics
@app.get("/api/metrics")
async def get_metrics(days: int = 30, types: Optional[str] = None) -> List[Dict]:
    metric_types = types.split(",") if types else None
    return await get_health_metrics(days=days, metric_types=metric_types)


@app.post("/api/metrics/manual")
async def add_manual_metric(metric: ManualMetric):
    await upsert_health_metric(metric.model_dump())
    return {"status": "saved"}


# AI Suggestions
@app.get("/api/suggestions")
async def list_suggestions(days: int = 7) -> List[Dict]:
    return await get_suggestions(days=days)


@app.get("/api/suggestions/latest")
async def latest_suggestion() -> Dict:
    suggestion = await get_latest_suggestion()
    if not suggestion:
        raise HTTPException(status_code=404, detail="No suggestions found")
    return suggestion


@app.post("/api/suggestions/generate")
async def generate_suggestions(request: SuggestionsRequest = SuggestionsRequest()):
    sleep_sessions = await get_sleep_sessions(days=30)
    health_metrics = await get_health_metrics(days=30)

    suggestions = await generate_daily_suggestions(
        sleep_sessions=sleep_sessions,
        health_metrics=health_metrics,
        user_context=request.user_context,
    )

    await save_suggestions(str(date.today()), suggestions)
    return suggestions


@app.post("/api/suggestions/stream")
async def stream_suggestions(request: SuggestionsRequest = SuggestionsRequest()):
    sleep_sessions = await get_sleep_sessions(days=30)
    health_metrics = await get_health_metrics(days=30)

    async def event_generator():
        from datetime import datetime
        import re

        client = anthropic.Anthropic()
        trends = calculate_trends(sleep_sessions, health_metrics)
        today = datetime.now().strftime("%A, %B %d, %Y")

        user_message = f"""Today is {today}. Please analyze my health data and provide personalized recommendations.

## EIGHT SLEEP DATA — Last 30 Days
{_format_sleep_table(sleep_sessions)}

## HEALTH METRICS — Last 30 Days (Steps, HR, Workouts, etc.)
{_format_metrics_table(health_metrics)}

## COMPUTED TRENDS
**7-Day Averages:**
{json.dumps({k: v for k, v in trends["7_day"].items() if v is not None}, indent=2)}

**30-Day Baselines:**
{json.dumps({k: v for k, v in trends["30_day"].items() if v is not None}, indent=2)}

**Active Alerts:**
{chr(10).join(trends["alerts"]) if trends["alerts"] else "None — data looks healthy!"}

{f"Additional Context: {request.user_context}" if request.user_context else ""}

Analyze trends over the full period and provide specific, actionable recommendations.
Respond with valid JSON only — no markdown, no preamble."""

        full_text = ""
        try:
            with client.messages.stream(
                model="claude-opus-4-7",
                max_tokens=4096,
                thinking={"type": "adaptive"},
                output_config={"effort": "high"},
                system=[
                    {
                        "type": "text",
                        "text": HEALTH_COACH_SYSTEM,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_message}],
            ) as stream:
                for text in stream.text_stream:
                    full_text += text
                    yield f"data: {json.dumps({'chunk': text})}\n\n"

            # Parse and save the complete response
            json_match = re.search(r"\{[\s\S]*\}", full_text)
            if json_match:
                suggestions = json.loads(json_match.group())
                await save_suggestions(str(date.today()), suggestions)
                yield f"data: {json.dumps({'done': True, 'suggestions': suggestions})}\n\n"
            else:
                yield f"data: {json.dumps({'done': True, 'error': 'Could not parse JSON'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Dashboard — combined view
@app.get("/api/dashboard")
async def get_dashboard():
    sleep_sessions = await get_sleep_sessions(days=30)
    health_metrics = await get_health_metrics(days=30)
    latest = await get_latest_suggestion()
    trends = calculate_trends(sleep_sessions, health_metrics)

    # Today's sleep (most recent)
    today_sleep = sleep_sessions[0] if sleep_sessions else None

    # Today's metrics grouped by type
    today_str = str(date.today())
    today_metrics = {
        m["metric_type"]: m["value"]
        for m in health_metrics
        if m.get("date") == today_str
    }

    return {
        "today": {
            "date": today_str,
            "sleep": today_sleep,
            "metrics": today_metrics,
        },
        "trends": trends,
        "latest_suggestion": latest,
        "sleep_history": sleep_sessions[:14],
        "metrics_history": health_metrics,
    }


# Settings
@app.get("/api/settings/{key}")
async def get_setting_endpoint(key: str):
    value = await get_setting(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return {"key": key, "value": value}


@app.put("/api/settings/{key}")
async def update_setting(key: str, body: SettingUpdate):
    await set_setting(key, body.value)
    return {"key": key, "value": body.value}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
