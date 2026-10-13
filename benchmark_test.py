"""
Benchmark Test Suite for RailOpt-IR.
Compares Google OR-Tools CP-SAT against Baseline First-Come-First-Served (FCFS)
under 3 operational scenarios:
1. Standard High-Density Mixed Traffic
2. Heavy Injected Delay on Express Train (+25 mins)
3. Temporary Speed Restriction (TSR: 45 km/h Caution Order)
"""

import time
from app.simulation.corridor_data import build_ghaziabad_aligarh_corridor, get_default_train_traffic
from app.engine.cp_sat_solver import SectionDispatchOptimizer
from app.engine.heuristic_baseline import BaselineDispatcher
from app.engine.conflict_detector import ConflictDetector
from app.engine.explainability import DecisionExplainabilityEngine


def run_benchmark():
    print("=" * 80)
    print(" RAILOPT-IR: ALGORITHMIC BENCHMARK & EVALUATION SUITE")
    print(" Section: Ghaziabad (GZB) to Aligarh (ALJN) - 106 km Double Line ABS")
    print("=" * 80)

    scenarios = [
        ("Scenario 1: Standard High-Density Peak Traffic", 0, False),
        ("Scenario 2: Disruption - Injected +25m Loco Delay on 12418 Prayagraj Exp", 1500, False),
        ("Scenario 3: Severe TSR - 45 km/h Caution Order between Km 48 & 52", 0, True),
    ]

    for title, added_delay_sec, enable_tsr in scenarios:
        print(f"\n--- {title} ---")
        corridor = build_ghaziabad_aligarh_corridor()
        trains = get_default_train_traffic()

        if added_delay_sec > 0:
            target = next(t for t in trains if t.number == "12418")
            target.initial_delay_sec += added_delay_sec

        if enable_tsr:
            tsr = next(s for s in corridor.speed_restrictions if s.id == "TSR-01")
            tsr.active = True

        optimizer = SectionDispatchOptimizer(corridor)
        baseline = BaselineDispatcher(corridor)
        explainer = DecisionExplainabilityEngine(corridor)
        detector = ConflictDetector(corridor)

        # 1. Run Baseline (FCFS)
        t0 = time.time()
        base_res = baseline.simulate(trains)
        base_time = round((time.time() - t0) * 1000, 2)
        base_metrics = base_res["metrics"]

        # 2. Run OR-Tools CP-SAT
        t1 = time.time()
        opt_res = optimizer.solve(trains)
        opt_time = round((time.time() - t1) * 1000, 2)
        opt_metrics = opt_res.metrics

        summary = explainer.generate_comparative_summary(base_metrics, opt_metrics)

        print(f"  [Baseline FCFS] Total Delay: {base_metrics['total_delay_min']} min | Punctuality: {base_metrics['punctuality_rate_pct']}% | Runtime: {base_time} ms")
        print(f"  [AI CP-SAT]     Total Delay: {opt_metrics['total_delay_min']} min | Punctuality: {opt_metrics['punctuality_rate_pct']}% | Runtime: {opt_time} ms")
        print(f"  >> PERFORMANCE GAIN:")
        print(f"     * Net Delay Saved:      {summary['delay_saved_min']} minutes (-{summary['delay_reduction_pct']}%)")
        print(f"     * Punctuality Boost:    +{summary['punctuality_gain_pct']}% improvement")
        print(f"     * Overtakes Executed:   {len(opt_res.overtakes)} dynamic loop overtakes")
        for ot in opt_res.overtakes:
            print(f"       -> Train {ot['overtaken_train_number']} ({ot['overtaken_train_name'][:18]}) looped at {ot['station_name']} for {ot['overtaking_train_number']} ({ot['overtaking_train_name'][:18]})")

    print("\n" + "=" * 80)
    print(" ALL BENCHMARK SCENARIOS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
