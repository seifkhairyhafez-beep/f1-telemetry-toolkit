# F1 25 Telemetry Dashboard — Setup Guide

## What's in this folder

| File | Purpose |
|------|---------|
| `start.bat` | **Double-click this to launch everything** |
| `listener.py` | UDP listener + WebSocket + HTTP server |
| `packets.py` | F1 25 binary packet parser (spec v6.0) |
| `db.py` | SQLite session logger |
| `dashboard.html` | Live telemetry dashboard |
| `compare.html` | Lap comparison viewer |
| `requirements.txt` | Python dependencies (just `websockets`) |

---

## Step 1 — Install Python

Download Python 3.10 or newer from https://python.org  
During install, **tick "Add Python to PATH"**.

---

## Step 2 — Configure F1 25

In-game: **Settings → Telemetry Settings**

| Setting | Value |
|---------|-------|
| UDP Telemetry | **On** |
| UDP Broadcast Mode | **Off** (directed to PC) |
| UDP IP Address | `127.0.0.1` (same machine) |
| UDP Port | `20777` |
| UDP Send Rate | **60Hz** (or highest available) |
| UDP Format | **2025** |

> If you play on a different PC than where the listener runs (unlikely on PC, relevant for consoles), set **UDP IP Address** to the IP address of the machine running `start.bat`. You can find it by running `ipconfig` in a command prompt and looking for your Wi-Fi or Ethernet IPv4 address (e.g. `192.168.1.42`).

---

## Step 3 — Launch the listener

Double-click **`start.bat`**.

The first run will install `websockets` automatically (requires internet). After that it starts instantly.

The browser opens automatically to the dashboard. If it doesn't, navigate to:

- **Live dashboard:** http://localhost:8766/dashboard  
- **Lap comparison:** http://localhost:8766/compare  

---

## Step 4 — Start a session in F1 25

Once you're in a practice, qualifying, or race session the dashboard should show **LIVE** in the top-right corner and data will populate immediately.

The track map builds itself as you drive — after one lap you'll see your car position updating in real time.

---

## Ports used

| Port | Protocol | Purpose |
|------|----------|---------|
| 20777 | UDP | Receives packets from F1 25 |
| 8765 | WebSocket | Pushes live data to the browser |
| 8766 | HTTP | Serves dashboard/compare pages + history API |

If any port is blocked by Windows Firewall, allow it in: **Windows Security → Firewall → Allow an app through firewall**, or run:
```
netsh advfirewall firewall add rule name="F1 Telemetry" dir=in action=allow protocol=UDP localport=20777
```

---

## Lap comparison

1. Open http://localhost:8766/compare
2. Select a session from the dropdown
3. The lap table shows all recorded laps — click two rows (alternates between Lap A / Lap B), or use the dropdowns directly
4. Click **Compare** — overlaid speed/throttle/brake/gear/RPM traces appear, aligned by lap distance

All session data is saved in **`f1_telemetry.db`** (SQLite) in the same folder. You can open it with any SQLite viewer (e.g. DB Browser for SQLite) for custom queries.

---

## Advanced: command-line options

```
python listener.py --udp-port 20777 --ws-port 8765 --http-port 8766 --no-browser
```

---

## Troubleshooting

**"NO SIGNAL" in dashboard**  
→ Check UDP settings in game match Step 2.  
→ Confirm `start.bat` console shows no Python errors.  
→ Try disabling Windows Firewall temporarily to rule it out.

**Dashboard opens but data is all zeros / "--"**  
→ You must be in an active on-track session (not the main menu).  
→ Make sure UDP Format is set to **2025** (not 2024).

**"No laps recorded yet" in Compare**  
→ The listener must be running *during* the session. Laps are saved when you cross the finish line.  
→ The first lap of a session is not saved (no previous lap time exists yet).

**Port 8766 already in use**  
→ Run `python listener.py --http-port 8767` and visit http://localhost:8767/dashboard

---

## Data logged per session

- Frame-by-frame: speed, throttle, brake, steer, gear, RPM, DRS, tyre temps (surface + inner), brake temps, tyre wear, fuel, ERS, world position — logged every 5th frame (~12 samples/s)
- Per-lap: lap time, S1/S2/S3, tyre compound + age, fuel, validity
- Events: fastest laps, DRS open/close, safety car, penalties, retirements, overtakes
- Final classification at session end
