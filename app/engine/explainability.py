"""
Explainability & Decision Support Module for Indian Railways Section Controllers.
Translates mathematical solver outputs into clear, professional Indian Railways Control Advisories.
Generates comparative KPI analytics (Baseline vs AI Optimized).
"""

from typing import List, Dict, Any
from app.models.railway_network import CorridorSection
from app.models.train import Train, TrainCategory


class DispatchAdvisory:
    def __init__(self, advisory_id: str, priority_level: str, station_code: str, station_name: str, 
                 train_number: str, train_name: str, action_type: str, action_summary: str, 
                 detailed_rationale: str, impact_kpi: str):
        self.advisory_id = advisory_id
        self.priority_level = priority_level
        self.station_code = station_code
        self.station_name = station_name
        self.train_number = train_number
        self.train_name = train_name
        self.action_type = action_type
        self.action_summary = action_summary
        self.detailed_rationale = detailed_rationale
        self.impact_kpi = impact_kpi

    def to_dict(self) -> Dict[str, Any]:
        return {
            "advisory_id": self.advisory_id,
            "priority_level": self.priority_level,
            "station_code": self.station_code,
            "station_name": self.station_name,
            "train_number": self.train_number,
            "train_name": self.train_name,
            "action_type": self.action_type,
            "action_summary": self.action_summary,
            "detailed_rationale": self.detailed_rationale,
            "impact_kpi": self.impact_kpi,
        }


class DecisionExplainabilityEngine:
    def __init__(self, corridor: CorridorSection):
        self.corridor = corridor

    def generate_advisories(self, trains: List[Train], optimized_schedule: Dict, 
                            overtakes: List[Dict], baseline_schedule: Dict) -> List[Dict[str, Any]]:
        """
        Generate operational recommendations for the Section Controller.
        """
        advisories: List[Dict[str, Any]] = []
        adv_id = 1

        # 1. Advisories for overtakes and loop line diversions
        for ot in overtakes:
            st_code = ot["station_code"]
            st_name = ot["station_name"]
            slow_train_num = ot["overtaken_train_number"]
            slow_train_name = ot["overtaken_train_name"]
            fast_train_num = ot["overtaking_train_number"]
            fast_train_name = ot["overtaking_train_name"]
            dwell_mins = round(ot["dwell_sec"] / 60, 1)

            # Find fast train delay in baseline vs optimized
            fast_train = next((t for t in trains if t.number == fast_train_num), None)
            dest_st = "ALJN" if fast_train and fast_train.direction == "DOWN" else "GZB"

            base_delay = baseline_schedule.get(fast_train.id, {}).get(dest_st, {}).get("delay_sec", 0) if fast_train else 0
            opt_delay = optimized_schedule.get(fast_train.id, {}).get(dest_st, {}).get("delay_sec", 0) if fast_train else 0
            delay_saved_mins = max(0, round((base_delay - opt_delay) / 60, 1))

            adv = DispatchAdvisory(
                advisory_id=f"ADV-{adv_id:03d}",
                priority_level="CRITICAL",
                station_code=st_code,
                station_name=st_name,
                train_number=slow_train_num,
                train_name=slow_train_name,
                action_type="LOOP_DIVERSION",
                action_summary=f"Divert {slow_train_num} to Loop 1 at {st_name}. Hold for ~{dwell_mins} min.",
                detailed_rationale=(
                    f"Prioritize Flagship/Superfast {fast_train_num} ({fast_train_name}). "
                    f"Holding lower-priority train {slow_train_num} in the loop line clears the Main Line "
                    f"for 130 km/h unobstructed run under green ABS aspects."
                ),
                impact_kpi=f"Saves ~{delay_saved_mins} mins delay for {fast_train_num} and maintains section throughput."
            )
            advisories.append(adv.to_dict())
            adv_id += 1

        # 2. Advisories for through-running green wave for high priority trains
        for t in trains:
            if t.category in (TrainCategory.VANDE_BHARAT, TrainCategory.RAJDHANI):
                adv = DispatchAdvisory(
                    advisory_id=f"ADV-{adv_id:03d}",
                    priority_level="HIGH",
                    station_code="CORRIDOR",
                    station_name="Entire Section",
                    train_number=t.number,
                    train_name=t.name,
                    action_type="GREEN_CORRIDOR",
                    action_summary=f"Maintain uninterrupted Main Line green wave for {t.name} ({t.number}).",
                    detailed_rationale=(
                        f"Train {t.number} is a Priority 1 service (Weight {t.priority_weight}). "
                        f"All station approaches must maintain Route Set & Signal Off at least 4 automatic blocks in advance."
                    ),
                    impact_kpi="100% Section Punctuality & Zero Knocks-on."
                )
                advisories.append(adv.to_dict())
                adv_id += 1

        return advisories

    def generate_comparative_summary(self, baseline_metrics: Dict, optimized_metrics: Dict) -> Dict[str, Any]:
        """Generate high-level comparison between Baseline and AI Optimized dispatching."""
        base_delay = baseline_metrics.get("total_delay_min", 0)
        opt_delay = optimized_metrics.get("total_delay_min", 0)
        delay_saved = max(0, round(base_delay - opt_delay, 1))
        reduction_pct = round(((base_delay - opt_delay) / max(1, base_delay)) * 100, 1) if base_delay > 0 else 0

        base_punc = baseline_metrics.get("punctuality_rate_pct", 0)
        opt_punc = optimized_metrics.get("punctuality_rate_pct", 0)

        return {
            "baseline_total_delay_min": base_delay,
            "optimized_total_delay_min": opt_delay,
            "delay_saved_min": delay_saved,
            "delay_reduction_pct": reduction_pct,
            "baseline_punctuality_pct": base_punc,
            "optimized_punctuality_pct": opt_punc,
            "punctuality_gain_pct": round(opt_punc - base_punc, 1),
            "baseline_avg_delay_min": baseline_metrics.get("average_delay_min", 0),
            "optimized_avg_delay_min": optimized_metrics.get("average_delay_min", 0),
            "baseline_avg_transit_min": baseline_metrics.get("average_transit_time_min", 0),
            "optimized_avg_transit_min": optimized_metrics.get("average_transit_time_min", 0)
        }
