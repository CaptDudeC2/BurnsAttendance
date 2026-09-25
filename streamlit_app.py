"""Burns Attendance - staff-only daily attendance board.

Reads the "Attendance Calendar 2026-2027" Google Sheet (link-shared, read-only)
and shows who's out and who's here today, plus the week's notes.

Staff only: NOT linked from the Fixed Ops Pulse landing page. Reached from
the Tech Pulse and Advisor Pulse apps.

This app is READ ONLY - all editing stays in the Google Sheet. Note format
the app parses (written in the cells under the day number in the month tab):
    "Danny Called out"  -> out, reason "Called out"
    "PTO - Matt"        -> out, reason "PTO"
"""

from datetime import date, timedelta

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


def month_tab_name(d):
    return d.strftime("%B %Y")


def day_notes(df, day):
    """Note strings written under the given day number in a month tab.

    Layout: a day-number row (several numeric cells), then 4 note rows.
    """
    rows = df.values.tolist()
    for i, row in enumerate(rows):
        cells = [str(c).strip() for c in row]
        if sum(c.isdigit() for c in cells) >= 3 and str(day) in cells:
            col = cells.index(str(day))
            notes = []
            for r in rows[i + 1 : i + 5]:
                if col < len(r):
                    v = str(r[col]).strip()
                    if v:
                        notes.append(v)
            return notes
    return []


def notes_for(d):
    tab = month_tab_name(d)
    gid = TAB_GIDS.get(tab)
    if not gid:
        return []
    return day_notes(load_tab(gid), d.day)


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


def closed_reason(d):
    """Holiday name if the shop is closed this date, else None."""
    if d.weekday() == 6:  # Sunday
        return "Sunday - shop closed"
    try:
        df = load_tab(TAB_GIDS["Closed Dates"])
    except Exception:
        return None
    iso = d.isoformat()
    for row in df.values.tolist():
        if len(row) >= 1 and str(row[0]).strip() == iso:
            return str(row[1]).strip() if len(row) > 1 else "Holiday - shop closed"
    return None


st.set_page_config(page_title="Burns Attendance", page_icon="🗓️", layout="centered")

st.title("🗓️ Burns Attendance")
st.caption("Staff only · Live from the Attendance Calendar · Read-only")

if st.button("↻ Refresh now"):
    st.cache_data.clear()
    st.rerun()

try:
    today = date.today()
    closed = closed_reason(today)
    todays_notes = [] if closed else notes_for(today)
except Exception as exc:
    st.error(
        "Couldn't load the calendar "
        "(is the sheet shared 'Anyone with the link'?): "
        f"{exc}"
    )
    st.stop()

st.subheader(today.strftime("%A, %B %d, %Y"))

if closed:
    st.warning(f"🏠 Shop closed — {closed}")
else:
    out = {}  # full name -> reason
    unnamed = []
    for note in todays_notes:
        name, reason = parse_note(note)
        if name:
            out[name] = reason
        elif reason:
            unnamed.append(f"{note} ({reason})")
        # notes with no reason keyword (e.g. holiday names) are ignored

    st.markdown("### ❌ Out today")
    if out or unnamed:
        for first, full, role in ROSTER:
            if full in out:
                st.write(f"**{full}** — {out[full]} ({role})")
        for u in unnamed:
            st.write(u)
    else:
        st.write("Everyone is in. 🎉")

    st.markdown("### ✅ Here today")
    here = [full for _f, full, _r in ROSTER if full not in out]
    st.write(", ".join(here) if here else "—")

st.markdown("---")
st.markdown("### This week")
monday = today - timedelta(days=today.weekday())
for i in range(6):  # Mon-Sat
    d = monday + timedelta(days=i)
    if d > today + timedelta(days=6):
        break
    try:
        cr = closed_reason(d)
        notes = [] if cr else notes_for(d)
    except Exception:
        cr, notes = None, []
    label = d.strftime("%a %m/%d")
    if cr:
        st.write(f"**{label}** — closed ({cr})")
    elif notes:
        st.write(f"**{label}** — " + "; ".join(notes))
    else:
        st.write(f"**{label}** — —")
