"""
F1 25 Telemetry Listener
========================
• Listens for UDP packets on port 20777 (configurable)
• Parses all packet types using the official F1 25 spec
• Broadcasts live state as JSON over WebSocket (port 8765)
• Serves a tiny HTTP API for the history viewer (port 8766)
• Logs everything to SQLite via db.py

Usage:
    python listener.py [--udp-port 20777] [--ws-port 8765] [--http-port 8766]
"""

import asyncio
import json
import logging
import socket
import time
import argparse
import webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.parse import urlparse, parse_qs

import websockets
try:
    from websockets.asyncio.server import serve as ws_serve  # websockets 14+
except ImportError:
    from websockets.server import serve as ws_serve  # websockets <14

from packets import (
    parse_packet,
    PacketMotionData, PacketSessionData, PacketLapData, PacketEventData,
    PacketParticipantsData, PacketCarSetupData, PacketCarTelemetryData,
    PacketCarStatusData, PacketFinalClassificationData, PacketCarDamageData,
    PacketSessionHistoryData, PacketTyreSetsData, PacketMotionExData,
)
from db import TelemetryDB, init_db, sessions_json, laps_json, frames_json

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("f1")

HERE = Path(__file__).parent

# ── shared live state ─────────────────────────────────────────────────────────
class LiveState:
    def __init__(self):
        self.session_uid: int = 0
        self.player_idx: int = 0

        # session
        self.track_name: str = "—"
        self.session_type: int = 0
        self.weather: str = "—"
        self.total_laps: int = 0
        self.track_length: int = 0
        self.session_time_left: int = 0
        self.safety_car: int = 0
        self.sector2_dist: float = 0
        self.sector3_dist: float = 0

        # participants
        self.driver_names: list = ["" for _ in range(24)]

        # telemetry
        self.speed: int = 0
        self.throttle: float = 0
        self.brake: float = 0
        self.steer: float = 0
        self.gear: int = 0
        self.rpm: int = 0
        self.drs: int = 0
        self.rev_lights_pct: int = 0
        self.engine_temp: int = 0
        self.brakes_temp: list = [0, 0, 0, 0]
        self.tyres_surface_temp: list = [0, 0, 0, 0]
        self.tyres_inner_temp: list = [0, 0, 0, 0]
        self.tyres_pressure: list = [0.0, 0.0, 0.0, 0.0]

        # car status
        self.fuel: float = 0
        self.fuel_remaining_laps: float = 0
        self.fuel_mix: int = 0
        self.ers_store_pct: float = 0
        self.ers_deploy_mode: int = 0
        self.tyre_compound: str = "—"
        self.tyre_age: int = 0
        self.drs_allowed: int = 0
        self.actual_compound: int = 0

        # damage
        self.tyre_wear: list = [0.0, 0.0, 0.0, 0.0]
        self.tyres_damage: list = [0, 0, 0, 0]
        self.brakes_damage: list = [0, 0, 0, 0]
        self.tyre_blisters: list = [0, 0, 0, 0]
        self.fl_wing: int = 0; self.fr_wing: int = 0; self.rear_wing: int = 0
        self.floor_dmg: int = 0; self.diffuser_dmg: int = 0
        self.gearbox_dmg: int = 0; self.engine_dmg: int = 0
        self.drs_fault: int = 0

        # lap data
        self.car_position: int = 0
        self.current_lap: int = 0
        self.lap_distance: float = 0
        self.total_distance: float = 0
        self.current_lap_ms: int = 0
        self.last_lap_ms: int = 0
        self.s1_ms: int = 0; self.s1_min: int = 0
        self.s2_ms: int = 0; self.s2_min: int = 0
        self.lap_invalid: int = 0
        self.pit_status: int = 0
        self.num_pit_stops: int = 0
        self.penalties_s: int = 0
        self.sector: int = 0
        # sector snapshots: saved at sector boundary, used at lap completion
        self.snap_s1_ms: int = 0
        self.snap_s2_ms: int = 0

        # position data for all cars (live leaderboard)
        self.all_positions: list = [0] * 24
        self.all_lap_distances: list = [0.0] * 24

        # world position (track map)
        self.world_x: float = 0
        self.world_y: float = 0
        self.world_z: float = 0
        self.all_world_x: list = [0.0] * 24
        self.all_world_z: list = [0.0] * 24

        # session history (player)
        self.best_lap_ms: int = 0
        self.best_lap_num: int = 0
        self.best_s1_ms: int = 0
        self.best_s2_ms: int = 0
        self.best_s3_ms: int = 0

        # events log (last 20)
        self.recent_events: list = []

        # motion ex
        self.suspension_pos: list = [0.0]*4
        self.wheel_slip_ratio: list = [0.0]*4
        self.g_lat: float = 0; self.g_long: float = 0; self.g_vert: float = 0

        # car setup
        self.car_setup: dict = {}

        self.last_packet_time: float = 0

    def to_dict(self) -> dict:
        return {
            "ts": time.time(),
            "session": {
                "uid": str(self.session_uid),
                "track": self.track_name,
                "weather": self.weather,
                "total_laps": self.total_laps,
                "time_left": self.session_time_left,
                "safety_car": self.safety_car,
                "sector2_dist": self.sector2_dist,
                "sector3_dist": self.sector3_dist,
            },
            "lap": {
                "num": self.current_lap,
                "distance": self.lap_distance,
                "current_ms": self.current_lap_ms,
                "last_ms": self.last_lap_ms,
                "best_ms": self.best_lap_ms,
                "best_lap_num": self.best_lap_num,
                "s1_ms": self.s1_ms + self.s1_min * 60000,
                "s2_ms": self.s2_ms + self.s2_min * 60000,
                "best_s1_ms": self.best_s1_ms,
                "best_s2_ms": self.best_s2_ms,
                "best_s3_ms": self.best_s3_ms,
                "invalid": self.lap_invalid,
                "position": self.car_position,
                "pit_status": self.pit_status,
                "pit_stops": self.num_pit_stops,
                "penalties": self.penalties_s,
                "sector": self.sector,
            },
            "car": {
                "speed": self.speed,
                "throttle": round(self.throttle, 3),
                "brake": round(self.brake, 3),
                "steer": round(self.steer, 3),
                "gear": self.gear,
                "rpm": self.rpm,
                "drs": self.drs,
                "drs_allowed": self.drs_allowed,
                "rev_pct": self.rev_lights_pct,
                "engine_temp": self.engine_temp,
                "brakes_temp": self.brakes_temp,
                "tyres_surface": self.tyres_surface_temp,
                "tyres_inner": self.tyres_inner_temp,
                "tyres_pressure": [round(p, 1) for p in self.tyres_pressure],
            },
            "status": {
                "fuel": round(self.fuel, 2),
                "fuel_laps": round(self.fuel_remaining_laps, 1),
                "fuel_mix": self.fuel_mix,
                "ers_pct": round(self.ers_store_pct, 1),
                "ers_mode": self.ers_deploy_mode,
                "tyre_compound": self.tyre_compound,
                "tyre_age": self.tyre_age,
            },
            "damage": {
                "tyre_wear": [round(w, 1) for w in self.tyre_wear],
                "tyres_damage": list(self.tyres_damage),
                "brakes_damage": list(self.brakes_damage),
                "tyre_blisters": list(self.tyre_blisters),
                "fl_wing": self.fl_wing, "fr_wing": self.fr_wing,
                "rear_wing": self.rear_wing, "floor": self.floor_dmg,
                "diffuser": self.diffuser_dmg, "gearbox": self.gearbox_dmg,
                "engine": self.engine_dmg, "drs_fault": self.drs_fault,
            },
            "position": {
                "x": self.world_x, "y": self.world_y, "z": self.world_z,
                "g_lat": round(self.g_lat, 2),
                "g_long": round(self.g_long, 2),
                "g_vert": round(self.g_vert, 2),
                "suspension": [round(s, 3) for s in self.suspension_pos],
                "slip": [round(s, 4) for s in self.wheel_slip_ratio],
            },
            "leaderboard": [
                {
                    "car_idx": i,
                    "position": self.all_positions[i],
                    "name": self.driver_names[i],
                    "lap_dist": round(self.all_lap_distances[i], 1),
                    "world_x": round(self.all_world_x[i], 1),
                    "world_z": round(self.all_world_z[i], 1),
                }
                for i in range(24)
                if self.all_positions[i] > 0
            ],
            "events": self.recent_events[-10:],
            "setup": self.car_setup,
        }


state = LiveState()
db: TelemetryDB = None
connected_ws: set = set()
frame_buffer_count = 0
FRAME_LOG_INTERVAL = 5  # log every 5th frame (~12fps at 60Hz)


# ── packet handlers ───────────────────────────────────────────────────────────
def handle_session(pkt: PacketSessionData):
    state.track_name = pkt.track_name
    state.weather = pkt.weather_name
    state.total_laps = pkt.total_laps
    state.track_length = pkt.track_length
    state.session_time_left = pkt.session_time_left
    state.safety_car = pkt.safety_car_status
    state.sector2_dist = pkt.sector2_dist
    state.sector3_dist = pkt.sector3_dist
    uid = pkt.header.session_uid
    stype = pkt.session_type
    # Use a synthetic UID that encodes both the game UID and session type so
    # that a session-type change within the same game UID creates a new DB row
    # rather than overwriting the previous session's data.
    synthetic_uid = (uid ^ (stype << 48)) if uid else 0
    new_session = synthetic_uid and synthetic_uid != state.session_uid
    if new_session:
        state.session_uid = synthetic_uid
        state.session_type = stype
        # Reset per-session live state so the dashboard doesn't serve the previous
        # session's best lap / delta reference / events into the new one (online
        # lobbies especially — the game sends a fresh session before any new lap).
        state.best_lap_ms = 0
        state.best_lap_num = 0
        state.best_s1_ms = 0
        state.best_s2_ms = 0
        state.best_s3_ms = 0
        state.recent_events = []
        log.info(f"New session: {pkt.track_name} type={stype} (uid={uid} synthetic={synthetic_uid})")
        if db:
            db.upsert_session(synthetic_uid, pkt.track_name, stype,
                              pkt.weather_name, pkt.total_laps, pkt.track_length)
    elif synthetic_uid and db:
        state.session_type = stype
        if not state.track_name or state.track_name == "—":
            log.info(f"Session data: track={pkt.track_name} type={stype} uid={uid}")
        db.upsert_session(synthetic_uid, pkt.track_name, stype,
                          pkt.weather_name, pkt.total_laps, pkt.track_length)


def handle_lap_data(pkt: PacketLapData):
    idx = pkt.header.player_car_idx
    state.player_idx = idx
    for i, ld in enumerate(pkt.lap_data):
        state.all_positions[i] = ld.car_position
        state.all_lap_distances[i] = ld.lap_distance
    if idx < 24:
        ld = pkt.lap_data[idx]
        prev_lap = state.current_lap
        state.current_lap = ld.current_lap
        state.lap_distance = ld.lap_distance
        state.current_lap_ms = ld.current_lap_ms
        state.last_lap_ms = ld.last_lap_ms
        state.s1_ms = ld.s1_ms
        state.s1_min = ld.s1_min
        state.s2_ms = ld.s2_ms
        state.s2_min = ld.s2_min
        state.lap_invalid = ld.lap_invalid
        state.car_position = ld.car_position
        state.pit_status = ld.pit_status
        state.num_pit_stops = ld.num_pit_stops
        state.penalties_s = ld.penalties

        prev_sector = state.sector
        state.sector = ld.sector
        # Level-triggered snapshots: update every frame while in the correct
        # sector and the value is non-zero. Edge-triggering was unreliable
        # because the game's s1/s2_ms fields can be 0 on the exact transition
        # frame and only populate one frame later.
        if ld.sector >= 1 and ld.s1_ms > 0:
            state.snap_s1_ms = ld.s1_ms + ld.s1_min * 60000
        if ld.sector >= 2 and ld.s2_ms > 0:
            state.snap_s2_ms = ld.s2_ms + ld.s2_min * 60000

        # detect lap completion
        if ld.current_lap > prev_lap and prev_lap > 0:
            log.info(f"LAP CROSSED: lap {prev_lap}→{ld.current_lap}  last_lap_ms={ld.last_lap_ms}  session_uid={state.session_uid}")
        if db and state.session_uid and ld.last_lap_ms > 0 and ld.current_lap > prev_lap and prev_lap > 0:
            s1 = state.snap_s1_ms
            s2 = state.snap_s2_ms
            s3 = max(0, ld.last_lap_ms - s1 - s2)
            db.upsert_lap(
                state.session_uid, idx, prev_lap,
                ld.last_lap_ms, s1, s2, s3,
                state.tyre_compound, state.tyre_age,
                state.fuel, 0,
                position=ld.car_position,
            )
            log.info(f"LAP SAVED: lap {prev_lap}  time={ld.last_lap_ms}ms  s1={s1}  s2={s2}  s3={s3}")
            db.commit()  # flush frames immediately so delta ref is available
            state.snap_s1_ms = 0
            state.snap_s2_ms = 0


def handle_telemetry(pkt: PacketCarTelemetryData):
    global frame_buffer_count
    idx = pkt.header.player_car_idx
    if idx >= 24:
        return
    ct = pkt.cars[idx]
    state.speed = ct.speed
    state.throttle = ct.throttle
    state.brake = ct.brake
    state.steer = ct.steer
    state.gear = ct.gear
    state.rpm = ct.engine_rpm
    if ct.drs != state.drs:
        log.info(f"ACTIVE_AERO field changed: {state.drs}→{ct.drs}  speed={ct.speed}kph")
    state.drs = ct.drs

    # DRS/active-aero byte-hunt: log raw car bytes at high speed.
    # Current struct reads byte offset 18 as drs. If drs is always 0 on a track
    # with a long DRS zone (Montreal etc), a field was added before it in the
    # 2026 spec. Check the log: byte 18 should flip to non-zero on the straight.
    # If it's 0 while another byte changes, that's the real active-aero offset.
    if ct.speed > 280 and pkt.raw_car_bytes:
        raw = pkt.raw_car_bytes[idx]
        indexed = " ".join(f"[{i:02d}]{b:02x}" for i, b in enumerate(raw))
        log.info(f"AERO_HUNT spd={ct.speed} b18(drs)={raw[18]:02x} | {indexed}")
    state.rev_lights_pct = ct.rev_lights_pct
    state.engine_temp = ct.engine_temp
    state.brakes_temp = list(ct.brakes_temp)
    state.tyres_surface_temp = list(ct.tyres_surface_temp)
    state.tyres_inner_temp = list(ct.tyres_inner_temp)
    state.tyres_pressure = list(ct.tyres_pressure)

    frame_buffer_count += 1
    if frame_buffer_count % (FRAME_LOG_INTERVAL * 12) == 0:
        log.info(f"FRAME_DEBUG: db={db is not None} uid={state.session_uid} lap={state.current_lap} dist={state.lap_distance:.0f} count={frame_buffer_count}")
    if db and state.session_uid and frame_buffer_count % FRAME_LOG_INTERVAL == 0:
        db.insert_frame(
            session_uid=state.session_uid,
            frame_id=pkt.header.frame_id,
            session_time=pkt.header.session_time,
            lap_num=state.current_lap,
            lap_distance=state.lap_distance,
            speed=ct.speed,
            throttle=ct.throttle,
            brake=ct.brake,
            steer=state.steer,
            gear=ct.gear,
            rpm=ct.engine_rpm,
            drs=ct.drs,
            tyre_surf=ct.tyres_surface_temp,
            tyre_inner=ct.tyres_inner_temp,
            brake_temp=ct.brakes_temp,
            fuel=state.fuel,
            ers_pct=state.ers_store_pct,
            ers_mode=state.ers_deploy_mode,
            tyre_wear=state.tyre_wear,
            pos=(state.world_x, state.world_y, state.world_z),
            lap_time_ms=state.current_lap_ms,
            wheel_slip=state.wheel_slip_ratio,
            tyre_blisters=state.tyre_blisters,
        )
        if frame_buffer_count % (FRAME_LOG_INTERVAL * 6) == 0:  # commit every ~3 seconds
            db.commit()


def handle_car_status(pkt: PacketCarStatusData):
    idx = pkt.header.player_car_idx
    if idx >= 24:
        return
    cs = pkt.cars[idx]
    state.fuel = cs.fuel_in_tank
    state.fuel_remaining_laps = cs.fuel_remaining_laps
    state.fuel_mix = cs.fuel_mix
    state.ers_store_pct = cs.ers_pct
    state.ers_deploy_mode = cs.ers_deploy_mode
    state.tyre_compound = cs.tyre_name
    state.tyre_age = cs.tyres_age_laps
    state.drs_allowed = cs.drs_allowed
    state.actual_compound = cs.actual_tyre_compound


def handle_damage(pkt: PacketCarDamageData):
    idx = pkt.header.player_car_idx
    if idx >= 24:
        return
    cd = pkt.cars[idx]
    state.tyre_wear = list(cd.tyres_wear)
    state.tyres_damage = list(cd.tyres_damage)
    state.brakes_damage = list(cd.brakes_damage)
    state.tyre_blisters = list(cd.tyre_blisters)
    state.fl_wing = cd.fl_wing_dmg
    state.fr_wing = cd.fr_wing_dmg
    state.rear_wing = cd.rear_wing_dmg
    state.floor_dmg = cd.floor_dmg
    state.diffuser_dmg = cd.diffuser_dmg
    state.gearbox_dmg = cd.gearbox_dmg
    state.engine_dmg = cd.engine_dmg
    state.drs_fault = cd.drs_fault


def handle_motion(pkt: PacketMotionData):
    idx = pkt.header.player_car_idx
    if idx >= 24:
        return
    state.world_x = pkt.cars[idx].x
    state.world_y = pkt.cars[idx].y
    state.world_z = pkt.cars[idx].z
    # g-force values are quantised int16 in the 2026 spec; divide by 1000 for actual g
    state.g_lat = pkt.cars[idx].g_lat / 1000.0
    state.g_long = pkt.cars[idx].g_long / 1000.0
    state.g_vert = pkt.cars[idx].g_vert / 1000.0
    for i, car in enumerate(pkt.cars):
        state.all_world_x[i] = car.x
        state.all_world_z[i] = car.z


def handle_participants(pkt: PacketParticipantsData):
    for i, p in enumerate(pkt.participants[:pkt.num_active_cars]):
        state.driver_names[i] = p.name
        if db and state.session_uid:
            db.upsert_participant(
                state.session_uid, i, p.name, p.team_id, p.race_number, p.ai_controlled
            )


def handle_session_history(pkt: PacketSessionHistoryData):
    if pkt.car_idx != state.player_idx:
        return
    # best_lap_num is the 1-indexed lap NUMBER the best lap was set on;
    # lap_history is 0-indexed by array position (index 0 = lap 1's data).
    # Using best_lap_num directly as the index was off by one.
    if pkt.num_laps > 0 and 0 < pkt.best_lap_num <= len(pkt.lap_history):
        bl = pkt.lap_history[pkt.best_lap_num - 1]
        if bl:
            state.best_lap_num = pkt.best_lap_num
            state.best_lap_ms = bl.lap_time_ms
            state.best_s1_ms = bl.s1_ms + bl.s1_min * 60000
            state.best_s2_ms = bl.s2_ms + bl.s2_min * 60000
            state.best_s3_ms = bl.s3_ms + bl.s3_min * 60000


def handle_car_setup(pkt: PacketCarSetupData):
    idx = pkt.header.player_car_idx
    if idx >= 24:
        return
    su = pkt.setups[idx]
    state.car_setup = {
        "front_wing":        su.front_wing,
        "rear_wing":         su.rear_wing,
        "on_throttle":       su.on_throttle,
        "off_throttle":      su.off_throttle,
        "front_camber":      round(su.front_camber, 2),
        "rear_camber":       round(su.rear_camber, 2),
        "front_toe":         round(su.front_toe, 2),
        "rear_toe":          round(su.rear_toe, 2),
        "front_susp":        su.front_susp,
        "rear_susp":         su.rear_susp,
        "front_arb":         su.front_arb,
        "rear_arb":          su.rear_arb,
        "front_susp_height": su.front_susp_height,
        "rear_susp_height":  su.rear_susp_height,
        "brake_pressure":    su.brake_pressure,
        "brake_bias":        su.brake_bias,
        "engine_braking":    su.engine_braking,
        "fl_tyre_psi":       round(su.fl_tyre_psi, 1),
        "fr_tyre_psi":       round(su.fr_tyre_psi, 1),
        "rl_tyre_psi":       round(su.rl_tyre_psi, 1),
        "rr_tyre_psi":       round(su.rr_tyre_psi, 1),
        "ballast":           su.ballast,
        "fuel_load":         round(su.fuel_load, 1),
    }
    if db and state.session_uid:
        db.upsert_setup(state.session_uid, state.car_setup)


def handle_motion_ex(pkt: PacketMotionExData):
    state.suspension_pos = list(pkt.suspension_position)
    state.wheel_slip_ratio = list(pkt.wheel_slip_ratio)


def handle_event(pkt: PacketEventData):
    ev = {
        "code": pkt.event_code.decode("ascii", errors="replace"),
        "name": pkt.event_name,
        "time": pkt.header.session_time,
        "details": pkt.details,
    }
    state.recent_events.append(ev)
    if len(state.recent_events) > 50:
        state.recent_events.pop(0)
    log.info(f"EVENT: {pkt.event_name} {pkt.details}")
    if db and state.session_uid:
        db.insert_event(state.session_uid, pkt.header.session_time,
                        ev["code"], pkt.event_name, pkt.details)


def handle_final_classification(pkt: PacketFinalClassificationData):
    if db and state.session_uid:
        for i, clf in enumerate(pkt.classifications[:pkt.num_cars]):
            db.insert_final_classification(
                state.session_uid, i, clf.position, clf.num_laps,
                clf.best_lap_ms, clf.total_race_time, clf.penalties_time,
                [{"actual": a, "visual": v, "end_lap": e}
                 for a, v, e in zip(clf.tyre_stints_actual,
                                    clf.tyre_stints_visual,
                                    clf.tyre_stints_end_laps)],
            )


HANDLERS = {
    0:  handle_motion,
    1:  handle_session,
    2:  handle_lap_data,
    3:  handle_event,
    4:  handle_participants,
    5:  handle_car_setup,
    6:  handle_telemetry,
    7:  handle_car_status,
    8:  handle_final_classification,
    10: handle_damage,
    11: handle_session_history,
    13: handle_motion_ex,
}


# ── UDP listener ──────────────────────────────────────────────────────────────
class UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, broadcast_q: asyncio.Queue):
        self.q = broadcast_q
        self._packets_received = 0

    def datagram_received(self, data: bytes, addr):
        if self._packets_received == 0:
            log.info(f"*** FIRST PACKET RECEIVED from {addr}, size={len(data)} bytes ***")
        self._packets_received += 1
        if self._packets_received % 60 == 0:
            log.info(f"Packets received: {self._packets_received} (last from {addr})")
        pkt = parse_packet(data)
        if pkt is None:
            if self._packets_received <= 5:
                log.warning(f"Packet #{self._packets_received} from {addr} could not be parsed (size={len(data)}, first bytes={data[:4].hex()})")
            return
        state.last_packet_time = time.time()
        # Always capture session_uid from the header — so if the session packet
        # body fails to parse, we still know the uid and can save laps/frames.
        # Use the same synthetic UID scheme as handle_session (uid ^ stype<<48).
        uid = pkt.header.session_uid
        synthetic_uid = (uid ^ (state.session_type << 48)) if uid else 0
        if synthetic_uid and synthetic_uid != state.session_uid:
            state.session_uid = synthetic_uid
            # same per-session reset as handle_session (see note there)
            state.best_lap_ms = 0
            state.best_lap_num = 0
            state.best_s1_ms = 0
            state.best_s2_ms = 0
            state.best_s3_ms = 0
            state.recent_events = []
            log.info(f"Session UID updated from header: {uid} (synthetic={synthetic_uid})")
            if db:
                db.upsert_session(synthetic_uid, state.track_name or "Unknown",
                                  state.session_type,
                                  state.weather or "", state.total_laps, state.track_length)
        handler = HANDLERS.get(pkt.header.packet_id)
        if handler:
            handler(pkt)
        # queue broadcast (non-blocking, drop if slow consumer)
        try:
            self.q.put_nowait(None)  # signal: state updated
        except asyncio.QueueFull:
            pass

    def error_received(self, exc):
        log.warning(f"UDP error: {exc}")


# ── WebSocket server ──────────────────────────────────────────────────────────
async def ws_handler(ws):
    connected_ws.add(ws)
    log.info(f"Dashboard connected ({len(connected_ws)} total)")
    try:
        # Send current state immediately on connect
        await ws.send(json.dumps(state.to_dict()))
        async for _ in ws:
            pass  # ignore incoming messages
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_ws.discard(ws)
        log.info(f"Dashboard disconnected ({len(connected_ws)} remaining)")


async def broadcast_loop(q: asyncio.Queue):
    """Coalesce rapid updates: broadcast at most ~30fps regardless of packet rate."""
    while True:
        await q.get()
        # drain any queued-up signals
        while not q.empty():
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                break
        if connected_ws:
            msg = json.dumps(state.to_dict())
            dead = set()
            for ws in connected_ws.copy():
                try:
                    await ws.send(msg)
                except Exception:
                    dead.add(ws)
            connected_ws.difference_update(dead)
        await asyncio.sleep(1/30)  # cap at 30fps


# ── HTTP API for history viewer ───────────────────────────────────────────────
class HistoryAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        path = parsed.path

        def send_json(data):
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_file(filepath: Path):
            if not filepath.exists():
                self.send_error(404)
                return
            body = filepath.read_bytes()
            ct = "text/html" if filepath.suffix == ".html" else "text/plain"
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        try:
            if path == "/api/sessions":
                send_json(sessions_json(db))
            elif path == "/api/laps":
                uid = int(qs.get("session_uid", [0])[0])
                send_json(laps_json(db, uid))
            elif path == "/api/frames":
                uid = int(qs.get("session_uid", [0])[0])
                lap = int(qs.get("lap_num", [1])[0])
                send_json(frames_json(db, uid, lap))
            elif path == "/api/export":
                uid = int(qs.get("session_uid", [state.session_uid])[0])
                csv_data = db.export_session_full(uid)
                body = csv_data.encode("utf-8")
                from datetime import datetime
                fname = f"f1_session_{uid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            elif path == "/api/ai_export":
                uid = int(qs.get("session_uid", [state.session_uid])[0])
                md_data = db.export_ai_summary(uid)
                body = md_data.encode("utf-8")
                from datetime import datetime
                fname = f"f1_ai_summary_{uid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown")
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            elif path == "/api/export_multi":
                uids = [int(u) for u in qs.get("session_uid", [])]
                if not uids:
                    uids = [state.session_uid]
                parts = []
                for i, uid in enumerate(uids, 1):
                    parts.append(db.export_ai_summary(uid, prefix=f"[{i}/{len(uids)}] "))
                md_data = "\n\n---\n\n".join(parts)
                body = md_data.encode("utf-8")
                from datetime import datetime
                fname = f"f1_ai_merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown")
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            elif path == "/api/live":
                send_json(state.to_dict())
            elif path == "/" or path == "/dashboard":
                send_file(HERE / "dashboard.html")
            elif path == "/compare":
                send_file(HERE / "compare.html")
            elif path == "/sessions":
                send_file(HERE / "sessions.html")
            elif path.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
                img_path = HERE / path.lstrip("/")
                if img_path.exists():
                    ext = img_path.suffix.lower()
                    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                            "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml"}.get(ext[1:], "application/octet-stream")
                    body = img_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(404)
            else:
                self.send_error(404)
        except Exception as e:
            log.error(f"HTTP handler error: {e}")
            self.send_error(500)

    def log_message(self, *args):
        pass  # suppress default HTTP logging


def start_http_server(port: int):
    server = HTTPServer(("0.0.0.0", port), HistoryAPIHandler)
    t = Thread(target=server.serve_forever, daemon=True)
    t.start()
    log.info(f"HTTP API + file server on http://localhost:{port}/")
    log.info(f"  Dashboard:  http://localhost:{port}/dashboard")
    log.info(f"  Compare:    http://localhost:{port}/compare")
    return server


# ── main ──────────────────────────────────────────────────────────────────────
async def main(udp_port: int, ws_port: int, http_port: int, no_browser: bool):
    global db
    init_db()
    db = TelemetryDB()

    q: asyncio.Queue = asyncio.Queue(maxsize=500)

    loop = asyncio.get_event_loop()

    # UDP socket — bind on all interfaces so console players can send packets
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.bind(("0.0.0.0", udp_port))
    transport, _ = await loop.create_datagram_endpoint(
        lambda: UDPProtocol(q),
        sock=udp_sock,
    )

    # WebSocket server
    ws_server = await ws_serve(ws_handler, "0.0.0.0", ws_port)

    # HTTP server (blocking, in thread)
    start_http_server(http_port)

    log.info("=" * 60)
    log.info(f"F1 25 Telemetry Listener started")
    log.info(f"  UDP listener:  port {udp_port}")
    log.info(f"  WebSocket:     ws://localhost:{ws_port}")
    log.info(f"  Dashboard:     http://localhost:{http_port}/dashboard")
    log.info(f"  Compare laps:  http://localhost:{http_port}/compare")
    log.info("=" * 60)
    log.info("Waiting for packets from F1 25...")

    if not no_browser:
        import threading
        def open_browser():
            import time as _t
            _t.sleep(1.5)
            webbrowser.open(f"http://localhost:{http_port}/dashboard")
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        await broadcast_loop(q)
    finally:
        transport.close()
        ws_server.close()
        if db:
            db.commit()
            db.conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="F1 25 Telemetry Listener")
    parser.add_argument("--udp-port", type=int, default=20777)
    parser.add_argument("--ws-port",  type=int, default=8765)
    parser.add_argument("--http-port",type=int, default=8766)
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't auto-open the browser")
    args = parser.parse_args()

    try:
        asyncio.run(main(args.udp_port, args.ws_port, args.http_port, args.no_browser))
    except KeyboardInterrupt:
        log.info("Stopped by user.")
