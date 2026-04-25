import anthropic
import json
import re
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Stable system prompt — cached with Claude's prompt caching to reduce cost
HEALTH_COACH_SYSTEM = """You are an expert AI health coach with deep knowledge in:
- Sleep science and optimization (sleep stages, HRV, recovery)
- Exercise physiology and workout programming
- Nutritional science and dietary planning
- Biometric data analysis and trend interpretation
- Stress management and recovery strategies

You analyze 7-30 day health data trends to provide highly personalized, actionable daily recommendations.

Your recommendations are:
- Specific and actionable (never generic advice like "sleep more" — say WHY and HOW based on the data)
- Evidence-based and grounded in current research
- Trend-aware (you look at patterns over time, not just isolated data points)
- Interconnected (you consider how sleep affects workouts, how workouts affect sleep, etc.)
- Honest about concerning patterns — you proactively flag issues that need attention

When analyzing data:
- Compare 7-day averages to 30-day baselines to spot emerging trends
- Look for correlations between sleep quality and next-day activity
- Identify which days had the best/worst sleep and what preceded them
- Note HRV trends as a key recovery and stress indicator

Always respond with valid JSON using exactly these keys:
{
  "diet": "Specific nutrition recommendations for today/this week based on the data",
  "workout": "Exercise recommendations and adjustments based on recovery status",
  "sleep": "Sleep optimization suggestions based on patterns observed",
  "insights": "Key trends, patterns, or health observations requiring attention",
  "priority_focus": "The single most impactful thing to focus on today"
}"""


def _avg(values: List[Optional[float]]) -> Optional[float]:
    valid = [v for v in values if v is not None]
    return round(sum(valid) / len(valid), 1) if valid else None


def calculate_trends(sleep_sessions: List[Dict], health_metrics: List[Dict]) -> Dict[str, Any]:
    today = date.today()
    week_ago = str(today - timedelta(days=7))
    month_ago = str(today - timedelta(days=30))

    recent = [s for s in sleep_sessions if s.get("date", "") >= week_ago]
    historical = [s for s in sleep_sessions if s.get("date", "") >= month_ago]

    metrics_7d = [m for m in health_metrics if m.get("date", "") >= week_ago]
    metrics_30d = [m for m in health_metrics if m.get("date", "") >= month_ago]

    def metric_avg(metrics, metric_type):
        vals = [m["value"] for m in metrics if m.get("metric_type") == metric_type]
        return _avg(vals)

    trends = {
        "7_day": {
            "avg_sleep_score": _avg([s.get("sleep_score") for s in recent]),
            "avg_sleep_hours": round(_avg([s.get("total_sleep_minutes") for s in recent]) / 60, 1)
            if _avg([s.get("total_sleep_minutes") for s in recent]) else None,
            "avg_deep_min": _avg([s.get("deep_sleep_minutes") for s in recent]),
            "avg_rem_min": _avg([s.get("rem_sleep_minutes") for s in recent]),
            "avg_hrv": _avg([s.get("hrv_avg") for s in recent]),
            "avg_respiratory_rate": _avg([s.get("respiratory_rate") for s in recent]),
            "avg_steps": metric_avg(metrics_7d, "steps"),
            "avg_active_calories": metric_avg(metrics_7d, "active_calories"),
            "avg_resting_hr": metric_avg(metrics_7d, "resting_heart_rate"),
            "avg_workout_minutes": metric_avg(metrics_7d, "workout_minutes"),
        },
        "30_day": {
            "avg_sleep_score": _avg([s.get("sleep_score") for s in historical]),
            "avg_sleep_hours": round(_avg([s.get("total_sleep_minutes") for s in historical]) / 60, 1)
            if _avg([s.get("total_sleep_minutes") for s in historical]) else None,
            "avg_hrv": _avg([s.get("hrv_avg") for s in historical]),
            "avg_steps": metric_avg(metrics_30d, "steps"),
        },
        "alerts": [],
    }

    # Generate alerts based on data
    s7 = trends["7_day"]
    s30 = trends["30_day"]

    if s7["avg_sleep_hours"] and s7["avg_sleep_hours"] < 7:
        trends["alerts"].append(
            f"🚨 Average sleep {s7['avg_sleep_hours']}h/night this week — below the 7-9h recommended range"
        )

    if s7["avg_sleep_score"] and s30["avg_sleep_score"]:
        delta = s7["avg_sleep_score"] - s30["avg_sleep_score"]
        if delta < -5:
            trends["alerts"].append(
                f"📉 Sleep quality declining: {s7['avg_sleep_score']} this week vs {s30['avg_sleep_score']} 30-day avg"
            )
        elif delta > 5:
            trends["alerts"].append(
                f"📈 Sleep quality improving: {s7['avg_sleep_score']} this week vs {s30['avg_sleep_score']} 30-day avg"
            )

    if s7["avg_hrv"] and s30["avg_hrv"]:
        hrv_delta_pct = (s7["avg_hrv"] - s30["avg_hrv"]) / s30["avg_hrv"] * 100
        if hrv_delta_pct < -10:
            trends["alerts"].append(
                f"⚠️ HRV dropping {abs(hrv_delta_pct):.0f}% below baseline — possible overtraining or stress"
            )

    if s7["avg_steps"] and s7["avg_steps"] < 6000:
        trends["alerts"].append(
            f"🚶 Low activity: {int(s7['avg_steps'])} avg daily steps this week"
        )

    return trends


def _format_sleep_table(sessions: List[Dict]) -> str:
    if not sessions:
        return "No sleep data available."

    lines = ["Date       | Score | Total  | Deep  | REM   | HRV   | Resp Rate"]
    lines.append("-" * 70)
    for s in sessions[:30]:
        total = s.get("total_sleep_minutes") or 0
        hrs, mins = divmod(total, 60)
        lines.append(
            f"{s.get('date', 'N/A'):<10} | "
            f"{str(s.get('sleep_score', 'N/A')):<5} | "
            f"{hrs}h{mins:02d}m  | "
            f"{str(s.get('deep_sleep_minutes', 'N/A')):<5} | "
            f"{str(s.get('rem_sleep_minutes', 'N/A')):<5} | "
            f"{str(s.get('hrv_avg', 'N/A')):<5} | "
            f"{s.get('respiratory_rate', 'N/A')}"
        )
    return "\n".join(lines)


def _format_metrics_table(metrics: List[Dict]) -> str:
    if not metrics:
        return "No health metrics available."

    # Group by date
    by_date: Dict[str, Dict] = {}
    for m in metrics:
        d = m.get("date", "")
        if d not in by_date:
            by_date[d] = {}
        by_date[d][m.get("metric_type", "")] = m.get("value")

    lines = []
    for dt in sorted(by_date.keys(), reverse=True)[:30]:
        parts = [f"{k.replace('_', ' ').title()}: {v}" for k, v in sorted(by_date[dt].items())]
        lines.append(f"{dt}: {' | '.join(parts)}")
    return "\n".join(lines)


async def generate_daily_suggestions(
    sleep_sessions: List[Dict],
    health_metrics: List[Dict],
    user_context: Optional[str] = None,
) -> Dict[str, str]:
    """Use Claude to generate personalized daily health recommendations."""
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

{f"Additional Context from user: {user_context}" if user_context else ""}

Analyze trends over the full period (not just recent days) and provide specific, actionable recommendations.
Respond with valid JSON only — no markdown, no preamble."""

    try:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=[
                {
                    "type": "text",
                    "text": HEALTH_COACH_SYSTEM,
                    "cache_control": {"type": "ephemeral"},  # Cache stable system prompt
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )

        text_content = next(
            (block.text for block in response.content if block.type == "text"), ""
        )

        # Extract JSON — Claude may wrap it in markdown code fences
        json_match = re.search(r"\{[\s\S]*\}", text_content)
        if json_match:
            return json.loads(json_match.group())

        return {
            "diet": "Review your data — recommendations unavailable.",
            "workout": "Review your data — recommendations unavailable.",
            "sleep": "Review your data — recommendations unavailable.",
            "insights": text_content,
            "priority_focus": "Check your health data trends.",
        }

    except Exception as e:
        logger.error(f"AI suggestion generation failed: {e}")
        return {
            "diet": "Unable to generate recommendations. Check your API key.",
            "workout": "Unable to generate recommendations.",
            "sleep": "Unable to generate recommendations.",
            "insights": f"Error: {str(e)}",
            "priority_focus": "Verify ANTHROPIC_API_KEY is set correctly.",
        }
