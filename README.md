# jadwal-pelayanan

Automated church service schedule generator. Assigns people and groups to service roles across a 3-month period while respecting spacing, availability, and load balancing constraints.

## Features

- **Configurable roles** — individual or group-based, with custom minimum gaps
- **Week alternation** — roles can be assigned to odd weeks (1st, 3rd, 5th Saturday), even weeks (2nd, 4th), or all weeks
- **Service type grouping** — related roles (e.g., `pemimpin-pa-besar` and `pemimpin-ibadah`) share gap enforcement
- **No duplicate assignments** — a person or group can only serve in one role per Saturday
- **Unavailability** — block specific people from specific dates, including multiple ranges per person (does not affect their group's assignment)
- **Locked-in overrides** — pin a specific person to a specific role/date; conflicts are flagged, not silently applied
- **Hidden roles** — pseudo-roles set only via overrides, with no output column, that still feed a `service_type`'s gap/count tracking
- **Load balancing** — distributes assignments evenly across candidates
- **Previous schedule continuity** — reads prior schedules to maintain proper spacing across quarters
- **Reproducible & re-rollable** — configurable seed; change it to get a different arrangement

## Requirements

- Python 3.10+
- `openpyxl` (only needed if using `.xlsx` previous schedules)

```bash
pip install openpyxl
```

## Quick Start

1. Edit the files in `rosters/` with your people/groups
2. Edit `groups.txt` with group membership
3. Edit `unavailability.txt` with date blackouts
4. Edit `config.txt` with your date range, roles, and seed
5. (Optional) Place prior schedule files in `previous_schedules/`
6. (Optional) Add locked-in assignments to `overrides.txt`
7. Run:

```bash
python scheduler.py
```

Output: `schedule_output.csv` — open in Excel or import to Google Sheets.

## File Structure

```
├── scheduler.py              # main program
├── config.txt                # configuration
├── groups.txt                # group membership
├── unavailability.txt        # date blackouts
├── overrides.txt             # locked-in role/date assignments
├── rosters/                  # one .txt file per role
│   ├── pemimpin-pa-besar.txt
│   ├── pemimpin-ibadah.txt
│   ├── pemusik-pa-besar.txt
│   ├── pemusik-ibadah.txt
│   ├── piket.txt
│   ├── masak.txt
│   ├── akomodasi.txt
│   └── multimedia.txt
├── previous_schedules/       # prior .csv or .xlsx files (untracked, folder kept via .gitkeep)
├── unit-tests/               # unit tests (python -m unittest discover -s unit-tests)
└── schedule_output.csv       # generated output
```

## Configuration

### config.txt

```
# Date range
scheduling_start: 2026-07-04
scheduling_end: 2026-09-26

# Change seed to get a different arrangement
seed: 42

# Role definitions
# format: role-name: min_gap=<weeks>, type=<individual|group>, week=<odd|even|all>, service_type=<name>
pemimpin-pa-besar: min_gap=4, type=individual, week=odd, service_type=pemimpin
pemimpin-ibadah: min_gap=4, type=individual, week=even, service_type=pemimpin
piket: min_gap=2, type=group, week=all
masak: min_gap=2, type=group, week=even
```

| Field | Description |
|-------|-------------|
| `min_gap` | Minimum weeks between assignments for the same person/group |
| `type` | `individual` (one person) or `group` (one group name) |
| `week` | `odd` (1st/3rd/5th Sat), `even` (2nd/4th Sat), or `all` |
| `service_type` | Optional. Roles sharing this value enforce gaps across each other |
| `hidden` | Optional, default `false`. No output column, never auto-assigned — only settable via `overrides.txt`, still counts toward its `service_type` siblings' gaps |

### rosters/\<role-name\>.txt

One candidate per line. For group-type roles, list group names. For individual-type roles, list person names.

```
# rosters/pemimpin-pa-besar.txt
Steffen
Aldi
Danny
```

```
# rosters/piket.txt
Group 1
Group 2
Group 3
```

### groups.txt

Maps group names to their members. Used to prevent a person from being individually assigned on the same day their group is serving.

```
Group 1: Wynnona, Toni, Wira, Trevor, Winston S, Andrew, Ellin M
Group 2: Aldi, Erico, Reynold, Nina, Beatrix, Jason, Kelly
```

### unavailability.txt

Block specific people/groups from specific dates. Supports single dates and ranges.

```
Toni: 2026-07-04 to 2026-09-26
John: 2026-08-01, 2026-08-08
```

Note: If a person is unavailable, their **group** can still be assigned — only the individual is excused from individual roles.

### overrides.txt

Lock a specific person into a specific role/date. The scheduler won't reassign it, and it still counts toward that person's history for future gap/load-balancing.

```
multimedia: 2026-09-05: Oliver
pembawa-khotbah: 2026-08-15: Steffen
```

- If the pin conflicts with unavailability or double-books someone already assigned that day, the run **stops with an error** — it never silently overrides or skips.
- A pin on an off-parity week (e.g. an odd-only role pinned to an even Saturday) is honored, not treated as a conflict.
- Works with `hidden` roles too (see `config.txt`) — e.g. `pembawa-khotbah` above has no output column but still gaps out its `pemimpin` siblings.

### previous_schedules/

Drop `.csv` or `.xlsx` files from prior quarters here. The scheduler reads them to:
- Enforce gaps across the quarter boundary
- Balance load considering prior assignments

Files must have a `Date` column and role-name columns matching `config.txt`.

## Changing the Schedule

Don't like the generated arrangement? Change the `seed` value in `config.txt` and re-run. Each seed produces a deterministic but different schedule.

## Constraints Summary

| Constraint | Type | Description |
|-----------|------|-------------|
| One role per person per day | Hard | A person appears at most once per Saturday |
| One role per group per day | Hard | A group name appears at most once per Saturday |
| Minimum gap | Hard | Weeks between same person/group in same role (or sibling roles) |
| Unavailability | Hard | Blocked dates for individuals |
| Override conflict | Hard | A pin conflicting with unavailability or double-booking stops the run |
| Group member conflict | Soft | If a group is assigned, its members are preferably not assigned individually |
| Load balancing | Soft | Prefer candidates with fewer total assignments |

## Testing

```bash
python -m unittest discover -s unit-tests
```

## License

Free to use and modify.
