# PRD — UpTown FC Match Dashboard

**Owner:** Product
**Status:** Draft v1 for build
**Date:** 2026-08-25
**Data source of record:** `UP_Country_Lions_vs_New_Youngs_FC_2026-08-23.csv` (278 events, 16 columns)

---

## 1. Problem

The club now tags matches event-by-event, producing a clean per-match CSV with normalised pitch coordinates. That file is currently the end of the pipeline: to answer "how many shots did we have in the first half, and where from?", a coach opens the raw CSV in Excel, filters columns by hand, and still cannot see *where* anything happened. The spatial half of the data — the reason it was tagged with x/y coordinates in the first place — is effectively unreadable.

At the same time, the tagged data is thinner than it looks. Only one team is recorded, ordinary passes are not logged, and match minute is blank on 93% of rows. Any product built on it has to be honest about that boundary rather than inventing numbers to fill a layout.

**The problem:** match event data exists but is not consumable. Coaches cannot see a match summary or a shot map without manual spreadsheet work, so tagged matches go unreviewed.

## 2. Target users

| User | Need | Implication for the product |
|---|---|---|
| **Head coach / assistant coach** (primary) | Post-match review in the team room. Wants the headline numbers in ten seconds and shot/duel locations to talk over. | Big legible tiles, one pitch view, minimal controls, desktop-first. |
| **Club stakeholders and supporters** (secondary — drives the deploy target) | A credible public match page they can open from a link. | Deployed to Streamlit Community Cloud with a public URL. See §8 privacy note. |
| **Match analyst** (implicit) | Confirmation their tagging landed correctly; visibility of what is missing. | Raw-event table for coordinate-less types; a data-completeness note. |

**Non-users in v1:** players on phones (mobile layout is explicitly out of scope), opposition scouts (no opponent data exists).

## 3. Data reality — what the CSV can and cannot support

Validated against the actual file, not assumed.

**Columns:** `match_minute`, `period`, `event_type`, `team_name`, `player_name`, `jersey_number`, `assist_name`, `sub_in_name`, `goal_type`, `outcome`, `duel_type`, `card_color`, `pitch_x`, `pitch_y`, `end_pitch_x`, `end_pitch_y`.

**Event types (278 rows):** Possession Lost 64 · Duel 55 · Key Pass 49 · Interception 42 · Shot 28 · Corner 9 · Foul 7 · Goal 6 · Save 5 · Substitution 4 · Block 3 · Clearance 3 · Offside 3.

**Facts that shape the build:**

1. **Coordinates are normalised 0–1.** `pitch_x` maps to length, `pitch_y` to width.
2. **Only Key Pass carries end coordinates** (49/49). Every other type is a point marker; Key Pass is the only arrow layer.
3. **Three types carry no coordinates at all:** Corner (0/9), Save (0/5), Substitution (0/4). Additionally 17 of 64 Possession Lost and 1 of 28 Shot rows have blank coordinates.
4. **Attacking direction flips between halves.** First-half shots cluster at x≈0.20, second-half at x≈0.76. Coordinates are absolute pitch positions, not attack-normalised. **Decision: render raw, as recorded.** The half filter is therefore not cosmetic — it is what makes the map readable.
5. **Rows are in reverse chronological order** (second-half events appear first in the file). Any list ordering must reverse the file, not trust it.
6. **Cards are an attribute of Foul rows** (`card_color`), not a separate event type. 2 yellow, 0 red.
7. **`match_minute` is present on only 20 of 278 rows.** There is no usable timeline.
8. **Only one team is recorded.** `team_name` is "UP Country Lions" on all 278 rows. Nothing about the opponent exists in this file — which is why possession % cannot be computed.
9. **Ordinary passes are not tagged.** "Key Pass" is a judgement-call subset with no completion flag, so total passes / accurate passes / pass accuracy cannot be derived.
10. **No match metadata in the file.** Venue, competition, kickoff, final score and YouTube link are absent; the filename carries only the two team names and the date.

**Open assumption to confirm with the analyst:** `Save` rows are tagged to UP Country Lions, which we read as *our goalkeeper saving an opposition shot*. If instead it means an opposition keeper saving our shot, the Shots-on-Target definition in §5 changes. Flagged, not blocking.

## 4. User stories

**Coach**
- As a coach, I want the match heading, date, venue and final score at the top, so I know which match I am looking at without checking the filename.
- As a coach, I want the full-match video embedded on the same page, so review and numbers sit together instead of in two tabs.
- As a coach, I want key stats in one glance row, so I can open the debrief in ten seconds.
- As a coach, I want stats grouped into general play, attack, defence and discipline, so I can go straight to the area I want to coach.
- As a coach, I want to pick an event type and see every one of them plotted on a pitch, so I can show the squad where we lost the ball or where our shots came from.
- As a coach, I want to filter the pitch to one player, so I can run an individual review.
- As a coach, I want to switch between first and second half, so positions make sense given we changed ends.

**Analyst**
- As an analyst, I want event types with no coordinates listed in a table rather than silently dropped, so I can see all nine corners were logged even though none has a position.
- As an analyst, I want the page to tell me which fields are incomplete, so I know what to fix in the next tagging session.

**Stakeholder**
- As a supporter, I want to open a link and read the match summary without installing anything.

## 5. Stat definitions

Every figure below is computable from the CSV. Values shown are for the reference match.

### Key Stats (headline row)
| Tile | Definition | Value |
|---|---|---|
| Goals | `event_type == Goal` | 6 |
| Shots | `Shot` + `Goal` | 34 |
| Shots on Target | `Goal` + `Shot` where `outcome == saved` | 12 |
| Corners | `event_type == Corner` | 9 |
| Offsides | `event_type == Offside` | 3 |
| Fouls | `event_type == Foul` | 7 |
| Yellow Cards | `card_color == yellow` | 2 |
| Red Cards | `card_color == red` | 0 |

**Cut from the headline row:** Possession %, Passes, Pass Accuracy — not derivable (§3.8, §3.9). Per decision, these are removed from MVP entirely rather than shown as blanks. They return when the tagging tool logs ordinary passes and opponent possession.

### General Play
Key Passes (49) · Interceptions (42) · Possession Lost (64) · Corners (9) · Offsides (3)

*This section replaces the originally requested possession/pass-accuracy panel with the ball-progression and turnover metrics the data actually holds.*

### Attack
| Tile | Definition | Value |
|---|---|---|
| Total Shots | `Shot` + `Goal` | 34 |
| On Target | `Goal` + `Shot(saved)` | 12 |
| Off Target | `Shot(off_target)` | 15 |
| Blocked | `Shot(blocked)` | 6 |
| Goals | `Goal` | 6 |

One Shot row has a null `outcome` and is counted in Total only — surfaced in the analyst note, not silently absorbed into another bucket.

### Defence
| Tile | Definition | Value |
|---|---|---|
| Duels | `event_type == Duel` | 55 |
| Duels Won % | `won / (won + lost)` | 67.3% (37–18) |
| Clearances | `event_type == Clearance` | 3 |
| Interceptions | `event_type == Interception` | 42 |
| Blocks | `event_type == Block` | 3 |
| Saves | `event_type == Save` | 5 |

Duel split by `duel_type` (grounded 32 / aerial 23) shown as a secondary line.

### Discipline
Yellow Cards (2) · Red Cards (0) · Fouls (7)

All four section stats respect the active half filter and recompute on change.

## 6. Core features

### MVP

**F1 — Match picker.** App scans a `matches/` folder and lists every CSV in a dropdown. Adding a match means dropping in two files; no code change.

**F2 — Match header.** Home vs away, competition, date, kickoff, venue, final score. Sourced from a sidecar JSON beside each CSV (`<same-name>.json`), auto-paired by filename. Missing sidecar → the app falls back to parsing teams and date from the filename and shows the rest as unset, rather than erroring.

**F3 — Video panel.** YouTube link from the sidecar, embedded via `st.video`. Panel hidden entirely when no link is set.

**F4 — Stat sections.** Key Stats row, then General Play, Attack, Defence, Discipline as described in §5. Rendered as `st.metric` tiles in columns.

**F5 — Half filter.** First Half / Second Half selector governing the pitch map and, when "Full Match" is selected, the stat tiles. Default: **First Half** (per the requested behaviour). The control is prominent because attacking direction flips (§3.4).

**F6 — Event navigator (left column).** Scrollable list of the 13 event types, each showing its count for the current half and player filter. Clicking one selects it. **Single selection**, default **Goals**. Types with zero events under the current filter render disabled, not hidden, so the coach can see the count is genuinely zero.

**F7 — Pitch map (right column).** Club-supplied pitch SVG with the selected event type's markers overlaid:
- Point events → circles at (`pitch_x`, `pitch_y`)
- Key Pass → arrow from (`pitch_x`,`pitch_y`) to (`end_pitch_x`,`end_pitch_y`)
- Goals visually distinct from other shots
- Hover shows player, outcome, and duel type where present

**F8 — Player filter.** Dropdown above the pitch, default "All players", listing the 15 named players. Filters both the pitch markers and the event-navigator counts. 18 rows have no `player_name` and are grouped as "Unattributed" rather than dropped.

**F9 — Coordinate-less fallback.** When the selected type has no plottable rows (Corner, Save, Substitution, and the blank-coordinate subsets), the pitch area shows an explanatory notice and the events render beside it as a detail table (player, outcome, half, plus `sub_in_name` for substitutions). Nothing is hidden from the coach.

**F10 — Data completeness note.** A collapsed expander stating what is untracked in this file: possession, ordinary passes, opponent events, match minute on 258 rows, coordinates on 37 rows. This is the analyst's feedback loop and the club's honesty guarantee on a public page.

### Later (v2+)

- **L1** Multi-select event layers (Shots + Key Passes overlaid, colour-coded).
- **L2** Drill-down from event type to individual events, clicking one to highlight its marker.
- **L3** Per-player comparison view — stat table across the squad, sortable.
- **L4** Heatmap / zone density rendering as an alternative to point markers.
- **L5** Season aggregation across matches, once several are in `matches/`.
- **L6** Video deep-linking — jump to an event's clip. **Blocked** until `match_minute` is tagged reliably (currently 7% coverage).
- **L7** Possession and pass-accuracy tiles. **Blocked** on tagging-tool changes (§3.8, §3.9).
- **L8** Attack-direction normalisation toggle, if coaches ask for a combined full-match map.
- **L9** Opponent events, if the club begins tagging both teams.
- **L10** Mobile-responsive layout for players.

## 7. Technical validation — is this attainable in Streamlit?

Yes, all of MVP. Component by component:

| Requirement | Mechanism | Verdict |
|---|---|---|
| Two-column layout, stat tiles | `st.columns`, `st.metric` | Native |
| Match heading | `st.title` / `st.markdown` | Native |
| YouTube embed | `st.video(url)` — accepts YouTube URLs directly | Native |
| Scrollable event list | `st.container(height=…)` (Streamlit ≥1.29) with `st.button` per type | Native |
| Selection state across reruns | `st.session_state` | Native |
| Half switch | `st.segmented_control` (≥1.40) or `st.radio(horizontal=True)` | Native |
| Player filter | `st.selectbox` | Native |
| Pitch SVG + markers | Build one SVG string in Python — club pitch SVG as the base, `<circle>`/`<line>` children injected for events — rendered via `st.components.v1.html`. Full styling control, no markdown sanitiser, CSS hover tooltips available. | **Recommended approach** |
| Alternative pitch render | Plotly scatter with the pitch as a background image (`layout.images`, data-URI) — gives zoom, pan and native hover, at the cost of styling control | Viable fallback |
| Load performance | `st.cache_data` on CSV read; 278 rows is trivial | Native |
| Public deploy | Streamlit Community Cloud, GitHub-backed | Native |

**One genuine constraint:** `components.html` is one-way — the pitch cannot send clicks back to Python without a custom bidirectional component. This does not affect MVP, because all interaction happens through the left-column buttons and the filters. It *does* affect **L2** (click a marker to select an event), which would need either Plotly's `on_select` or a custom component. Noted so it is a v2 design decision rather than a v2 surprise.

## 8. Success metrics

**Primary**
- **Match review coverage:** ≥80% of tagged matches opened in the dashboard within 72 hours of the fixture. The dashboard exists to stop tagged matches going unreviewed.
- **Time to first insight:** a coach can state shots, shots on target and duel success from a cold open in under 30 seconds. Measured by timing three coaches once.

**Secondary**
- **Spreadsheet displacement:** zero manual Excel filtering of match CSVs by week 4.
- **Tagging quality:** share of rows with coordinates rises from 87% and match-minute coverage rises from 7%, driven by F10 making the gaps visible.
- **Public engagement:** unique visitors per published match page (stakeholder-facing goal).

**Guardrail**
- **Zero fabricated statistics.** No tile on the page shows a number the CSV does not support. This is a pass/fail check at every release, not a trend.

## 9. Edge cases

| Case | Present in data | Handling |
|---|---|---|
| Event type with no coordinates | Corner 9, Save 5, Substitution 4 | F9 notice + detail table |
| Partial coordinates within a type | 17/64 Possession Lost, 1/28 Shot | Plot what exists; footnote "17 of 64 have no recorded position" |
| Missing player name | 18 rows | Grouped as "Unattributed" in the filter; never dropped |
| Missing `outcome` on a Shot | 1 row | Counted in Total Shots only; listed in the completeness note |
| Zero events for a filter combination | e.g. Offside in 2nd half (0) | Type shown disabled with count 0, empty pitch with "No offsides in this half" |
| Reverse-ordered file | All rows | Reverse on load; never rely on file order for chronology |
| Attacking direction flip | H1 x≈0.20 vs H2 x≈0.76 | Raw coordinates retained; half selector is the mitigation; header caption states direction of attack |
| Substituted player | 4 subs | Player filter lists everyone who appears in `player_name`; `sub_in_name` players with no events do not appear (correct — they have no data) |
| Sidecar JSON missing or malformed | Likely on new matches | Graceful fallback to filename parsing; app must not crash |
| Coordinates outside 0–1 | None currently | Clamp and log rather than draw off-pitch |
| Empty or headers-only CSV | Not currently | Show "No events recorded for this match" instead of raising |
| Duels with neither won nor lost | None currently | Excluded from the Duels Won % denominator |
| Red card appears in a future match | 0 currently | Tile is already defined; needs no code change |

## 10. Out of scope (v1)

- **Possession %, total passes, accurate passes, pass accuracy** — removed from MVP, not stubbed. Returns only when the tagging pipeline supports it.
- **Opponent analysis** — no opponent events are tagged.
- **Timeline / minute-by-minute view and video deep-links** — `match_minute` is 7% populated.
- **xG or any modelled metric** — would require shot context the CSV does not carry.
- **Season and multi-match aggregation** — single-match views only.
- **Mobile-optimised layout.**
- **Editing or tagging inside the dashboard** — read-only over the CSV; the tagging tool stays the system of record.
- **Authentication, user accounts, per-user saved views.**
- **Attack-direction normalisation** — explicitly rejected for v1; raw coordinates as recorded.
- **Automated data ingestion** — files are placed in `matches/` manually.

**Privacy note for the public deploy:** publishing this page puts named, per-player performance data (turnovers, duels lost, cards) on a public URL. That is a club decision, not a technical one, and it should be made deliberately before the first deploy — particularly if any squad member is a minor. If it becomes a concern, the lowest-cost mitigation is a jersey-number-only display mode for the public build while the team-room build keeps names.

## 11. Build sequence

1. Data loader + stat engine (§5 definitions, half and player filters) — the correctness core.
2. Match header, sidecar JSON schema, video panel.
3. Stat sections.
4. Event navigator + pitch renderer, once the club supplies the pitch SVG.
5. Coordinate-less fallback and the completeness note.
6. Deploy to Streamlit Community Cloud.

**Dependency:** the pitch SVG is required for step 4. Steps 1–3 can proceed without it.
