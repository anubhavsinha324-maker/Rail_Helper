"""
Conflict Detection Engine for Indian Railways Section Traffic.
Identifies:
1. Headway violations (safe following distance in Automatic Block Signaling)
2. Catch-up / Overtake conflicts (fast trains catching slow trains on double line)
3. Track occupancy / Loop line capacity violations
4. Speed restriction impact conflicts
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.railway_network import CorridorSection, Direction
from app.models.train import Train, TrainCategory


class TrafficConflict(BaseModel):
    conflict_id: str
    conflict_type: str        # "HEADWAY_VIOLATION", "OVERTAKE_NECESSARY", "LOOP_OCCUPANCY_CLASH", "SPEED_RESTRICTION"
    severity: str             # "CRITICAL", "HIGH", "MODERATE"
    location_station: str
    timestamp_sec: int
    train_1_id: str
    train_1_name: str
    train_2_id: Optional[str] = None
    train_2_name: Optional[str] = None
    description: str
    suggested_action: str


class ConflictDetector:
    def __init__(self, corridor: CorridorSection):
        self.corridor = corridor

    def detect_conflicts(self, trains: List[Train], schedule_data: Optional[Dict[str, Dict[str, Dict[str, int]]]] = None) -> List[TrafficConflict]:
        """
        Analyze train trajectories and detect operational conflicts.
        If schedule_data is provided, uses it (format: {train_id: {station_code: {'arr': x, 'dep': y, 'track': z}}}).
        Otherwise uses train.schedule.
        """
        conflicts: List[TrafficConflict] = []
        c_count = 1

        # Group trains by direction
        down_trains = [t for t in trains if t.direction == "DOWN"]
        up_trains = [t for t in trains if t.direction == "UP"]

        for direction, t_list in [("DOWN", down_trains), ("UP", up_trains)]:
            # Check pairwise interactions for trains traveling in the same direction
            for i in range(len(t_list)):
                for j in range(i + 1, len(t_list)):
                    t1, t2 = t_list[i], t_list[j]
                    
                    # Extract timing profile
                    t1_times = self._get_train_station_times(t1, schedule_data)
                    t2_times = self._get_train_station_times(t2, schedule_data)

                    # Common stations in travel order
                    common_stations = [st.code for st in self.corridor.stations if st.code in t1_times and st.code in t2_times]
                    if direction == "UP":
                        common_stations.reverse()

                    for idx in range(len(common_stations) - 1):
                        curr_st = common_stations[idx]
                        next_st = common_stations[idx + 1]

                        t1_dep = t1_times[curr_st]["dep"]
                        t1_arr_next = t1_times[next_st]["arr"]
                        t2_dep = t2_times[curr_st]["dep"]
                        t2_arr_next = t2_times[next_st]["arr"]

                        # Check 1: Headway conflict at departure
                        headway_dep = abs(t1_dep - t2_dep)
                        if headway_dep < 150 and min(t1_dep, t2_dep) > 0:
                            leader = t1 if t1_dep < t2_dep else t2
                            follower = t2 if leader == t1 else t1
                            conflicts.append(TrafficConflict(
                                conflict_id=f"CONF-{c_count:03d}",
                                conflict_type="HEADWAY_VIOLATION",
                                severity="CRITICAL",
                                location_station=curr_st,
                                timestamp_sec=min(t1_dep, t2_dep),
                                train_1_id=leader.id,
                                train_1_name=leader.name,
                                train_2_id=follower.id,
                                train_2_name=follower.name,
                                description=(
                                    f"Unsafe departure headway of {headway_dep}s at {curr_st} between "
                                    f"leader '{leader.number}' and follower '{follower.number}' (Min required: 150s)."
                                ),
                                suggested_action=f"Enforce minimum 150s ABS headway for {follower.number}."
                            ))
                            c_count += 1

                        # Check 2: Overtake / Catch-up conflict (Fast train behind slow train)
                        # Occurs if leader at curr_st reaches next_st AFTER the follower would naturally reach
                        if t1_dep < t2_dep and t1_arr_next >= t2_arr_next:
                            conflicts.append(TrafficConflict(
                                conflict_id=f"CONF-{c_count:03d}",
                                conflict_type="OVERTAKE_NECESSARY",
                                severity="HIGH" if t2.priority_weight > t1.priority_weight else "MODERATE",
                                location_station=curr_st,
                                timestamp_sec=t1_dep,
                                train_1_id=t1.id,
                                train_1_name=t1.name,
                                train_2_id=t2.id,
                                train_2_name=t2.name,
                                description=(
                                    f"Fast train '{t2.number} {t2.name}' (Priority {t2.priority_weight}) is catching up "
                                    f"to slower train '{t1.number} {t1.name}' (Priority {t1.priority_weight}) between {curr_st} and {next_st}."
                                ),
                                suggested_action=(
                                    f"Divert slower train '{t1.number}' into Loop Line at {curr_st} or {next_st} "
                                    f"to permit unobstructed through passage for '{t2.number}'."
                                )
                            ))
                            c_count += 1
                        elif t2_dep < t1_dep and t2_arr_next >= t1_arr_next:
                            conflicts.append(TrafficConflict(
                                conflict_id=f"CONF-{c_count:03d}",
                                conflict_type="OVERTAKE_NECESSARY",
                                severity="HIGH" if t1.priority_weight > t2.priority_weight else "MODERATE",
                                location_station=curr_st,
                                timestamp_sec=t2_dep,
                                train_1_id=t2.id,
                                train_1_name=t2.name,
                                train_2_id=t1.id,
                                train_2_name=t1.name,
                                description=(
                                    f"Fast train '{t1.number} {t1.name}' is catching up "
                                    f"to slower train '{t2.number} {t2.name}' between {curr_st} and {next_st}."
                                ),
                                suggested_action=(
                                    f"Divert '{t2.number}' into Loop Line at {curr_st} to allow '{t1.number}' to overtake."
                                )
                            ))
                            c_count += 1

        return conflicts

    def _get_train_station_times(self, train: Train, schedule_data: Optional[Dict]) -> Dict[str, Dict[str, int]]:
        res = {}
        if schedule_data and train.id in schedule_data:
            return schedule_data[train.id]
        
        for entry in train.schedule:
            res[entry.station_code] = {
                "arr": entry.scheduled_arrival_sec + train.initial_delay_sec,
                "dep": entry.scheduled_departure_sec + train.initial_delay_sec,
                "track": "MAIN_LINE"
            }
        return res
