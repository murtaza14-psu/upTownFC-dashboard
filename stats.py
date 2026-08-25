"""Stat computations over a match event DataFrame.

Definitions match the PRD (section 5). All figures are counted directly
from event rows — nothing here is estimated or inferred beyond what the
CSV records.
"""

import pandas as pd


def compute_key_stats(df: pd.DataFrame) -> dict:
    shots_on_target = (
        (df.event_type == "Goal") | ((df.event_type == "Shot") & (df.outcome == "saved"))
    ).sum()

    return {
        "Goals": (df.event_type == "Goal").sum(),
        "Shots": df.event_type.isin(["Shot", "Goal"]).sum(),
        "Shots on Target": shots_on_target,
        "Corners": (df.event_type == "Corner").sum(),
        "Offsides": (df.event_type == "Offside").sum(),
        "Fouls": (df.event_type == "Foul").sum(),
        "Yellow Cards": (df.card_color == "yellow").sum(),
        "Red Cards": (df.card_color == "red").sum(),
    }


def compute_general_play(df: pd.DataFrame) -> dict:
    return {
        "Key Passes": (df.event_type == "Key Pass").sum(),
        "Interceptions": (df.event_type == "Interception").sum(),
        "Possession Lost": (df.event_type == "Possession Lost").sum(),
        "Corners": (df.event_type == "Corner").sum(),
        "Offsides": (df.event_type == "Offside").sum(),
    }


def compute_attack(df: pd.DataFrame) -> dict:
    shots_and_goals = df[df.event_type.isin(["Shot", "Goal"])]
    return {
        "Total Shots": len(shots_and_goals),
        "On Target": (
            (df.event_type == "Goal") | ((df.event_type == "Shot") & (df.outcome == "saved"))
        ).sum(),
        "Off Target": ((df.event_type == "Shot") & (df.outcome == "off_target")).sum(),
        "Blocked": ((df.event_type == "Shot") & (df.outcome == "blocked")).sum(),
        "Goals": (df.event_type == "Goal").sum(),
    }


def compute_defense(df: pd.DataFrame) -> dict:
    duels = df[df.event_type == "Duel"]
    won = (duels.outcome == "won").sum()
    lost = (duels.outcome == "lost").sum()
    duels_won_pct = (won / (won + lost) * 100) if (won + lost) > 0 else None

    return {
        "Duels": len(duels),
        "Duels Won %": duels_won_pct,
        "Clearances": (df.event_type == "Clearance").sum(),
        "Interceptions": (df.event_type == "Interception").sum(),
        "Blocks": (df.event_type == "Block").sum(),
        "Saves": (df.event_type == "Save").sum(),
    }


def compute_duel_split(df: pd.DataFrame) -> dict:
    duels = df[df.event_type == "Duel"]
    return {
        "Grounded": (duels.duel_type == "grounded").sum(),
        "Aerial": (duels.duel_type == "aerial").sum(),
    }


def compute_discipline(df: pd.DataFrame) -> dict:
    return {
        "Yellow Cards": (df.card_color == "yellow").sum(),
        "Red Cards": (df.card_color == "red").sum(),
        "Fouls": (df.event_type == "Foul").sum(),
    }
