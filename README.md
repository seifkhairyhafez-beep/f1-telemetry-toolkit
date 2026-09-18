# F1 Telemetry & Setup Toolkit

A real-time telemetry dashboard and data-driven car setup generator for F1 25/26 (Codemasters/EA Sports F1 series), built from scratch around the game's UDP telemetry protocol.

## What it does

**Live telemetry dashboard** — parses the game's binary UDP packet stream in real time and serves a live browser dashboard over WebSocket: track map (built live from car position data), per-corner mini-sector timing deltas against your session best, tyre/brake temps, ERS, and lap history — all persisted to SQLite as you drive.

**Lap comparison tool** — pulls any two recorded laps from the session database and overlays their speed/throttle/brake/gear/RPM traces on shared distance-based charts, so you can see exactly where time is won or lost between two laps.

**Setup generator** — a standalone web app that outputs a full 18-parameter car setup for every track on the calendar, based on real community "meta" setup data researched per track rather than a generic formula (see [`f1-26-meta-setups.md`](f1-26-meta-setups.md) for the sourcing and reasoning behind the values).

## How it works

```
F1 game  --UDP packets-->  listener.py  --parses via packets.py-->  db.py (SQLite)
                                |
                                +--WebSocket-->  dashboard.html (live view)
                                +--HTTP API---->  compare.html (lap analysis)
```

- `listener.py` — UDP listener + WebSocket broadcaster + lightweight HTTP server, all in one process
- `packets.py` — binary parser for the F1 telemetry UDP spec (motion, lap data, car telemetry, session, events, etc.)
- `db.py` — SQLite persistence layer for sessions, laps, and per-frame telemetry
- `dashboard.html` — live in-browser dashboard (vanilla JS, canvas-rendered track map, no framework)
- `compare.html` — lap-vs-lap comparison charts
- `f1-26-setup-guide.html` — the setup generator (independent of the telemetry stack, pure client-side)

## Tech stack

Python (asyncio, `websockets`) for the backend · SQLite for storage · vanilla HTML/CSS/JS for both frontends — no frameworks, no build step, runs entirely locally.

## Quick start

```
1. Enable UDP Telemetry in the game's settings (port 20777, format matching your game version)
2. Double-click start.bat (installs the one dependency, then launches everything)
3. Open http://localhost:8766/dashboard while on track
```

Full setup instructions, port reference, and troubleshooting: [`SETUP.md`](SETUP.md).

## Why this exists

Built to answer a practical question while learning to drive with a new wheel setup: *where exactly, corner by corner, am I losing time — and is it the car's setup or the driver?* The dashboard's mini-sector deltas and the lap comparison tool were both built to make that answer visible instead of guessed at, and the setup generator grew out of researching how the game's setup meta actually behaves (which turned out to not follow real-world car physics).
