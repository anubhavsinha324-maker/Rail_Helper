"""
RailOpt-IR: Application Runner Script
Launches the FastAPI Uvicorn web server.
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("  RailOpt-IR: Indian Railways AI Section Traffic Control & Dispatch")
    print("  Corridor: Ghaziabad (GZB) - Aligarh (ALJN) High Density Network")
    print("  Solver: Google OR-Tools CP-SAT (Constraint Programming)")
    print("  Server: http://127.0.0.1:8000")
    print("=" * 70)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
