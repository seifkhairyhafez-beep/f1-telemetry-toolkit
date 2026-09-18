# F1 26 Time Trial — Setup Development Log

Separate from the race season log (`f1-26-career-season-log.md`). This log exists to **find the perfect setup** per track by iterating in Time Trial, where conditions are fully controlled (fuel locked 10.0 kg, tyre wear 0%, ERS pinned 100%) so the only variable is the setup + driving. Each entry records the setup, the pace it produced, and the Corner Balance (understeer/oversteer) signature, so setup changes can be judged against a clean baseline.

**TT caveats (always true here):** no tyre-wear or degradation data (locked at 0%), fuel locked at 10 kg, ERS locked at 100%. Pace and balance/handling are the only usable signals — which is exactly what setup development needs.

**Numbering:** TT rounds are numbered independently (TT Round 1, 2, 3…), NOT tied to the race calendar round numbers.

---

## TT Round 1 — Silverstone — "Dedicated TT setup" (Rear Wing 0)

**Date:** 2026-07-07 · Compound C4 · 14 flying laps
**Setup used:** Custom low-drag Time-Trial setup — **NOT the app formula** (rear wing 0 is impossible from `genSetup`, which min-clips rear wing at 5). This is the "suited more for TT" setup, run for comparison against the app setup (app-setup TT run pending — export not yet provided).

| Setting | Value |
|---|---|
| Front / Rear Wing | **42 / 0** |
| On / Off-Throttle Diff | 100% / 10% |
| Front / Rear Suspension | 41 / 41 |
| Front / Rear ARB | 5 / 1 |
| Front / Rear Camber | -3.5 / -2.0 |
| Front / Rear Toe | 0.0 / 0.1 |
| Front / Rear Ride Height | 21 / 43 |
| Brake Pressure / Bias | 100% / 58% |
| Tyre PSI (F / R) | 29.5 / 20.5 |
| Engine Braking / Ballast / Fuel | 50 / 6 / 10.0 kg (TT-locked) |

### Pace
- **Best lap: 1:28.377** (lap 14) — improving through the whole run, still finding time at the end.
- Best sectors: S1 **27.904** (lap 13) · S2 **36.248** (lap 14) · S3 **24.118** (lap 14) → **theoretical best 1:28.270** (~0.1s on the table). Near the setup's ceiling; driver-limited more than setup-limited.
- Top speed 313–321 km/h.

### Corner Balance (understeer / oversteer)
Baseline this run: straight-line rear slip **0.0162**, front **-0.0005**. Positive = oversteer, negative = understeer.

| Corner | Dist (m) | Balance | Character |
|---|---|---|---|
| C1 | -940 | +0.006 | neutral |
| C2 | -397 | **+0.018** | oversteer |
| C3 | 349 | -0.001 | neutral |
| C4 | 595 | +0.001 | neutral |
| C5 | 848 | **+0.016** | oversteer |
| C6 | 1199 | **+0.011** | oversteer |
| C7 | 1892 | **+0.015** | oversteer |
| C8 | 3012 | +0.002 | neutral |
| C9 | 3690 | +0.006 | neutral |
| C10 | 4868 | +0.005 | neutral |
| C11 | 4954 | +0.006 | neutral |
| C12 | 5424 | **+0.018** | oversteer |
| C13 | 5492 | **+0.017** | oversteer |

**Read:** Mild but consistent **oversteer in the fast corners only** (C2, C5, C6, C7, C12, C13 → +0.011 to +0.018), neutral everywhere else, **zero understeer anywhere**. This is the direct signature of **Rear Wing 0** unloading the rear through the high-speed sections (Copse, Maggotts-Becketts, the Vale/Club complex), amplified by the very open off-throttle diff (10%) freeing turn-in rotation. Not snappy — "lively rear in the fast stuff," not a spin risk.

### Hypothesis for next iteration (toward "perfect")
- **+2 to +4 clicks rear wing** — settle the fast-corner oversteer for minimal top-speed cost (already 320 km/h; Silverstone rewards fast-corner confidence more than a few km/h). Expect the +0.011–0.018 fast-corner readings to move toward neutral; watch whether best lap improves or the extra drag costs more than the stability gains.
- Front tyre PSI is very high (29.5 vs 20.5 rear) — if front bite feels short, dropping front PSI a touch is a cheap thing to test.
- **Still needed:** the **app-setup TT run** at Silverstone, to compare balance traces directly. App setup is high-downforce (rear wing ~39) → expect the opposite signature (neutral-to-understeer). The "perfect" TT setup likely sits between the two.

### Corner name note
Silverstone corners show as generic C1–C13 (only Monaco has real names in the exporter's `CORNER_NAMES`). Can add Silverstone names if we want the balance table to read Copse/Maggotts/etc.

---

## Setup Iteration Tracker (Silverstone)

| Iteration | Rear Wing | Off-Thr Diff | Best Lap | Fast-corner balance | Verdict |
|---|---|---|---|---|---|
| TT R1 (baseline) | 0 | 10% | 1:28.377 | +0.011 to +0.018 (oversteer) | Loose rear in fast corners |
| *(app setup — pending)* | ~39 | — | — | — | — |
| *(next test)* | | | | | |

---

## TT Round 2 — Bahrain (Sakhir) — App setup (PRE-RETUNE), baseline for A/B

**Date:** 2026-07-09 · Compound C3 · only **3 flying laps** (still improving — pace not fully settled)
**Setup used:** App **Stable** setup for Bahrain — but the **PRE-retune version** (matches the Round 4 race setup saved in-game, predates the 2026-07-03 formula retune). Every value confirmed against the *old* `genSetup`.

> ⚠️ Current retuned formula would differ on 4 values: **Front Wing 30→33, Front ARB 7→6, Front Ride Height 27→31, Rear Ride Height 53→57.** The other 14 are identical. To test the *current* app setup, bump those four.

| Setting | Value (old app) |
|---|---|
| Front / Rear Wing | 30 / 31 |
| On / Off-Throttle Diff | 50% / 50% |
| Front / Rear Suspension | 13 / 15 |
| Front / Rear ARB | 7 / 5 |
| Front / Rear Camber | -3.0 / -1.5 |
| Front / Rear Toe | 0.12 / 0.23 |
| Front / Rear Ride Height | 27 / 53 |
| Brake Pressure / Bias | 87% / 56% |
| Tyre PSI (F / R) | 24.7 / 21.8 |
| Engine Braking / Ballast / Fuel | 50 / 6 / 10.0 kg (TT-locked) |

### Pace
- **Best lap: 1:29.511** (lap 3 — the last flying lap, still dropping). Sectors 28.978 / 38.460 / 22.073. Small sample; treat as a soft baseline, not a settled time.
- Top speed 314 km/h. Brake usage ~13–14% (heavier braking track than Silverstone).

### Corner Balance (understeer / oversteer)
Baseline this run: straight-line rear slip **0.0203**, front **-0.0007**. Positive = oversteer, negative = understeer.

| Corner | Dist (m) | Balance | Character |
|---|---|---|---|
| C1 | -539 | +0.007 | neutral |
| C2 | 689 | **+0.025** | oversteer |
| C3 | 1473 | +0.012 | oversteer |
| C4 | 1815 | +0.002 | neutral |
| C5 | 2223 | **+0.024** | oversteer |
| C6 | 2594 | +0.007 | neutral |
| C7 | 3408 | +0.010 | neutral |
| C8 | 3738 | +0.001 | neutral |
| C9 | 4049 | +0.003 | neutral |
| C10 | 4878 | +0.009 | neutral |

**Read:** **Oversteer, not understeer** — strongest at C2 (+0.025) and C5 (+0.024), mild at C3, neutral elsewhere. No understeer anywhere. The app setup here is a touch rear-loose at a couple of corners rather than pushing. (Note: opposite of the Monaco *race* read, which was heavy understeer — balance is track- and TT-vs-race-dependent, not a fixed trait.)

### Next step
Same track, switch to a dedicated **TT setup**, and log it below as the A/B partner. Compare: does the TT setup trade this mild oversteer for pace, or make the rear worse?

## Setup Iteration Tracker (Bahrain)

| Iteration | Wings (F/R) | Off-Thr Diff | Best Lap | Balance signature | Verdict |
|---|---|---|---|---|---|
| TT R2 — app (pre-retune) | 30 / 31 | 50% | 1:29.511* | oversteer C2/C5 (+0.024/5), rest neutral | Slightly rear-loose, no understeer. *3 laps, unsettled |
| TT R3 — dedicated TT | **50 / 50** | 10% | **1:28.573** | oversteer C2 (+0.028), C7 (+0.019), C5 (+0.013) | **−0.94s vs app**, faster in all 3 sectors. Still oversteery |
| *(retuned app 33/31 — optional)* | 33 / 31 | 50% | | | |

---

## TT Round 3 — Bahrain (Sakhir) — Dedicated TT setup (A/B partner to TT R2)

**Date:** 2026-07-09 · C3 · 3 flying laps · best **1:28.573** (lap 2)
**Setup used:** Dedicated high-downforce TT setup — **max wing 50/50**, very stiff, low ride height.

| Setting | TT setup (R3) | App setup (R2) |
|---|---|---|
| Front / Rear Wing | **50 / 50** | 30 / 31 |
| On / Off-Throttle Diff | 100% / 10% | 50% / 50% |
| Front / Rear Suspension | 33 / 41 | 13 / 15 |
| Front / Rear ARB | 18 / 21 | 7 / 5 |
| Front / Rear Camber | -3.2 / -2.0 | -3.0 / -1.5 |
| Front / Rear Toe | 0.04 / 0.1 | 0.12 / 0.23 |
| Front / Rear Ride Height | **20 / 42** | 27 / 53 |
| Brake Pressure / Bias | 100% / 57% | 87% / 56% |
| Tyre PSI (F / R) | 25.0 / 20.5 | 24.7 / 21.8 |

**Driver feel:** "felt very nice, really smooth" — high confidence, planted. (Feel matches the max-downforce platform. Note: felt on TT-perfect conditions — 10kg fuel, 0% wear, 100% ERS — race transfer untested.)

### Result — TT setup is ~0.94s faster
- **1:28.573 vs 1:29.511 = −0.938s.** Faster in **all three sectors**: S1 −0.36, S2 −0.34, S3 −0.23. Consistent gain, not one flukey sector. (Both small samples — 3 laps each — but a ~0.9s margin across every sector is almost certainly real.)
- Top speed identical: **314 km/h** on both setups.

### Corner Balance
Baseline this run: rear **0.0224**, front **-0.0007**.

| Corner | Dist (m) | TT (R3) | App (R2) |
|---|---|---|---|
| C2 | ~690 | **+0.028** oversteer | +0.025 oversteer |
| C5 | ~2222 | +0.013 oversteer | +0.024 oversteer |
| C7 | ~3408 | **+0.019** oversteer | +0.010 neutral |
| rest | | neutral | neutral |

Still **oversteer-biased, no understeer** on either setup. The TT setup didn't fix balance — C2 is if anything slightly looser. So the lap-time gain came from **grip + platform**, not from correcting handling.

### Two big findings
1. **Max wing (50/50) cost ZERO top speed** — 314 km/h on both the 50/50 TT setup and the 30/31 app setup. This is direct in-game confirmation of the retune's core thesis: *in 2026, active aero + ERS pay the straight-line cost of extra wing, so more downforce is nearly free.* The faster setup ran maximum wing. Our retuned app (more wing) moves in this direction. ✅
2. **BUT the fast setup ran LOW ride height (20/42)** — the opposite of the retune, which *raised* ride height on real-2026-physics grounds. This is a **⚠️ conflict**: EA's in-game model may still reward a low, slammed platform even though real 2026 regs don't. **Confounded** — the TT setup changed ~9 things at once, so ride height's isolated effect is unknown. Needs a controlled one-variable test (see below).

### Persistent target: C2
C2 (~690m, the Turn 1–2 area) is the strongest oversteer on **both** setups (+0.025 / +0.028). If we chase the perfect Bahrain setup, that's the corner to aim a rear-stability tweak at.

### Next controlled test to run
Take **one** setup and change **only ride height** (e.g. app setup but drop RH from 27/53 toward 20/42) — that isolates whether the in-game speed came from the low platform (contradicting the retune) or from the wing/stiffness. Until then we can't attribute the 0.94s.
