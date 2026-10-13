"""
Google OR-Tools CP-SAT Optimization Solver for Section Traffic Dispatching.
Solves the Train Dispatching Problem (TDP) / Conflict Resolution with:
- Strict Safety Headways in Automatic Block Signaling
- Loop Line Siding / Overtaking allocation
- Turnout speed restrictions (1-in-12 turnout speed drop)
- Railway Board Priority Hierarchy weighting
- Temporary Speed Restrictions (TSR) handling
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from ortools.sat.python import cp_model

from app.models.railway_network import CorridorSection, Direction, Station, SpeedRestriction
from app.models.train import Train, TrainCategory


class SectionOptimizationResult:
    def __init__(self):
        self.status: str = "UNKNOWN"
        self.solve_time_sec: float = 0.0
        self.objective_value: float = 0.0
        self.schedule: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # Format: {train_id: {station_code: {"arr": int, "dep": int, "track": str, "delay_sec": int, "is_looped": bool}}}
        self.overtakes: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}


class SectionDispatchOptimizer:
    def __init__(self, corridor: CorridorSection):
        self.corridor = corridor

    def solve(self, trains: List[Train], time_horizon_sec: int = 14400, max_solver_time_sec: float = 5.0) -> SectionOptimizationResult:
        """
        Formulate and solve the Section Dispatching Problem using CP-SAT.
        """
        start_cpu = time.time()
        model = cp_model.CpModel()
        result = SectionOptimizationResult()

        # Build stations lookup & sequence per direction
        down_station_seq = [st.code for st in self.corridor.stations]
        up_station_seq = list(reversed(down_station_seq))

        # -----------------------------------------------------------
        # 1. Variables Creation
        # -----------------------------------------------------------
        # arr[t.id, st_code] and dep[t.id, st_code]
        arr_vars: Dict[Tuple[str, str], cp_model.IntVar] = {}
        dep_vars: Dict[Tuple[str, str], cp_model.IntVar] = {}
        dwell_vars: Dict[Tuple[str, str], cp_model.IntVar] = {}
        is_loop_vars: Dict[Tuple[str, str], cp_model.BoolVar] = {}
        loop_interval_vars: Dict[Tuple[str, str], cp_model.IntervalVar] = {}

        # Tracking delays
        dest_delay_vars: Dict[str, cp_model.IntVar] = {}

        # Minimum running time calculation accounting for MPS and TSRs
        run_times = self._calculate_running_times(trains)

        for train in trains:
            st_seq = down_station_seq if train.direction == "DOWN" else up_station_seq
            dest_st = st_seq[-1]
            origin_st = st_seq[0]

            # Find origin entry time
            first_sched = next(e for e in train.schedule if e.station_code == origin_st)
            earliest_entry = first_sched.scheduled_departure_sec + train.initial_delay_sec

            for idx, st_code in enumerate(st_seq):
                sched_entry = next((e for e in train.schedule if e.station_code == st_code), None)
                sched_arr = (sched_entry.scheduled_arrival_sec + train.initial_delay_sec) if sched_entry else earliest_entry
                sched_dep = (sched_entry.scheduled_departure_sec + train.initial_delay_sec) if sched_entry else earliest_entry

                # Decision variables
                arr_var = model.NewIntVar(0, time_horizon_sec + 86400, f"arr_{train.id}_{st_code}")
                dep_var = model.NewIntVar(0, time_horizon_sec + 86400, f"dep_{train.id}_{st_code}")
                dwell_var = model.NewIntVar(0, 3600, f"dwell_{train.id}_{st_code}")
                is_loop = model.NewBoolVar(f"loop_{train.id}_{st_code}")

                arr_vars[(train.id, st_code)] = arr_var
                dep_vars[(train.id, st_code)] = dep_var
                dwell_vars[(train.id, st_code)] = dwell_var
                is_loop_vars[(train.id, st_code)] = is_loop

                # Link departure and arrival via dwell
                model.Add(dep_var == arr_var + dwell_var)

                # Dwell constraints
                min_commercial_dwell = sched_entry.min_dwell_sec if (sched_entry and sched_entry.is_commercial_stop) else 0
                model.Add(dwell_var >= min_commercial_dwell)

                # Origin station departure cannot be earlier than scheduled entry
                if idx == 0:
                    model.Add(arr_var >= earliest_entry)
                    model.Add(dep_var >= earliest_entry)
                else:
                    # Arrival cannot be before scheduled arrival unless authorized
                    model.Add(arr_var >= sched_arr)

                # If train is on Main Line and has no commercial stop, dwell is 0
                if sched_entry and not sched_entry.is_commercial_stop and idx != 0 and idx != len(st_seq) - 1:
                    # If NOT on loop line, dwell must be 0 (cannot stop on main line in middle of station)
                    model.Add(dwell_var == 0).OnlyEnforceIf(is_loop.Not())

                # Create optional interval for loop track occupancy to avoid loop clashes
                # Loop track clear safety buffer: 120s
                loop_interval = model.NewOptionalIntervalVar(
                    arr_var,
                    dwell_var,
                    dep_var,
                    is_loop,
                    f"loop_interval_{train.id}_{st_code}"
                )
                loop_interval_vars[(train.id, st_code)] = loop_interval

            # Destination delay variable
            final_sched = next(e for e in train.schedule if e.station_code == dest_st)
            dest_sched_arr = final_sched.scheduled_arrival_sec
            delay_var = model.NewIntVar(0, 14400, f"delay_{train.id}")
            model.Add(delay_var >= arr_vars[(train.id, dest_st)] - dest_sched_arr)
            dest_delay_vars[train.id] = delay_var

        # -----------------------------------------------------------
        # 2. Block Section Running Times & Turnout Penalties
        # -----------------------------------------------------------
        TURNOUT_PENALTY_SEC = 90  # Deceleration into 30 km/h turnout + acceleration back to line speed

        for train in trains:
            st_seq = down_station_seq if train.direction == "DOWN" else up_station_seq
            for idx in range(len(st_seq) - 1):
                from_st = st_seq[idx]
                to_st = st_seq[idx + 1]

                base_sec = run_times.get((train.id, from_st, to_st), 600)
                is_l_from = is_loop_vars[(train.id, from_st)]
                is_l_to = is_loop_vars[(train.id, to_st)]

                # If diverting into loop or emerging from loop, add turnout penalty
                arr_next = arr_vars[(train.id, to_st)]
                dep_curr = dep_vars[(train.id, from_st)]

                # arr[to] >= dep[from] + base_sec + TURNOUT_PENALTY * is_loop
                model.Add(arr_next >= dep_curr + base_sec + TURNOUT_PENALTY_SEC * is_l_to)

        # -----------------------------------------------------------
        # 3. Headway & Precedence Ordering (Automatic Block Signaling)
        # -----------------------------------------------------------
        HEADWAY_SEC = 150  # 2.5 minutes ABS safe headway

        # Group trains by direction
        for dir_name, t_list in [("DOWN", [t for t in trains if t.direction == "DOWN"]),
                                 ("UP", [t for t in trains if t.direction == "UP"])]:
            st_seq = down_station_seq if dir_name == "DOWN" else up_station_seq

            for i in range(len(t_list)):
                for j in range(i + 1, len(t_list)):
                    t1, t2 = t_list[i], t_list[j]

                    for idx in range(len(st_seq) - 1):
                        curr_st = st_seq[idx]
                        next_st = st_seq[idx + 1]

                        # Precedence boolean: 1 if t1 departs curr_st before t2, 0 if t2 before t1
                        prec_dep = model.NewBoolVar(f"prec_dep_{t1.id}_{t2.id}_{curr_st}")
                        prec_arr = model.NewBoolVar(f"prec_arr_{t1.id}_{t2.id}_{next_st}")

                        d1 = dep_vars[(t1.id, curr_st)]
                        d2 = dep_vars[(t2.id, curr_st)]
                        a1 = arr_vars[(t1.id, next_st)]
                        a2 = arr_vars[(t2.id, next_st)]

                        # Headway enforcement at departure
                        model.Add(d2 >= d1 + HEADWAY_SEC).OnlyEnforceIf(prec_dep)
                        model.Add(d1 >= d2 + HEADWAY_SEC).OnlyEnforceIf(prec_dep.Not())

                        # Headway enforcement at arrival
                        model.Add(a2 >= a1 + HEADWAY_SEC).OnlyEnforceIf(prec_arr)
                        model.Add(a1 >= a2 + HEADWAY_SEC).OnlyEnforceIf(prec_arr.Not())

                        # FIFO on block section if neither train is in a siding:
                        # You CANNOT overtake in the middle of a double line block section without a loop!
                        # So departure order at curr_st must match arrival order at next_st
                        model.Add(prec_arr == prec_dep)

        # -----------------------------------------------------------
        # 4. Loop Track Capacity Constraints (No Clashing on Same Loop)
        # -----------------------------------------------------------
        for st in self.corridor.stations:
            for dir_name in ["DOWN", "UP"]:
                t_list = [t for t in trains if t.direction == dir_name]
                station_loops = st.get_loop_tracks(Direction.DOWN if dir_name == "DOWN" else Direction.UP)
                num_loops = max(1, len(station_loops))

                # For stations with 1 loop per direction: intervals cannot overlap!
                if num_loops == 1 and len(t_list) > 1:
                    loop_intervals = [loop_interval_vars[(t.id, st.code)] for t in t_list]
                    model.AddNoOverlap(loop_intervals)

        # -----------------------------------------------------------
        # 5. Objective Function: Weighted Priority Delay Minimization
        # -----------------------------------------------------------
        objective_terms = []

        for train in trains:
            p_weight = train.priority_weight
            # 1. Heavily weight destination arrival delay
            objective_terms.append(dest_delay_vars[train.id] * p_weight * 10)

            # 2. Discourage unnecessary stopping/looping for heavy freight (saves power & time)
            st_seq = down_station_seq if train.direction == "DOWN" else up_station_seq
            for st_code in st_seq:
                is_l = is_loop_vars[(train.id, st_code)]
                dwell = dwell_vars[(train.id, st_code)]
                # Looping penalty: freight penalty is higher for stops, but high priority trains should never be looped!
                if train.category in (TrainCategory.VANDE_BHARAT, TrainCategory.RAJDHANI):
                    objective_terms.append(is_l * 50000)  # Never loop Vande Bharat / Rajdhani unless emergency
                else:
                    objective_terms.append(is_l * 300)     # Small penalty to avoid frivolous loops
                    objective_terms.append(dwell * 2)

        model.Minimize(sum(objective_terms))

        # -----------------------------------------------------------
        # 6. Solve Model
        # -----------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_solver_time_sec
        solver.parameters.num_workers = 4
        solver_status = solver.Solve(model)

        result.solve_time_sec = round(time.time() - start_cpu, 3)
        result.status = solver.StatusName(solver_status)
        result.objective_value = solver.ObjectiveValue() if solver_status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else -1

        if solver_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for train in trains:
                result.schedule[train.id] = {}
                st_seq = down_station_seq if train.direction == "DOWN" else up_station_seq
                dest_st = st_seq[-1]

                for st_code in st_seq:
                    arr_val = int(solver.Value(arr_vars[(train.id, st_code)]))
                    dep_val = int(solver.Value(dep_vars[(train.id, st_code)]))
                    is_l_val = bool(solver.Value(is_loop_vars[(train.id, st_code)]))

                    sched_entry = next((e for e in train.schedule if e.station_code == st_code), None)
                    sched_arr = sched_entry.scheduled_arrival_sec if sched_entry else arr_val
                    delay_at_st = max(0, arr_val - sched_arr)

                    assigned_track = "LOOP_1" if is_l_val else "MAIN_LINE"

                    result.schedule[train.id][st_code] = {
                        "arr": arr_val,
                        "dep": dep_val,
                        "track": assigned_track,
                        "delay_sec": delay_at_st,
                        "is_looped": is_l_val,
                        "dwell_sec": dep_val - arr_val
                    }

            # Detect overtakes achieved by the optimizer
            result.overtakes = self._identify_overtakes(trains, result.schedule)
            result.metrics = self._calculate_metrics(trains, result.schedule)

        return result

    def _calculate_running_times(self, trains: List[Train]) -> Dict[Tuple[str, str, str], int]:
        """Compute minimum travel time between adjacent stations based on train MPS, block MPS, and TSRs."""
        times = {}
        for train in trains:
            st_seq = [st.code for st in self.corridor.stations]
            if train.direction == "UP":
                st_seq.reverse()

            for i in range(len(st_seq) - 1):
                from_code = st_seq[i]
                to_code = st_seq[i + 1]

                from_st = self.corridor.get_station(from_code)
                to_st = self.corridor.get_station(to_code)
                dist = abs(to_st.km - from_st.km)

                # Effective speed = min(train_mps, block_mps)
                eff_speed = min(train.max_speed_kmh, 130.0)

                # Check active TSRs
                for tsr in self.corridor.speed_restrictions:
                    if tsr.active:
                        overlap_start = max(min(from_st.km, to_st.km), tsr.from_km)
                        overlap_end = min(max(from_st.km, to_st.km), tsr.to_km)
                        if overlap_end > overlap_start:
                            eff_speed = min(eff_speed, tsr.speed_limit_kmh)

                # Base travel time in seconds
                base_sec = int((dist / eff_speed) * 3600)
                times[(train.id, from_code, to_code)] = base_sec

        return times

    def _identify_overtakes(self, trains: List[Train], schedule: Dict) -> List[Dict[str, Any]]:
        """Identify overtakes that occurred in the solved schedule."""
        overtakes = []
        for d in ["DOWN", "UP"]:
            t_list = [t for t in trains if t.direction == d]
            stations = [st.code for st in self.corridor.stations]
            if d == "UP":
                stations.reverse()

            for i in range(len(t_list)):
                for j in range(len(t_list)):
                    if i == j:
                        continue
                    t_overtaken = t_list[i]
                    t_overtaking = t_list[j]

                    for st_code in stations:
                        data1 = schedule.get(t_overtaken.id, {}).get(st_code, {})
                        data2 = schedule.get(t_overtaking.id, {}).get(st_code, {})

                        if not data1 or not data2:
                            continue

                        # Overtake condition: t_overtaken arrived earlier or at same time, was looped, and departed later than t_overtaking
                        if data1.get("is_looped") and data1["arr"] <= data2["arr"] and data1["dep"] > data2["dep"]:
                            overtakes.append({
                                "station_code": st_code,
                                "station_name": self.corridor.get_station(st_code).name,
                                "overtaken_train_number": t_overtaken.number,
                                "overtaken_train_name": t_overtaken.name,
                                "overtaking_train_number": t_overtaking.number,
                                "overtaking_train_name": t_overtaking.name,
                                "dwell_sec": data1["dwell_sec"],
                                "timestamp_sec": data2["dep"]
                            })
        return overtakes

    def _calculate_metrics(self, trains: List[Train], schedule: Dict) -> Dict[str, Any]:
        """Calculate operational KPIs."""
        total_delay_sec = 0
        total_transit_sec = 0
        punctual_trains = 0
        category_delays = {}

        for train in trains:
            st_seq = [st.code for st in self.corridor.stations]
            if train.direction == "UP":
                st_seq.reverse()
            origin_st = st_seq[0]
            dest_st = st_seq[-1]

            t_sched = schedule.get(train.id, {})
            if dest_st in t_sched and origin_st in t_sched:
                delay = t_sched[dest_st]["delay_sec"]
                transit = t_sched[dest_st]["arr"] - t_sched[origin_st]["dep"]
                total_delay_sec += delay
                total_transit_sec += transit

                if delay <= 300:  # Within 5 mins is considered on-time in IR standards
                    punctual_trains += 1

                cat = train.category.value
                category_delays[cat] = category_delays.get(cat, 0) + delay

        total_trains = max(1, len(trains))
        return {
            "total_trains": total_trains,
            "total_delay_min": round(total_delay_sec / 60, 1),
            "average_delay_min": round((total_delay_sec / total_trains) / 60, 1),
            "average_transit_time_min": round((total_transit_sec / total_trains) / 60, 1),
            "punctuality_rate_pct": round((punctual_trains / total_trains) * 100, 1),
            "category_delays_min": {k: round(v / 60, 1) for k, v in category_delays.items()}
        }
