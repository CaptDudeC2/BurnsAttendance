"""Burns Attendance - staff-only daily attendance board.

Reads the "Attendance Calendar 2026-2027" Google Sheet (link-shared, read-only)
and renders it like the AT-A-GLANCE wall calendar in the shop: a monthly grid,
Sunday-Saturday, with the day number and notes in each cell. Today gets a
blue outline; Sundays and dealership holidays are greyed out.

Top strip shows today's out/here summary. Staff only: NOT linked from the
Fixed Ops Pulse landing page. Reached from the Tech Pulse, Advisor Pulse,
and Dispatch apps.

This app is READ ONLY - all editing stays in the Google Sheet. Note format
the app parses (written in the cells under the day number in the month tab):
    "Danny Called out"  -> out, reason "Called out"
    "PTO - Matt"        -> out, reason "PTO"
"""

from datetime import date
from html import escape

import pandas as pd
import streamlit as st

SHEET_ID = "1PZPpWbfWYGi1SqjvEMtAPpxukRTxnrnlqQWHNSZ4pRI"

# Month tab name -> gid. Tabs are fixed Sept 2026 - Dec 2027.
TAB_GIDS = {
    "September 2026": "1000",
    "October 2026": "1001",
    "November 2026": "1002",
    "December 2026": "1003",
    "January 2027": "1004",
    "February 2027": "1005",
    "March 2027": "1006",
    "April 2027": "1007",
    "May 2027": "1008",
    "June 2027": "1009",
    "July 2027": "1010",
    "August 2027": "1011",
    "September 2027": "1012",
    "October 2027": "1013",
    "November 2027": "1014",
    "December 2027": "1015",
    "Closed Dates": "1016",
}
MONTHS = [m for m in TAB_GIDS if m != "Closed Dates"]

# (first name as written in calendar notes, full name, role)
ROSTER = [
    ("Danny", "Daniel Estrada", "Technician"),
    ("Sammy", "Samuel Mosqueda", "Technician"),
    ("Angel", "Angel Estrada", "Technician"),
    ("Eugene", "Eugene Philpotts", "Technician"),
    ("Matt", "Matthew Wilson", "Technician"),
    ("Emmett", "Emmett Knapp", "Technician"),
    ("Mitchell", "Mitchell Lanier", "Technician"),
    ("Brad", "Bradley Lotze", "Technician"),
    ("Felicia", "Felicia Foster", "BDC"),
    ("Dylan", "Dylan Patton", "Advisor"),
    ("Jessica", "Jessica Schurz", "Advisor"),
]

# keyword (lowercase) -> display reason, checked in order
REASONS = [
    ("called out", "Called out"),
    ("call out", "Called out"),
    ("callout", "Called out"),
    ("pto", "PTO"),
    ("vacation", "Vacation"),
    ("sick", "Sick"),
    ("bereavement", "Bereavement"),
    ("funeral", "Bereavement"),
    ("jury duty", "Jury duty"),
]


@st.cache_data(ttl=300)
def load_tab(gid):
    """Load one sheet tab as a dataframe of strings (no header)."""
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/export?format=csv&gid={gid}"
    )
    return pd.read_csv(url, header=None, dtype=str).fillna("")


@st.cache_data(ttl=3600)
def closed_map():
    """ISO date -> holiday name from the Closed Dates tab."""
    try:
        df = load_tab(TAB_GIDS["Closed Dates"])
    except Exception:
        return {}
    out = {}
    for row in df.values.tolist():
        if len(row) >= 1 and str(row[0]).strip():
            name = (
                str(row[1]).strip()
                if len(row) > 1 and str(row[1]).strip()
                else "Closed"
            )
            out[str(row[0]).strip()] = name
    return out


def month_weeks(df):
    """Parse a month tab into weeks; each week is 7 cells (Sun..Sat).

    A cell is None (blank) or (day_number, [note strings]).
    Layout: a day-number row (several numeric cells), then 4 note rows.
    """
    rows = df.values.tolist()
    weeks = []
    i, n = 0, len(rows)
    while i < n:
        cells = [str(c).strip() for c in rows[i]]
        if sum(c.isdigit() for c in cells) >= 3:
            week = []
            for col in range(7):
                c = cells[col] if col < len(cells) else ""
                if c.isdigit():
                    notes = []
                    for r in rows[i + 1 : i + 5]:
                        if col < len(r):
                            v = str(r[col]).strip()
                            if v:
                                notes.append(v)
                    week.append((int(c), notes))
                else:
                    week.append(None)
            weeks.append(week)
            i += 5
        else:
            i += 1
    return weeks


def parse_note(note):
    """Return (full_name, reason). Name may be None if no roster match."""
    low = note.lower()
    reason = None
    for key, label in REASONS:
        if key in low:
            reason = label
            break
    if not reason:
        return None, None
    for first, full, _role in ROSTER:
        if first.lower() in low or full.lower() in low:
            return full, reason
    return None, reason


def note_class(note):
    """CSS class for a calendar cell note."""
    _name, reason = parse_note(note)
    if reason in ("PTO", "Vacation"):
        return "pto"
    if reason in ("Called out", "Sick"):
        return "out"
    if reason:
        return "other"
    return "holiday"


CAL_CSS = """
<style>
.cal{border:2px solid #1a1a1a;border-radius:4px;overflow:hidden;
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}
.cal-row{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));}
.cal-h{background:#1a1a1a;color:#fff;font-weight:700;text-align:center;
padding:7px 2px;font-size:13px;}
.cal-c{border:1px solid #d5d5d5;min-height:92px;padding:4px 5px;background:#fff;}
.cal-c .dn{font-weight:700;font-size:14px;line-height:1.1;}
.cal-c.today{box-shadow:inset 0 0 0 3px #0B74C5;background:#eef6ff;}
.cal-c.shut{background:#f2f2f2;}
.cal-c.shut .dn{color:#999;}
.note{font-size:12px;margin-top:3px;line-height:1.3;word-break:break-word;}
.note.pto{color:#0B74C5;font-weight:600;}
.note.out{color:#c0392b;font-weight:600;}
.note.other{color:#333;}
.note.holiday{color:#8a8a8a;font-style:italic;}
@media (max-width:640px){.cal-c{min-height:74px;}.note{font-size:11px;}.cal-h{font-size:11px;}}
</style>
"""


def render_month(year, month, weeks, closed, today):
    """Build the calendar-grid HTML for one month."""
    parts = [CAL_CSS, '<div class="cal">']
    parts.append(
        '<div class="cal-row">'
        + "".join(f'<div class="cal-h">{d}</div>' for d in
                  ["Sunday", "Monday", "Tuesday", "Wednesday",
                   "Thursday", "Friday", "Saturday"])
        + "</div>"
    )
    for week in weeks:
        parts.append('<div class="cal-row">')
        for col, cell in enumerate(week):
            if cell is None:
                parts.append('<div class="cal-c"></div>')
                continue
            daynum, notes = cell
            d = date(year, month, daynum)
            iso = d.isoformat()
            classes = ["cal-c"]
            if d == today:
                classes.append("today")
            shut_name = closed.get(iso)
            if col == 6 or shut_name:  # Sunday or holiday
                classes.append("shut")
            inner = [f'<div class="dn">{daynum}</div>']
            if shut_name:
                inner.append(
                    f'<div class="note holiday">{escape(shut_name)}</div>')
            for note in notes:
                inner.append(
                    f'<div class="note {note_class(note)}">'
                    f"{escape(note)}</div>")
            parts.append(
                f'<div class="{" ".join(classes)}">{"".join(inner)}</div>')
        parts.append("</div>")
    parts.append("</div>")
    return "".join(parts)


st.set_page_config(page_title="Burns Attendance", page_icon="🗓️", layout="wide")

st.title("🗓️ Burns Attendance")
st.caption("Staff only · Live from the Attendance Calendar · Read-only")

if st.button("↻ Refresh now"):
    st.cache_data.clear()
    st.rerun()

try:
    today = date.today()
    closed = closed_map()
    cur_name = today.strftime("%B %Y")
    cur_idx = MONTHS.index(cur_name) if cur_name in MONTHS else 0
    if "moff" not in st.session_state:
        st.session_state.moff = 0
    st.session_state.moff = max(-cur_idx,
                                min(len(MONTHS) - 1 - cur_idx,
                                    st.session_state.moff))
    sel = MONTHS[cur_idx + st.session_state.moff]
    year, mon = int(sel.split()[1]), [
        "January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December",
    ].index(sel.split()[0]) + 1
    weeks = month_weeks(load_tab(TAB_GIDS[sel]))
except Exception as exc:
    st.error(
        "Couldn't load the calendar "
        "(is the sheet shared 'Anyone with the link'?): "
        f"{exc}"
    )
    st.stop()

# ---- today strip ----
st.subheader(today.strftime("%A, %B %d, %Y"))
closed_today = closed.get(today.isoformat())
if today.weekday() == 6 or closed_today:
    st.warning(f"🏠 Shop closed — {closed_today or 'Sunday'}")
else:
    todays_notes = []
    for week in weeks:
        for cell in week:
            if cell and cell[0] == today.day and sel == cur_name:
                todays_notes = cell[1]
    out = {}
    unnamed = []
    for note in todays_notes:
        name, reason = parse_note(note)
        if name:
            out[name] = reason
        elif reason:
            unnamed.append(f"{note} ({reason})")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**❌ Out today**")
        if out or unnamed:
            for _f, full, role in ROSTER:
                if full in out:
                    st.write(f"**{full}** — {out[full]} ({role})")
            for u in unnamed:
                st.write(u)
        else:
            st.write("Everyone is in. 🎉")
    with c2:
        st.markdown("**✅ Here today**")
        here = [full for _f, full, _r in ROSTER if full not in out]
        st.write(", ".join(here) if here else "—")

# ---- month grid ----
st.markdown("---")
n1, n2, n3 = st.columns([1, 4, 1])
with n1:
    if st.button("◀ Prev", disabled=(cur_idx + st.session_state.moff) <= 0):
        st.session_state.moff -= 1
        st.rerun()
with n2:
    st.markdown(f"<h3 style='text-align:center;margin:0'>{sel}</h3>",
                unsafe_allow_html=True)
with n3:
    if st.button("Next ▶",
                 disabled=(cur_idx + st.session_state.moff) >= len(MONTHS) - 1):
        st.session_state.moff += 1
        st.rerun()

st.markdown(render_month(year, mon, weeks, closed, today),
            unsafe_allow_html=True)
st.caption("Notes are written in the Attendance Calendar sheet — "
           "this page is read-only.")
