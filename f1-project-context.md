# F1 26 Project — Full Context Briefing

Paste this at the start of a new Claude chat to resume with zero context loss.

---

## What This Project Is

Seif races F1 26 Career Mode (Haas F1 Team, Difficulty 105, in-game name "Safox Safox"). He also builds his own Python telemetry-capture app (`listener.py`) that hooks into the F1 26 UDP stream and exports race/quali/practice data. There are two persistent deliverables:

1. **`f1-26-setup-guide.html`** — a single-file HTML/CSS/JS app that generates F1 26 car setups from a formula. Seif races the app-generated "Stable" setup each weekend and we track how well it matches the in-game recommended setup value-by-value (18 parameters).
2. **`f1-26-career-season-log.md`** — a running season log tracking setup-match accuracy, race/quali results, tyre degradation per stint, telemetry app bugs, and cross-track patterns.

Both files live at:
`C:\Users\seifk\AppData\Roaming\Claude\local-agent-mode-sessions\cd4671e5-ccd7-4b3c-b8c8-a70affa94819\fc00dcf7-ab00-4f21-82fc-e31aabe84df8\local_e1335665-0ae2-4223-9491-421814059b36\outputs\`

---

## CRITICAL STANDING CONSTRAINT — Never Violate

Verbatim from Seif: *"no i dont want you to copy the setups i just want you to know the ranges of the number inputs you get what i mean iu will test your setups and we will se"*

**What this means in practice:**
- Real-world raced setup data may be compared against the app's formula output (setup-match verification).
- Real-world data must NEVER be used to calibrate, copy, or adjust the `genSetup` formula logic itself.
- The formula is the fixed control baseline. We validate against it, not into it.

**New rule added (confirmed by Seif):** The Corner Balance / wheel-slip data can be used to suggest manual setup tweaks for Seif to test in-game. These are ad-hoc engineering suggestions SEPARATE from the app's formula. Formula stays untouched.

---

## The App — Structure & Formula

**File:** `f1-26-setup-guide.html` (read it directly if you need exact formula code)

**Key structures:**
- `TRACKS` array: 24 circuits, each with `tags: {df, tr, br, bm, kb, gr, td}` (downforce, traction, braking, brake management, kerb, grip, tyre deg — all 0-10 scale) and `corners: {slow, medium, fast}` counts.
- `STYLE` object: `stable` and `aggressive` delta objects.
- `genSetup(track, styleKey)` → produces 18 output parameters.
- Helpers: `clip(v, lo, hi)`, `r0` (round to int), `r1` (1dp), `r2` (2dp), `r5` (nearest 0.5).
- **JS rounding caveat**: JavaScript `Math.round` is half-up. Python's `round()` is banker's rounding. Matters when hand-verifying formula outputs in Python — replicate JS behavior explicitly.

**The 18 output parameters:** Front Wing, Rear Wing, On-Throttle Diff, Off-Throttle Diff, Front Camber, Rear Camber, Front Toe, Rear Toe, Front Suspension, Rear Suspension, Front ARB, Rear ARB, Front Ride Height, Rear Ride Height, Brake Pressure, Brake Bias, Front Tyre Pressure, Rear Tyre Pressure.

(Engine Braking, Ballast, and Fuel Load are also set in-game but are NOT part of the app's 18 formula outputs — they're constants and don't count toward the match score.)

**Setup match verification methodology:**
1. Manually compute `genSetup(track, "stable")` for the given track's tags/corners.
2. Compare value-by-value against Seif's raced setup.
3. Report N/18 matching.
4. Current streak: **Suzuka 17/18 → Bahrain 18/18 → Saudi Arabia 18/18 → Miami 18/18 → Montreal 18/18 → Monaco 18/18** (6 rounds).

---

## Tyre Degradation Methodology

- **Formula:** (last clean lap time − peak lap time) ÷ number of lap-to-lap intervals = avg s/lap degradation.
- **Peak lap** = fastest representative lap of the stint (usually lap 2-3 of stint after out-lap warm-up).
- **Exclude:** out-laps, in-laps, standing-start lap 1, pit laps (anomalously slow).
- **Always ask Seif push vs. manage per stint** before locking in interpretation. Push stints inflate the number; managed stints suppress it. This is now a confirmed, standing practice — confirmed at Montreal (150%+ spread between push/managed) and re-confirmed at Monaco (track-dependent: push/managed barely moved the number there, ~10-15% spread vs Montreal's 150%+).

---

## Season Results & Log Summary

The full detailed log is in `f1-26-career-season-log.md`. Summary of all logged rounds:

### Round 3 — Suzuka — 17/18 setup match
- Race: P12 → P1 (win, 27 laps). 2-stop: Medium/Hard/Soft.
- Deg: Medium ~0.35, Hard ~0.15, Soft ~0.49 s/lap. Push/manage not confirmed (pre-policy).

### Round 4 — Bahrain — 18/18 setup match (perfect)
- Race: P10 → P3 (podium, 29 laps). 3-stop: Soft/Hard/Medium.
- Deg: Soft ~0.46, Hard ~0.24* (noisy), Medium ~0.21 s/lap. *Push/manage not confirmed.

### Round 5 — Saudi Arabia (Jeddah) — 18/18 setup match (perfect)
- Race: started last → P9 (25 laps). Double-pit error on laps 13-14 cost positions from P1.
- Deg: Hard ~0.21* (noisy, constant overtaking), Medium ~0.28, Soft discarded (2 laps).

### Round 6 — Miami (Sprint Weekend) — 18/18 setup match (perfect)
- Sprint: P5. Race: P1 (win, no telemetry captured).
- Front wing experiment: fw=37 tested vs Stable fw=33, showed marginal benefit in Sprint S1 but inconclusive — needs controlled retest before touching formula.
- Deg (sprint only): Medium ~0.36 s/lap. Highest Medium deg recorded.

### Round 7 — Montreal — 18/18 setup match (perfect)
- Qualifying (Q3): P3. Position column in export showed P10 (known bug, stale field — confirmed P3 directly).
- Race: P3 start → P1 by end of lap 1, held through lap 34. 2-stop: C5/C4/C6 (Medium/Hard/Soft inferred).
- Deg: Medium (C5) ~0.38 push, Hard (C4) ~0.15 managed, Soft (C6) ~0.28 low-confidence.
- Key note: session was originally labeled "Type 16" (stale header from prior session) — now confirmed as the Race; see stale-session-snapshot bug below.

### Round 8 — Monaco — 18/18 setup match (perfect, rear wing at hard-clip ceiling 50)
- Qualifying: Q1 P10, Q2 P3, Q3 **P1 (pole)** — best 1:10.883, 0.186s clear of Piastri.
- Race: P1 → P1 (lights-to-flag win, 39 laps, 50% distance). Margin +4.819s over Norris. 2-stop: C4/C3/C3 (Medium/Hard/Hard).
- Race export was mislabeled "Sprint Shootout 2" (stale-session-snapshot bug) with 5.0kg fuel in setup block (vs actual ~30.6kg race fuel). This is the cleanest evidence of the bug mechanism.
- Deg: Medium (C4) ~0.26 push, Hard (C3 stint 1) ~0.25 managed, Hard (C3 stint 2) ~0.28 push. All in tight ~0.03s band — Monaco is track-driven, push/manage barely matters here.
- Corner Balance (new export feature): 8/9 corners understeering, strongest at C9 (-0.032) and Casino/C8 (-0.030). One oversteer at Sainte Devote entry (+0.016). Will use this data for future manual setup tweaks (ad-hoc, separate from formula).

### Round 10 — Madring/Madrid — Setup match PENDING
- Only data so far: Time Trial (8 laps, Soft/C5). Best lap 1:29.684, theoretical best 1:29.512.
- Time Trial caveats: fuel locked 10.0kg, wear 0.0%, ERS pinned 100% — data only useful for line/throttle-brake analysis.
- Setup was NOT the app-generated Stable setup — Seif used a custom setup. Values not yet shared. Match check pending.
- No race/quali data yet.

---

## Tyre Degradation Tracker (current)

| Track | Medium (s/lap) | Hard (s/lap) | Soft (s/lap) | Notes |
|---|---|---|---|---|
| Suzuka | ~0.35 | ~0.15 | ~0.49 | Push/manage unconfirmed |
| Bahrain | ~0.21 | ~0.24* | ~0.46 | *Hard noisy (traffic + collision) |
| Saudi Arabia | ~0.28 | ~0.21* | — | *Hard noisy (constant overtaking) |
| Miami | ~0.36 | — | — | Sprint only, no Hard |
| Montreal | ~0.38† | ~0.15‡ | ~0.28* | †Push. ‡Managed. *Low confidence |
| Monaco | ~0.26§ | ~0.25-0.28§ | — | §All confirmed push/managed — yet ~0.03s apart. Monaco is track-driven |

---

## Telemetry App — Export Formats Seen

Seif's `listener.py` has evolved through multiple export generations:

1. **Lap-summary-only CSV** — early format, buggy (S1/S2 blank, S3=full lap time).
2. **Merged CSV** — full ~20Hz telemetry rows + CAR SETUP blocks per session.
3. **Time Trial CSV** — no setup data, fuel/wear/ERS locked (game constraint).
4. **Markdown "AI summary" reports** — current format:
   - `Car Setup` block (wings, diff, suspension, camber, toe, ride height, brakes, tyre PSI, fuel, ballast)
   - `Lap Times` table: Lap / Time / S1 / S2 / S3 / Compound / Age / Note (gap-to-best or BEST flag)
   - `Per-Lap Telemetry Averages`: AvgSpd / MaxSpd / Thr% / Brk% / ERS% / Fuel(kg)
   - `Tyre Wear & Blisters`: W-FL/FR/RL/RR and B-FL/FR/RL/RR per lap (%)
   - `Wheel Slip`: FL/FR/RL/RR avg absolute per lap
   - `Corner Balance` *(new, first seen Monaco race re-export)*: per-corner oversteer/understeer from wheel-slip deviation vs straight-line baseline. Positive = oversteer, negative = understeer.
   - `Final Classification` *(in merged multi-session files)*: Pos / Driver / Laps / Best Lap / Total Time / Penalties

**Merged files** contain multiple sessions concatenated, each with their own header block.

---

## Bug Taxonomy — Current Status

### Fixed
| Bug | Fix |
|---|---|
| Duplicate Classification rows (Q1 2x, Q3 40x+) | `UNIQUE(session_uid, car_idx)` + `ON CONFLICT DO UPDATE` — deduplicates on next restart |
| `SESSION_TYPE_LABELS` map wrong for types 10-17 | Full map corrected; `sessionBadgeClass` updated (races red, quali/shootouts blue, practice green, TT yellow) |
| Track ID 42 not resolving | Added ID 42 → Madrid (plus 34-44 range for 2026 tracks) |
| Track length 0 | Shows "?" placeholder *(caveat: Monaco Practice 2 re-export still printed "0 m" — fix may not cover this report path)* |
| Position column in quali exports | Removed from lap times table for non-race sessions (Q1/Q2/Q3/Sprint Shootouts) |
| Session type in CSV header | Now shows resolved name instead of raw integer |
| Sector times S1/S2 blank in early exports | Fixed in earlier session |

### Explained / Not Code-Fixable
| Bug | Status |
|---|---|
| Q3 header showing Track "—" / Session "Unknown" | DB row written before game sent session packet (listener started mid-session). Null fields, not a mapping bug. Not retroactively fixable. If recurs = listener started mid-session again |
| Montreal lap 35 interleaved rows | Game-side issue at session end (duplicate frames under same lap number). Not fixable without knowing source |
| Tyre wear not resetting cleanly on practice pit stop (Monaco P2 lap 6 showed ~19.7% on fresh C5) | Needs more investigation into how game reports wear on newly fitted tyre during practice stop |

### Still Open / Under Investigation
| Bug | Status |
|---|---|
| `ActiveAero(0=Corner,1=SLM)` always reads 0 despite 300+ kph speeds | Seif running AERO_HUNT logging in listener.py at >280kph to find correct byte offset in packet struct |
| **Stale session-type/setup snapshot** — Race exports inherit the previous session's session-type code + Car Setup block (including qualifying-low fuel load). Confirmed at both Montreal (Type 16 header on Race, 5.0kg fuel) and Monaco (Sprint Shootout 2 header on Race, 5.0kg fuel vs 30.6kg actual). | Mechanism understood; not yet fixed in code. Consequence: session-type label wrong, fuel in setup block unreliable, Pos column dropped from Race lap table (because listener thinks it's a qualifying session). Race telemetry/lap times/wear/classification data is still trustworthy. |
| Final lap missing from Lap Times table while present in Telemetry/Wear/Wheel-Slip | Seen at Montreal (lap 35) and Monaco race (lap 39). Lap-summary writer finalizes slightly before per-lap-telemetry writer at session end |
| Corner Balance: Sainte Devote appears twice (27m oversteer +0.016, 179m understeer -0.030) | Likely entry vs exit sampling, not a bug — but worth confirming |

---

## Standing Workflow for Each New Race Weekend

When Seif uploads new telemetry data:

1. **Identify the session type** from file structure (not the header label — the label may be stale). A Race is: multiple stints, tyre-wear resets at pit stops, fuel draining over 20+ laps, full field in Final Classification.
2. **Verify setup match**: compute `genSetup(track, "stable")` from the app's formula and compare value-by-value against the Car Setup block in the export. Report N/18. (Exclude Fuel Load from match count on Race exports — it's likely a stale prior-session value.)
3. **Log quali result**: note session type (Q1/Q2/Q3), best lap, position. Position column in export is unreliable for qualifying sessions (removed) — confirm position from Final Classification table instead.
4. **Race narrative**: start position, end position, strategy (compound codes + lap ranges), fastest lap, key incidents.
5. **Tyre degradation per stint**: peak lap → last clean lap ÷ intervals. Then **ask Seif push or managed per stint** before locking in reliability interpretation.
6. **Bug-flag any new anomalies** in the data.
7. **Update `f1-26-career-season-log.md`** with all of the above.
8. **Ask** about anything that could be push-vs-manage or otherwise ambiguous before assuming.

---

## Compound Coding Convention

Compound C-numbers shift by track (different compounds nominated per race). General rule:
- Higher C-number = softer compound within a given race weekend's nominated set.
- E.g., Monaco: C3=Hard, C4=Medium, C5=Soft (softer end of the range, low-deg track).
- E.g., Montreal: C4=Hard, C5=Medium, C6=Soft (harder end of range, higher energy).
- Infer from strategy logic (first stint is usually Medium, final stint is Soft or Hard depending on race length).

---

## Key Cross-Track Patterns (Running Observations)

- **Setup match streak is 6 rounds deep** (17/18 or 18/18 every round). Formula appears to track the game's own recommendation logic closely across very different circuit types.
- **Soft degradation looks compound-driven** (~0.46-0.49s/lap at Suzuka and Bahrain regardless of track character). Montreal's Soft (~0.28) is low-confidence (managed stint). Monaco ran no Soft in race.
- **Push/manage matters a lot at high-energy tracks** (Montreal: 150%+ spread). Almost doesn't matter at low-energy tracks (Monaco: ~10-15% spread). Track-energy appears to be the variable.
- **Double/extra pit stops have cost positions** at Saudi Arabia (laps 13-14 double stop) — worth being deliberate about strategy calls.
- **Front wing experiment (fw=37 vs Stable fw=33 at Miami):** fw=37 showed marginal S1 benefit under confounded conditions. Verdict inconclusive — needs clean same-compound same-conditions back-to-back test before touching formula.
- **Session-type/setup snapshot lags one session behind:** confirmed mechanism at both Montreal and Monaco. Race data is still valid; just ignore the session header label and fuel field from the Car Setup block on Race exports.
- **A session's final lap drops from Lap Times but not Telemetry/Wear** — seen twice (Montreal, Monaco). Treat lap count in Final Classification as authoritative, not Lap Times table row count.
- **Corner Balance data** (new export feature, Monaco race): understeer dominant at 8/9 corners. Will use for manual setup tweak suggestions to Seif — NOT for adjusting the genSetup formula.

---

## What's Pending

- **Round 10 Madrid**: setup values not yet shared, no race/quali data. Time Trial data already logged.
- **Stale-session-snapshot bug**: mechanism confirmed, not yet fixed in listener.py.
- **ActiveAero byte offset**: Seif is actively hunting it via AERO_HUNT logging.
- **Front wing fw=37 retest**: needs a clean, controlled back-to-back at a future track.
- **Corner Balance at other tracks**: first data point is Monaco (heavy understeer). Need more tracks to tell if this is Monaco-specific or a general car characteristic.
