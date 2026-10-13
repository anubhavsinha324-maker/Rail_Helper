"""
Baseline / First-Come-First-Served (FCFS) Dispatcher Simulator.
Simulates conventional manual / reactive section control without predictive optimization:
- Dispatches trains in arrival sequence.
- Fast trains follow slow freight trains without timely loop line overtakes,
  accumulating knock-on delays at automatic block signals.
Used as the benchmark against the CP-SAT AI optimizer.
"""

from typing import List, Dict, Any, Tuple
from app.models.railway_network import CorridorSection, Direction
from app.models.train import Train, TrainCategory


class BaselineDispatcher:
    def __init__(self, corridor: CorridorSection):
        self.corridor = corridor

    def simulate(self, trains: List[Train]) -> Dict[str, Any]:
        """
        Simulate train movements under standard First-Come-First-Served dispatching.
        Returns schedule dictionary, metrics, and conflicts encountered.
        """
        HEADWAY_SEC = 150
        schedule: Dict[str, Dict[str, Dict[str, Any]]] = {}

        down_station_seq = [st.code for st in self.corridor.stations]
        up_station_seq = list(reversed(down_station_seq))

        # Separate by direction and sort by scheduled entry time into the section
        for dir_name in ["DOWN", "UP"]:
            t_list = [t for t in trains if t.direction == dir_name]
            st_seq = down_station_seq if dir_name == "DOWN" else up_station_seq
            origin_st = st_seq[0]

            def get_entry_time(tr: Train) -> int:
                entry = next(e for e in tr.schedule if e.station_code == origin_st)
                return entry.scheduled_departure_sec + tr.initial_delay_sec

            t_list.sort(key=get_entry_time)

            # Track last departure from each station to enforce headway
            last_dep: Dict[str, int] = {st: 0 for st in st_seq}
            last_arr: Dict[str, int] = {st: 0 for st in st_seq}

            for tr in t_list:
                schedule[tr.id] = {}
                for idx, st_code in enumerate(st_seq):
                    sched_entry = next((e for e in tr.schedule if e.station_code == st_code), None)
                    min_dwell = sched_entry.min_dwell_sec if (sched_entry and sched_entry.is_commercial_stop) else 0

                    if idx == 0:
                        # Entry station
                        earliest_dep = get_entry_time(tr)
                        actual_dep = max(earliest_dep, last_dep[st_code] + HEADWAY_SEC)
                        actual_arr = actual_dep - min_dwell

                        schedule[tr.id][st_code] = {
                            "arr": actual_arr,
                            "dep": actual_dep,
                            "track": "MAIN_LINE",
                            "delay_sec": max(0, actual_arr - (sched_entry.scheduled_arrival_sec if sched_entry else earliest_dep)),
                            "is_looped": False,
                            "dwell_sec": min_dwell
                        }
                        last_dep[st_code] = actual_dep
                        last_arr[st_code] = actual_arr
                    else:
                        prev_st = st_seq[idx - 1]
                        prev_dep = schedule[tr.id][prev_st]["dep"]

                        # Calculate running time between prev_st and st_code
                        st1 = self.corridor.get_station(prev_st)
                        st2 = self.corridor.get_station(st_code)
                        dist = abs(st2.km - st1.km)
                        eff_speed = min(tr.max_speed_kmh, 130.0)

                        for tsr in self.corridor.speed_restrictions:
                            if tsr.active:
                                overlap_start = max(min(st1.km, st2.km), tsr.from_km)
                                overlap_end = min(max(st1.km, st2.km), tsr.to_km)
                                if overlap_end > overlap_start:
                                    eff_speed = min(eff_speed, tsr.speed_limit_kmh)

                        run_time_sec = int((dist / eff_speed) * 3600)
                        earliest_arr = prev_dep + run_time_sec

                        # In FCFS, train cannot arrive closer than HEADWAY_SEC to the preceding train
                        actual_arr = max(earliest_arr, last_arr[st_code] + HEADWAY_SEC)
                        actual_dep = max(actual_arr + min_dwell, last_dep[st_code] + HEADWAY_SEC)

                        sched_arr = sched_entry.scheduled_arrival_sec if sched_entry else actual_arr
                        delay = max(0, actual_arr - sched_arr)

                        schedule[tr.id][st_code] = {
                            "arr": actual_arr,
                            "dep": actual_dep,
                            "track": "MAIN_LINE",
                            "delay_sec": delay,
                            "is_looped": False,
                            "dwell_sec": actual_dep - actual_arr
                        }

                        last_arr[st_code] = actual_arr
                        last_dep[st_code] = actual_dep

        # Compute metrics
        metrics = self._calculate_metrics(trains, schedule)
        return {
            "schedule": schedule,
            "metrics": metrics
        }

    def _calculate_metrics(self, trains: List[Train], schedule: Dict) -> Dict[str, Any]:
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

                if delay <= 300:
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
