"""
Chess.com username import for DCO.
Fetches monthly archives via the public Chess.com API and returns PGN strings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple
import json
import urllib.request
import urllib.error


BASE_URL = "https://api.chess.com/pub/player"


def fetch_chesscom_pgns(
    username: str,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    rated_only: bool = False,
    time_class: Optional[str] = None,
    rules: Optional[str] = None
) -> Tuple[List[str], List[str]]:
    """
    Fetch PGNs from Chess.com for a username and date range.

    Args:
        username: Chess.com username
        start_date: Inclusive start date (UTC) or None
        end_date: Inclusive end date (UTC) or None
        rated_only: If True, only include rated games
        time_class: Optional time class filter (bullet/blitz/rapid/classical)
        rules: Optional rules filter ("chess", "chess960", etc.)

    Returns:
        Tuple of (pgn_list, errors)
    """
    errors: List[str] = []
    pgns: List[str] = []

    username = username.strip().lower()
    if not username:
        return [], ["Username is required."]

    archive_urls = _get_archives(username, errors)
    if not archive_urls:
        if not errors:
            errors.append("No archive months available for this username.")
        return [], errors

    start_ym = _to_year_month(start_date)
    end_ym = _to_year_month(end_date)

    for archive_url in archive_urls:
        year_month = _parse_archive_year_month(archive_url)
        if year_month is None:
            continue
        if not _month_in_range(year_month, start_ym, end_ym):
            continue

        games, fetch_errors = _fetch_games(archive_url)
        errors.extend(fetch_errors)
        for game in games:
            pgn = game.get("pgn")
            if not pgn:
                continue

            if rated_only and not game.get("rated", False):
                continue
            if time_class and game.get("time_class") != time_class:
                continue
            if rules and game.get("rules") != rules:
                continue

            if not _game_in_range(game, start_date, end_date):
                continue

            pgns.append(pgn)

    return pgns, errors


def _get_archives(username: str, errors: List[str]) -> List[str]:
    """Fetch list of archive URLs for a username."""
    url = f"{BASE_URL}/{username}/games/archives"
    data, fetch_errors = _fetch_json(url)
    errors.extend(fetch_errors)
    if not data:
        return []
    return data.get("archives", []) or []


def _fetch_games(archive_url: str) -> Tuple[List[dict], List[str]]:
    """Fetch games for a monthly archive URL."""
    data, errors = _fetch_json(archive_url)
    if not data:
        return [], errors
    return data.get("games", []) or [], errors


def _fetch_json(url: str) -> Tuple[Optional[dict], List[str]]:
    """Fetch JSON data with a basic user agent."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DCO/1.0 (https://github.com/SV-Nikolov/DCO)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status != 200:
                return None, [f"HTTP {response.status} for {url}"]
            data = json.loads(response.read().decode("utf-8"))
            return data, []
    except urllib.error.HTTPError as exc:
        return None, [f"HTTP error {exc.code} for {url}"]
    except urllib.error.URLError as exc:
        return None, [f"Network error for {url}: {exc.reason}"]
    except Exception as exc:
        return None, [f"Failed to fetch {url}: {exc}"]


def _game_in_range(
    game: dict,
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> bool:
    """Check if game end_time is within the date range."""
    if start_date is None and end_date is None:
        return True

    end_time = game.get("end_time")
    if not isinstance(end_time, int):
        return True

    game_dt = datetime.fromtimestamp(end_time, tz=timezone.utc)

    if start_date:
        start = _ensure_utc(start_date)
        if game_dt < start:
            return False
    if end_date:
        end = _ensure_utc(end_date)
        if game_dt > end:
            return False
    return True


def _ensure_utc(value: datetime) -> datetime:
    """Ensure datetime is timezone-aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_year_month(value: Optional[datetime]) -> Optional[Tuple[int, int]]:
    if value is None:
        return None
    return value.year, value.month


def _parse_archive_year_month(url: str) -> Optional[Tuple[int, int]]:
    """Extract (year, month) from an archive URL."""
    parts = url.strip("/").split("/")
    if len(parts) < 2:
        return None
    try:
        year = int(parts[-2])
        month = int(parts[-1])
        return year, month
    except ValueError:
        return None


def _month_in_range(
    value: Tuple[int, int],
    start: Optional[Tuple[int, int]],
    end: Optional[Tuple[int, int]]
) -> bool:
    """Return True if year-month is within inclusive start/end bounds."""
    year, month = value
    if start:
        if (year, month) < start:
            return False
    if end:
        if (year, month) > end:
            return False
    return True
