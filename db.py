"""
SQLite logging for F1 25 telemetry.
All data is stored in f1_telemetry.db in the same directory as this file.
"""

import sqlite3
import json
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "f1_telemetry.db"


def _s64(v: int) -> int:
    """Convert an unsigned 64-bit int to signed so SQLite doesn't overflow."""
    v = int(v) & 0xFFFFFFFFFFFFFFFF
    return v if v < (1 << 63) else v - (1 << 64)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        conn = get_conn()
        conn.execute("SELECT 1 FROM sessions LIMIT 1")
        conn.close()
    except Exception:
        # DB is missing or corrupted — delete and start fresh
        try:
            DB_PATH.unlink(missing_ok=True)
        except Exception:
            pass
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_uid     INTEGER PRIMARY KEY,
            started_at      REAL,
            track_name      TEXT,
            session_type    INTEGER,
            weather         TEXT,
            total_laps      INTEGER,
            track_length    INTEGER
        );

        CREATE TABLE IF NOT EXISTS participants (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_uid     INTEGER,
            car_idx         INTEGER,
            driver_name     TEXT,
            team_id         INTEGER,
            race_number     INTEGER,
            ai_controlled   INTEGER,
            UNIQUE(session_uid, car_idx)
        );

        CREATE TABLE IF NOT EXISTS telemetry_frames (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_uid     INTEGER,
            frame_id        INTEGER,
            session_time    REAL,
            lap_num         INTEGER,
            lap_distance    REAL,
            speed           INTEGER,
            throttle        REAL,
            brake           REAL,
            steer           REAL,
            gear            INTEGER,
            engine_rpm      INTEGER,
            drs             INTEGER,
            tyre_sl_temp    INTEGER,
            tyre_sr_temp    INTEGER,
            tyre_il_temp    INTEGER,
            tyre_ir_temp    INTEGER,
            brake_temp_fl   INTEGER,
            brake_temp_fr   INTEGER,
            brake_temp_rl   INTEGER,
            brake_temp_rr   INTEGER,
            fuel_in_tank    REAL,
            ers_store_pct   REAL,
            ers_deploy_mode INTEGER,
            tyre_wear_fl    REAL,
            tyre_wear_fr    REAL,
            tyre_wear_rl    REAL,
            tyre_wear_rr    REAL,
            world_x         REAL,
            world_y         REAL,
            world_z         REAL,
            lap_time_ms     INTEGER DEFAULT 0,
            slip_fl         REAL DEFAULT 0,
            slip_fr         REAL DEFAULT 0,
            slip_rl         REAL DEFAULT 0,
            slip_rr         REAL DEFAULT 0,
            blisters_fl     REAL DEFAULT 0,
            blisters_fr     REAL DEFAULT 0,
            blisters_rl     REAL DEFAULT 0,
            blisters_rr     REAL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_tf_session ON telemetry_frames(session_uid, lap_num, lap_distance);

        CREATE TABLE IF NOT EXISTS laps (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_uid     INTEGER,
            car_idx         INTEGER,
            lap_num         INTEGER,
            lap_time_ms     INTEGER,
            s1_ms           INTEGER,
            s2_ms           INTEGER,
            s3_ms           INTEGER,
            tyre_compound   TEXT,
            tyre_age        INTEGER,
            fuel_at_start   REAL,
            lap_invalid     INTEGER,
            position        INTEGER,
            UNIQUE(session_uid, car_idx, lap_num)
        );
        CREATE INDEX IF NOT EXISTS idx_laps_session ON laps(session_uid);

        CREATE TABLE IF NOT EXISTS events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_uid     INTEGER,
            session_time    REAL,
            event_code      TEXT,
            event_name      TEXT,
            details_json    TEXT
        );

        CREATE TABLE IF NOT EXISTS final_classification (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_uid     INTEGER,
            car_idx         INTEGER,
            position        INTEGER,
            num_laps        INTEGER,
            best_lap_ms     INTEGER,
            total_time_s    REAL,
            penalties_s     INTEGER,
            tyre_stints_json TEXT,
            UNIQUE(session_uid, car_idx)
        );
    """)
    # migrations for existing databases
    try:
        conn.execute("ALTER TABLE laps ADD COLUMN position INTEGER")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE sessions ADD COLUMN setup_json TEXT")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE telemetry_frames ADD COLUMN lap_time_ms INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    # add UNIQUE constraint to final_classification if missing (recreate table)
    try:
        conn.execute("SELECT 1 FROM final_classification LIMIT 1")
        # check if unique index exists
        idx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='final_classification' AND sql LIKE '%UNIQUE%'"
        ).fetchone()
        if not idx:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS final_classification_new (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_uid     INTEGER,
                    car_idx         INTEGER,
                    position        INTEGER,
                    num_laps        INTEGER,
                    best_lap_ms     INTEGER,
                    total_time_s    REAL,
                    penalties_s     INTEGER,
                    tyre_stints_json TEXT,
                    UNIQUE(session_uid, car_idx)
                );
                INSERT OR IGNORE INTO final_classification_new
                    (session_uid, car_idx, position, num_laps, best_lap_ms, total_time_s, penalties_s, tyre_stints_json)
                SELECT DISTINCT session_uid, car_idx, position, num_laps, best_lap_ms, total_time_s, penalties_s, tyre_stints_json
                FROM final_classification;
                DROP TABLE final_classification;
                ALTER TABLE final_classification_new RENAME TO final_classification;
            """)
            conn.commit()
    except Exception:
        pass
    for col in ["slip_fl REAL DEFAULT 0", "slip_fr REAL DEFAULT 0",
                "slip_rl REAL DEFAULT 0", "slip_rr REAL DEFAULT 0",
                "blisters_fl REAL DEFAULT 0", "blisters_fr REAL DEFAULT 0",
                "blisters_rl REAL DEFAULT 0", "blisters_rr REAL DEFAULT 0"]:
        try:
            conn.execute(f"ALTER TABLE telemetry_frames ADD COLUMN {col}")
            conn.commit()
        except Exception:
            pass
    conn.close()


class TelemetryDB:
    def __init__(self):
        self.conn = get_conn()

    def upsert_session(self, uid: int, track_name: str, session_type: int,
                       weather: str, total_laps: int, track_length: int):
        self.conn.execute("""
            INSERT INTO sessions(session_uid, started_at, track_name, session_type, weather, total_laps, track_length)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(session_uid) DO UPDATE SET
                track_name=excluded.track_name, session_type=excluded.session_type,
                weather=excluded.weather, total_laps=excluded.total_laps
        """, (_s64(uid), time.time(), track_name, session_type, weather, total_laps, track_length))
        self.conn.commit()

    def upsert_setup(self, session_uid: int, setup: dict):
        self.conn.execute(
            "UPDATE sessions SET setup_json=? WHERE session_uid=?",
            (json.dumps(setup), _s64(session_uid))
        )
        self.conn.commit()

    def upsert_participant(self, session_uid: int, car_idx: int, name: str,
                           team_id: int, race_number: int, ai: int):
        self.conn.execute("""
            INSERT INTO participants(session_uid, car_idx, driver_name, team_id, race_number, ai_controlled)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(session_uid, car_idx) DO UPDATE SET driver_name=excluded.driver_name
        """, (_s64(session_uid), car_idx, name, team_id, race_number, ai))
        self.conn.commit()

    def insert_frame(self, session_uid: int, frame_id: int, session_time: float,
                     lap_num: int, lap_distance: float,
                     speed: int, throttle: float, brake: float, steer: float,
                     gear: int, rpm: int, drs: int,
                     tyre_surf: tuple, tyre_inner: tuple, brake_temp: tuple,
                     fuel: float, ers_pct: float, ers_mode: int,
                     tyre_wear: tuple, pos: tuple, lap_time_ms: int = 0,
                     wheel_slip: tuple = (0,0,0,0), tyre_blisters: tuple = (0,0,0,0)):
        self.conn.execute("""
            INSERT INTO telemetry_frames(
                session_uid, frame_id, session_time, lap_num, lap_distance,
                speed, throttle, brake, steer, gear, engine_rpm, drs,
                tyre_sl_temp, tyre_sr_temp, tyre_il_temp, tyre_ir_temp,
                brake_temp_fl, brake_temp_fr, brake_temp_rl, brake_temp_rr,
                fuel_in_tank, ers_store_pct, ers_deploy_mode,
                tyre_wear_fl, tyre_wear_fr, tyre_wear_rl, tyre_wear_rr,
                world_x, world_y, world_z, lap_time_ms,
                slip_fl, slip_fr, slip_rl, slip_rr,
                blisters_fl, blisters_fr, blisters_rl, blisters_rr
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            _s64(session_uid), frame_id, session_time, lap_num, lap_distance,
            speed, throttle, brake, steer, gear, rpm, drs,
            tyre_surf[2], tyre_surf[3], tyre_inner[2], tyre_inner[3],
            brake_temp[2], brake_temp[3], brake_temp[0], brake_temp[1],
            fuel, ers_pct, ers_mode,
            tyre_wear[2], tyre_wear[3], tyre_wear[0], tyre_wear[1],
            pos[0], pos[1], pos[2], lap_time_ms,
            wheel_slip[2], wheel_slip[3], wheel_slip[0], wheel_slip[1],
            tyre_blisters[2], tyre_blisters[3], tyre_blisters[0], tyre_blisters[1],
        ))

    def commit(self):
        self.conn.commit()

    def upsert_lap(self, session_uid: int, car_idx: int, lap_num: int,
                   lap_time_ms: int, s1_ms: int, s2_ms: int, s3_ms: int,
                   tyre_compound: str, tyre_age: int, fuel: float, invalid: int,
                   position: int = 0):
        self.conn.execute("""
            INSERT INTO laps(session_uid, car_idx, lap_num, lap_time_ms,
                s1_ms, s2_ms, s3_ms, tyre_compound, tyre_age, fuel_at_start, lap_invalid, position)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(session_uid, car_idx, lap_num) DO UPDATE SET
                lap_time_ms=excluded.lap_time_ms,
                s1_ms=excluded.s1_ms, s2_ms=excluded.s2_ms, s3_ms=excluded.s3_ms,
                position=excluded.position
        """, (_s64(session_uid), car_idx, lap_num, lap_time_ms,
              s1_ms, s2_ms, s3_ms, tyre_compound, tyre_age, fuel, invalid, position))
        self.conn.commit()

    def insert_event(self, session_uid: int, session_time: float,
                     code: str, name: str, details: dict):
        self.conn.execute("""
            INSERT INTO events(session_uid, session_time, event_code, event_name, details_json)
            VALUES (?,?,?,?,?)
        """, (_s64(session_uid), session_time, code, name, json.dumps(details)))
        self.conn.commit()

    def insert_final_classification(self, session_uid: int, car_idx: int,
                                    position: int, num_laps: int, best_lap_ms: int,
                                    total_time_s: float, penalties_s: int,
                                    tyre_stints: list):
        self.conn.execute("""
            INSERT INTO final_classification(
                session_uid, car_idx, position, num_laps, best_lap_ms,
                total_time_s, penalties_s, tyre_stints_json)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(session_uid, car_idx) DO UPDATE SET
                position=excluded.position, num_laps=excluded.num_laps,
                best_lap_ms=excluded.best_lap_ms, total_time_s=excluded.total_time_s,
                penalties_s=excluded.penalties_s, tyre_stints_json=excluded.tyre_stints_json
        """, (_s64(session_uid), car_idx, position, num_laps, best_lap_ms,
              total_time_s, penalties_s, json.dumps(tyre_stints)))
        self.conn.commit()

    def list_sessions(self) -> list:
        cur = self.conn.execute("""
            SELECT s.*,
                   COUNT(DISTINCT l.lap_num) as lap_count,
                   MIN(CASE WHEN l.lap_time_ms > 0 THEN l.lap_time_ms END) as best_lap_ms
            FROM sessions s
            LEFT JOIN laps l ON l.session_uid=s.session_uid
            GROUP BY s.session_uid
            ORDER BY s.started_at DESC LIMIT 50
        """)
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            d["session_uid"] = str(int(d["session_uid"]))  # stringify to preserve int64 precision in JSON
            rows.append(d)
        return rows

    def get_session_laps(self, session_uid: int) -> list:
        cur = self.conn.execute("""
            SELECT * FROM laps WHERE session_uid=? AND lap_time_ms > 0 ORDER BY lap_num
        """, (_s64(session_uid),))
        return [dict(r) for r in cur.fetchall()]

    def get_lap_frames(self, session_uid: int, lap_num: int) -> list:
        cur = self.conn.execute("""
            SELECT session_time, lap_distance, lap_time_ms, speed, throttle, brake, steer, gear,
                   engine_rpm, drs, tyre_sl_temp, tyre_sr_temp, tyre_il_temp, tyre_ir_temp,
                   ers_store_pct, fuel_in_tank, tyre_wear_fl, tyre_wear_fr,
                   tyre_wear_rl, tyre_wear_rr, world_x, world_y, world_z
            FROM telemetry_frames
            WHERE session_uid=? AND lap_num=?
            ORDER BY lap_distance
        """, (_s64(session_uid), lap_num))
        return [dict(r) for r in cur.fetchall()]

    def export_session_csv(self, session_uid: int) -> str:
        import csv, io
        from datetime import datetime
        out = io.StringIO()

        uid = _s64(session_uid)
        cur = self.conn.execute("SELECT * FROM sessions WHERE session_uid=?", (uid,))
        session = cur.fetchone()
        if not session:
            return "No session found."
        s = dict(session)

        cur2 = self.conn.execute(
            "SELECT car_idx, driver_name, team_id, race_number FROM participants WHERE session_uid=? ORDER BY car_idx",
            (uid,))
        participants = {r["car_idx"]: dict(r) for r in cur2.fetchall()}

        cur3 = self.conn.execute(
            "SELECT * FROM laps WHERE session_uid=? ORDER BY car_idx, lap_num", (uid,))
        laps = [dict(r) for r in cur3.fetchall()]

        cur4 = self.conn.execute(
            "SELECT * FROM final_classification WHERE session_uid=? ORDER BY position", (uid,))
        classification = [dict(r) for r in cur4.fetchall()]

        writer = csv.writer(out)

        _stype_names = {
            0:'Unknown', 1:'Practice 1', 2:'Practice 2', 3:'Practice 3', 4:'Short Practice',
            5:'Q1', 6:'Q2', 7:'Q3', 8:'Short Qualifying', 9:'One-Shot Qualifying',
            10:'Race', 11:'Race 2', 12:'Race 3', 13:'Time Trial',
            14:'Sprint Shootout 1', 15:'Sprint Shootout 2', 16:'Sprint Shootout 3', 17:'Sprint Race',
        }
        _st = s.get("session_type", 0)
        writer.writerow(["=== SESSION INFO ==="])
        writer.writerow(["Track", s.get("track_name", "?")])
        writer.writerow(["Session Type", _stype_names.get(_st, f"Type {_st}")])
        writer.writerow(["Weather", s.get("weather", "?")])
        writer.writerow(["Total Laps", s.get("total_laps", "?")])
        writer.writerow(["Track Length (m)", s.get("track_length") or "?"])
        started = s.get("started_at")
        writer.writerow(["Date", datetime.fromtimestamp(started).strftime("%Y-%m-%d %H:%M") if started else "?"])
        writer.writerow([])

        setup_raw = s.get("setup_json")
        if setup_raw:
            try:
                setup = json.loads(setup_raw)
                writer.writerow(["=== CAR SETUP ==="])
                for k, v in [
                    ("Front Wing", setup.get("front_wing","?")), ("Rear Wing", setup.get("rear_wing","?")),
                    ("On-Throttle Diff", setup.get("on_throttle","?")), ("Off-Throttle Diff", setup.get("off_throttle","?")),
                    ("Front Camber", setup.get("front_camber","?")), ("Rear Camber", setup.get("rear_camber","?")),
                    ("Front Toe", setup.get("front_toe","?")), ("Rear Toe", setup.get("rear_toe","?")),
                    ("Front Susp", setup.get("front_susp","?")), ("Rear Susp", setup.get("rear_susp","?")),
                    ("Front ARB", setup.get("front_arb","?")), ("Rear ARB", setup.get("rear_arb","?")),
                    ("Front Ride Height", setup.get("front_susp_height","?")), ("Rear Ride Height", setup.get("rear_susp_height","?")),
                    ("Brake Pressure %", setup.get("brake_pressure","?")), ("Brake Bias %", setup.get("brake_bias","?")),
                    ("Engine Braking", setup.get("engine_braking","?")),
                    ("FL PSI", setup.get("fl_tyre_psi","?")), ("FR PSI", setup.get("fr_tyre_psi","?")),
                    ("RL PSI", setup.get("rl_tyre_psi","?")), ("RR PSI", setup.get("rr_tyre_psi","?")),
                    ("Ballast", setup.get("ballast","?")), ("Fuel Load kg", setup.get("fuel_load","?")),
                ]:
                    writer.writerow([k, v])
                writer.writerow([])
            except Exception:
                pass

        writer.writerow(["=== LAP TIMES ==="])
        writer.writerow(["Car", "Driver", "Lap", "Lap Time", "S1", "S2", "S3", "Tyre", "Tyre Age", "Valid"])

        def ms_to_str(ms):
            if not ms:
                return ""
            m = ms // 60000
            s = (ms % 60000) / 1000
            return f"{m}:{s:06.3f}"

        for lap in laps:
            p = participants.get(lap["car_idx"], {})
            writer.writerow([
                lap["car_idx"],
                p.get("driver_name", f"Car {lap['car_idx']}"),
                lap["lap_num"],
                ms_to_str(lap["lap_time_ms"]),
                ms_to_str(lap["s1_ms"]),
                ms_to_str(lap["s2_ms"]),
                ms_to_str(lap["s3_ms"]),
                lap.get("tyre_compound", "?"),
                lap.get("tyre_age", "?"),
                "No" if lap.get("lap_invalid") else "Yes",
            ])
        writer.writerow([])

        if classification:
            writer.writerow(["=== FINAL CLASSIFICATION ==="])
            writer.writerow(["Position", "Driver", "Laps", "Best Lap", "Total Time", "Penalties (s)"])
            for clf in classification:
                p = participants.get(clf["car_idx"], {})
                total = clf.get("total_time_s")
                writer.writerow([
                    clf["position"],
                    p.get("driver_name", f"Car {clf['car_idx']}"),
                    clf["num_laps"],
                    ms_to_str(clf.get("best_lap_ms")),
                    f"{total:.3f}s" if total else "",
                    clf.get("penalties_s", 0),
                ])
            writer.writerow([])

        writer.writerow(["=== TELEMETRY SUMMARY (player car, per lap) ==="])
        writer.writerow(["Lap", "Avg Speed", "Max Speed", "Avg Throttle%", "Avg Brake%",
                         "Avg Fuel (kg)", "Avg ERS%", "FL Wear%", "FR Wear%", "RL Wear%", "RR Wear%"])
        telem_cur = self.conn.execute("""
            SELECT lap_num,
                   ROUND(AVG(speed),1) avg_spd, MAX(speed) max_spd,
                   ROUND(AVG(throttle)*100,1) avg_thr, ROUND(AVG(brake)*100,1) avg_brk,
                   ROUND(AVG(fuel_in_tank),2) avg_fuel, ROUND(AVG(ers_store_pct),1) avg_ers,
                   ROUND(MAX(tyre_wear_fl),1) fl, ROUND(MAX(tyre_wear_fr),1) fr,
                   ROUND(MAX(tyre_wear_rl),1) rl, ROUND(MAX(tyre_wear_rr),1) rr
            FROM telemetry_frames WHERE session_uid=?
            GROUP BY lap_num ORDER BY lap_num
        """, (uid,))
        for row in telem_cur.fetchall():
            writer.writerow(list(row))

        return out.getvalue()

    def _write_session_to_csv(self, writer, session_uid: int, prefix: str = ""):
        """Write full session data (lap summary + telemetry frames) to an open csv.writer."""
        from datetime import datetime
        uid = _s64(session_uid)
        cur = self.conn.execute("SELECT * FROM sessions WHERE session_uid=?", (uid,))
        session = cur.fetchone()
        if not session:
            return False
        s = dict(session)

        SESSION_TYPE_NAMES = {
            0:'Unknown',
            1:'Practice 1', 2:'Practice 2', 3:'Practice 3', 4:'Short Practice',
            5:'Q1', 6:'Q2', 7:'Q3', 8:'Short Qualifying', 9:'One-Shot Qualifying',
            10:'Race', 11:'Race 2', 12:'Race 3', 13:'Time Trial',
            14:'Sprint Shootout 1', 15:'Sprint Shootout 2', 16:'Sprint Shootout 3',
            17:'Sprint Race',
        }

        def ms_to_str(ms):
            if not ms: return ""
            m = ms // 60000; s2 = (ms % 60000) / 1000
            return f"{m}:{s2:06.3f}"

        type_name = SESSION_TYPE_NAMES.get(s.get('session_type', 0), f"Type {s.get('session_type','?')}")
        started = s.get("started_at")
        date_str = datetime.fromtimestamp(started).strftime("%Y-%m-%d %H:%M") if started else "?"

        label = f"{prefix}{s.get('track_name','?')} | {type_name} | {date_str}"
        writer.writerow([f"=== {label} ==="])
        writer.writerow(["Track", s.get("track_name","?"), "Type", type_name,
                         "Weather", s.get("weather","?"), "Date", date_str])
        writer.writerow([])

        # — car setup —
        setup_raw = s.get("setup_json")
        if setup_raw:
            try:
                setup = json.loads(setup_raw)
                writer.writerow(["CAR SETUP"])
                setup_labels = [
                    ("Front Wing",          setup.get("front_wing","?")),
                    ("Rear Wing",           setup.get("rear_wing","?")),
                    ("On-Throttle Diff",    setup.get("on_throttle","?")),
                    ("Off-Throttle Diff",   setup.get("off_throttle","?")),
                    ("Front Camber",        setup.get("front_camber","?")),
                    ("Rear Camber",         setup.get("rear_camber","?")),
                    ("Front Toe",           setup.get("front_toe","?")),
                    ("Rear Toe",            setup.get("rear_toe","?")),
                    ("Front Suspension",    setup.get("front_susp","?")),
                    ("Rear Suspension",     setup.get("rear_susp","?")),
                    ("Front ARB",           setup.get("front_arb","?")),
                    ("Rear ARB",            setup.get("rear_arb","?")),
                    ("Front Ride Height",   setup.get("front_susp_height","?")),
                    ("Rear Ride Height",    setup.get("rear_susp_height","?")),
                    ("Brake Pressure (%)",  setup.get("brake_pressure","?")),
                    ("Brake Bias (%)",      setup.get("brake_bias","?")),
                    ("Engine Braking",      setup.get("engine_braking","?")),
                    ("FL Tyre PSI",         setup.get("fl_tyre_psi","?")),
                    ("FR Tyre PSI",         setup.get("fr_tyre_psi","?")),
                    ("RL Tyre PSI",         setup.get("rl_tyre_psi","?")),
                    ("RR Tyre PSI",         setup.get("rr_tyre_psi","?")),
                    ("Ballast",             setup.get("ballast","?")),
                    ("Fuel Load (kg)",      setup.get("fuel_load","?")),
                ]
                for k, v in setup_labels:
                    writer.writerow([k, v])
                writer.writerow([])
            except Exception:
                pass

        # — lap summary —
        writer.writerow(["LAP SUMMARY"])
        writer.writerow(["Lap", "Position", "Lap Time", "S1", "S2", "S3", "Tyre", "Tyre Age", "Valid"])
        cur2 = self.conn.execute(
            "SELECT * FROM laps WHERE session_uid=? AND lap_time_ms > 0 ORDER BY lap_num", (uid,))
        for lap in [dict(r) for r in cur2.fetchall()]:
            writer.writerow([
                lap["lap_num"], lap.get("position") or "—",
                ms_to_str(lap["lap_time_ms"]),
                ms_to_str(lap["s1_ms"]), ms_to_str(lap["s2_ms"]), ms_to_str(lap["s3_ms"]),
                lap.get("tyre_compound","?"), lap.get("tyre_age","?"),
                "No" if lap.get("lap_invalid") else "Yes",
            ])
        writer.writerow([])

        # — full telemetry frames —
        writer.writerow(["TELEMETRY (one row per sample ~20Hz)"])
        writer.writerow([
            "Lap", "Distance(m)", "Session Time(s)",
            "Speed(kph)", "Throttle%", "Brake%", "Steer", "Gear", "RPM", "ActiveAero(0=Corner,1=SLM)",
            "TyreSL_Temp", "TyreSR_Temp", "TyreIL_Temp", "TyreIR_Temp",
            "BrakeFL_Temp", "BrakeFR_Temp", "BrakeRL_Temp", "BrakeRR_Temp",
            "Fuel(kg)", "ERS_Store%", "ERS_Mode",
            "WearFL%", "WearFR%", "WearRL%", "WearRR%",
            "World_X", "World_Y", "World_Z",
            "SlipFL", "SlipFR", "SlipRL", "SlipRR",
            "BlistersFL%", "BlistersFR%", "BlistersRL%", "BlistersRR%",
        ])
        cur3 = self.conn.execute("""
            SELECT lap_num, ROUND(lap_distance,1), ROUND(session_time,3),
                   speed, ROUND(throttle*100,1), ROUND(brake*100,1), ROUND(steer,3),
                   gear, engine_rpm, drs,
                   tyre_sl_temp, tyre_sr_temp, tyre_il_temp, tyre_ir_temp,
                   brake_temp_fl, brake_temp_fr, brake_temp_rl, brake_temp_rr,
                   ROUND(fuel_in_tank,3), ROUND(ers_store_pct,1), ers_deploy_mode,
                   ROUND(tyre_wear_fl,2), ROUND(tyre_wear_fr,2),
                   ROUND(tyre_wear_rl,2), ROUND(tyre_wear_rr,2),
                   ROUND(world_x,2), ROUND(world_y,2), ROUND(world_z,2),
                   ROUND(slip_fl,4), ROUND(slip_fr,4), ROUND(slip_rl,4), ROUND(slip_rr,4),
                   ROUND(blisters_fl,2), ROUND(blisters_fr,2), ROUND(blisters_rl,2), ROUND(blisters_rr,2)
            FROM telemetry_frames WHERE session_uid=?
            ORDER BY lap_num, lap_distance
        """, (uid,))
        for row in cur3.fetchall():
            writer.writerow(list(row))
        writer.writerow([])
        return True

    def export_session_full(self, session_uid: int) -> str:
        import csv, io
        out = io.StringIO()
        writer = csv.writer(out)
        if not self._write_session_to_csv(writer, session_uid):
            return "No session found."
        return out.getvalue()

    def export_ai_summary(self, session_uid: int, prefix: str = "") -> str:
        """Plain-text markdown summary optimised for pasting into an AI chat."""
        from datetime import datetime
        uid = _s64(session_uid)

        cur = self.conn.execute("SELECT * FROM sessions WHERE session_uid=?", (uid,))
        session = cur.fetchone()
        if not session:
            return "No session found."
        s = dict(session)

        SESSION_TYPE_NAMES = {
            0:'Unknown',
            1:'Practice 1', 2:'Practice 2', 3:'Practice 3', 4:'Short Practice',
            5:'Q1', 6:'Q2', 7:'Q3', 8:'Short Qualifying', 9:'One-Shot Qualifying',
            10:'Race', 11:'Race 2', 12:'Race 3', 13:'Time Trial',
            14:'Sprint Shootout 1', 15:'Sprint Shootout 2', 16:'Sprint Shootout 3',
            17:'Sprint Race',
        }
        stype_id = s.get('session_type', 0)
        stype = SESSION_TYPE_NAMES.get(stype_id, f"Type {stype_id}")
        is_race = stype_id in (10, 11, 12, 17)
        started = s.get("started_at")
        date_str = datetime.fromtimestamp(started).strftime("%Y-%m-%d %H:%M") if started else "?"

        def ms(v):
            if not v: return "—"
            m = v // 60000; sc = (v % 60000) / 1000
            return f"{m}:{sc:06.3f}"

        lines = []
        lines.append(f"# {prefix}F1 Telemetry Report")
        lines.append(f"**Track:** {s.get('track_name','?')}  |  **Session:** {stype}  |  **Date:** {date_str}")
        tlen = s.get('track_length') or '?'
        lines.append(f"**Weather:** {s.get('weather','?')}  |  **Track length:** {tlen} m")
        lines.append("")

        # Car setup
        setup_raw = s.get("setup_json")
        if setup_raw:
            try:
                setup = json.loads(setup_raw)
                lines.append("## Car Setup")
                lines.append(f"Wings: Front {setup.get('front_wing','?')} / Rear {setup.get('rear_wing','?')}")
                lines.append(f"Diff: On-throttle {setup.get('on_throttle','?')}% / Off-throttle {setup.get('off_throttle','?')}%")
                lines.append(f"Suspension: Front {setup.get('front_susp','?')} / Rear {setup.get('rear_susp','?')}  |  ARB: F {setup.get('front_arb','?')} / R {setup.get('rear_arb','?')}")
                lines.append(f"Camber: F {setup.get('front_camber','?')} / R {setup.get('rear_camber','?')}  |  Toe: F {setup.get('front_toe','?')} / R {setup.get('rear_toe','?')}")
                lines.append(f"Ride height: F {setup.get('front_susp_height','?')} / R {setup.get('rear_susp_height','?')}")
                lines.append(f"Brakes: Pressure {setup.get('brake_pressure','?')}% / Bias {setup.get('brake_bias','?')}% / Engine braking {setup.get('engine_braking','?')}")
                lines.append(f"Tyre PSI: FL {setup.get('fl_tyre_psi','?')} / FR {setup.get('fr_tyre_psi','?')} / RL {setup.get('rl_tyre_psi','?')} / RR {setup.get('rr_tyre_psi','?')}")
                lines.append(f"Fuel load: {setup.get('fuel_load','?')} kg  |  Ballast: {setup.get('ballast','?')}")
                lines.append("")
            except Exception:
                pass

        # Lap summary
        cur2 = self.conn.execute(
            "SELECT * FROM laps WHERE session_uid=? AND lap_time_ms > 0 ORDER BY lap_num", (uid,))
        laps = [dict(r) for r in cur2.fetchall()]

        if laps:
            best_ms = min(l["lap_time_ms"] for l in laps)
            lines.append("## Lap Times")
            if is_race:
                lines.append(f"{'Lap':>4}  {'Time':>9}  {'S1':>8}  {'S2':>8}  {'S3':>8}  {'Compound':<10}  {'Age':>3}  {'Pos':>3}  Note")
                lines.append(f"{'---':>4}  {'----':>9}  {'--':>8}  {'--':>8}  {'--':>8}  {'--------':<10}  {'---':>3}  {'---':>3}  ----")
            else:
                lines.append(f"{'Lap':>4}  {'Time':>9}  {'S1':>8}  {'S2':>8}  {'S3':>8}  {'Compound':<10}  {'Age':>3}  Note")
                lines.append(f"{'---':>4}  {'----':>9}  {'--':>8}  {'--':>8}  {'--':>8}  {'--------':<10}  {'---':>3}  ----")
            for lap in laps:
                lt = lap["lap_time_ms"]
                delta = f"+{(lt-best_ms)/1000:.3f}s" if lt > best_ms else "BEST"
                invalid = " [DELETED]" if lap.get("lap_invalid") else ""
                if is_race:
                    lines.append(
                        f"{lap['lap_num']:>4}  {ms(lt):>9}  {ms(lap.get('s1_ms')):>8}  {ms(lap.get('s2_ms')):>8}  {ms(lap.get('s3_ms')):>8}"
                        f"  {lap.get('tyre_compound','?'):<10}  {lap.get('tyre_age','?'):>3}  {lap.get('position') or '—':>3}  {delta}{invalid}"
                    )
                else:
                    lines.append(
                        f"{lap['lap_num']:>4}  {ms(lt):>9}  {ms(lap.get('s1_ms')):>8}  {ms(lap.get('s2_ms')):>8}  {ms(lap.get('s3_ms')):>8}"
                        f"  {lap.get('tyre_compound','?'):<10}  {lap.get('tyre_age','?'):>3}  {delta}{invalid}"
                    )
            lines.append(f"\n**Best lap:** {ms(best_ms)}")
            lines.append("")

        # Per-lap telemetry averages
        telem = self.conn.execute("""
            SELECT lap_num,
                   ROUND(AVG(speed),0)            avg_spd,
                   MAX(speed)                      max_spd,
                   ROUND(AVG(throttle)*100,1)      avg_thr,
                   ROUND(AVG(brake)*100,1)         avg_brk,
                   ROUND(AVG(fuel_in_tank),2)      avg_fuel,
                   ROUND(MIN(fuel_in_tank),2)      end_fuel,
                   ROUND(AVG(ers_store_pct),0)     avg_ers,
                   ROUND(MAX(tyre_wear_fl),1)      wfl,
                   ROUND(MAX(tyre_wear_fr),1)      wfr,
                   ROUND(MAX(tyre_wear_rl),1)      wrl,
                   ROUND(MAX(tyre_wear_rr),1)      wrr,
                   ROUND(MAX(blisters_fl),1)       bfl,
                   ROUND(MAX(blisters_fr),1)       bfr,
                   ROUND(MAX(blisters_rl),1)       brl,
                   ROUND(MAX(blisters_rr),1)       brr,
                   ROUND(AVG(ABS(slip_fl)),4)      sfl,
                   ROUND(AVG(ABS(slip_fr)),4)      sfr,
                   ROUND(AVG(ABS(slip_rl)),4)      srl,
                   ROUND(AVG(ABS(slip_rr)),4)      srr
            FROM telemetry_frames WHERE session_uid=?
            GROUP BY lap_num ORDER BY lap_num
        """, (uid,)).fetchall()

        if telem:
            lines.append("## Per-Lap Telemetry Averages")
            if is_race:
                lines.append("_Note: Fuel(kg) is the lap-average fuel level. Lap 1 may read lower than setup fuel load if a formation lap was driven before telemetry recording began._")
            lines.append(f"{'Lap':>4}  {'AvgSpd':>6}  {'MaxSpd':>6}  {'Thr%':>5}  {'Brk%':>5}  {'ERS%':>5}  {'Fuel(kg)':>8}")
            lines.append(f"{'---':>4}  {'------':>6}  {'------':>6}  {'----':>5}  {'----':>5}  {'----':>5}  {'--------':>8}")
            for r in telem:
                lines.append(f"{r['lap_num']:>4}  {r['avg_spd']:>6}  {r['max_spd']:>6}  {r['avg_thr']:>5}  {r['avg_brk']:>5}  {r['avg_ers']:>5}  {r['avg_fuel']:>8}")
            lines.append("")

            lines.append("## Tyre Wear & Blisters (peak per lap, %)")
            lines.append(f"{'Lap':>4}  {'W-FL':>5}  {'W-FR':>5}  {'W-RL':>5}  {'W-RR':>5}  {'B-FL':>5}  {'B-FR':>5}  {'B-RL':>5}  {'B-RR':>5}")
            lines.append(f"{'---':>4}  {'----':>5}  {'----':>5}  {'----':>5}  {'----':>5}  {'----':>5}  {'----':>5}  {'----':>5}  {'----':>5}")
            for r in telem:
                lines.append(
                    f"{r['lap_num']:>4}  {r['wfl']:>5}  {r['wfr']:>5}  {r['wrl']:>5}  {r['wrr']:>5}"
                    f"  {r['bfl']:>5}  {r['bfr']:>5}  {r['brl']:>5}  {r['brr']:>5}"
                )
            lines.append("")

            lines.append("## Wheel Slip (avg absolute per lap — higher = more wheelspin/lockup)")
            lines.append(f"{'Lap':>4}  {'FL':>7}  {'FR':>7}  {'RL':>7}  {'RR':>7}")
            lines.append(f"{'---':>4}  {'--':>7}  {'--':>7}  {'--':>7}  {'--':>7}")
            for r in telem:
                lines.append(f"{r['lap_num']:>4}  {r['sfl']:>7.4f}  {r['sfr']:>7.4f}  {r['srl']:>7.4f}  {r['srr']:>7.4f}")
            lines.append("")

        # Corner balance analysis
        # m_wheelSlip is combined slip dominated by longitudinal (traction).
        # To isolate lateral balance: compute the rear/front slip ratio in corners
        # and compare it against the straight-line traction baseline ratio.
        # ratio_corner > ratio_straight  → rear sliding extra → oversteer
        # ratio_corner < ratio_straight  → fronts relatively worse → understeer

        CORNER_NAMES = {
            # Monaco (~3337 m)
            "Monaco": [
                (130,  "Sainte Devote"),
                (380,  "Beau Rivage"),
                (520,  "Massenet"),
                (620,  "Casino"),
                (780,  "Mirabeau Haute"),
                (900,  "Mirabeau Bas"),
                (1030, "Grand Hotel Hairpin"),
                (1280, "Portier"),
                (1560, "Chicane"),
                (1760, "Tabac"),
                (1870, "Piscine S1"),
                (1960, "Piscine S2"),
                (2180, "La Rascasse"),
                (2430, "Anthony Noghes"),
            ],
            # add more tracks here as needed
        }

        track_name = s.get("track_name", "")
        corner_name_map = CORNER_NAMES.get(track_name, [])

        def _corner_name(dist):
            if not corner_name_map:
                return ""
            best, best_d = "", 9999
            for cd, cn in corner_name_map:
                d = abs(dist - cd)
                if d < best_d and d < 200:
                    best_d, best = d, cn
            return best

        # straight-line baseline: |steer| < 0.03, speed > 100, throttle > 0.5
        baseline = self.conn.execute("""
            SELECT AVG(slip_fl + slip_fr) / 2.0 AS avg_front,
                   AVG(slip_rl + slip_rr) / 2.0 AS avg_rear
            FROM telemetry_frames
            WHERE session_uid=? AND ABS(steer) < 0.03 AND speed > 100
              AND throttle > 0.5 AND slip_fl IS NOT NULL
        """, (uid,)).fetchone()

        base_front = baseline["avg_front"] or 0.0
        base_rear  = baseline["avg_rear"]  or 0.0

        corner_rows = self.conn.execute("""
            SELECT lap_num, lap_distance,
                   (slip_rl + slip_rr) / 2.0 AS rear_slip,
                   (slip_fl + slip_fr) / 2.0 AS front_slip
            FROM telemetry_frames
            WHERE session_uid=? AND ABS(steer) > 0.08 AND speed > 50
              AND slip_fl IS NOT NULL AND slip_rl IS NOT NULL
            ORDER BY lap_num, lap_distance
        """, (uid,)).fetchall()

        if corner_rows:
            from collections import defaultdict
            lap_corners = defaultdict(list)
            prev_lap, prev_dist = None, None
            seg_entry, seg_vals = None, []

            def _flush_seg(lap, entry, vals):
                if len(vals) >= 3:
                    lap_corners[lap].append((entry, sum(vals) / len(vals)))

            for row in corner_rows:
                row = dict(row)
                lap, dist = row["lap_num"], row["lap_distance"]
                front = row["front_slip"]
                # normalised balance: how much more/less rear-biased vs straight baseline
                # positive = rear slipping extra beyond traction = oversteer
                # negative = fronts relatively worse = understeer
                # rear_excess: how much rear slips beyond its straight-line traction baseline
                # front_excess: how much front slips beyond its (near-zero) straight baseline
                # positive balance = rear sliding extra = oversteer
                # negative balance = fronts sliding extra = understeer
                rear_excess  = row["rear_slip"]  - base_rear
                front_excess = row["front_slip"] - base_front
                bal = rear_excess - front_excess
                if lap != prev_lap or (prev_dist is not None and dist - prev_dist > 80):
                    if prev_lap is not None:
                        _flush_seg(prev_lap, seg_entry, seg_vals)
                    seg_entry, seg_vals = dist, []
                seg_vals.append(bal)
                prev_lap, prev_dist = lap, dist
            if prev_lap is not None:
                _flush_seg(prev_lap, seg_entry, seg_vals)

            all_segs = []
            for corners in lap_corners.values():
                all_segs.extend(corners)
            all_segs.sort(key=lambda x: x[0])

            # cluster corners within 60 m into one entry
            clusters = []  # [centroid_dist, [balance_vals]]
            for entry, bal in all_segs:
                placed = False
                for cl in clusters:
                    if abs(entry - cl[0]) < 60:
                        n = len(cl[1])
                        cl[0] = (cl[0] * n + entry) / (n + 1)
                        cl[1].append(bal)
                        placed = True
                        break
                if not placed:
                    clusters.append([entry, [bal]])

            clusters.sort(key=lambda x: x[0])

            if clusters:
                lines.append("## Corner Balance (averaged across laps)")
                lines.append(f"_Straight-line slip baseline — rear: {base_rear:.4f}, front: {base_front:.4f}. "
                             f"Balance = (rear excess) − (front excess) vs baseline. Positive = oversteer, negative = understeer._")
                has_names = bool(corner_name_map)
                if has_names:
                    lines.append(f"{'Corner':<22}  {'Dist(m)':>7}  {'Balance':>8}  Character")
                    lines.append(f"{'------':<22}  {'-------':>7}  {'-------':>8}  ---------")
                else:
                    lines.append(f"{'Corner':>7}  {'Dist(m)':>7}  {'Balance':>8}  Character")
                    lines.append(f"{'------':>7}  {'-------':>7}  {'-------':>8}  ---------")
                for i, (cdist, bals) in enumerate(clusters, 1):
                    avg_bal = sum(bals) / len(bals)
                    if avg_bal > 0.010:
                        char = "oversteer"
                    elif avg_bal < -0.015:
                        char = "understeer"
                    else:
                        char = "neutral"
                    name = _corner_name(cdist)
                    label = name if name else f"C{i}"
                    if has_names:
                        lines.append(f"{label:<22}  {int(cdist):>7}  {avg_bal:>+8.3f}  {char}")
                    else:
                        lines.append(f"{'C'+str(i):>7}  {int(cdist):>7}  {avg_bal:>+8.3f}  {char}")
                lines.append("")

        # Final classification if present
        cur3 = self.conn.execute(
            "SELECT fc.*, p.driver_name FROM final_classification fc "
            "LEFT JOIN participants p ON p.session_uid=fc.session_uid AND p.car_idx=fc.car_idx "
            "WHERE fc.session_uid=? ORDER BY fc.position", (uid,))
        clf = cur3.fetchall()
        if clf:
            lines.append("## Final Classification")
            lines.append(f"{'Pos':>3}  {'Driver':<20}  {'Laps':>4}  {'Best Lap':>9}  {'Total Time':>12}  {'Penalties':>9}")
            lines.append(f"{'---':>3}  {'------':<20}  {'----':>4}  {'--------':>9}  {'----------':>12}  {'---------':>9}")
            for r in clf:
                r = dict(r)
                total = r.get("total_time_s")
                total_str = f"{total:.3f}s" if total else "—"
                dname = r.get('driver_name') or f"Car {r['car_idx']}"
                lines.append(
                    f"{r['position']:>3}  {dname:<20}"
                    f"  {r['num_laps']:>4}  {ms(r.get('best_lap_ms')):>9}  {total_str:>12}  {r.get('penalties_s',0):>9}s"
                )
            lines.append("")

        return "\n".join(lines)

    def export_sessions_csv(self, session_uids: list) -> str:
        import csv, io
        from datetime import datetime
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["=== MERGED EXPORT ===",
                         f"Sessions: {len(session_uids)}",
                         f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
        writer.writerow([])
        for i, uid in enumerate(session_uids, 1):
            self._write_session_to_csv(writer, uid, prefix=f"[{i}/{len(session_uids)}] ")
        return out.getvalue()


# ── HTTP API helpers ──────────────────────────────────────────────────────────
def sessions_json(db: TelemetryDB) -> list:
    return db.list_sessions()

def laps_json(db: TelemetryDB, session_uid: int) -> list:
    return db.get_session_laps(int(session_uid))

def frames_json(db: TelemetryDB, session_uid: int, lap_num: int) -> list:
    return db.get_lap_frames(session_uid, lap_num)
