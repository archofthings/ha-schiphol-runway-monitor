"""
DataUpdateCoordinator for Schiphol Runway Monitor.

Data source: dutchplanespotters.nl/runways/ams/
  - Fully server-rendered HTML (no JS execution needed)
  - Sourced from LVNL, updated every 5 minutes
  - Shows LANDING RWY / TAKEOFF RWY for the current moment at the top of the page
  - Also contains a full time-slot table as a reliable fallback
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    RUNWAYS,
    STATE_BOTH,
    STATE_INBOUND,
    STATE_NOT_IN_USE,
    STATE_OUTBOUND,
    STATE_UNAVAILABLE,
)

_LOGGER = logging.getLogger(__name__)

# dutchplanespotters.nl renders full HTML server-side (no JS needed).
# It sources its data from LVNL and shows LANDING RWY / TAKEOFF RWY for now.
DATA_URL = "https://www.dutchplanespotters.nl/runways/ams/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Schiphol is in CET/CEST = UTC+1 / UTC+2
_NL_UTC_OFFSET_SUMMER = 2   # CEST (late Mar – late Oct)
_NL_UTC_OFFSET_WINTER = 1   # CET  (late Oct – late Mar)


def _nl_now() -> datetime:
    """Return current local time in the Netherlands (approximated)."""
    now_utc = datetime.now(timezone.utc)
    # Simple DST heuristic: month 4-10 = summer (+2), else winter (+1)
    offset = _NL_UTC_OFFSET_SUMMER if 4 <= now_utc.month <= 10 else _NL_UTC_OFFSET_WINTER
    return now_utc + timedelta(hours=offset)


def _parse_runway_list(raw: str) -> list[str]:
    """Split a runway string like '18R, 06' into ['18R', '06']."""
    return [
        r.strip().upper()
        for r in re.split(r"[\s,]+", raw)
        if re.match(r"^\d{2}[LRC]?$", r.strip())
    ]


class SchipholRunwayCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls dutchplanespotters.nl for Schiphol runway data."""

    def __init__(self, hass: HomeAssistant, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=scan_interval),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Main update
    # ─────────────────────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            html = await self._fetch()
        except Exception as exc:
            raise UpdateFailed(f"Error fetching runway data: {exc}") from exc

        active = self._parse(html)
        _LOGGER.debug(
            "Schiphol runways — landing: %s  takeoff: %s",
            active["landing"],
            active["takeoff"],
        )
        return _build_runway_states(active)

    # ─────────────────────────────────────────────────────────────────────────
    # Network
    # ─────────────────────────────────────────────────────────────────────────

    async def _fetch(self) -> str:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(headers=_HEADERS, timeout=timeout) as session:
            async with session.get(DATA_URL) as resp:
                if resp.status != 200:
                    raise UpdateFailed(
                        f"dutchplanespotters.nl returned HTTP {resp.status}"
                    )
                return await resp.text(encoding="utf-8", errors="replace")

    # ─────────────────────────────────────────────────────────────────────────
    # Parsing
    # ─────────────────────────────────────────────────────────────────────────

    def _parse(self, html: str) -> dict[str, list[str]]:
        """
        Parse current landing/takeoff runways from the page.

        Strategy 1 (primary): the page shows prominently at the top:
            LANDING RWY: 18R
            TAKEOFF RWY: 24
        These are the *current* active runways — exactly what we need.

        Strategy 2 (fallback): walk the time-slot table and find the slot
        that matches the current Netherlands local time.
        """
        landing: list[str] = []
        takeoff: list[str] = []

        # ── Strategy 1: top-of-page current runway banners ────────────────
        landing_match = re.search(
            r"LANDING\s+RWY\s*:\s*([\d,\s]+(?:[LRC](?:\s*,\s*)?)?)",
            html,
            re.IGNORECASE,
        )
        takeoff_match = re.search(
            r"TAKEOFF\s+RWY\s*:\s*([\d,\s]+(?:[LRC](?:\s*,\s*)?)?)",
            html,
            re.IGNORECASE,
        )

        if landing_match:
            landing = _parse_runway_list(landing_match.group(1))
        if takeoff_match:
            takeoff = _parse_runway_list(takeoff_match.group(1))

        if landing or takeoff:
            _LOGGER.debug("Parsed via strategy 1 (banner): landing=%s takeoff=%s", landing, takeoff)
            return {"landing": landing, "takeoff": takeoff}

        # ── Strategy 2: time-slot table lookup ───────────────────────────
        _LOGGER.debug("Banner pattern not found — falling back to time-slot table")
        landing, takeoff = self._parse_timeslot_table(html)

        if landing or takeoff:
            _LOGGER.debug("Parsed via strategy 2 (time-slot): landing=%s takeoff=%s", landing, takeoff)
            return {"landing": landing, "takeoff": takeoff}

        _LOGGER.warning(
            "Could not parse any runway data from dutchplanespotters.nl. "
            "The site layout may have changed."
        )
        return {"landing": [], "takeoff": []}

    def _parse_timeslot_table(self, html: str) -> tuple[list[str], list[str]]:
        """
        Walk the time-slot table and return the runways active right now.

        Table rows look like:
            From - Until  14:30 - 15:15 | Landing  18R, 06 | Takeoff  09
        """
        now = _nl_now()
        current_minutes = now.hour * 60 + now.minute

        # Strip HTML tags for easier regex
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)

        pattern = re.compile(
            r"(\d{2}):(\d{2})\s*-\s*(\d{2}):(\d{2})"   # time range
            r".*?Landing\s+([\w,\s]+?)"                   # landing runways
            r"\s+Takeoff\s+([\w,\s]+?)"                   # takeoff runways
            r"(?=\d{2}:\d{2}|$)",                         # lookahead: next slot or end
            re.IGNORECASE | re.DOTALL,
        )

        best_landing: list[str] = []
        best_takeoff: list[str] = []

        for m in pattern.finditer(text):
            sh, sm, eh, em = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            start_min = sh * 60 + sm
            end_min = eh * 60 + em

            # Handle overnight slots (e.g. 22:10 - 01:55)
            if end_min < start_min:
                in_slot = current_minutes >= start_min or current_minutes <= end_min
            else:
                in_slot = start_min <= current_minutes <= end_min

            if in_slot:
                best_landing = _parse_runway_list(m.group(5))
                best_takeoff = _parse_runway_list(m.group(6))
                break  # first matching slot wins

        return best_landing, best_takeoff


# ─────────────────────────────────────────────────────────────────────────────
# State builder (pure function, easy to test)
# ─────────────────────────────────────────────────────────────────────────────

def _build_runway_states(active: dict[str, list[str]]) -> dict[str, Any]:
    """
    Map raw landing/takeoff runway lists onto the RUNWAYS config table
    and return a dict keyed by runway designator (e.g. "18L/36R").
    """
    landing_set = {h.upper() for h in active.get("landing", [])}
    takeoff_set = {h.upper() for h in active.get("takeoff", [])}

    result: dict[str, Any] = {
        "_raw_landing": list(landing_set),
        "_raw_takeoff": list(takeoff_set),
    }

    for designator, meta in RUNWAYS.items():
        is_landing = any(h in landing_set for h in meta["inbound_headings"])
        is_takeoff = any(h in takeoff_set for h in meta["outbound_headings"])

        active_landing = next(
            (h for h in meta["inbound_headings"] if h in landing_set), None
        )
        active_takeoff = next(
            (h for h in meta["outbound_headings"] if h in takeoff_set), None
        )

        if is_landing and is_takeoff:
            state = STATE_BOTH
        elif is_landing:
            state = STATE_INBOUND
        elif is_takeoff:
            state = STATE_OUTBOUND
        else:
            state = STATE_NOT_IN_USE

        result[designator] = {
            "state": state,
            "name": meta["name"],
            "landing_heading": active_landing,
            "takeoff_heading": active_takeoff,
        }

    return result
