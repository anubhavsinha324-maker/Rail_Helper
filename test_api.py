"""
API Smoke Test for RailOpt-IR FastAPI Endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app

def test_endpoints():
    client = TestClient(app)

    print("Testing GET / ...")
    r = client.get("/")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print("[OK] GET / returned HTML console")

    print("Testing GET /api/state ...")
    r = client.get("/api/state")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "corridor" in data
    assert "trains" in data
    assert "optimized" in data
    assert "advisories" in data
    print(f"[OK] GET /api/state returned {len(data['trains'])} trains, {len(data['advisories'])} advisories")

    print("Testing POST /api/optimize ...")
    r = client.post("/api/optimize")
    assert r.status_code == 200
    opt_data = r.json()
    assert opt_data["status"] in ("OPTIMAL", "FEASIBLE")
    print(f"[OK] POST /api/optimize status: {opt_data['status']} in {opt_data['solve_time_sec']}s")

    print("Testing POST /api/inject-delay ...")
    r = client.post("/api/inject-delay", json={"train_id": "TR_DN_SF_12418", "delay_sec": 900})
    assert r.status_code == 200
    print("[OK] POST /api/inject-delay successful")

    print("Testing POST /api/toggle-tsr ...")
    r = client.post("/api/toggle-tsr", json={"tsr_id": "TSR-01", "active": True})
    assert r.status_code == 200
    print("[OK] POST /api/toggle-tsr successful")

    print("Testing POST /api/toggle-signal-failure ...")
    r = client.post("/api/toggle-signal-failure", json={"signal_id": "SIG_DN_HOME_DKDE", "is_failed": True})
    assert r.status_code == 200
    print("[OK] POST /api/toggle-signal-failure successful")

    print("Testing POST /api/reset ...")
    r = client.post("/api/reset")
    assert r.status_code == 200
    print("[OK] POST /api/reset successful")

    print("\nAll API tests PASSED successfully!")

if __name__ == "__main__":
    test_endpoints()
