# RailOpt-IR: Indian Railways Section Traffic & Signaling Control Optimization System

**RailOpt-IR** is an intelligent, real-time decision support system designed specifically for **Indian Railways (IR) Section Controllers**. It optimizes section throughput, manages train priority hierarchies, resolves track and block conflicts, minimizes cumulative transit delays, and simulates real-world **Multi-Aspect Colour Light Signaling (MACLS 4-Aspect)** and **KAVACH (TCAS)** Automatic Train Protection on high-density corridors using **Google OR-Tools CP-SAT (Constraint Programming)**.

---

## 1. Operational Problem in Indian Railways

Indian Railways operates one of the most congested and heterogeneous mixed-traffic railway networks in the world. On key trunk sections (such as High Density Network **HDN-1: Delhi–Kanpur–Howrah**):

1. **Heterogeneous Traffic Mix**:
   - **Premium Flagship**: Vande Bharat Express & Tejas (MPS: 130–160 km/h, high acceleration EMU)
   - **Premium Long-Distance**: Rajdhani & Shatabdi Express (MPS: 130 km/h)
   - **Superfast / Mail Express**: Prayagraj Express, Purushottam Express (MPS: 110 km/h)
   - **Suburban / Commuter**: MEMU & Passenger trains (MPS: 80–90 km/h, halts at all stations)
   - **Freight**: Heavy Haul Bulk Coal (BOXN) and Container rakes (MPS: 60–75 km/h, slow acceleration)

2. **The Dispatcher Bottleneck**:
   - Section Controllers monitor 100–150 km of track and manually make split-second decisions on precedence, crossings, and loop line berthing.
   - Under naive or manual **First-Come-First-Served (FCFS)** dispatching, when a slow 60 km/h goods train enters a section ahead of a 130 km/h Vande Bharat, the fast train gets trapped behind the freight at yellow/red automatic block signals, suffering 35–45 minutes of delay.
   - **RailOpt-IR** eliminates this guesswork by predicting conflicts up to 2 hours ahead and calculating mathematically optimal loop-line overtakes in milliseconds.

---

## 2. Indian Railways Signaling Systems (MACLS & KAVACH)

### Multi-Aspect Colour Light Signaling (MACLS 4-Aspect ABS)
In Automatic Block Signaling territory, signals automatically drop to danger behind a train and cascade aspects backwards to provide speed warnings:
- 🟢 **GREEN (Clear)**: Run at Section MPS (130 km/h). At least 2 block sections ahead are clear.
- 🟡🟡 **DOUBLE YELLOW (Attention)**: Prepare to pass next signal at restricted speed (60–75 km/h) or entering loop turnout.
- 🟡 **YELLOW (Caution)**: Exactly 1 block clear ahead. Prepare to stop at next signal (max 30 km/h on approach).
- 🔴 **RED (Danger / Stop)**: Block section occupied. Absolute stop before signal.

### Station Interlocking & Route Indicator Feathers
- At station approaches, Home Signals feature illuminated **white directional feathers** (5 angled lamps).
- When the AI optimizer diverts a train into a loop siding (e.g. for an overtake at Dankaur or Khurja), the Home Signal displays **Yellow + Illuminated Route Feather**, enforcing 30 km/h turnout speed restrictions.
- When set for through main line passage, the signal displays **Green** without feather.

### KAVACH (TCAS - Train Collision Avoidance System)
- Replicates the in-cab Driver Machine Interface (DMI) for the loco pilot:
  - **In-Cab Signal Aspect**: Continuous cab signaling repeating the trackside signal ahead.
  - **Movement Authority (MA)**: Dynamically calculated braking envelope in meters.
  - **Speed Supervision Curve**: Displays actual speed vs ceiling permitted speed curve.
  - **SPAD (Signal Passed at Danger) Protection**: Intervenes with automatic emergency braking if speed exceeds authority.

---

## 3. Mathematical Optimization Core (Google OR-Tools CP-SAT)

The core optimization engine is formulated as a disjunctive resource-constrained scheduling problem:

### Decision Variables:
- $A_{t, s} \in [0, T_{max}]$: Integer arrival time of train $t$ at station $s$ (seconds).
- $D_{t, s} \in [0, T_{max}]$: Integer departure time of train $t$ at station $s$ (seconds).
- $R_{t, s} \in \{0, 1\}$: Binary track choice variable ($0 = \text{Main Line Through}$, $1 = \text{Loop Line Siding}$).
- $P_{t_1, t_2, s} \in \{0, 1\}$: Precedence ordering between train pair $(t_1, t_2)$ on section $s$.

### Constraints:
1. **Running Times & Turnout Penalties**:
   $$A_{t, s+1} \ge D_{t, s} + T_{run}(t, s \to s+1) + R_{t, s+1} \cdot T_{turnout}$$
   where $T_{turnout} \approx 90\text{s}$ accounts for deceleration and acceleration over 1-in-12 turnouts (30 km/h speed restriction).

2. **Station Dwell & Passenger Halts**:
   $$D_{t, s} - A_{t, s} \ge \text{MinDwell}_{t, s}$$
   If train $t$ has no commercial stop and uses the Main Line ($R_{t, s} = 0$), $D_{t, s} = A_{t, s}$ (non-stop through run). If diverted to a Loop Line ($R_{t, s} = 1$), it may dwell to permit an overtake.

3. **Safe Automatic Block Signaling (ABS) Headway**:
   If train $t_1$ departs before $t_2$:
   $$D_{t_2, s} - D_{t_1, s} \ge H_{min} \quad (150\text{ seconds})$$
   $$A_{t_2, s+1} - A_{t_1, s+1} \ge H_{min} \quad (150\text{ seconds})$$

4. **FIFO Preservation on Main Line Sections**:
   $$P_{t_1, t_2, s+1} = P_{t_1, t_2, s}$$
   Overtaking in the middle of a double-line block section without a loop is physically prohibited. Overtaking occurs if and only if the slower train is placed on a station loop line ($R_{t_1, s} = 1$).

5. **Loop Line Capacity (Non-Overlap)**:
   For any station $s$, each loop track has capacity 1:
   $$\text{NoOverlap}\left( \left[ A_{t, s}, D_{t, s} \right] \text{ where } R_{t, s} = 1 \right)$$

6. **Objective Function (Priority-Weighted Penalty Minimization)**:
   $$\min \sum_{t} \left[ W_t \cdot \max(0, A_{t, \text{dest}} - \text{SchedArr}_{t, \text{dest}}) + \sum_{s} \left( 300 \cdot R_{t, s} + 2 \cdot (D_{t, s} - A_{t, s}) \right) \right]$$
   where $W_t$ is the Railway Board Priority Weight:
   - Vande Bharat: $W = 120$
   - Rajdhani: $W = 100$
   - Superfast Express: $W = 70$
   - Passenger / MEMU: $W = 45$
   - Container Freight (CONCOR): $W = 30$
   - Bulk Coal Freight (BOXN): $W = 15$

---

## 4. Benchmark Performance & Evaluation

Running `python benchmark_test.py` produces the following quantitative comparison across real-world scenarios:

| Metric | Baseline (FCFS / Manual) | RailOpt-IR (AI CP-SAT) | Improvement |
| :--- | :---: | :---: | :---: |
| **Total Section Delay** | 149.0 minutes | **42.5 minutes** | **-71.5% Delay Saved (106.5 min)** |
| **Punctuality Index** | 44.4% | **55.6%** | **+11.2% Boost** |
| **Vande Bharat Delay** | 36.0 minutes | **0.0 minutes (100% On-Time)** | **-100% (Green wave preserved)** |
| **Rajdhani Delay** | 28.0 minutes | **0.0 minutes (100% On-Time)** | **-100% (Green wave preserved)** |
| **Dynamic Overtakes** | 0 | **3 Loop Overtakes** | Optimized at Dankaur siding |
| **Solver Latency** | -- | **230 milliseconds** | Real-time response |

---

## 5. System Architecture

```
Project/
├── app/
│   ├── models/
│   │   ├── railway_network.py    # Station, Block Section, Loop Line, Signal & TSR models
│   │   └── train.py              # Train specs, categories, priority weights, schedules
│   ├── engine/
│   │   ├── cp_sat_solver.py      # Google OR-Tools CP-SAT mathematical optimization solver
│   │   ├── heuristic_baseline.py # First-Come-First-Served (FCFS) conventional dispatcher
│   │   ├── conflict_detector.py  # Headway violation & catch-up conflict detection
│   │   └── explainability.py     # Converts solver decisions into human Section Controller advisories
│   ├── simulation/
│   │   ├── corridor_data.py      # 106 km Ghaziabad–Aligarh corridor dataset (HDN-1)
│   │   └── simulator.py          # Real-time discrete-event engine, signals state & Kavach
│   ├── static/
│   │   ├── index.html            # Indian Railways Section Controller & Signaling Console
│   │   ├── css/style.css         # Dark glassmorphism Control Room theme
│   │   └── js/
│   │       ├── yard_schematic.js # Live Yard & 4-Aspect Signal Schematic renderer
│   │       └── app.js            # Controller interactivity, Kavach DMI & state sync
│   └── main.py                   # FastAPI REST API & asset server
├── benchmark_test.py             # Head-to-head evaluation test suite
├── test_api.py                   # API unit and smoke tests
├── run_server.py                 # Application launcher
└── README.md
```

---

## 6. How to Run

### Step 1: Install Dependencies
The project uses `fastapi`, `uvicorn`, and `ortools`:
```bash
python -m pip install fastapi uvicorn ortools
```

### Step 2: Launch Web Application
```bash
python run_server.py
```
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

### Step 3: Run Algorithmic Benchmark Suite
```bash
python benchmark_test.py
```

### Step 4: Run API Smoke Tests
```bash
python test_api.py
```
