# F1 26 Career Mode — Season Tracking Log

Running record of races, setups used (from the F1 26 Setup Guide app), results, and what each weekend told us about whether the app's formula-generated setups hold up in real racing conditions.

**How to use this**: At the start of any new session, share this file plus your latest race/quali data, and pick up the analysis from there — no need to re-explain prior results.

---

## Round 3 — Suzuka (Japan) — Haas F1 Team

**Setup used**: App-generated Suzuka "Stable" setup (matched almost exactly — 17/18 values identical; only Off-Throttle Diff differed, app=45 vs in-game=40, a single slider increment apart).

| Setting | Value |
|---|---|
| Front/Rear Wing | 40 / 43 |
| On/Off-Throttle Diff | 60 / 40 |
| Front/Rear Camber | -3.3 / -1.8 |
| Front/Rear Toe | 0.16 / 0.18 |
| Front/Rear Suspension | 18 / 20 |
| Front/Rear ARB | 14 / 13 |
| Front/Rear Ride Height | 25 / 51 |
| Brake Pressure / Front Bias | 90 / 53 |
| Tyre Pressures (F/R) | 24.7 / 21.5 |

### Qualifying
- Best lap: **1:30.336** (personal best by -0.369s, gains spread evenly across all 3 sectors)
- Tyre wear pattern: front-left wore ~2x faster than rears (4.3% vs ~2.1-2.2%) — likely track-inherent (Suzuka's Esses load the left-front hard), not a setup flaw
- Notable: heavy gearbox/engine damage (18%/36%) even this early — later explained by lap-1 race contact

### Race (27 laps, Dry, Difficulty 105)
- **Started P12 → Finished P1** (win, 25 points) — gained 11 positions
- Survived 7x "Small Collision" warnings on lap 1 (midfield pack chaos from starting P12) — already recovered to P8 by lap 1's end
- Took the race lead by ~lap 9-10; defended it through 2 pit stops (laps 10 and 22)
- 2-stop strategy: Medium (1-10) → Hard (11-22) → Soft (23-27)
- Fastest lap: 1:31.728 (lap 24, fresh Softs) — **3rd fastest of the entire race**, ahead of Verstappen, Norris, Leclerc
- Won by 0.434s over Russell (Mercedes) — tightest possible margin

### Tyre Degradation (lap-time fall-off per stint)
Using each stint's peak (fastest representative) lap as the baseline and tracking how lap times rose from there to the last clean lap before pitting (excludes out-laps, in-laps, and the chaotic opening lap):

| Compound | Stint | Peak lap → Last clean lap | Total fall-off | Avg deg/lap |
|---|---|---|---|---|
| Medium | Laps 2–9 (8 laps) | 1:32.080 → 1:34.503 | +2.423s | **~0.35s/lap** |
| Hard | Laps 13–21 (9 laps) | 1:32.237 → 1:33.433 | +1.196s | **~0.15s/lap** |
| Soft | Laps 24–27 (4 laps) | 1:31.728 → 1:33.209 | +1.481s | **~0.49s/lap** |

Pattern matches expected compound behavior — Soft is fastest out the box but degrades fastest (~3x the Hard rate), Hard is the most stable over a long stint, Medium sits in between. Useful baseline number for Suzuka specifically: roughly **0.15 / 0.35 / 0.49 s of lap-time loss per lap** for Hard/Medium/Soft respectively, under these track/weather/setup conditions. Worth checking whether these rates hold at other tracks or shift with temperature, surface abrasiveness, or downforce level.

### Takeaway
Strongest validation data point so far: the formula-generated setup didn't just produce one good lap — it held up across 3 tyre compounds, changing fuel loads, contact damage, and a full race distance, in a backmarker car, recovering from deep in the pack. That's a much harder thing to fake than a single qualifying lap.

---

## Round 4 — Bahrain (Sakhir) — Haas F1 Team

**Setup used**: App-generated Bahrain "Stable" setup — **PERFECT 18/18 match**, every single value identical to what was raced (even better than Suzuka's 17/18).

| Setting | Value |
|---|---|
| Front/Rear Wing | 30 / 31 |
| On/Off-Throttle Diff | 50 / 50 |
| Front/Rear Camber | -3.0 / -1.5 |
| Front/Rear Toe | 0.12 / 0.23 |
| Front/Rear Suspension | 13 / 15 |
| Front/Rear ARB | 7 / 5 |
| Front/Rear Ride Height | 27 / 53 |
| Brake Pressure / Front Bias | 87 / 56 |
| Tyre Pressures (F/R) | 24.7 / 21.8 |

### Race (29 laps, Dry)
- **Started P10 → Finished P3** (podium, 15 points) — gained 7 positions
- 3-stop strategy: Soft (1-8) → Hard (9-20) → Medium (21-29)
- Ran as high as **P1** on laps 18-19 before the second stop, then pitted from the lead and recovered to P3
- Best lap: **1:31.039** (lap 22, fresh Mediums) — roughly 7th-fastest lap of the race (Russell topped it at 1:30.488)
- Minor fracas: 2x "Small Collision" warnings on lap 1, another on lap 12, plus 2x "Crossed Pit Exit Lane" warnings (laps 21-22) — none carried time penalties
- Notable: Antonelli posted the 5th-fastest lap of the race (1:30.929) but finished P21, over 4 minutes down — clear sign of a major incident/issue on his side, not pace-related

### Tyre Degradation (lap-time fall-off per stint)

| Compound | Stint | Peak lap → Last clean lap | Total fall-off | Avg deg/lap |
|---|---|---|---|---|
| Soft | Laps 2-7 (5 laps) | 1:31.538 → 1:33.846 | +2.308s | **~0.46s/lap** |
| Hard | Laps 14-19 (5 laps) | 1:31.665 → 1:32.861 | +1.196s | **~0.24s/lap** |
| Medium | Laps 22-29 (7 laps) | 1:31.039 → 1:32.490 | +1.451s | **~0.21s/lap** |

Note: the Hard stint's lap times were noisier than Suzuka's (likely traffic + the lap-12 collision warning), so that 0.24s/lap reading is less clean than the others — treat it as a rough estimate. The headline finding: Soft degradation (~0.46s/lap) lines up closely with Suzuka (~0.49s/lap), suggesting that rate may be largely **compound-driven** rather than track-driven. But Hard and Medium came out much closer together here (0.24 vs 0.21) than at Suzuka (0.15 vs 0.35) — possibly Bahrain's sandy, abrasive surface (it's literally tagged as a track challenge) erodes the gap between those two compounds, or this is just noise from a shorter sample. Worth watching whether that pattern repeats at other abrasive tracks.

### Takeaway
Second straight race where the app's setup matched the raced setup almost perfectly — and this time it was a flawless 18/18, not 17/18. Two different tracks (a technical, high-speed circuit and a heavy-braking, abrasive one), two strong results (a win and a podium), two near-identical setups. That's a meaningful pattern now, not a coincidence — the formula logic appears to be tracking the game's own setup recommendations closely across very different track characters.

---

## Round 5 — Saudi Arabia (Jeddah) — Haas F1 Team

**Setup used**: App-generated Jeddah "Stable" setup — **PERFECT 18/18 match** (apparent ftp discrepancy 24.4 vs 24.5 was a Python rounding artefact; the app outputs 24.5 correctly).

| Setting | Value |
|---|---|
| Front/Rear Wing | 26 / 27 |
| On/Off-Throttle Diff | 60 / 45 |
| Front/Rear Camber | -3.3 / -1.8 |
| Front/Rear Toe | 0.17 / 0.18 |
| Front/Rear Suspension | 10 / 13 |
| Front/Rear ARB | 17 / 17 |
| Front/Rear Ride Height | 28 / 54 |
| Brake Pressure / Front Bias | 88 / 54 |
| Tyre Pressures (F/R) | 24.5 / 21.2 |

### Race (25 laps, Dry, started from the back — component penalties)
- **Started last → Finished P9** (2 points) — gained ~13 positions
- Charged to **P1 by lap 13**, pitted from the lead — exactly as at Bahrain
- Double pit stop on laps 13-14: pitted at end of L13 (Hard out), then came back in almost immediately on L14 before completing sector 1 (explains the 49.9s S1 on L14) — this cost significant time and positions from P1
- **Best lap: 1:32.502** (lap 15, fresh Mediums) — **2nd fastest of the entire race**, only Verstappen (1:32.427) was quicker; ahead of Hadjar, Piastri, Hamilton, Antonelli, Norris, Russell, and Leclerc
- Small Collision warning (lap 22, no time penalty)

### Tyre Degradation

| Compound | Stint | Peak lap → Last clean lap | Total fall-off | Avg deg/lap | Reliability |
|---|---|---|---|---|---|
| Hard | Laps 3-12 (9 laps) | 1:33.047 → 1:34.943 | +1.896s | **~0.21s/lap** | Low — constant overtaking, heavy traffic interference |
| Medium | Laps 15-20 (5 laps) | 1:32.502 → 1:33.910 | +1.408s | **~0.28s/lap** | Good |
| Soft | Laps 23-25 (2 laps) | 1:32.895 → 1:35.040 | +2.145s | — | Too short (2 intervals), discard |

Medium (~0.28s/lap) is the only reliable number from this race. Soft stint was cut too short by the race ending; Hard stint is contaminated by traffic from constant overtaking from the back.

### Takeaway
Fastest Haas-sized result in terms of raw pace so far — 2nd-fastest lap of the field from the back of the grid. The pit lane (again) is the variable undoing strong race pace. Worth being deliberate about pit lane speed limiter activation — engaging it early and staying well under the limit.

---

## Round 6 — Miami (Sprint Weekend) — Haas F1 Team

**Setup used**: App-generated Miami "Stable" setup — **18/18 perfect match** (fourth consecutive near-perfect or perfect match).

| Setting | Value |
|---|---|
| Front/Rear Wing | 33 / 35 |
| On/Off-Throttle Diff | 55 / 45 |
| Front/Rear Camber | -3.2 / -1.7 |
| Front/Rear Toe | 0.14 / 0.21 |
| Front/Rear Suspension | 12 / 14 |
| Front/Rear ARB | 9 / 8 |
| Front/Rear Ride Height | 30 / 55 |
| Brake Pressure / Bias | 87 / 55 |
| Tyre Pressures (F/R) | 24.4 / 21.4 |

### Practice 1 (Mixed conditions — front wing experiment)
- Ran **test setup: fw=37, rw=35** (all other values identical to Stable) on hard tyres (laps 10-19)
- Hard stint P1 throughout; best lap 1:29.127; deg ~0.26 s/lap (mixed conditions, not reliable for deg tracking)
- Average S1 on fw=37 (hard stint): **0.316s**

### Sprint Race (10 laps, Dry)
- **Finished P5** — Mediums throughout, no pit stop
- Best lap: 1:28.827 (lap 2)
- Average S1 on fw=33 (sprint): **0.317s**
- Couldn't follow AI through sector 1 — felt like a pace gap, not a setup issue

### Wing Experiment — Conclusion (revised)
**Inconclusive but leans toward fw=37 being better.** Initial read was that S1 averages were identical (0.316s fw=37 vs 0.317s fw=33), suggesting no difference. But: practice used Hards + high fuel load, inherently ~0.7-1.0s/lap slower than Mediums + sprint fuel. Despite this, practice avg (1:30.540) matched sprint avg (1:30.597) almost exactly — meaning fw=37 was overcoming a significant compound+fuel disadvantage. Same logic applies to S1: Mediums should be faster than Hards there, yet times matched, implying fw=37 was contributing real front-end grip. Mixed vs dry conditions in practice are a confound that prevents a clean conclusion. **Verdict: needs a cleaner retest** — same compound, same fuel load, dry conditions both runs. Don't change the formula yet, but don't dismiss the front wing signal either.

### Qualifying 3 (fw=37 carried over)
- Carried the test setup (fw=37, rest Stable) into qualifying — Softs, dry, low fuel
- **P4**, 0.197s off pole — ahead of Leclerc, Piastri, Hamilton, Sainz, and Verstappen
- Strongest single data point for fw=37 yet, though it's one lap on a different (low) fuel load than the deg comparisons above, not a controlled back-to-back

### Race (Grand Prix)
- Ran fw=37 again for the race
- **Finished P1 (win)** — 2-stop strategy instead of the usual 3-stop
- No telemetry captured (app wasn't running) — no lap-by-lap pace or tyre deg data for this race

**Weekend outcome**: P4 quali + a win on fw=37 is a positive signal, but it's still not the controlled test that's needed (different sessions, fuel loads, and no clean same-lap baseline). The cleaner retest at another track remains the real next step before touching the formula.

### Tyre Degradation

| Compound | Stint | Peak → Last clean | Total | Avg deg/lap |
|---|---|---|---|---|
| Medium | Laps 2-9 (7 laps) | 1:28.827 → 1:31.366 | +2.539s | **~0.36 s/lap** |

Notable: Miami Medium degradation (~0.36 s/lap) is the highest recorded so far — bumpy, low-grip surface chews tyres faster than Bahrain or Saudi.

---

## Round 7 — Montreal (Circuit Gilles Villeneuve) — Haas F1 Team

**Setup used**: App-generated Montreal "Stable" setup — **PERFECT 18/18 match**, identical in both Qualifying and the Race (same setup carried across the weekend). Fifth straight round at a perfect or near-perfect match (Suzuka 17/18 → Bahrain 18/18 → Saudi Arabia 18/18 → Miami 18/18 → Montreal 18/18).

| Setting | Value |
|---|---|
| Front/Rear Wing | 26 / 27 |
| On/Off-Throttle Diff | 50 / 55 |
| Front/Rear Camber | -3.0 / -1.5 |
| Front/Rear Toe | 0.12 / 0.23 |
| Front/Rear Suspension | 9 / 12 |
| Front/Rear ARB | 7 / 5 |
| Front/Rear Ride Height | 32 / 58 |
| Brake Pressure / Bias | 86 / 57 |
| Tyre Pressures (F/R) | 24.2 / 21.3 |

(Engine Braking 50, Ballast 6, Fuel Load 5.0kg were also set but aren't part of the app's 18 formula outputs — same as every prior round.)

### Qualifying (Q3)
- Only 2 laps captured by the app: 1:10.779 then **1:09.786** (best), both on C6
- **P3.** The app's own Position column reads "10" for both laps, but that's wrong/stale — confirmed P3 directly. Another telemetry app bug to track: the Position field in the lap summary isn't trustworthy, at least for Q3 exports
- First time this app has exported real car-setup data — previous formats (lap-summary-only, then full telemetry) never carried it

### Race (34 laps logged, Dry, 2-stop)
- Started P3, up to **P1 by the end of lap 1** — a 2-position opening-lap gain, consistent with the P3 quali result above (the race's Position column checks out here; it was specifically Q3's that was stale/wrong)
- Stints: C5 (laps 1-9) → pit lap 10 (dropped to P12) → C4 (laps 11-28) → pit lap 29 → C6 (laps 30-34)
- Recovered from P12 back to P1 by lap 16 and held it through lap 34, the last lap with a clean entry in the lap summary
- Fastest lap of the race: **1:12.393** (lap 2, C5)
- **Data quality issue**: the telemetry contains lap-35 rows that aren't in the lap summary at all, and those rows aren't in chronological order (two session-time sequences ~75s apart interleaved together). Can't confirm the exact final lap time or whether the race finished on lap 34 or 35 from this file — everything points to a win, but the precise finish isn't verifiable here
- **Fuel discrepancy**: CAR SETUP block says Fuel Load 5.0kg, but the first telemetry row reads 3.219kg. Given the stale-session-snapshot pattern confirmed at Monaco (Round 8 below), 5.0kg was likely never the real race fuel either — probably a leftover qualifying-fuel value from whatever session preceded the Race in the listener's session-block tracking, not a formation-lap burn-off.
- `ActiveAero(0=Corner,1=SLM)` field still reads 0 for all 11,209 race rows and all 1,750 qualifying rows despite hitting 341-344 kph — same bug as the old DRS column and the Madrid Time Trial export, persists in this file too
- **Session-type question resolved**: this session's raw header was originally captured as Type 16 ("Sprint Shootout 3" under the corrected map), which looked structurally wrong for 34 laps/2 pit stops. Monaco's race export (Round 8 below) shows the identical pattern — labeled "Sprint Shootout 2" with a qualifying-low 5.0kg fuel value, while the lap-by-lap data is unmistakably a full Race. That confirms a stale session-type/setup snapshot carried over from the session before the Race starts, not a mislabeled Race. **This entry stays "Race."**

### Tyre Degradation
Compound letters inferred from the strategy order (C4→C5→C6 is the standard pattern of three consecutive nominated compounds, softest = highest number) and cross-checked against a sensible Medium→Hard→Soft race strategy shape — not explicitly labeled in this export.

| Compound | Stint | Peak lap → Last clean lap | Total fall-off | Avg deg/lap | Reliability |
|---|---|---|---|---|---|
| Medium (C5) | Laps 2-9 (7 laps) | 1:12.393 → 1:15.051 | +2.658s | **~0.38s/lap** | Confirmed push stint — this is fall-off under attack, not a neutral baseline |
| Hard (C4) | Laps 14-28 (14 laps) | 1:12.996 → 1:15.023 | +2.027s | **~0.15s/lap** | Confirmed deliberate tyre management — this reflects a conserved stint, not the Hard's true wear rate under full attack (traffic during the laps 11-16 recovery from P12 adds some extra noise on top) |
| Soft (C6) | Laps 31-34 (3 laps) | 1:13.569 → 1:14.414 | +0.845s | **~0.28s/lap** | Low — only 3 intervals; given the Hard stint was confirmed managed, this stint (run with a comfortable lead) was likely managed too rather than flat out |

Driver-confirmed context changes the read here: the Medium stint was pushed hard, so ~0.38s/lap is degradation-under-attack rather than a clean baseline — and the Hard stint's low ~0.15s/lap is explained by deliberate management, not just traffic noise as originally assumed. Soft's ~0.28s/lap (vs ~0.49 at Suzuka, ~0.46 at Bahrain) is consistent with that same conservative pattern continuing into the final stint, not a real signal that Montreal's Soft is gentler on tyres.

### Takeaway
Setup match streak is now 5 rounds deep and the first to come with an actual exported setup file rather than a manually-noted one — strong continued validation. The app itself is also evolving fast: real car setups now export, which opens the door to fully automated match-checking, but lap 35's corrupted/out-of-order telemetry, the fuel-value mismatch, and Q3's stale Position field are new bugs worth watching in future exports. Just as important: this round showed that raw lap-time degradation numbers can't be read on their own — Medium was a push stint and Hard was deliberately managed, confirmed directly rather than guessed. Going forward, worth asking "push or managed?" per stint whenever it's not obvious, since it changes what the degradation number actually means.

---

## Round 8 — Monaco (Circuit de Monaco) — Haas F1 Team

**Setup used**: App-generated Monaco "Stable" setup — **PERFECT 18/18 match** (sixth straight round at a perfect or near-perfect match: Suzuka 17/18 → Bahrain 18/18 → Saudi Arabia 18/18 → Miami 18/18 → Montreal 18/18 → Monaco 18/18). First round where one value only landed because of the app's hard clip ceiling — the raw rear-wing formula would've produced 51, but the 50 cap brought it down to exactly the raced value.

| Setting | Value |
|---|---|
| Front/Rear Wing | 47 / 50 |
| On/Off-Throttle Diff | 45 / 45 |
| Front/Rear Camber | -2.8 / -1.3 |
| Front/Rear Toe | 0.09 / 0.23 |
| Front/Rear Suspension | 19 / 21 |
| Front/Rear ARB | 2 / 3 |
| Front/Rear Ride Height | 26 / 53 |
| Brake Pressure / Bias | 87 / 55 |
| Tyre Pressures (F/R) | 24.0 / 21.1 |

### Qualifying
- Q1: P10, best lap 1:12.108 (C5) — lap 2 was a throwaway (1:34.031, sectors way off normal pace, likely an off-track moment), advanced on laps 1/3 pace
- Q2: P3, best lap 1:11.489 (C5)
- Q3: **P1 — pole position**, best lap 1:10.883 (C5), 0.186s ahead of Piastri (P2) and 0.272s ahead of Russell (P3). Another scrappy lap mid-run (lap 2, 1:23.336) didn't cost the session
- Same Stable setup carried through Q1-Q3, matching what was run in Practice 2 the same weekend

### New bugs spotted in this export
- **Final Classification table duplicates every row** — each position appears twice in Q1, not at all in Q2, and roughly 40+ times each in Q3. Looks like a write-loop tied to something that scales (lap count or sample count?) rather than a clean one-row-per-driver list. **Fixed**: added `UNIQUE(session_uid, car_idx)` + `ON CONFLICT DO UPDATE` on the classification table; existing rows dedupe on next listener restart.
- **Q3's own session header didn't resolve**: Track "—", Session "Unknown", Weather "—". Turned out not to be a mapping bug — that session row was written before the game sent its session packet with track/type info, so the DB had genuine nulls for it. Not retroactively fixable; if it recurs it means the listener started mid-session.
- Q3 lap 4 (1:11.209) matches lap 1 (1:11.209) to the millisecond despite different sector splits (19.054/33.560/18.595 vs 18.925/33.683/18.601) — probably coincidence, flagging anyway.
- The classification table's Total Time for the player's own entry doesn't match summing the visible Lap Times rows (e.g. Q1: visible laps sum to ~239s vs a listed 299.858s) — might include an out-lap not shown in the Lap Times table.

### Race (39 laps, ~50% distance, Dry, 2-stop)
- **Exported under a wrong session label** — this file's header reads "Sprint Shootout 2," and the Car Setup block's Fuel Load shows a qualifying-low 5.0kg. Both are clearly stale: the Lap Times/Telemetry/Wear/Final Classification tables are unmistakably a full 39-lap Race (fuel burning from ~30.6kg down to ~1.7kg, full 22-driver classification, 2 real pit stops with tyre-wear resets). This is the cleanest evidence yet that the listener carries a stale session-type + setup snapshot over from whatever session ran immediately before the Race, rather than a label-mapping bug — and it resolves the open question on Round 7 Montreal above the same way.
- Wing/diff/camber/toe/suspension/ARB/ride-height/brake/tyre-pressure values in the (stale-labeled) setup block match the confirmed Monaco Stable setup raced all weekend, so the **18/18 match still holds** — just exclude the Fuel Load field here, it's not a genuine race-fuel reading.
- Finished **P1** — pole to flag, 39/39 laps, no penalties. Margin over P2 (Norris) at the flag: **4.819s**. No live position trace available (the Pos column was dropped from this lap table too, since the listener bucketed the session as qualifying-format), so a lap-by-lap lead history isn't confirmable from this file — but pole-to-win with a clean gap and no incidents visible in the data points to a lights-to-flag run.
- Strategy: C4 (laps 1-15) → pit → C3 (laps 16-29) → pit → C3 again (laps 30-38/39). 2 stops, no Soft used in the race.
- Fastest lap of the race: **1:13.400** (lap 33, second C3 stint)
- **Data quality**: lap 39 has Per-Lap Telemetry/Wear/Wheel-Slip rows but is missing from the Lap Times table entirely (table stops at lap 38) — same bug family as Montreal's lap-35 issue (a final lap present in telemetry but dropped from the lap summary)
- **New section: Corner Balance** (oversteer/understeer per corner, from wheel-slip deviation off a straight-line baseline) appeared in a re-export of this same race a few minutes later. Across 9 sampled corner points around Monaco, 8 read understeer — mildest at Grand Hotel Hairpin (-0.017), strongest at C9 (-0.032), with Casino and C8 close behind (-0.030 each). The lone oversteer reading was right at Sainte Devote's entry (+0.016). Sainte Devote shows up twice (27m: +0.016 oversteer, 179m: -0.030 understeer) — probably entry vs. exit sampling rather than a naming bug, but worth a glance

### Tyre Degradation
Compounds: C4 (used first) and C3 (used twice, one step harder). Practice 2/Qualifying both ran C4 for long stints and C5 for single-lap pace, so the working read is **C4 = Medium, C3 = Hard**, with no Soft used in the race.

| Compound | Stint | Peak lap → Last clean lap | Total fall-off | Avg deg/lap | Reliability |
|---|---|---|---|---|---|
| Medium (C4) | Laps 2-15 (13 laps) | 1:14.199 → 1:17.580 | +3.381s | **~0.26s/lap** | Confirmed push stint |
| Hard (C3, stint 1) | Laps 21-29 (8 laps) | 1:13.902 → 1:15.881 | +1.979s | **~0.25s/lap** | Confirmed conservative/managed stint |
| Hard (C3, stint 2) | Laps 33-38 (5 laps) | 1:13.400 → 1:14.813 | +1.413s | **~0.28s/lap** | Confirmed push stint — the race's fastest lap opened this stint, consistent with attacking |

Driver-confirmed: stints 1 and 3 were pushed, stint 2 was deliberately conservative. The notable part is how little that changed the numbers — the managed Hard stint (~0.25s/lap) is barely below the two push stints (~0.26-0.28s/lap), maybe a 10-15% spread. Compare that to Montreal, where a confirmed push stint and a confirmed managed stint landed at ~0.38 vs ~0.15s/lap — a 150%+ spread. Same push/managed contrast, wildly different sensitivity. Points toward Monaco's degradation being mostly track-driven (low speeds, low loads) with driving intensity barely moving the needle, versus Montreal where intensity was most of the story.

### Takeaway
Pole to lights-to-flag win, setup match streak intact (fuel field excluded as a known stale-session artifact) — best result of the season. The race export also handed over the clearest evidence yet of the listener's session-type/setup snapshot lagging one session behind, which settles the Round 7 Montreal question in favor of keeping that entry as "Race."

---

## Round 10 — Madring (Madrid) — Haas F1 Team

**Setup used**: Custom/own setup, not the app-generated "Stable" setup — values not shared yet, will add once provided.

### Time Trial (8 laps, Dry, Soft/C5, single stint, 2026-06-19)

| Lap | Time | S1 | S2 | S3 |
|---|---|---|---|---|
| 1 | 1:30.416 | 27.695 | 33.109 | 29.612 |
| 2 | 1:30.899 | 27.786 | 33.083 | 30.030 |
| 3 | 1:29.751 | 27.468 | 32.762 | 29.521 |
| 4 | 1:30.492 | 27.759 | 33.377 | 29.356 |
| 5 | 1:30.238 | 27.572 | 33.061 | 29.605 |
| 6 | 1:29.730 | 27.394 | 32.805 | 29.531 |
| 7 | 1:29.994 | 27.427 | 33.010 | 29.557 |
| 8 | 1:29.684 | 27.489 | 32.831 | 29.364 |

- **Best lap: 1:29.684** (lap 8). Theoretical best (best sectors stacked): 1:29.512 (S1 from lap 6, S2 from lap 3, S3 from lap 4) — still ~0.17s on the table.
- Time Trial mode caveats: fuel locked at 10.0kg, tyre wear stayed at 0.0% on all four corners, ERS_Store% pinned at 100% the whole session — none of this mode's data is usable for fuel/deg/ERS-management analysis, only for line/throttle-brake/speed trace work.
- Telemetry quirk: the `ActiveAero(0=Corner,1=SLM)` field never read 1 across all 9 laps despite hitting 300 kph on the straights — same flavor of bug as the old DRS column, just under a new name.
- Raw export logged this as "Track#42" — confirmed this is Madring/Madrid (round 10 in the app's track list). Worth adding ID 42 → Madrid to the telemetry app's track-name lookup.

### Setup match — pending
No setup values in this export (Time Trial telemetry doesn't carry car setup data). Once the actual front/rear wing, camber, toe, suspension, ARB, ride height, brake, and tyre pressure values are shared, will run the usual match check against the app's Madrid "Stable" output and log it here.

---

## Round ? — [Next track]

*(Add new entries below as races come in.)*

---

## Tyre Degradation Tracker (cross-track comparison)

Average lap-time fall-off per lap, by compound and track — peak lap to last clean lap of each stint, excluding out-laps/in-laps. Building this up over the season should make it possible to spot which tracks chew through tyres fastest, and whether degradation rates are mostly track-driven, compound-driven, or setup-sensitive.

| Track | Medium (s/lap) | Hard (s/lap) | Soft (s/lap) | Notes |
|---|---|---|---|---|
| Suzuka | ~0.35 | ~0.15 | ~0.49 | Dry, Difficulty 105, app "Stable" setup |
| Bahrain | ~0.21 | ~0.24* | ~0.46 | Dry, app "Stable" setup. *Hard reading noisy (traffic + lap-12 collision) |
| Saudi Arabia (Jeddah) | ~0.28 | ~0.21* | — | Dry, app "Stable" setup, started last. *Hard noisy (constant overtaking). Soft too short to measure |
| Miami | ~0.36 | — | — | Dry, sprint (10 laps). Hard stint in mixed conditions (practice) excluded. Highest Medium deg recorded so far |
| Montreal | ~0.38† | ~0.15‡ | ~0.28* | Dry, app "Stable" setup, race (34 laps). Compound letters inferred, not labeled. †Medium was a confirmed push stint (inflated vs. a neutral pace). ‡Hard was confirmed deliberately managed (suppressed vs. full attack). *Soft sample too small, likely managed too |
| Monaco | ~0.26§ | ~0.25-0.28§ | — | Dry, app "Stable" setup, race (39 laps, ~50% distance). Compound letters inferred. §Confirmed: stints 1 (Medium) and 3 (Hard) were pushed, stint 2 (Hard) was managed — yet all three landed within ~0.03s/lap of each other, a far smaller push/managed gap than Montreal's. No Soft run in the race |
| *(next track)* | | | | |

---

## Running Observations Across Rounds

- *(Patterns that show up more than once go here — e.g., "front-left consistently wears fastest" or "the formula's [X] output seems to work better on high-speed tracks than technical ones.")*
- Suzuka: Soft degrades roughly **3x faster** than Hard (~0.49 vs ~0.15 s/lap), Medium sits in between (~0.35 s/lap) — a useful baseline to see whether this ratio holds at other tracks or shifts with track abrasiveness/temperature.
- **Setup match streak**: Two races, two near-perfect matches between the app's "Stable" output and the in-game-recommended setup raced (Suzuka 17/18, Bahrain 18/18 — perfect). Both produced strong results (a win and a podium). This is becoming a real pattern, not a one-off.
- **Double-stop situations have cost positions in multiple races**: Saudi Arabia laps 13-14 double pit cost time from P1. Worth being deliberate about strategy calls to avoid unnecessary extra stops.
- **Setup match streak**: Suzuka 17/18 → Bahrain 18/18 → Saudi Arabia 18/18 → Miami 18/18 → Montreal 18/18 → Monaco 18/18. Formula appears to be tracking the game's logic accurately across very different circuit types (technical/high-speed, heavy-braking/abrasive, fast street circuit, power circuit with chicanes, tight low-speed street circuit).
- **Telemetry app bugs keep showing up in the same category right after a fix lands**: fixing the Type 16 session-name mapping didn't catch Q3's session code in the very next export — turned out to be a different cause (null DB row from a mid-session listener start, not a mapping gap), but worth staying alert for this pattern. Update: the full `SESSION_TYPE_LABELS` map for types 10–17 has since been corrected (was wrong across the whole 10-17 range, not just 16) and `sessionBadgeClass` updated to match (races red, quali/shootouts blue, practice green, TT yellow).
- **Soft tyre degradation looks compound-driven, not track-driven**: ~0.49s/lap at Suzuka vs ~0.46s/lap at Bahrain — two very different track types, nearly identical Soft fall-off rate. Worth testing whether Hard/Medium show the same track-independence or whether (as Bahrain hinted) abrasive surfaces compress the gap between compounds. Montreal's Soft reading (~0.28s/lap) breaks this pattern, but it's a low-confidence number (tiny sample, driver cruising in a comfortable lead) — not strong enough to overturn the compound-driven theory yet.
- **Telemetry app bugs, recurring across exports**: a "phantom DRS/ActiveAero" field that never reads true despite high top speeds has now shown up under two different column names (`DRS` in the Montreal Sprint export, `ActiveAero(0=Corner,1=SLM)` in both the Madrid Time Trial and Montreal Qualifying+Race exports) — looks like a capture bug rather than a one-off. The Montreal Race export also showed a lap-35 chronology/duplication bug and a Fuel Load setup-vs-telemetry mismatch (5.0kg vs 3.219kg) — first two new data-quality issues since the original sector-time and DRS bugs.
- **Session-type/setup snapshot can lag one session behind the real one**: confirmed at Monaco — the Race export was headered "Sprint Shootout 2" with a qualifying-low 5.0kg Fuel Load in the setup block, while the Lap Times/Telemetry/Classification were unmistakably the full Race (39 laps, fuel 30.6kg→1.7kg, full field classified). This is almost certainly the same bug behind Montreal's "Type 16" header and its 5.0kg-vs-3.219kg fuel mismatch — both now read as the listener carrying over the *previous* session's type/setup snapshot rather than mislabeling the session it's actually recording. Resolves that open question in favor of keeping Round 7 Montreal labeled "Race."
- **A session's final lap sometimes drops out of the Lap Times table while still appearing in Telemetry/Wear/Wheel-Slip**: seen at both Montreal (lap 35) and Monaco's race (lap 39). Looks like the lap-summary writer and the per-lap-telemetry writer close out a session slightly differently at the very end — worth checking whether the lap summary is finalizing one tick before the last lap's data actually arrives.
- **New export feature: Corner Balance** (per-corner oversteer/understeer from wheel-slip deviation off a straight-line baseline) — first seen on a re-export of the Monaco race file. Genuinely useful coaching layer: Monaco's race showed understeer at 8 of 9 sampled corners, strongest at C9 and Casino. Worth watching whether this stays this lopsided at other tracks or whether Monaco's slow, low-grip-build corners make understeer the default read here.
- **The lap summary's Position column isn't always trustworthy**: Montreal's Q3 export showed P10 for both laps, but the actual result was P3 — confirmed directly. The race session's Position column for the same weekend was accurate, so this looks specific to Q3 captures rather than a global bug. Worth treating any single-session Position reading with mild suspicion until cross-checked.
- **Degradation numbers conflate tyre wear with driving intensity** — confirmed at Montreal: the Medium stint was a push, the Hard stint was deliberately managed, and that alone explains most of the gap between their fall-off rates (~0.38 vs ~0.15 s/lap), not necessarily the compounds themselves. This calls into question how much of the Suzuka/Bahrain/Saudi/Miami numbers reflect genuine compound behavior vs. how hard each stint was actually being pushed — none of those were confirmed push-or-manage at the time. Going forward, worth asking "push or managed?" per stint whenever it isn't obvious from the race situation.
- **...but how much push/managed matters looks track-dependent**: at Monaco, two confirmed push stints and one confirmed managed stint all landed within ~0.03s/lap of each other (~0.25-0.28), nothing like Montreal's 150%+ swing for the same push/managed contrast. Working theory: low-speed, low-load circuits like Monaco compress the gap between driving styles, while higher-energy tracks like Montreal amplify it. Worth tracking whether this holds at the next few low-speed vs. high-energy tracks.
