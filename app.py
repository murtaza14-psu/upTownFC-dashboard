"""UpTown FC Match Dashboard — Step 2: + match header and video panel."""

import streamlit as st

from data import (
    EVENT_TYPES,
    HALF_OPTIONS,
    NO_COORDINATE_TYPES,
    DEFAULT_NONE_LABEL,
    SUB_FILTER_COLUMNS,
    SUB_FILTER_LABELS,
    SUB_FILTER_NONE_LABEL,
    apply_filters,
    event_counts,
    event_detail_table,
    list_matches,
    load_match,
    player_display_label,
    player_options,
)
from pitch import direction_label, render_pitch
from metadata import find_lineup_image, load_metadata
from stats import (
    compute_attack,
    compute_defense,
    compute_discipline,
    compute_duel_split,
    compute_general_play,
    compute_key_stats,
)


def render_metric_row(stats: dict) -> None:
    cols = st.columns(len(stats))
    for col, (label, value) in zip(cols, stats.items()):
        if value is None:
            col.metric(label, "—")
        elif isinstance(value, float):
            col.metric(label, f"{value:.1f}%")
        else:
            col.metric(label, int(value))

st.set_page_config(page_title="UpTown FC Match Dashboard", layout="wide")

matches = list_matches()

if not matches:
    st.error("No match files found in the matches/ folder.")
    st.stop()

match_labels = {m.stem.replace("_", " "): m for m in matches}
selected_label = st.selectbox("Select match", list(match_labels.keys()))
selected_path = match_labels[selected_label]

df = load_match(str(selected_path))
meta, has_sidecar = load_metadata(selected_path)

# --- Match header -----------------------------------------------------

home_team = meta["home_team"] or "Home"
away_team = meta["away_team"] or "Away"

SCORE_COLOR = "#FFD700"  # matches the Goal marker color on the pitch

if meta["home_score"] is not None and meta["away_score"] is not None:
    header_html = f"""
    <div style="text-align:center; margin-bottom:0.5rem;">
      <span style="font-size:2.6rem; font-weight:700;">{home_team}</span>
      <span style="font-size:3.2rem; font-weight:800; color:{SCORE_COLOR}; padding:0 2rem;">
        {int(meta['home_score'])} – {int(meta['away_score'])}
      </span>
      <span style="font-size:2.6rem; font-weight:700;">{away_team}</span>
    </div>
    """
else:
    header_html = f"""
    <div style="text-align:center; margin-bottom:0.5rem;">
      <span style="font-size:2.6rem; font-weight:700;">{home_team} vs {away_team}</span>
    </div>
    """
st.markdown(header_html, unsafe_allow_html=True)

# Ordered top-down by how useful it is to a coach identifying/reviewing the match.
# Match Source is a link, not plain text, so it's rendered as one when present.
row_template = "<div style='text-align:center; color:gray; line-height:1.6;'>{content}</div>"
detail_row_html = []
for label, value in [
    ("Competition", meta["competition"]),
    ("Date", meta["date"]),
    ("Referee", meta["referee"]),
]:
    if value:
        detail_row_html.append(row_template.format(content=f"{label}: {value}"))

if meta["youtube_url"]:
    link = f'<a href="{meta["youtube_url"]}" target="_blank">Match Source</a>'
    detail_row_html.append(row_template.format(content=link))

for label, value in [
    ("Venue", meta["venue"]),
    ("Kickoff", meta["kickoff_time"]),
]:
    if value:
        detail_row_html.append(row_template.format(content=f"{label}: {value}"))

if detail_row_html:
    st.markdown(f"<div style='margin-bottom:1rem;'>{''.join(detail_row_html)}</div>", unsafe_allow_html=True)

st.markdown(
    f"<div style='text-align:left; font-size:1.5rem;'>"
    f"<b style='color:{SCORE_COLOR};'>Description:</b> These are the Stats logged for {home_team} "
    f"only during their match against {away_team}"
    f"</div>",
    unsafe_allow_html=True,
)

if not has_sidecar:
    st.info(
        f"Match details incomplete — add `{selected_path.with_suffix('.json').name}` "
        "to fill in venue, competition, kickoff time, and score.",
        icon="ℹ️",
    )

# --- Key Stats + grouped sections (whole match, unaffected by Event Explorer filters) --
# Each section is its own bordered card with a spacer after it, so they read
# as distinct entities rather than one continuous block.

SECTION_SPACER = "<div style='margin-bottom:2.5rem'></div>"


def render_section(title: str) -> None:
    st.markdown(f"#### {title}")


st.divider()

with st.container(border=True):
    render_section("Key Stats")
    render_metric_row(compute_key_stats(df))
st.markdown(SECTION_SPACER, unsafe_allow_html=True)

with st.container(border=True):
    render_section("General Play")
    render_metric_row(compute_general_play(df))
st.markdown(SECTION_SPACER, unsafe_allow_html=True)

with st.container(border=True):
    render_section("Attack")
    render_metric_row(compute_attack(df))
st.markdown(SECTION_SPACER, unsafe_allow_html=True)

with st.container(border=True):
    render_section("Defense")
    render_metric_row(compute_defense(df))
    duel_split = compute_duel_split(df)
    st.caption(f"Duel type: {duel_split['Grounded']} grounded · {duel_split['Aerial']} aerial")
st.markdown(SECTION_SPACER, unsafe_allow_html=True)

with st.container(border=True):
    render_section("Discipline")
    render_metric_row(compute_discipline(df))
st.markdown(SECTION_SPACER, unsafe_allow_html=True)

# --- Lineup -----------------------------------------------------------------

st.divider()
st.subheader("Lineup")

lineup_image = find_lineup_image(selected_path)
if lineup_image:
    st.image(str(lineup_image), width="stretch")
else:
    st.info(
        f"No lineup image found — add `{selected_path.stem}_lineup.png` "
        "(or .jpg) to the matches/ folder to show it here.",
        icon="ℹ️",
    )

# --- Event explorer -------------------------------------------------------
# Half / Player filters below apply ONLY to this section (list, pitch, table) —
# the stat sections above always reflect the whole match.

st.divider()
st.subheader("Event Explorer")

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    selected_half = st.segmented_control("Half", HALF_OPTIONS, default="First Half")
with filter_col2:
    selected_player = st.selectbox(
        "Player", player_options(df), format_func=lambda p: player_display_label(df, p)
    )

selected_half = selected_half or "First Half"
fdf = apply_filters(df, selected_half, selected_player)
st.caption(f"Event Explorer showing {len(fdf)} of {len(df)} events — {selected_half} · {selected_player}")

if "selected_event_type" not in st.session_state:
    st.session_state.selected_event_type = "Goal"

counts = event_counts(fdf)

# --- Sub-filters for the selected event type -------------------------------
# e.g. Shot -> was it saved / off target / blocked. These narrow only the
# pitch + detail table below, not the event-type counts in the list.

selected_type = st.session_state.selected_event_type
type_rows = fdf[fdf.event_type == selected_type]

sub_filter_cols = SUB_FILTER_COLUMNS.get(selected_type, [])
if sub_filter_cols:
    sub_cols = st.columns(len(sub_filter_cols))
    for sub_col, col_name in zip(sub_cols, sub_filter_cols):
        series = type_rows[col_name]
        options = sorted(series.dropna().unique().tolist())
        none_label = SUB_FILTER_NONE_LABEL.get(col_name, DEFAULT_NONE_LABEL)
        has_none = series.isna().any()
        display_options = options + ([none_label] if has_none else [])

        with sub_col:
            if display_options:
                selected_vals = st.multiselect(
                    SUB_FILTER_LABELS.get(col_name, col_name),
                    display_options,
                    default=display_options,
                    key=f"subfilter_{selected_type}_{col_name}",
                )
                mask = series.isin([v for v in selected_vals if v != none_label])
                if none_label in selected_vals:
                    mask = mask | series.isna()
                type_rows = type_rows[mask]
            else:
                st.caption(f"No {SUB_FILTER_LABELS.get(col_name, col_name)} data for this type.")

list_col, pitch_col, table_col = st.columns([3, 9, 4])

with list_col:
    with st.container(height=480, border=True):
        for event_type in EVENT_TYPES:
            count = counts[event_type]
            is_selected = st.session_state.selected_event_type == event_type
            if st.button(
                f"{event_type} ({count})",
                key=f"evtbtn_{event_type}",
                width="stretch",
                type="primary" if is_selected else "secondary",
                disabled=(count == 0),
            ):
                st.session_state.selected_event_type = event_type
                st.rerun()

with pitch_col:
    if selected_type in NO_COORDINATE_TYPES:
        st.warning(
            f"**{selected_type}** events have no recorded pitch location "
            f"({len(type_rows)} logged with current filters). See the table on the right."
        )
    else:
        svg_html, plotted, missing = render_pitch(type_rows, selected_type)
        st.iframe(svg_html, height=620)

        label = direction_label(selected_half)
        if label:
            st.markdown(
                f"<div style='text-align:center; font-size:1.15rem; font-weight:600; "
                f"margin-top:0.25rem;'>{label}</div>",
                unsafe_allow_html=True,
            )

        caption = f"{plotted} {selected_type} event(s) plotted"
        if missing:
            caption += f" · {missing} more logged with no recorded position"
        st.caption(caption)

with table_col:
    detail_df = event_detail_table(type_rows, selected_type)
    st.caption(f"{selected_type} — {len(detail_df)} event(s)")
    st.dataframe(detail_df, width="stretch", height=420, hide_index=True)
