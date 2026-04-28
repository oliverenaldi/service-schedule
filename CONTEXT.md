# Project Context: jadwal-pelayanan (Church Service Scheduler)

## Purpose
Automated scheduling of church service roles for a 3-month period (quarterly), outputting a CSV compatible with Google Sheets/Excel.

## Architecture
Single-file Python script (`scheduler.py`) using a greedy algorithm with scoring.

## Core Concepts

### Service Types
Roles can share a `service_type` (e.g., `pemimpin-pa-besar` and `pemimpin-ibadah` both belong to `pemimpin`). The minimum gap is enforced **across** sibling roles sharing the same service_type.

### Week Alternation
- **odd** = 1st, 3rd, 5th Saturday of the month (pa-besar services)
- **even** = 2nd, 4th Saturday of the month (ibadah services)
- **all** = every Saturday

Roles active only on even weeks: `pemimpin-ibadah`, `pemusik-ibadah`, `masak`, `akomodasi`, `multimedia`
Roles active only on odd weeks: `pemimpin-pa-besar`, `pemusik-pa-besar`
Roles active every week: `piket`

### Assignment Types
- **individual** — one person per role per Saturday
- **group** — one group name per role per Saturday (group assigned as a unit)

## Hard Constraints (must never be violated)
1. A person cannot be assigned to two different roles on the same Saturday
2. A group cannot be assigned to two different roles on the same Saturday
3. Minimum gap (in weeks) between same person/group in the same role (or sibling roles sharing service_type)
4. Individual unavailability blocks individual role assignments

## Soft Constraints (best effort)
1. When a group is assigned, its members are marked as "used" to avoid individual assignment on the same day — but this is soft, meaning if no other candidate is available, it can be overridden
2. Load balancing — prefer candidates with fewer total assignments

## Scoring (Greedy Selection)
For each slot, eligible candidates are scored by:
1. Total assignment count (lower = better), combined across sibling roles
2. Days since last assignment (higher = better)
3. Random tiebreaker (controlled by seed)

Roles are processed in order of most constrained first (fewest eligible candidates).

## Key Design Decisions
- Unavailability does NOT cancel group assignments — only the individual is excused, the group still serves
- Previous schedules (CSV or XLSX) feed into history for continuity across quarters
- Seed is configurable for reproducibility and re-rolling

## File Structure
```
├── scheduler.py              # main program
├── config.txt                # role definitions, gaps, date range, seed
├── groups.txt                # group name → member mapping
├── unavailability.txt        # per-person date blackouts
├── rosters/
│   └── <role-name>.txt       # one candidate per line
├── previous_schedules/       # drop prior .csv/.xlsx files here
└── schedule_output.csv       # generated output
```

## Potential Future Improvements
- Backtracking or CSP solver if greedy produces empty slots
- Weighted soft constraints (configurable priority)
- Multi-service days (morning + evening)
- Web UI or Google Sheets integration for input
- Validation report showing constraint violations or near-misses
- Support for partial manual overrides (lock certain assignments, schedule the rest)
- Per-person max assignments per quarter
- Holiday/special event handling (skip certain Saturdays or assign specific people)
