"""
Corridor Traffic Simulator & Dynamic Scenario Sandbox.
Maintains state, supports disruption injections (loco failure, TSR, delay),
calculates live train positions, block occupancy, and signal aspects.
"""

import copy
from typing import List, Dict, Any, Optional
from app.models.railway_network import CorridorSection, Direction, SignalAspect, SignalType
from app.models.train import Train, TrainCategory
from app.simulation.corridor_data import build_ghaziabad_aligarh_corridor, get_default_train_traffic
from app.engine.conflict_detector import ConflictDetector
from app.engine.cp_sat_solver import SectionDispatchOptimizer, SectionOptimizationResult
from app.engine.heuristic_baseline import BaselineDispatcher
from app.engine.explainability import DecisionExplainabilityEngine


class CorridorSimulator:
    def __init__(self):
        self.corridor: CorridorSection = build_ghaziabad_aligarh_corridor()
        self.trains: List[Train] = get_default_train_traffic()
        
        self.conflict_detector = ConflictDetector(self.corridor)
        self.optimizer = SectionDispatchOptimizer(self.corridor)
        self.baseline_dispatcher = BaselineDispatcher(self.corridor)
        self.explainability_engine = DecisionExplainabilityEngine(self.corridor)

        # Simulation clock in seconds from midnight (default 14:30:00 = 52200s)
        self.current_sim_time_sec: int = 52200

        # Cached results
        self.last_optimized_result: Optional[SectionOptimizationResult] = None
        self.last_baseline_result: Optional[Dict[str, Any]] = None
        
        # Run initial baseline & solve
        self.refresh()

    def refresh(self):
        """Run both baseline and optimization solver on current state."""
        self.last_baseline_result = self.baseline_dispatcher.simulate(self.trains)
        self.last_optimized_result = self.optimizer.solve(self.trains)

    def inject_train_delay(self, train_id: str, added_delay_sec: int) -> bool:
        """Inject unexpected delay (e.g. loco trouble, passenger alarm chain pull)."""
        for t in self.trains:
            if t.id == train_id:
                t.initial_delay_sec += added_delay_sec
                self.refresh()
                return True
        return False

    def toggle_speed_restriction(self, tsr_id: str, active: bool) -> bool:
        """Toggle a Temporary Speed Restriction (TSR / Caution Order)."""
        for tsr in self.corridor.speed_restrictions:
            if tsr.id == tsr_id:
                tsr.active = active
                self.refresh()
                return True
        return False

    def reset_to_defaults(self):
        """Reset scenario back to clean pristine state."""
        self.corridor = build_ghaziabad_aligarh_corridor()
        self.trains = get_default_train_traffic()
        self.refresh()

    def get_full_state(self) -> Dict[str, Any]:
        """Return complete state for dashboard rendering."""
        baseline_sched = self.last_baseline_result["schedule"] if self.last_baseline_result else {}
        baseline_metrics = self.last_baseline_result["metrics"] if self.last_baseline_result else {}

        opt_sched = self.last_optimized_result.schedule if self.last_optimized_result else {}
        opt_metrics = self.last_optimized_result.metrics if self.last_optimized_result else {}
        overtakes = self.last_optimized_result.overtakes if self.last_optimized_result else []

        # Detect conflicts in baseline vs optimized
        baseline_conflicts = [c.dict() for c in self.conflict_detector.detect_conflicts(self.trains, baseline_sched)]
        optimized_conflicts = [c.dict() for c in self.conflict_detector.detect_conflicts(self.trains, opt_sched)]

        # Advisories
        advisories = self.explainability_engine.generate_advisories(
            self.trains, opt_sched, overtakes, baseline_sched
        )
        comparative_summary = self.explainability_engine.generate_comparative_summary(
            baseline_metrics, opt_metrics
        )

        # Real-time train positions at current_sim_time_sec
        live_positions = self.calculate_live_train_positions(self.current_sim_time_sec, opt_sched)
        block_occupancies = self.calculate_block_occupancies(live_positions)
        signals_state = self.calculate_signals_state(live_positions, opt_sched)
        kavach_telemetry = self.calculate_kavach_telemetry(live_positions, signals_state)

        return {
            "corridor": {
                "name": self.corridor.name,
                "description": self.corridor.description,
                "total_km": self.corridor.total_km,
                "stations": [s.dict() for s in self.corridor.stations],
                "speed_restrictions": [sr.dict() for sr in self.corridor.speed_restrictions],
                "signals": [sig.dict() for sig in self.corridor.signals]
            },
            "trains": [t.dict() for t in self.trains],
            "current_sim_time_sec": self.current_sim_time_sec,
            "baseline": {
                "schedule": baseline_sched,
                "metrics": baseline_metrics,
                "conflicts": baseline_conflicts
            },
            "optimized": {
                "status": self.last_optimized_result.status if self.last_optimized_result else "UNKNOWN",
                "solve_time_sec": self.last_optimized_result.solve_time_sec if self.last_optimized_result else 0.0,
                "schedule": opt_sched,
                "metrics": opt_metrics,
                "overtakes": overtakes,
                "conflicts": optimized_conflicts
            },
            "advisories": advisories,
            "comparison": comparative_summary,
            "live_positions": live_positions,
            "block_occupancies": block_occupancies,
            "signals": signals_state,
            "kavach": kavach_telemetry
        }

    def calculate_live_train_positions(self, sim_time_sec: int, schedule: Dict) -> List[Dict[str, Any]]:
        """Compute the interpolated km position, current speed, and status of each train at sim_time_sec."""
        positions = []
        down_seq = [st.code for st in self.corridor.stations]
        up_seq = list(reversed(down_seq))

        for train in self.trains:
            st_seq = down_seq if train.direction == "DOWN" else up_seq
            t_sched = schedule.get(train.id, {})
            if not t_sched:
                continue

            origin_st = st_seq[0]
            dest_st = st_seq[-1]

            origin_dep = t_sched[origin_st]["dep"]
            dest_arr = t_sched[dest_st]["arr"]

            if sim_time_sec < origin_dep:
                status = "NOT_ENTERED"
                km = self.corridor.get_station(origin_st).km
                speed = 0.0
                track = "YARD"
            elif sim_time_sec >= dest_arr:
                status = "CLEARED_SECTION"
                km = self.corridor.get_station(dest_st).km
                speed = 0.0
                track = "TERMINAL"
            else:
                # Train is actively in the section
                status = "RUNNING"
                km = 0.0
                speed = train.max_speed_kmh
                track = "MAIN_LINE"

                # Find which segment or station the train is currently in
                for idx in range(len(st_seq) - 1):
                    s1 = st_seq[idx]
                    s2 = st_seq[idx + 1]

                    s1_arr = t_sched[s1]["arr"]
                    s1_dep = t_sched[s1]["dep"]
                    s2_arr = t_sched[s2]["arr"]

                    st1_km = self.corridor.get_station(s1).km
                    st2_km = self.corridor.get_station(s2).km

                    # 1. Is train dwelling at station s1?
                    if s1_arr <= sim_time_sec <= s1_dep:
                        status = "DWELLING_AT_STATION" if t_sched[s1]["dwell_sec"] > 0 else "RUNNING"
                        km = st1_km
                        speed = 0.0
                        track = t_sched[s1]["track"]
                        break
                    # 2. Is train travelling between s1 and s2?
                    elif s1_dep < sim_time_sec < s2_arr:
                        progress = (sim_time_sec - s1_dep) / max(1, s2_arr - s1_dep)
                        km = round(st1_km + progress * (st2_km - st1_km), 2)
                        speed = round(abs(st2_km - st1_km) / ((s2_arr - s1_dep) / 3600), 1)
                        track = "BLOCK_SECTION"
                        break

            positions.append({
                "train_id": train.id,
                "train_number": train.number,
                "train_name": train.name,
                "category": train.category.value,
                "direction": train.direction,
                "current_km": km,
                "current_speed_kmh": speed,
                "length_meters": train.length_meters,
                "status": status,
                "track": track,
                "color_hex": train.color_hex,
                "priority_weight": train.priority_weight
            })

        return positions

    def toggle_signal_failure(self, signal_id: str, is_failed: bool) -> bool:
        """Toggle fail-safe red clamp on a specific signal (simulates track circuit fault)."""
        for sig in self.corridor.signals:
            if sig.id == signal_id:
                sig.is_failed = is_failed
                self.refresh()
                return True
        return False

    def calculate_signals_state(self, live_positions: List[Dict[str, Any]], schedule: Dict) -> List[Dict[str, Any]]:
        """
        Dynamically calculate signal aspects according to Indian Railways Block Working:
        - When a train crosses signal Sk: Sk turns RED.
        - Previous signal Sk-1 turns YELLOW.
        - Two signals behind Sk-2 and earlier turn GREEN.
        """
        signals_out = []
        aspect_priority = {
            SignalAspect.RED: 3,
            SignalAspect.YELLOW: 2,
            SignalAspect.GREEN: 1
        }

        def apply_aspect(aspect_dict, sig_id, new_aspect):
            current = aspect_dict.get(sig_id, SignalAspect.GREEN)
            if aspect_priority[new_aspect] > aspect_priority[current]:
                aspect_dict[sig_id] = new_aspect

        # Process DOWN and UP directions separately
        for dir_enum, dir_str in [(Direction.DOWN, "DOWN"), (Direction.UP, "UP")]:
            dir_signals = [s for s in self.corridor.signals if s.direction == dir_enum]
            # DOWN sorted ascending by km; UP sorted descending by km
            dir_signals.sort(key=lambda s: s.km if dir_enum == Direction.DOWN else -s.km)

            # Active trains in this direction
            active_trains = [
                p for p in live_positions 
                if p["direction"] == dir_str and p["status"] in ("RUNNING", "DWELLING_AT_STATION")
            ]

            # Default all signals in this direction to GREEN (all clear ahead)
            aspect_map = {s.id: SignalAspect.GREEN for s in dir_signals}
            feather_map = {s.id: False for s in dir_signals}

            # For each active train, set RED at crossed signal and YELLOW at previous signal
            for tr in active_trains:
                tr_km = tr["current_km"]
                is_dwelling_in_loop = tr["status"] == "DWELLING_AT_STATION" and "LOOP" in tr.get("track", "")

                # Find the signal directly crossed by train front
                controlled_sig_idx = -1
                for idx, sig in enumerate(dir_signals):
                    if dir_enum == Direction.DOWN and sig.km <= tr_km:
                        controlled_sig_idx = idx
                    elif dir_enum == Direction.UP and sig.km >= tr_km:
                        controlled_sig_idx = idx

                if controlled_sig_idx >= 0:
                    sig_0 = dir_signals[controlled_sig_idx]

                    if is_dwelling_in_loop:
                        # Train is clear of the main line; station loop starter holds it at RED
                        for sig in dir_signals:
                            if sig.signal_type == SignalType.STARTER and sig.station_code and sig.station_code in tr.get("track", ""):
                                apply_aspect(aspect_map, sig.id, SignalAspect.RED)
                    else:
                        # 1. Crossed signal Sk snaps to RED
                        apply_aspect(aspect_map, sig_0.id, SignalAspect.RED)

                        # 2. Previous signal Sk-1 turns YELLOW
                        if controlled_sig_idx - 1 >= 0:
                            apply_aspect(aspect_map, dir_signals[controlled_sig_idx - 1].id, SignalAspect.YELLOW)

                        # Signals controlled_sig_idx - 2 and earlier remain GREEN by default!

                # Check Home Signal Route Feather for station approach
                for s_idx, sig in enumerate(dir_signals):
                    if sig.signal_type == SignalType.HOME and sig.station_code:
                        st_code = sig.station_code
                        dist_to_home = (sig.km - tr_km) if dir_enum == Direction.DOWN else (tr_km - sig.km)
                        if 0.0 < dist_to_home <= 3.0:
                            t_sched = schedule.get(tr["train_id"], {}).get(st_code, {})
                            if t_sched.get("is_looped", False) or "LOOP" in t_sched.get("track", ""):
                                # Route set to Loop Line!
                                feather_map[sig.id] = True
                                apply_aspect(aspect_map, sig.id, SignalAspect.YELLOW)

            # Build signal output records
            for s in dir_signals:
                final_aspect = SignalAspect.RED if s.is_failed else aspect_map[s.id]
                signals_out.append({
                    "id": s.id,
                    "name": s.name,
                    "km": s.km,
                    "direction": s.direction.value,
                    "signal_type": s.signal_type.value,
                    "aspect": final_aspect.value,
                    "route_feather_active": False if s.is_failed else feather_map[s.id],
                    "is_failed": s.is_failed,
                    "station_code": s.station_code
                })

        return signals_out

    def calculate_kavach_telemetry(self, live_positions: List[Dict[str, Any]], signals_state: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compute real-time KAVACH (TCAS - Train Collision Avoidance System) in-cab telemetry
        for active trains (Cab signal repeater, Movement Authority, and Target Distance).
        """
        kavach_list = []
        sig_map = {s["id"]: s for s in signals_state}

        for p in live_positions:
            if p["status"] not in ("RUNNING", "DWELLING_AT_STATION"):
                continue

            tr_km = p["current_km"]
            is_down = p["direction"] == "DOWN"

            # Find next signal ahead of this train
            ahead_signals = [
                s for s in signals_state 
                if s["direction"] == p["direction"] and ((s["km"] > tr_km) if is_down else (s["km"] < tr_km))
            ]
            if is_down:
                ahead_signals.sort(key=lambda s: s["km"])
            else:
                ahead_signals.sort(key=lambda s: -s["km"])

            if ahead_signals:
                target_sig = ahead_signals[0]
                dist_meters = round(abs(target_sig["km"] - tr_km) * 1000, 0)
                aspect = target_sig["aspect"]

                # Movement Authority (MA) in meters based on aspect
                if aspect == "GREEN":
                    ma_meters = dist_meters + 3600  # 3 clear blocks
                    perm_speed = p["priority_weight"] >= 90 and 130.0 or 110.0
                elif aspect == "DOUBLE_YELLOW":
                    ma_meters = dist_meters + 1800  # 2 clear blocks
                    perm_speed = 75.0
                elif aspect == "YELLOW":
                    ma_meters = dist_meters         # 1 clear block
                    perm_speed = 30.0
                else:  # RED
                    ma_meters = 0
                    perm_speed = 0.0

                # SPAD protection status
                if aspect == "RED" and dist_meters < 200 and p["current_speed_kmh"] > 0:
                    spad_alert = "EMERGENCY_BRAKE"
                elif p["current_speed_kmh"] > perm_speed + 5:
                    spad_alert = "OVERSPEED_WARNING"
                else:
                    spad_alert = "NORMAL"

                kavach_list.append({
                    "train_id": p["train_id"],
                    "train_number": p["train_number"],
                    "train_name": p["train_name"],
                    "direction": p["direction"],
                    "current_km": tr_km,
                    "current_speed_kmh": p["current_speed_kmh"],
                    "target_signal_name": target_sig["name"],
                    "target_signal_aspect": aspect,
                    "target_signal_distance_m": dist_meters,
                    "movement_authority_m": ma_meters,
                    "permitted_speed_kmh": perm_speed,
                    "spad_alert": spad_alert,
                    "route_feather": target_sig["route_feather_active"]
                })

        return kavach_list

    def calculate_block_occupancies(self, live_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determine track block occupancies and calculate signal aspects."""
        occupancies = {}
        for block in self.corridor.block_sections:
            from_st = self.corridor.get_station(block.from_station_code)
            to_st = self.corridor.get_station(block.to_station_code)
            min_km = min(from_st.km, to_st.km)
            max_km = max(from_st.km, to_st.km)

            trains_in_block = [
                p for p in live_positions 
                if p["direction"] == block.direction.value 
                and min_km <= p["current_km"] <= max_km
                and p["status"] == "RUNNING"
            ]

            is_occupied = len(trains_in_block) > 0
            signal_aspect = "RED" if is_occupied else "GREEN"

            occupancies[block.id] = {
                "block_id": block.id,
                "direction": block.direction.value,
                "is_occupied": is_occupied,
                "train_count": len(trains_in_block),
                "occupant_trains": [t["train_number"] for t in trains_in_block],
                "signal_aspect": signal_aspect
            }

        return occupancies

