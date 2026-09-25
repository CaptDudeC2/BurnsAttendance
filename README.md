# Burns Attendance

Staff-only daily attendance board for Burns Chevrolet Service. **Not** linked
from the Fixed Ops Pulse landing page — reachable from the Tech Pulse and
Advisor Pulse apps.

Live at: _(Streamlit URL after deploy)_

## How it works

Reads the "Attendance Calendar 2026-2027" Google Sheet (read-only, link-shared)
and shows who's out / who's here today, plus the week's notes.

## Note format (the contract)

Notes go in the cells **under the day number** in the month tab. The app
parses these patterns (case-insensitive):

- `Danny Called out` → out, reason "Called out"
- `PTO - Matt` → out, reason "PTO"
- Also understood: vacation, sick, bereavement/funeral, jury duty

Three ways a note gets in:

1. Christopher edits the sheet directly.
2. Little Bird writes it (same format).
3. Loki writes it when Christopher says e.g. "Danny Called out".

No hours tracking — presence only.

## Monday PTO run

Every Monday morning a scheduled job pulls the week's scheduled PTO and writes
`PTO - {FirstName}` into the first empty note cell under each PTO day. It never
overwrites existing notes (e.g. callouts). Exact PTO source per Christopher's
workflow video.

## Roster

Techs: Daniel "Danny" Estrada, Samuel "Sammy" Mosqueda, Angel Estrada,
Eugene Philpotts, Matthew "Matt" Wilson, Emmett Knapp, Mitchell Lanier,
Bradley "Brad" Lotze. Plus Felicia Foster (BDC), Dylan Patton and
Jessica Schurz (advisors).
