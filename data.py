"""Data loading for the UpTown FC match dashboard.

Scans the matches/ folder for event CSVs and loads them into a
chronologically-ordered DataFrame (the raw files are reverse-chronological).
"""

from pathlib import Path

import pandas as pd
import streamlit as st

MATCHES_DIR = Path(__file__).parent / "matches"


def list_matches() -> list[Path]:
    """Return every match CSV in the matches/ folder, sorted by filename."""
    if not MATCHES_DIR.exists():
        return []
    return sorted(MATCHES_DIR.glob("*.csv"))


@st.cache_data
def load_match(csv_path: str) -> pd.DataFrame:
    """Load one match's event CSV.

    Rows in the source file are reverse-chronological (2nd half first),
    so we reverse them here to restore chronological order.
    """
    df = pd.read_csv(csv_path)
    df = df.iloc[::-1].reset_index(drop=True)
    return df


EVENT_TYPES = [
    "Goal",
    "Shot",
    "Key Pass",
    "Duel",
    "Interception",
    "Possession Lost",
    "Corner",
    "Foul",
    "Save",
    "Substitution",
    "Block",
    "Clearance",
    "Offside",
]

# Event types with no pitch_x/pitch_y at all (F9 fallback in the PRD).
NO_COORDINATE_TYPES = {"Corner", "Save", "Substitution"}

UNATTRIBUTED = "Unattributed"

HALF_OPTIONS = ["First Half", "Second Half", "Full Match"]
_HALF_TO_PERIOD = {"First Half": "1st half", "Second Half": "2nd half"}


def player_options(df: pd.DataFrame) -> list[str]:
    """Player names for the filter dropdown, 'All Players' first, 'Unattributed' last if needed."""
    names = sorted(df.player_name.dropna().unique().tolist())
    options = ["All Players"] + names
    if df.player_name.isna().any():
        options.append(UNATTRIBUTED)
    return options


def player_display_label(df: pd.DataFrame, player_name: str) -> str:
    """'#7 Mohamed Akib' for the dropdown; sentinels ('All Players', 'Unattributed') pass through."""
    if player_name in ("All Players", UNATTRIBUTED):
        return player_name
    jersey = df.loc[df.player_name == player_name, "jersey_number"].dropna()
    if jersey.empty:
        return player_name
    return f"#{int(jersey.iloc[0])} {player_name}"


def event_counts(df: pd.DataFrame) -> dict:
    """Count of each event type in EVENT_TYPES order, for the given (already-filtered) df."""
    counts = df.event_type.value_counts()
    return {event_type: int(counts.get(event_type, 0)) for event_type in EVENT_TYPES}


DETAIL_COLUMNS = [
    "period",
    "player_name",
    "jersey_number",
    "outcome",
    "duel_type",
    "card_color",
    "goal_type",
    "assist_name",
    "sub_in_name",
    "match_minute",
]

DETAIL_COLUMN_LABELS = {
    "period": "Half",
    "player_name": "Player",
    "jersey_number": "#",
    "outcome": "Outcome",
    "duel_type": "Duel Type",
    "card_color": "Card",
    "goal_type": "Goal Type",
    "assist_name": "Assist",
    "sub_in_name": "Sub In",
    "match_minute": "Minute",
}


# Columns that carry meaningful sub-attributes for a given event type, used to
# build per-type sub-filters (e.g. Shot -> was it saved/blocked/off target).
SUB_FILTER_COLUMNS = {
    "Goal": ["goal_type"],
    "Shot": ["outcome"],
    "Duel": ["duel_type", "outcome"],
    "Save": ["outcome"],
    "Foul": ["card_color"],
}

SUB_FILTER_LABELS = {
    "goal_type": "Goal Type",
    "outcome": "Outcome",
    "duel_type": "Duel Type",
    "card_color": "Card",
}

# Label for the "blank/not recorded" bucket of a sub-filter column, so those
# rows stay selectable instead of silently disappearing when NaN is excluded
# from a dropna()'d options list.
SUB_FILTER_NONE_LABEL = {
    "card_color": "No Card",
}
DEFAULT_NONE_LABEL = "None"


def event_detail_table(df: pd.DataFrame, event_type: str) -> pd.DataFrame:
    """Detail rows for one event type, with all-empty columns dropped for a clean table."""
    rows = df[df.event_type == event_type][DETAIL_COLUMNS].copy()
    rows = rows.dropna(axis=1, how="all")
    rows = rows.rename(columns=DETAIL_COLUMN_LABELS)
    return rows.reset_index(drop=True)


def apply_filters(df: pd.DataFrame, half: str, player: str) -> pd.DataFrame:
    """Filter events by half and player. 'Full Match' / 'All Players' pass everything through."""
    filtered = df

    period = _HALF_TO_PERIOD.get(half)
    if period is not None:
        filtered = filtered[filtered.period == period]

    if player == UNATTRIBUTED:
        filtered = filtered[filtered.player_name.isna()]
    elif player != "All Players":
        filtered = filtered[filtered.player_name == player]

    return filtered
