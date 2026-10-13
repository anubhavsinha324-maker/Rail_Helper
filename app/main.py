"""
RailOpt-IR: Indian Railways AI Section Traffic Control & Dispatch Optimization System
FastAPI Backend Server & Real-time Section Controller API.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.models.train import TrainCategory
from app.simulation.simulator import CorridorSimulator

app = FastAPI(
    title="RailOpt-IR: Indian Railways Section Traffic Optimization",
    description="Real-Time Decision Support System for Indian Railways Section Controllers using Google OR-Tools CP-SAT",
    version="1.0.0"
)

# Disable caching for all responses so browser always gets the latest code immediately
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Initialize corridor simulator instance
simulator = CorridorSimulator()

# Serve static frontend assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/state")
def get_state():
    """Retrieve complete section status, schedules, KPIs, and advisories."""
    return simulator.get_full_state()


@app.post("/api/optimize")
def run_optimization():
    """Trigger Google OR-Tools CP-SAT optimization on the corridor."""
    simulator.refresh()
    return {
        "status": simulator.last_optimized_result.status if simulator.last_optimized_result else "UNKNOWN",
        "solve_time_sec": simulator.last_optimized_result.solve_time_sec if simulator.last_optimized_result else 0.0,
        "metrics": simulator.last_optimized_result.metrics if simulator.last_optimized_result else {},
        "overtakes_count": len(simulator.last_optimized_result.overtakes) if simulator.last_optimized_result else 0,
        "comparison": simulator.get_full_state()["comparison"]
    }


class AddTrainRequest(BaseModel):
    number: str
    name: str
    category: TrainCategory
    direction: str
    start_time: str
    stopping_stations: List[str] = []


@app.post("/api/add-train")
def add_train_endpoint(req: AddTrainRequest):
    """Dynamically schedule and insert a new train into the corridor."""
    try:
        new_train = simulator.add_train(
            number=req.number,
            name=req.name,
            category=req.category,
            direction=req.direction,
            start_time_str=req.start_time,
            stopping_stations=req.stopping_stations
        )
        return {
            "success": True,
            "message": f"Train {new_train.number} ({new_train.name}) added and corridor re-optimized!",
            "train": new_train.dict(),
            "full_state": simulator.get_full_state()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class DelayInjectionRequest(BaseModel):
    train_id: str
    delay_sec: int


@app.post("/api/inject-delay")
def inject_delay(req: DelayInjectionRequest):
    """Simulate an upstream or unexpected delay for a specific train."""
    success = simulator.inject_train_delay(req.train_id, req.delay_sec)
    if not success:
        raise HTTPException(status_code=404, detail="Train not found")
    return {"success": True, "message": f"Injected {req.delay_sec}s delay into {req.train_id}"}


class TSRToggleRequest(BaseModel):
    tsr_id: str
    active: bool


@app.post("/api/toggle-tsr")
def toggle_tsr(req: TSRToggleRequest):
    """Activate or deactivate a Temporary Speed Restriction (Caution Order)."""
    success = simulator.toggle_speed_restriction(req.tsr_id, req.active)
    if not success:
        raise HTTPException(status_code=404, detail="TSR not found")
    return {"success": True, "message": f"TSR {req.tsr_id} active set to {req.active}"}


class SignalFailureRequest(BaseModel):
    signal_id: str
    is_failed: bool


@app.post("/api/toggle-signal-failure")
def toggle_signal_failure(req: SignalFailureRequest):
    """Simulate a red clamp / track circuit failure on an automatic or station signal."""
    success = simulator.toggle_signal_failure(req.signal_id, req.is_failed)
    if not success:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"success": True, "message": f"Signal {req.signal_id} is_failed set to {req.is_failed}"}


class ClockRequest(BaseModel):
    time_sec: int


@app.post("/api/set-clock")
def set_clock(req: ClockRequest):
    """Update current simulation time (seconds from midnight)."""
    simulator.current_sim_time_sec = req.time_sec
    return {"success": True, "sim_time_sec": simulator.current_sim_time_sec}


@app.post("/api/reset")
def reset_simulation():
    """Reset simulation to initial baseline scenario."""
    simulator.reset_to_defaults()
    return {"success": True, "message": "Corridor scenario reset to initial state"}
