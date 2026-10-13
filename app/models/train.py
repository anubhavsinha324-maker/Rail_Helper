"""
Indian Railways Train Specifications, Priority Classifications, and Timetable Models.
Follows Railway Board priority standards (Vande Bharat > Rajdhani > Mail/Express > Passenger > Freight).
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TrainCategory(str, Enum):
    VANDE_BHARAT = "VANDE_BHARAT"       # Priority 1: High acceleration EMU, Premium, Flagship
    RAJDHANI = "RAJDHANI"               # Priority 1: Premium Superfast Long-Distance
    SUPERFAST = "SUPERFAST"             # Priority 2: Mail / Express / Jan Shatabdi
    PASSENGER = "PASSENGER"             # Priority 3: Stopping commuter / MEMU / Passenger
    CONCOR_CONTAINER = "CONCOR"         # Priority 4: High-priority container freight
    BOXN_FREIGHT = "BOXN_COAL"          # Priority 5: Heavy bulk freight (Coal, Iron Ore)


# Weight assigned in objective function for delays (higher weight = much stricter penalty for delay)
PRIORITY_WEIGHTS = {
    TrainCategory.VANDE_BHARAT: 120,
    TrainCategory.RAJDHANI: 100,
    TrainCategory.SUPERFAST: 70,
    TrainCategory.PASSENGER: 45,
    TrainCategory.CONCOR_CONTAINER: 30,
    TrainCategory.BOXN_FREIGHT: 15,
}

# Maximum Permissible Speed (MPS) in km/h for standard coaches/rakes
DEFAULT_MPS = {
    TrainCategory.VANDE_BHARAT: 130.0,  # Capable of 160 on upgraded tracks, 130 standard
    TrainCategory.RAJDHANI: 130.0,
    TrainCategory.SUPERFAST: 110.0,
    TrainCategory.PASSENGER: 90.0,
    TrainCategory.CONCOR_CONTAINER: 75.0,
    TrainCategory.BOXN_FREIGHT: 60.0,
}

# Average acceleration (m/s²)
ACCELERATION_RATES = {
    TrainCategory.VANDE_BHARAT: 0.70,   # High-acceleration distributed traction
    TrainCategory.RAJDHANI: 0.50,       # WAP-7 push-pull / twin locos
    TrainCategory.SUPERFAST: 0.40,
    TrainCategory.PASSENGER: 0.55,      # Electric Multiple Unit (MEMU) rapid acceleration
    TrainCategory.CONCOR_CONTAINER: 0.25,
    TrainCategory.BOXN_FREIGHT: 0.15,   # Heavy 58-wagon rake with WAG-9 / twin WAG-12
}


# Train rake length in meters depending on category (500m to 1000m)
CATEGORY_LENGTHS = {
    TrainCategory.VANDE_BHARAT: 500.0,       # 16-coach Vande Bharat EMU trainset (500m)
    TrainCategory.PASSENGER: 550.0,          # 12-16 coach commuter MEMU (550m)
    TrainCategory.SUPERFAST: 650.0,          # 22-coach Superfast Express rake (650m)
    TrainCategory.RAJDHANI: 700.0,           # 24-coach full LHB Rajdhani rake (700m)
    TrainCategory.CONCOR_CONTAINER: 850.0,   # 45-wagon double-stack Container rake (850m)
    TrainCategory.BOXN_FREIGHT: 1000.0,      # 58-wagon heavy bulk Coal freight (1000m / 1 km)
}


class TimetableEntry(BaseModel):
    station_code: str
    scheduled_arrival_sec: int        # Seconds from baseline midnight (00:00:00)
    scheduled_departure_sec: int
    min_dwell_sec: int = 120           # Minimum time required if stopped (e.g. 2 mins)
    is_commercial_stop: bool = False   # True if scheduled passenger stop, False for through-run
    assigned_track_id: Optional[str] = None


class Train(BaseModel):
    id: str
    number: str                         # 5-digit IR train number (e.g. "22436", "12301", "BOXN-912")
    name: str                           # e.g. "Vande Bharat Express", "Howrah Rajdhani"
    category: TrainCategory
    direction: str                      # "UP" or "DOWN"
    max_speed_kmh: float = 130.0
    length_meters: float = 650.0        # Range 500m to 1000m depending on category
    priority_weight: int = 70
    schedule: List[TimetableEntry]
    
    # Real-time state
    current_station_code: Optional[str] = None
    initial_delay_sec: int = 0          # Injected or upstream delay
    is_active: bool = True
    color_hex: str = "#3B82F6"

    @classmethod
    def create(cls, id: str, number: str, name: str, category: TrainCategory, direction: str, 
               schedule: List[TimetableEntry], initial_delay_sec: int = 0, color: Optional[str] = None):
        weight = PRIORITY_WEIGHTS.get(category, 50)
        mps = DEFAULT_MPS.get(category, 100.0)
        rake_len = CATEGORY_LENGTHS.get(category, 650.0)
        
        # Color coding palette
        palette = {
            TrainCategory.VANDE_BHARAT: "#8B5CF6",   # Royal Purple
            TrainCategory.RAJDHANI: "#EF4444",       # Expressive Red
            TrainCategory.SUPERFAST: "#0284C7",      # Vibrant Blue
            TrainCategory.PASSENGER: "#10B981",      # Emerald Green
            TrainCategory.CONCOR_CONTAINER: "#F59E0B",# Amber
            TrainCategory.BOXN_FREIGHT: "#6B7280",   # Steel Slate
        }
        
        return cls(
            id=id,
            number=number,
            name=name,
            category=category,
            direction=direction,
            max_speed_kmh=mps,
            length_meters=rake_len,
            priority_weight=weight,
            schedule=schedule,
            initial_delay_sec=initial_delay_sec,
            color_hex=color or palette.get(category, "#3B82F6")
        )
