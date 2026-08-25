"""Match metadata: sidecar JSON loading, with filename-derived fallback.

Each match CSV (matches/<name>.csv) may have a same-named JSON file
(matches/<name>.json) holding venue, competition, score, and a YouTube link.
None of this lives in the event CSV itself, so when the JSON is missing we
fall back to whatever we can parse out of the filename and leave the rest
blank rather than guessing.
"""

import json
import re
from pathlib import Path

FILENAME_PATTERN = re.compile(r"^(.*)_vs_(.*)_(\d{4}-\d{2}-\d{2})$")

METADATA_FIELDS = [
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "competition",
    "venue",
    "date",
    "kickoff_time",
    "referee",
    "youtube_url",
]


def _parse_filename(csv_path: Path) -> dict:
    """Best-effort team names and date from the filename, everything else blank."""
    match = FILENAME_PATTERN.match(csv_path.stem)
    if match:
        home_team, away_team, date = match.groups()
        home_team = home_team.replace("_", " ")
        away_team = away_team.replace("_", " ")
    else:
        home_team, away_team, date = csv_path.stem.replace("_", " "), "", ""

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_score": None,
        "away_score": None,
        "competition": "",
        "venue": "",
        "date": date,
        "kickoff_time": "",
        "referee": "",
        "youtube_url": "",
    }


def sidecar_path(csv_path: Path) -> Path:
    return csv_path.with_suffix(".json")


def load_metadata(csv_path: Path) -> tuple[dict, bool]:
    """Return (metadata dict, found_sidecar). Missing/invalid JSON -> filename fallback."""
    json_path = sidecar_path(csv_path)
    fallback = _parse_filename(csv_path)

    if not json_path.exists():
        return fallback, False

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return fallback, False

    merged = {**fallback, **{k: v for k, v in data.items() if k in METADATA_FIELDS}}
    return merged, True


LINEUP_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]


def find_lineup_image(csv_path: Path) -> Path | None:
    """Look for matches/<name>_lineup.<ext> next to the CSV. None if not present."""
    for ext in LINEUP_IMAGE_EXTENSIONS:
        candidate = csv_path.with_name(f"{csv_path.stem}_lineup{ext}")
        if candidate.exists():
            return candidate
    return None


def create_placeholder_json(csv_path: Path) -> Path:
    """Write a placeholder sidecar JSON next to the CSV, if one doesn't exist yet."""
    json_path = sidecar_path(csv_path)
    if json_path.exists():
        return json_path

    placeholder = _parse_filename(csv_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(placeholder, f, indent=2)
    return json_path
