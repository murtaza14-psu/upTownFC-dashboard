"""Pitch SVG rendering: overlays event markers onto the club's pitch.svg.

pitch_x/pitch_y are normalized 0-1 and map directly onto the SVG's
viewBox (0 0 5001 3258) — no coordinate transform needed. Only Key Pass
carries end coordinates, so it's the only type rendered as an arrow;
everything else is a point marker. Tooltips use native SVG <title>
elements, so no JS is needed for hover text.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from data import DETAIL_COLUMN_LABELS, DETAIL_COLUMNS

PITCH_SVG_PATH = Path(__file__).parent / "pitch.svg"
VIEWBOX_W = 5001
VIEWBOX_H = 3258

EVENT_COLORS = {
    "Goal": "#FFD700",
    "Shot": "#FF4B4B",
    "Key Pass": "#4B9CFF",
    "Duel": "#B266FF",
    "Interception": "#00C2A8",
    "Possession Lost": "#FF8C42",
    "Corner": "#FFFFFF",
    "Foul": "#FF3860",
    "Save": "#2ECC71",
    "Substitution": "#AAAAAA",
    "Block": "#F1C40F",
    "Clearance": "#3498DB",
    "Offside": "#E67E22",
}


@st.cache_data
def load_pitch_svg() -> str:
    return PITCH_SVG_PATH.read_text(encoding="utf-8")


def _tooltip(row: pd.Series, event_type: str) -> str:
    """Multi-line tooltip with every populated metadata field for this event."""
    lines = [event_type]
    for col in DETAIL_COLUMNS:
        value = row.get(col)
        if pd.notna(value):
            if col in ("jersey_number", "match_minute") and float(value).is_integer():
                value = int(value)
            lines.append(f"{DETAIL_COLUMN_LABELS[col]}: {value}")
    return "\n".join(lines)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_markers(df: pd.DataFrame, event_type: str) -> tuple[str, int, int]:
    """Return (svg marker fragment, plotted_count, missing_coord_count)."""
    rows = df[df.event_type == event_type]
    color = EVENT_COLORS.get(event_type, "#FFFFFF")

    has_coords = rows.pitch_x.notna() & rows.pitch_y.notna()
    plottable = rows[has_coords]
    missing = len(rows) - len(plottable)

    fragments = []
    for _, row in plottable.iterrows():
        cx = row.pitch_x * VIEWBOX_W
        cy = row.pitch_y * VIEWBOX_H
        tooltip = _escape(_tooltip(row, event_type))
        radius = 55 if event_type == "Goal" else 38

        if event_type == "Key Pass" and pd.notna(row.end_pitch_x) and pd.notna(row.end_pitch_y):
            ex = row.end_pitch_x * VIEWBOX_W
            ey = row.end_pitch_y * VIEWBOX_H
            fragments.append(
                f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                f'stroke="{color}" stroke-width="10" opacity="0.85" '
                f'marker-end="url(#arrowhead)"><title>{tooltip}</title></line>'
            )
            fragments.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="16" fill="{color}" opacity="0.9"/>'
            )
        else:
            fragments.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}" fill="{color}" '
                f'stroke="white" stroke-width="6" opacity="0.9">'
                f"<title>{tooltip}</title></circle>"
            )

    return "".join(fragments), len(plottable), missing


def direction_label(half: str) -> str | None:
    """Plain-text attack-direction label for the given half, for rendering in Streamlit
    (not the SVG) below the pitch. None for 'Full Match' since the two halves point
    opposite ways and a single arrow would misrepresent one of them."""
    if half == "First Half":
        return "⟵  UP Country Lions attacking: Right to Left"
    if half == "Second Half":
        return "UP Country Lions attacking: Left to Right  ⟶"
    return None


ARROWHEAD_DEFS = f"""
<defs>
  <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="7" refY="5"
          orient="auto-start-reverse">
    <polygon points="0 0, 10 5, 0 10" fill="{EVENT_COLORS['Key Pass']}" />
  </marker>
</defs>
""".strip()


def render_pitch(df: pd.DataFrame, event_type: str) -> tuple[str, int, int]:
    """Build the full SVG (pitch + markers), scaled to fill its container by aspect
    ratio rather than a fixed pixel height, so it never scrolls inside the iframe."""
    base_svg = load_pitch_svg()
    markers, plotted_count, missing_count = build_markers(df, event_type)

    injected = base_svg.replace("</svg>", f"{ARROWHEAD_DEFS}<g>{markers}</g></svg>")
    # Replace the fixed pixel width/height with a style that fills the wrapper div,
    # so the SVG scales by aspect ratio instead of by a hardcoded pixel size.
    injected = injected.replace(
        f'width="{VIEWBOX_W}" height="{VIEWBOX_H}"',
        'style="width:100%;height:100%;display:block;"',
    )

    aspect_ratio = VIEWBOX_W / VIEWBOX_H
    wrapped = f"""
    <div style="width:100%; aspect-ratio:{aspect_ratio}; margin:0; padding:0;">
      {injected}
    </div>
    """
    return wrapped, plotted_count, missing_count
