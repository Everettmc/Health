import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

EIGHT_SLEEP_API = "https://client-api.8slp.net/v1"


class EightSleepClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.user_id: Optional[str] = None
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def login(self) -> bool:
        try:
            response = await self.client.post(
                f"{EIGHT_SLEEP_API}/login",
                json={"email": self.email, "password": self.password},
                headers={"Content-Type": "application/json", "User-Agent": "eight_sleep/app"},
            )
            if response.status_code == 200:
                data = response.json()
                session = data.get("session", {})
                self.user_id = session.get("userId")
                self.token = session.get("token")
                return bool(self.user_id and self.token)
            logger.error(f"Eight Sleep login failed: {response.status_code} {response.text}")
            return False
        except Exception as e:
            logger.error(f"Eight Sleep login error: {e}")
            return False

    async def get_sleep_sessions(self, days: int = 30) -> List[Dict[str, Any]]:
        if not self.token:
            if not await self.login():
                return []

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        try:
            response = await self.client.get(
                f"{EIGHT_SLEEP_API}/users/{self.user_id}/intervals",
                params={
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d"),
                },
                headers={"Session-Token": self.token},
            )
            if response.status_code == 200:
                data = response.json()
                return self._parse_intervals(data.get("intervals", []))
            logger.error(f"Eight Sleep data fetch failed: {response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Eight Sleep fetch error: {e}")
            return []

    def _parse_intervals(self, intervals: List[Dict]) -> List[Dict]:
        sessions = []
        for interval in intervals:
            try:
                ts = interval.get("ts", "")
                session_date = ts[:10] if ts else ""
                if not session_date:
                    continue

                total_secs = interval.get("duration", 0) or 0

                session = {
                    "id": interval.get("id", f"unknown_{session_date}"),
                    "date": session_date,
                    "sleep_score": self._extract_score(interval),
                    "total_sleep_minutes": total_secs // 60 if total_secs else None,
                    "deep_sleep_minutes": self._extract_stage_minutes(interval, "deep"),
                    "rem_sleep_minutes": self._extract_stage_minutes(interval, "rem"),
                    "light_sleep_minutes": self._extract_stage_minutes(interval, "light"),
                    "awake_minutes": self._extract_stage_minutes(interval, "awake"),
                    "hrv_avg": self._extract_hrv(interval),
                    "respiratory_rate": self._extract_resp_rate(interval),
                    "bed_temp_delta": self._extract_temp(interval),
                    "toss_turns": interval.get("tossAndTurns"),
                }
                sessions.append(session)
            except Exception as e:
                logger.warning(f"Failed to parse interval: {e}")
        return sessions

    def _extract_score(self, interval: Dict) -> Optional[int]:
        score = interval.get("score")
        return int(score) if isinstance(score, (int, float)) else None

    def _extract_stage_minutes(self, interval: Dict, stage: str) -> Optional[int]:
        stages = interval.get("stages", []) or []
        total_secs = sum(s.get("duration", 0) for s in stages if s.get("stage") == stage)
        return total_secs // 60 if total_secs > 0 else None

    def _extract_hrv(self, interval: Dict) -> Optional[float]:
        fitness = interval.get("fitness") or {}
        hrv = fitness.get("hrv") or {}
        return hrv.get("avg")

    def _extract_resp_rate(self, interval: Dict) -> Optional[float]:
        rr = interval.get("respiratoryRate") or {}
        return rr.get("avg")

    def _extract_temp(self, interval: Dict) -> Optional[float]:
        td = interval.get("tempDelta") or {}
        return td.get("avg")

    async def close(self):
        await self.client.aclose()
