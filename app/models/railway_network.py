"""
Indian Railways Network & Infrastructure Data Models.
Models Stations, Main Lines, Loop Lines, Block Sections,
Automatic Block Signaling (ABS) circuits, and Speed Restrictions (PSR/TSR).
"""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class Direction(str, Enum):
    UP = "UP"      # In IR convention, typically towards headquarters / major terminal (e.g. towards New Delhi)
    DOWN = "DOWN"  # Away from headquarters / major terminal (e.g. towards Howrah / Kanpur)


class SignalingType(str, Enum):
    AUTOMATIC = "AUTOMATIC"   # Automatic Block Signaling (ABS) with 3/4-aspect signals
    ABSOLUTE = "ABSOLUTE"     # Absolute Block System (station-to-station token/lock & block)


class TrackType(str, Enum):
    MAIN_LINE = "MAIN_LINE"        # Non-stop through line (speed up to section MPS: 130/160 km/h)
    LOOP_LINE = "LOOP_LINE"        # Siding / loop for berthing, crossing & overtakes (turnout speed: 30 km/h)
    PLATFORM_LINE = "PLATFORM"     # Line with passenger platform
    COMMON_LOOP = "COMMON_LOOP"    # Reversible loop accessible from both UP and DOWN lines


class Track(BaseModel):
    id: str
    track_type: TrackType
    direction: Direction
    platform_number: Optional[int] = None
    length_meters: float = 750.0  # Standard IR CSR (Clear Standing Room) length is ~715-750m for 24-coach / full rake
    turnout_speed_kmh: float = 30.0  # 1-in-12 turnout speed limit
    current_occupant_train_id: Optional[str] = None


class Station(BaseModel):
    code: str
    name: str
    km: float
    tracks: List[Track]
    is_junction: bool = False
    
    def get_main_track(self, direction: Direction) -> Optional[Track]:
        for t in self.tracks:
            if t.track_type == TrackType.MAIN_LINE and t.direction == direction:
                return t
        return None

    def get_loop_tracks(self, direction: Direction) -> List[Track]:
        return [
            t for t in self.tracks 
            if (t.track_type in (TrackType.LOOP_LINE, TrackType.COMMON_LOOP, TrackType.PLATFORM_LINE)) 
            and (t.direction == direction or t.track_type == TrackType.COMMON_LOOP)
        ]


class SpeedRestriction(BaseModel):
    id: str
    from_km: float
    to_km: float
    speed_limit_kmh: float
    direction: Optional[Direction] = None  # None applies to both
    reason: str
    is_temporary: bool = True  # TSR vs PSR
    active: bool = True


class SignalAspect(str, Enum):
    RED = "RED"                     # Stop / Danger: Block occupied
    YELLOW = "YELLOW"               # Caution: 1 block clear, prepare to stop at next signal
    DOUBLE_YELLOW = "DOUBLE_YELLOW" # Attention: 2 blocks clear, pass next signal at caution
    GREEN = "GREEN"                 # Clear: 2+ blocks clear, run at full section MPS (130 km/h)


class SignalType(str, Enum):
    AUTOMATIC = "AUTOMATIC"           # Automatic Block Signal (ABS)
    HOME = "HOME"                     # Station Entry Signal with Route Indicator Feather
    STARTER = "STARTER"               # Station Platform/Loop Departure Signal
    ADVANCED_STARTER = "ADVANCED_STARTER" # Station Exit Signal into Section
    DISTANT = "DISTANT"               # Warning signal before Station Home


class RailwaySignal(BaseModel):
    id: str
    name: str                         # e.g. "S-42 (Auto)", "DKDE Home (Up)"
    km: float
    direction: Direction
    signal_type: SignalType
    current_aspect: SignalAspect = SignalAspect.GREEN
    route_feather_active: bool = False  # Illuminated feather when set for loop turnout
    is_failed: bool = False             # Red clamp / Track circuit failure simulation
    station_code: Optional[str] = None
    next_signal_id: Optional[str] = None


class KavachTelemetry(BaseModel):
    train_id: str
    train_number: str
    cab_signal_aspect: SignalAspect
    movement_authority_meters: float
    distance_to_signal_meters: float
    current_speed_kmh: float
    permitted_speed_kmh: float
    spad_alert: str = "NORMAL"  # "NORMAL", "BRAKE_APPLIED", "WARNING"


class BlockSection(BaseModel):
    id: str
    from_station_code: str
    to_station_code: str
    direction: Direction
    distance_km: float
    signaling: SignalingType = SignalingType.AUTOMATIC
    sub_blocks: int = 6  # ABS track circuits (e.g. 1.2 km each in a 7-15 km inter-station gap)
    safe_headway_sec: int = 150  # Minimum headway between consecutive trains (2.5 mins)
    section_mps_kmh: float = 130.0  # Maximum Permissible Speed


class CorridorSection(BaseModel):
    name: str
    description: str
    total_km: float
    stations: List[Station]
    block_sections: List[BlockSection]
    speed_restrictions: List[SpeedRestriction] = []
    signals: List[RailwaySignal] = []

    def get_station(self, code: str) -> Optional[Station]:
        for st in self.stations:
            if st.code == code:
                return st
        return None

    def get_block_section(self, from_code: str, to_code: str, direction: Direction) -> Optional[BlockSection]:
        for b in self.block_sections:
            if b.from_station_code == from_code and b.to_station_code == to_code and b.direction == direction:
                return b
        return None

    def get_signal(self, sig_id: str) -> Optional[RailwaySignal]:
        for s in self.signals:
            if s.id == sig_id:
                return s
        return None

