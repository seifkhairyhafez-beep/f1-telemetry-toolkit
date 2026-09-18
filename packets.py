"""
F1 25 UDP packet parser — built directly from the official EA spec v6.0
Little-endian, no padding, packetFormat == 2025
"""

import struct
from dataclasses import dataclass, field
from typing import Optional, List

# ── constants ────────────────────────────────────────────────────────────────
MAX_CARS      = 24   # 2026 Season Pack: 12 teams x 2 cars (was 22 pre-2026)
MAX_TYRE_SETS = 20   # 13 slick + 7 wet
MAX_STINTS    = 8
MAX_LAPS_HIST = 100
HEADER_FMT    = "<HBBBBBQfIIBB"  # 29 bytes
HEADER_SIZE   = struct.calcsize(HEADER_FMT)  # must be 29

# tyre order: RL=0, RR=1, FL=2, FR=3
TYRE_NAMES    = ["RL", "RR", "FL", "FR"]

COMPOUND_MAP = {
    16: "C5", 17: "C4", 18: "C3", 19: "C2", 20: "C1", 21: "C0", 22: "C6",
    7: "Inter", 8: "Wet",
    9: "Dry(Classic)", 10: "Wet(Classic)",
    11: "SuperSoft(F2)", 12: "Soft(F2)", 13: "Medium(F2)", 14: "Hard(F2)", 15: "Wet(F2)",
}
VISUAL_COMPOUND_MAP = {
    16: "Soft", 17: "Medium", 18: "Hard", 7: "Inter", 8: "Wet",
}
WEATHER_MAP  = {0:"Clear",1:"Light Cloud",2:"Overcast",3:"Light Rain",4:"Heavy Rain",5:"Storm"}
TRACK_MAP = {
    0:"Melbourne",1:"Paul Ricard",2:"Shanghai",3:"Sakhir",4:"Catalunya",5:"Monaco",
    6:"Montreal",7:"Silverstone",8:"Hockenheim",9:"Hungaroring",10:"Spa",
    11:"Monza",12:"Singapore",13:"Suzuka",14:"Abu Dhabi",15:"Texas",
    16:"Brazil",17:"Austria",18:"Sochi",19:"Mexico",20:"Baku",21:"Sakhir Short",
    22:"Silverstone Short",23:"Texas Short",24:"Suzuka Short",25:"Hanoi",
    26:"Zandvoort",27:"Imola",28:"Portimão",29:"Jeddah",30:"Miami",
    31:"Las Vegas",32:"Losail",33:"China Sprint",34:"Bahrain",35:"Saudi Arabia",
    36:"Australia",37:"Japan",38:"Bahrain Sprint",39:"China",40:"Miami Sprint",
    41:"Emilia Romagna",42:"Madrid",43:"Monaco (2026)",44:"Canada",
}

# ── header ───────────────────────────────────────────────────────────────────
@dataclass
class PacketHeader:
    packet_format: int
    game_year: int
    game_major: int
    game_minor: int
    packet_version: int
    packet_id: int
    session_uid: int
    session_time: float
    frame_id: int
    overall_frame_id: int
    player_car_idx: int
    secondary_player_idx: int

    @classmethod
    def unpack(cls, data: bytes) -> "PacketHeader":
        t = struct.unpack_from(HEADER_FMT, data, 0)
        return cls(*t)


# ── motion (packet 0) ────────────────────────────────────────────────────────
# 2026 spec CarMotionData (54 bytes per car):
#   3 floats pos, 3 floats vel,
#   3 int16 fwd dir, 3 int16 right dir, 3 int16 g-force (lat/long/vert, quantised /1000),
#   3 floats yaw/pitch/roll
# NOTE: g-force moved from "3 trailing floats" (old spec) to "3 quantised int16"
# in the middle of the struct. Old code assumed 6f+6h+6f (60 bytes) which is WRONG
# for the 2026 format — it under-counts the int16 group by 3, corrupting the
# per-car stride (and therefore world position / track map) for every car
# except car index 0.
_CAR_MOTION = struct.Struct("<" + "f"*6 + "h"*9 + "f"*3)  # 24 + 18 + 12 = 54 bytes ✓

@dataclass
class CarMotionData:
    x: float; y: float; z: float
    vx: float; vy: float; vz: float
    fwd_x: int; fwd_y: int; fwd_z: int
    right_x: int; right_y: int; right_z: int
    g_lat: int; g_long: int; g_vert: int   # quantised, divide by 1000 for actual g
    yaw: float; pitch: float; roll: float

@dataclass
class PacketMotionData:
    header: PacketHeader
    cars: List[CarMotionData]

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketMotionData":
        cars = []
        offset = HEADER_SIZE
        for _ in range(MAX_CARS):
            t = _CAR_MOTION.unpack_from(data, offset)
            cars.append(CarMotionData(*t))
            offset += _CAR_MOTION.size
        return cls(header, cars)


# ── session (packet 1) ───────────────────────────────────────────────────────
_MARSHAL_ZONE = struct.Struct("<fb")   # 5 bytes
# WeatherForecastSample has 8 fields: sessionType, timeOffset, weather,
# trackTemp, trackTempChange, airTemp, airTempChange, rainPercentage.
# Old code was missing the "weather" byte (only had 7 fields / 7 bytes),
# which misaligned the 64-sample array by 64 bytes and corrupted every
# session field read after it.
_WEATHER_SAMPLE = struct.Struct("<BBBbbbbB")  # 8 bytes

@dataclass
class PacketSessionData:
    header: PacketHeader
    weather: int
    track_temp: int
    air_temp: int
    total_laps: int
    track_length: int
    session_type: int
    track_id: int
    formula: int
    session_time_left: int
    session_duration: int
    pit_speed_limit: int
    game_paused: int
    is_spectating: int
    spectator_car_index: int
    safety_car_status: int
    num_weather_samples: int
    forecast_accuracy: int
    ai_difficulty: int
    pit_stop_window_ideal: int
    pit_stop_window_latest: int
    num_safety_car_periods: int
    num_vsc_periods: int
    num_red_flag_periods: int
    sector2_dist: float
    sector3_dist: float

    @property
    def track_name(self) -> str:
        return TRACK_MAP.get(self.track_id, f"Track#{self.track_id}")

    @property
    def weather_name(self) -> str:
        return WEATHER_MAP.get(self.weather, "Unknown")

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketSessionData":
        # Rewritten against the official 2026 Season Pack spec with exact
        # forward offsets (no more guessing / reading from end-of-packet —
        # the 2026 format added a bunch of new fields AFTER sector2/3 dist,
        # so "last 8 bytes = sector floats" is no longer true).
        off = HEADER_SIZE

        # weather, track_temp, air_temp, total_laps, track_length, session_type,
        # track_id, formula, session_time_left, session_duration, pit_speed_limit,
        # game_paused, is_spectating, spectator_car_index, sli_pro, num_marshal_zones
        base_fmt = struct.Struct("<BbbBHBbBHHBBBBBB")  # 16 fields, 19 bytes
        b = base_fmt.unpack_from(data, off)
        off += base_fmt.size

        off += 21 * _MARSHAL_ZONE.size  # MarshalZone[21], 105 bytes

        # safety_car_status, network_game, num_weather_forecast_samples
        safety_car_status, network_game, num_weather = struct.unpack_from("<BBB", data, off)
        off += 3

        off += 64 * _WEATHER_SAMPLE.size  # WeatherForecastSample[64], 512 bytes

        # forecast_accuracy, ai_difficulty
        forecast_accuracy, ai_difficulty = struct.unpack_from("<BB", data, off)
        off += 2

        # seasonLink(I), weekendLink(I), sessionLink(I),
        # pitStopWindowIdealLap(B), pitStopWindowLatestLap(B), pitStopRejoinPosition(B)
        link = struct.unpack_from("<IIIBBB", data, off)
        off += struct.calcsize("<IIIBBB")
        pit_stop_window_ideal = link[3]
        pit_stop_window_latest = link[4]

        # 11 single-byte assist/mode fields: steeringAssist..ruleSet
        off += 11

        # timeOfDay (I), sessionLength (B)
        off += struct.calcsize("<IB")

        # 4 unit fields: speedUnitsLead, tempUnitsLead, speedUnitsSec, tempUnitsSec
        off += 4

        # numSafetyCarPeriods, numVirtualSafetyCarPeriods, numRedFlagPeriods
        sc_periods = struct.unpack_from("<BBB", data, off)
        off += 3

        # 25 single-byte settings: equalCarPerformance .. numSessionsInWeekend
        off += 25

        # weekendStructure[12] (fixed-size array regardless of numSessionsInWeekend)
        off += 12

        # sector2LapDistanceStart, sector3LapDistanceStart
        try:
            s2, s3 = struct.unpack_from("<ff", data, off)
        except Exception:
            s2, s3 = 0.0, 0.0

        return cls(
            header=header,
            weather=b[0],
            track_temp=b[1],
            air_temp=b[2],
            total_laps=b[3],
            track_length=b[4],
            session_type=b[5],
            track_id=b[6],
            formula=b[7],
            session_time_left=b[8],
            session_duration=b[9],
            pit_speed_limit=b[10],
            game_paused=b[11],
            is_spectating=b[12],
            spectator_car_index=b[13],
            safety_car_status=safety_car_status,
            num_weather_samples=num_weather,
            forecast_accuracy=forecast_accuracy,
            ai_difficulty=ai_difficulty,
            pit_stop_window_ideal=pit_stop_window_ideal,
            pit_stop_window_latest=pit_stop_window_latest,
            num_safety_car_periods=sc_periods[0],
            num_vsc_periods=sc_periods[1],
            num_red_flag_periods=sc_periods[2],
            sector2_dist=s2,
            sector3_dist=s3,
        )


# ── lap data (packet 2) ──────────────────────────────────────────────────────
# LapData per car: see spec
_LAP_DATA_FMT = struct.Struct("<II HB HB HB HB ff f BBBBBBBBBBBB BB HHB fB")
# Let me spell this out:
# uint32 lastLapTimeInMS, uint32 currentLapTimeInMS
# uint16 sector1TimeMSPart, uint8 sector1TimeMinutesPart
# uint16 sector2TimeMSPart, uint8 sector2TimeMinutesPart
# uint16 deltaToCarInFrontMSPart, uint8 deltaToCarInFrontMinutesPart
# uint16 deltaToRaceLeaderMSPart, uint8 deltaToRaceLeaderMinutesPart
# float lapDistance, float totalDistance
# float safetyCarDelta
# uint8 carPosition, uint8 currentLapNum, uint8 pitStatus, uint8 numPitStops
# uint8 sector, uint8 currentLapInvalid, uint8 penalties, uint8 totalWarnings
# uint8 cornerCuttingWarnings, uint8 numUnservedDT, uint8 numUnservedSG, uint8 gridPosition
# uint8 driverStatus, uint8 resultStatus
# uint8 pitLaneTimerActive, uint16 pitLaneTimeInLaneInMS
# uint16 pitStopTimerInMS, uint8 pitStopShouldServePen
# float speedTrapFastestSpeed, uint8 speedTrapFastestLap

_LD = struct.Struct("<II HB HB HB HB ff f BBBBBBBBBBBB BB B HH B fB")
# sizes: 4+4 + (2+1)+(2+1)+(2+1)+(2+1) + 4+4 + 4 + 12B + 2B + 1B+2+2+1B + 4+1
# = 8 + 12 + 12 + 4 + 12 + 2 + 6 + 5 = 61 bytes per car

@dataclass
class LapData:
    last_lap_ms: int
    current_lap_ms: int
    s1_ms: int; s1_min: int
    s2_ms: int; s2_min: int
    delta_front_ms: int; delta_front_min: int
    delta_leader_ms: int; delta_leader_min: int
    lap_distance: float
    total_distance: float
    safety_car_delta: float
    car_position: int
    current_lap: int
    pit_status: int
    num_pit_stops: int
    sector: int
    lap_invalid: int
    penalties: int
    total_warnings: int
    corner_cutting_warnings: int
    unserved_dt: int
    unserved_sg: int
    grid_position: int
    driver_status: int
    result_status: int
    pit_lane_timer_active: int
    pit_lane_time_ms: int
    pit_stop_timer_ms: int
    pit_stop_serve_pen: int
    speed_trap_speed: float
    speed_trap_lap: int

    @property
    def current_lap_time_str(self) -> str:
        ms = self.current_lap_ms
        mins = ms // 60000
        secs = (ms % 60000) / 1000.0
        return f"{mins}:{secs:06.3f}"

    @property
    def last_lap_time_str(self) -> str:
        ms = self.last_lap_ms
        if ms == 0:
            return "--:--.---"
        mins = ms // 60000
        secs = (ms % 60000) / 1000.0
        return f"{mins}:{secs:06.3f}"


@dataclass
class PacketLapData:
    header: PacketHeader
    lap_data: List[LapData]
    time_trial_pb_idx: int
    time_trial_rival_idx: int

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketLapData":
        off = HEADER_SIZE
        laps = []
        for _ in range(MAX_CARS):
            t = _LD.unpack_from(data, off)
            laps.append(LapData(*t))
            off += _LD.size
        pb, rival = struct.unpack_from("<BB", data, off)
        return cls(header, laps, pb, rival)


# ── car telemetry (packet 6) ─────────────────────────────────────────────────
# 2026 spec: engine_temp is uint8 (was uint16 in old spec). Per car: 59 bytes.
# H fff Bb H BB H  4H 4B 4B B 4f 4B = 59 bytes
_CT = struct.Struct("<HfffBbHBBH4H4B4BB4f4B")
# H=speed, f=throttle, f=steer, f=brake, B=clutch, b=gear, H=rpm,
# B=drs, B=rev_pct, H=rev_bits, 4H=brake_temps, 4B=surf_temps,
# 4B=inner_temps, B=eng_temp, 4f=tyre_pressure, 4B=surface_type
# = 2+4+4+4+1+1+2+1+1+2+8+4+4+1+16+4 = 59 bytes
# (old code had eng_temp as H/uint16, which shifted every field after it by
# 1 byte per car — for any car after index 0 this scrambled speed/rpm/tyre
# temps once the cumulative offset drifted past field boundaries)

@dataclass
class CarTelemetryData:
    speed: int          # km/h
    throttle: float     # 0-1
    steer: float        # -1 to 1
    brake: float        # 0-1
    clutch: int         # 0-100
    gear: int           # -1=R, 0=N, 1-8
    engine_rpm: int
    drs: int            # 0/1
    rev_lights_pct: int
    rev_lights_bits: int
    brakes_temp: tuple  # RL RR FL FR celsius
    tyres_surface_temp: tuple  # RL RR FL FR celsius
    tyres_inner_temp: tuple    # RL RR FL FR celsius
    engine_temp: int
    tyres_pressure: tuple  # PSI
    surface_type: tuple


@dataclass
class PacketCarTelemetryData:
    header: PacketHeader
    cars: List[CarTelemetryData]
    mfd_panel: int
    mfd_panel_secondary: int
    suggested_gear: int
    raw_car_bytes: List[bytes] = field(default_factory=list)  # raw bytes per car for debugging

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketCarTelemetryData":
        off = HEADER_SIZE
        cars = []
        raw_car_bytes = []
        for _ in range(MAX_CARS):
            raw_car_bytes.append(data[off:off + _CT.size])
            t = _CT.unpack_from(data, off)
            off += _CT.size
            cars.append(CarTelemetryData(
                speed=t[0], throttle=t[1], steer=t[2], brake=t[3],
                clutch=t[4], gear=t[5], engine_rpm=t[6],
                drs=t[7], rev_lights_pct=t[8], rev_lights_bits=t[9],
                brakes_temp=t[10:14],
                tyres_surface_temp=t[14:18],
                tyres_inner_temp=t[18:22],
                engine_temp=t[22],
                tyres_pressure=t[23:27],
                surface_type=t[27:31],
            ))
        mfd, mfd2, sg = struct.unpack_from("<BBb", data, off)
        return cls(header, cars, mfd, mfd2, sg, raw_car_bytes)


# ── car status (packet 7) ────────────────────────────────────────────────────
# 2026 spec added m_ersHarvestLimitPerLap (float) — per car: 59 bytes (was 55).
_CS = struct.Struct("<BBBBBfffHHBBHBBBbfffBffffB")

@dataclass
class CarStatusData:
    traction_control: int
    abs: int
    fuel_mix: int
    front_brake_bias: int
    pit_limiter: int
    fuel_in_tank: float
    fuel_capacity: float
    fuel_remaining_laps: float
    max_rpm: int
    idle_rpm: int
    max_gears: int
    drs_allowed: int
    drs_activation_dist: int
    actual_tyre_compound: int
    visual_tyre_compound: int
    tyres_age_laps: int
    fia_flags: int
    engine_power_ice: float
    engine_power_mguk: float
    ers_store: float
    ers_deploy_mode: int
    ers_harvested_mguk: float
    ers_harvested_mguh: float
    ers_harvest_limit: float
    ers_deployed: float
    network_paused: int

    @property
    def tyre_name(self) -> str:
        return COMPOUND_MAP.get(self.actual_tyre_compound, f"?{self.actual_tyre_compound}")

    @property
    def visual_tyre_name(self) -> str:
        return VISUAL_COMPOUND_MAP.get(self.visual_tyre_compound, self.tyre_name)

    @property
    def ers_pct(self) -> float:
        max_ers = 4_000_000  # 4 MJ
        return min(100.0, self.ers_store / max_ers * 100) if max_ers > 0 else 0


@dataclass
class PacketCarStatusData:
    header: PacketHeader
    cars: List[CarStatusData]

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketCarStatusData":
        off = HEADER_SIZE
        cars = []
        for _ in range(MAX_CARS):
            t = _CS.unpack_from(data, off)
            off += _CS.size
            cars.append(CarStatusData(*t))
        return cls(header, cars)


# ── car damage (packet 10) ───────────────────────────────────────────────────
# Per car: 4f 4B 4B 4B B B B B B B B B B B B B B B B B B B = 22+22 = 44 bytes
_CD = struct.Struct("<4f4B4B4B" + "B"*18)  # 16+4+4+4+18 = 46 bytes per car

@dataclass
class CarDamageData:
    tyres_wear: tuple       # RL RR FL FR %
    tyres_damage: tuple     # %
    brakes_damage: tuple    # %
    tyre_blisters: tuple    # %
    fl_wing_dmg: int
    fr_wing_dmg: int
    rear_wing_dmg: int
    floor_dmg: int
    diffuser_dmg: int
    sidepod_dmg: int
    drs_fault: int
    ers_fault: int
    gearbox_dmg: int
    engine_dmg: int
    engine_mguh_wear: int
    engine_es_wear: int
    engine_ce_wear: int
    engine_ice_wear: int
    engine_mguk_wear: int
    engine_tc_wear: int
    engine_blown: int
    engine_seized: int


@dataclass
class PacketCarDamageData:
    header: PacketHeader
    cars: List[CarDamageData]

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketCarDamageData":
        off = HEADER_SIZE
        cars = []
        for _ in range(MAX_CARS):
            t = _CD.unpack_from(data, off)
            off += _CD.size
            cars.append(CarDamageData(
                tyres_wear=t[0:4],
                tyres_damage=t[4:8],
                brakes_damage=t[8:12],
                tyre_blisters=t[12:16],
                fl_wing_dmg=t[16], fr_wing_dmg=t[17], rear_wing_dmg=t[18],
                floor_dmg=t[19], diffuser_dmg=t[20], sidepod_dmg=t[21],
                drs_fault=t[22], ers_fault=t[23], gearbox_dmg=t[24],
                engine_dmg=t[25], engine_mguh_wear=t[26], engine_es_wear=t[27],
                engine_ce_wear=t[28], engine_ice_wear=t[29], engine_mguk_wear=t[30],
                engine_tc_wear=t[31], engine_blown=t[32], engine_seized=t[33],
            ))
        return cls(header, cars)


# ── participants (packet 4) ──────────────────────────────────────────────────
# 2026 spec: driverId, networkId, teamId widened from uint8 to uint16
# (12-team grid needs more headroom). Per participant: 60 bytes (was 57).
# B HHH B B B char[32] B B H B B[4*3]
# LiveryColour = 3 bytes (RGB), m_numColours + m_liveryColours[4] = 1 + 4*3 = 13 bytes
_PART_FMT = "<BHHHBBB32sBBHB13s"
_PART = struct.Struct(_PART_FMT)

@dataclass
class ParticipantData:
    ai_controlled: int
    driver_id: int
    network_id: int
    team_id: int
    my_team: int
    race_number: int
    nationality: int
    name: str
    your_telemetry: int
    show_online_names: int
    tech_level: int
    platform: int


@dataclass
class PacketParticipantsData:
    header: PacketHeader
    num_active_cars: int
    participants: List[ParticipantData]

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketParticipantsData":
        off = HEADER_SIZE
        num_cars = struct.unpack_from("<B", data, off)[0]
        off += 1
        parts = []
        for _ in range(MAX_CARS):
            t = _PART.unpack_from(data, off)
            off += _PART.size
            parts.append(ParticipantData(
                ai_controlled=t[0], driver_id=t[1], network_id=t[2],
                team_id=t[3], my_team=t[4], race_number=t[5],
                nationality=t[6],
                name=t[7].rstrip(b'\x00').decode("utf-8", errors="replace"),
                your_telemetry=t[8], show_online_names=t[9],
                tech_level=t[10], platform=t[11],
            ))
        return cls(header, num_cars, parts)


# ── motion ex (packet 13) ────────────────────────────────────────────────────
# Player car only: 4f*8 + f + 3f + 3f + 3f + f + 4f + 4f + f + f + f + f + f + 4f + 4f
_MEX = struct.Struct("<" + "f"*4*8 + "f" + "f"*3 + "f"*3 + "f"*3 + "f" + "f"*4 + "f"*4 + "f" + "f" + "f" + "f" + "f" + "f"*4 + "f"*4)
# Count: 32 + 1 + 3 + 3 + 3 + 1 + 4 + 4 + 1+1+1+1+1 + 4 + 4 = 64 floats = 256 bytes → actual spec size 273-29=244 bytes... let me recount

@dataclass
class PacketMotionExData:
    header: PacketHeader
    suspension_position: tuple
    suspension_velocity: tuple
    suspension_acceleration: tuple
    wheel_speed: tuple
    wheel_slip_ratio: tuple
    wheel_slip_angle: tuple
    wheel_lat_force: tuple
    wheel_long_force: tuple
    height_of_cog: float
    local_velocity: tuple   # x,y,z
    angular_velocity: tuple # x,y,z
    angular_accel: tuple    # x,y,z
    front_wheels_angle: float
    wheel_vert_force: tuple
    front_aero_height: float
    rear_aero_height: float
    front_roll_angle: float
    rear_roll_angle: float
    chassis_yaw: float
    chassis_pitch: float
    wheel_camber: tuple
    wheel_camber_gain: tuple

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketMotionExData":
        off = HEADER_SIZE
        # 4f * 8 groups for suspension_pos/vel/acc/wheelspeed/slipRatio/slipAngle/latForce/longForce
        fmt1 = struct.Struct("<32f")
        t1 = fmt1.unpack_from(data, off); off += fmt1.size
        # height of COG
        cog = struct.unpack_from("<f", data, off)[0]; off += 4
        # local vel (3f), angular vel (3f), angular accel (3f)
        fmt2 = struct.Struct("<9f")
        t2 = fmt2.unpack_from(data, off); off += fmt2.size
        # front wheels angle, wheel vert force (4f)
        fwa = struct.unpack_from("<f", data, off)[0]; off += 4
        wvf = struct.unpack_from("<4f", data, off); off += 16
        # front/rear aero height, roll angles, chassis yaw/pitch
        fmt3 = struct.Struct("<6f")
        t3 = fmt3.unpack_from(data, off); off += fmt3.size
        # wheel camber (4f), camber gain (4f)
        fmt4 = struct.Struct("<8f")
        t4 = fmt4.unpack_from(data, off)

        return cls(
            header=header,
            suspension_position=t1[0:4],
            suspension_velocity=t1[4:8],
            suspension_acceleration=t1[8:12],
            wheel_speed=t1[12:16],
            wheel_slip_ratio=t1[16:20],
            wheel_slip_angle=t1[20:24],
            wheel_lat_force=t1[24:28],
            wheel_long_force=t1[28:32],
            height_of_cog=cog,
            local_velocity=t2[0:3],
            angular_velocity=t2[3:6],
            angular_accel=t2[6:9],
            front_wheels_angle=fwa,
            wheel_vert_force=wvf,
            front_aero_height=t3[0],
            rear_aero_height=t3[1],
            front_roll_angle=t3[2],
            rear_roll_angle=t3[3],
            chassis_yaw=t3[4],
            chassis_pitch=t3[5],
            wheel_camber=t4[0:4],
            wheel_camber_gain=t4[4:8],
        )


# ── event (packet 3) ─────────────────────────────────────────────────────────
EVENT_CODES = {
    b"SSTA": "Session Started",
    b"SEND": "Session Ended",
    b"FTLP": "Fastest Lap",
    b"RTMT": "Retirement",
    b"DRSE": "DRS Enabled",
    b"DRSD": "DRS Disabled",
    b"TMPT": "Teammate In Pits",
    b"CHQF": "Chequered Flag",
    b"RCWN": "Race Winner",
    b"PENA": "Penalty",
    b"SPTP": "Speed Trap",
    b"STLG": "Start Lights",
    b"LGOT": "Lights Out",
    b"DTSV": "Drive Through Served",
    b"SGSV": "Stop Go Served",
    b"FLBK": "Flashback",
    b"BUTN": "Button Status",
    b"RDFL": "Red Flag",
    b"OVTK": "Overtake",
    b"SCAR": "Safety Car",
    b"COLL": "Collision",
}

@dataclass
class PacketEventData:
    header: PacketHeader
    event_code: bytes
    event_name: str
    details: dict

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketEventData":
        off = HEADER_SIZE
        code = data[off:off+4]
        name = EVENT_CODES.get(code, code.decode("ascii", errors="replace"))
        off += 4
        details = {}
        try:
            if code == b"FTLP":
                vidx, lt = struct.unpack_from("<Bf", data, off)
                details = {"vehicle_idx": vidx, "lap_time": lt}
            elif code == b"RTMT":
                vidx, reason = struct.unpack_from("<BB", data, off)
                details = {"vehicle_idx": vidx, "reason": reason}
            elif code == b"PENA":
                fields = struct.unpack_from("<BBBBBBB", data, off)
                details = {
                    "penalty_type": fields[0], "infringement_type": fields[1],
                    "vehicle_idx": fields[2], "other_vehicle_idx": fields[3],
                    "time": fields[4], "lap_num": fields[5], "places_gained": fields[6],
                }
            elif code == b"SPTP":
                v, sp, ofs, ods, fvi, fsp = struct.unpack_from("<BfBBBf", data, off)
                details = {"vehicle_idx": v, "speed": sp}
            elif code == b"OVTK":
                o, b = struct.unpack_from("<BB", data, off)
                details = {"overtaking_idx": o, "overtaken_idx": b}
            elif code == b"SCAR":
                st, et = struct.unpack_from("<BB", data, off)
                details = {"safety_car_type": st, "event_type": et}
        except struct.error:
            pass
        return cls(header, code, name, details)


# ── session history (packet 11) ───────────────────────────────────────────────
_LH = struct.Struct("<I HB HB HB B")  # lap history per lap

@dataclass
class LapHistoryEntry:
    lap_time_ms: int
    s1_ms: int; s1_min: int
    s2_ms: int; s2_min: int
    s3_ms: int; s3_min: int
    valid_bits: int

@dataclass
class TyreStintHistory:
    end_lap: int
    actual_compound: int
    visual_compound: int

@dataclass
class PacketSessionHistoryData:
    header: PacketHeader
    car_idx: int
    num_laps: int
    num_tyre_stints: int
    best_lap_num: int
    best_s1_lap: int
    best_s2_lap: int
    best_s3_lap: int
    lap_history: List[LapHistoryEntry]
    tyre_stints: List[TyreStintHistory]

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketSessionHistoryData":
        off = HEADER_SIZE
        car_idx, num_laps, num_stints, best_lap, best_s1, best_s2, best_s3 = \
            struct.unpack_from("<BBBBBBB", data, off)
        off += 7
        laps = []
        for i in range(MAX_LAPS_HIST):
            t = _LH.unpack_from(data, off)
            off += _LH.size
            laps.append(LapHistoryEntry(*t))
        stints = []
        for _ in range(MAX_STINTS):
            t = struct.unpack_from("<BBB", data, off)
            off += 3
            stints.append(TyreStintHistory(*t))
        return cls(header, car_idx, num_laps, num_stints, best_lap, best_s1, best_s2, best_s3, laps, stints)


# ── car setups (packet 5) ────────────────────────────────────────────────────
_CSU = struct.Struct("<BBBBffffBBBBBBBBBffffBf")

@dataclass
class CarSetupData:
    front_wing: int; rear_wing: int
    on_throttle: int; off_throttle: int
    front_camber: float; rear_camber: float
    front_toe: float; rear_toe: float
    front_susp: int; rear_susp: int
    front_arb: int; rear_arb: int
    front_susp_height: int; rear_susp_height: int
    brake_pressure: int; brake_bias: int; engine_braking: int
    rl_tyre_psi: float; rr_tyre_psi: float
    fl_tyre_psi: float; fr_tyre_psi: float
    ballast: int; fuel_load: float

@dataclass
class PacketCarSetupData:
    header: PacketHeader
    setups: List[CarSetupData]
    next_front_wing: float

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketCarSetupData":
        off = HEADER_SIZE
        setups = []
        for _ in range(MAX_CARS):
            t = _CSU.unpack_from(data, off)
            off += _CSU.size
            setups.append(CarSetupData(*t))
        nfw = struct.unpack_from("<f", data, off)[0]
        return cls(header, setups, nfw)


# ── final classification (packet 8) ──────────────────────────────────────────
_FC = struct.Struct("<BBBBBBBIdbBB8B8B8B")

@dataclass
class FinalClassificationData:
    position: int; num_laps: int; grid_position: int
    points: int; num_pit_stops: int; result_status: int; result_reason: int
    best_lap_ms: int; total_race_time: float
    penalties_time: int; num_penalties: int; num_tyre_stints: int
    tyre_stints_actual: tuple; tyre_stints_visual: tuple; tyre_stints_end_laps: tuple

@dataclass
class PacketFinalClassificationData:
    header: PacketHeader
    num_cars: int
    classifications: List[FinalClassificationData]

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketFinalClassificationData":
        off = HEADER_SIZE
        num_cars = struct.unpack_from("<B", data, off)[0]; off += 1
        clfs = []
        for _ in range(MAX_CARS):
            t = _FC.unpack_from(data, off)
            off += _FC.size
            clfs.append(FinalClassificationData(
                position=t[0], num_laps=t[1], grid_position=t[2],
                points=t[3], num_pit_stops=t[4], result_status=t[5], result_reason=t[6],
                best_lap_ms=t[7], total_race_time=t[8],
                penalties_time=t[9], num_penalties=t[10], num_tyre_stints=t[11],
                tyre_stints_actual=t[12:20], tyre_stints_visual=t[20:28], tyre_stints_end_laps=t[28:36],
            ))
        return cls(header, num_cars, clfs)


# ── tyre sets (packet 12) ─────────────────────────────────────────────────────
_TS = struct.Struct("<BBBBBBBhB")

@dataclass
class TyreSetData:
    actual_compound: int; visual_compound: int
    wear: int; available: int
    recommended_session: int; life_span: int; usable_life: int
    lap_delta_ms: int; fitted: int

@dataclass
class PacketTyreSetsData:
    header: PacketHeader
    car_idx: int
    tyre_sets: List[TyreSetData]
    fitted_idx: int

    @classmethod
    def unpack(cls, header: PacketHeader, data: bytes) -> "PacketTyreSetsData":
        off = HEADER_SIZE
        car_idx = struct.unpack_from("<B", data, off)[0]; off += 1
        sets = []
        for _ in range(MAX_TYRE_SETS):
            t = _TS.unpack_from(data, off)
            off += _TS.size
            sets.append(TyreSetData(*t))
        fitted = struct.unpack_from("<B", data, off)[0]
        return cls(header, car_idx, sets, fitted)


# ── top-level dispatcher ─────────────────────────────────────────────────────
PACKET_CLASSES = {
    0:  PacketMotionData,
    1:  PacketSessionData,
    2:  PacketLapData,
    3:  PacketEventData,
    4:  PacketParticipantsData,
    5:  PacketCarSetupData,
    6:  PacketCarTelemetryData,
    7:  PacketCarStatusData,
    8:  PacketFinalClassificationData,
    10: PacketCarDamageData,
    11: PacketSessionHistoryData,
    12: PacketTyreSetsData,
    13: PacketMotionExData,
}

def parse_packet(data: bytes):
    """Parse a raw UDP datagram. Returns a typed packet object or None."""
    import logging
    _log = logging.getLogger(__name__)
    if len(data) < HEADER_SIZE:
        return None
    try:
        header = PacketHeader.unpack(data)
    except (struct.error, IndexError):
        return None
    if header.packet_format not in (2025, 2026):
        _log.warning(f"Unknown packet format {header.packet_format} — expected 2025 or 2026")
        return None
    cls = PACKET_CLASSES.get(header.packet_id)
    if cls is None:
        return None
    try:
        return cls.unpack(header, data)
    except (struct.error, IndexError) as e:
        _log.warning(f"Failed to parse packet_id={header.packet_id} size={len(data)}: {e}")
        return None
