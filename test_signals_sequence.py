from app.simulation.simulator import CorridorSimulator
from app.simulation.corridor_data import build_ghaziabad_aligarh_corridor

corridor = build_ghaziabad_aligarh_corridor()
sim = CorridorSimulator()

down_sigs = [s for s in corridor.signals if s.direction.value == "DOWN"]
down_sigs.sort(key=lambda s: s.km)

print("First 5 DOWN signals:")
for i, s in enumerate(down_sigs[:5]):
    print(f"  S{i}: {s.id} ({s.name}) at km {s.km}")

print("\n--- Sequential Signal Test ---")
test_kms = [0.1, 0.4, 0.9, 2.7, 4.7]
for test_km in test_kms:
    pos = [{
        "train_id": "TEST",
        "train_number": "TEST_EXPRESS",
        "direction": "DOWN",
        "current_km": test_km,
        "status": "RUNNING",
        "track": "MAIN_LINE"
    }]
    res = sim.calculate_signals_state(pos, {})
    sig_map = {s["id"]: s["aspect"] for s in res}
    aspects = [f"S{i}({down_sigs[i].km}k)={sig_map[down_sigs[i].id]}" for i in range(5)]
    print(f"Train at km {test_km:4.1f} -> " + " | ".join(aspects))
