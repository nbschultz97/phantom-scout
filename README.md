# Ceradon Sim

**Virtual testbench for UxS + edge AI integration.**

Train and validate autonomous behaviors in a physics-based virtual environment before field deployment. Plug in your companion computer, connect via MAVLink, and test your full stack — perception, decision, and control — without risking hardware.

## The Problem

Every UxS developer knows this loop:
1. Configure on laptop
2. Walk outside, power up vehicle
3. Test — doesn't work
4. Walk back, reconfigure
5. Repeat 50 times

Each cycle costs 15-30 minutes and risks expensive hardware. Training an AI system on a 10" FPV means risking a $2K+ drone on every test flight.

## The Solution

Ceradon Sim creates a closed-loop virtual environment where:

- Your **actual edge AI code** (RAPTOR, Phantom-Scout, etc.) connects to a **simulated vehicle**
- The simulated vehicle has **physics-accurate flight/drive dynamics** (not toy physics)
- **Simulated cameras** feed your AI pipeline — it doesn't know it's in a sim
- **MAVLink-native** — same protocol as the real vehicle, same parameters, same everything
- **Settings carry over** — when it works in sim, flash the same config to real hardware

```
┌─────────────────────┐     Camera Feed      ┌──────────────┐
│   Gazebo World      │ ──────────────────▶  │  Jetson/PC   │
│   (3D environment   │                       │  running     │
│    + target objects  │  MAVLink Commands    │  RAPTOR      │
│    + physics)        │ ◀──────────────────  │  or any AI   │
└─────────┬───────────┘                       └──────────────┘
          │
          │ MAVLink (TCP/UDP)
          ▼
┌─────────────────────┐
│  ArduPilot SITL     │
│  (Copter/Rover/     │
│   Plane firmware)   │
└─────────────────────┘
```

## Features

### Core
- **One-command launch** — `ceradon-sim up --vehicle copter-10inch` spins up everything
- **Vehicle profiles** — Pre-configured physics for 5" FPV, 10" FPV, UGV rover, fixed-wing
- **Companion computer bridge** — Connect your Jetson or laptop over MAVLink (same as real)
- **Simulated sensors** — Cameras (RGB, thermal, depth), GPS, IMU, rangefinder
- **Mission Planner compatible** — Connect MP alongside your AI for monitoring

### AI Training & Validation
- **Target scenarios** — Place objects/people/vehicles in the virtual world
- **Autonomous behavior testing** — Track, follow, engage targets without crashing real hardware
- **Closed-loop validation** — AI sees → decides → commands → vehicle responds → repeat
- **Scenario scripting** — Reproducible test cases (wind, GPS denial, obstacle courses)

### Sim-to-Real
- **Parameter export** — `ceradon-sim export-params` dumps all tuned settings
- **Board config generation** — Generates `.param` files for ArduPilot hardware
- **PID tuning in sim** — Tune flight dynamics virtually, carry gains to real FC
- **Regression testing** — Run same scenario after code changes to catch regressions

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- (Optional) NVIDIA GPU for accelerated rendering

### Launch

```bash
# Start sim environment with a 10" quadcopter
ceradon-sim up --vehicle copter-10inch --world urban-search

# In another terminal, connect your AI
export MAVLINK_HOST=localhost:14550
export CAMERA_URL=rtsp://localhost:8554/fpv
python your_ai_system.py

# Or connect Mission Planner
# TCP: localhost:5762
```

### Export Settings to Real Hardware

```bash
# After tuning in sim, export params
ceradon-sim export-params --format ardupilot --output my-10inch.param

# Flash to real flight controller via Mission Planner or mavproxy
```

## Vehicle Profiles

| Profile | Type | Based On | Use Case |
|---------|------|----------|----------|
| `copter-5inch` | FPV Quad | 5" racing frame | Agile FPV AI training |
| `copter-10inch` | FPV Quad | 10" heavy-lift | Payload AI (RAPTOR) |
| `rover-ugv` | Ground Vehicle | Traxxas-class UGV | Ground autonomy |
| `plane-fixed` | Fixed Wing | ArduPlane VTOL | Long-range ISR |
| `custom` | User-defined | Your specs | Bring your own vehicle |

## Worlds

| World | Description | Targets |
|-------|-------------|---------|
| `empty` | Flat plane, no obstacles | Basic tuning |
| `urban-search` | City blocks, buildings | Search & track |
| `open-field` | Rural terrain, trees | Patrol scenarios |
| `indoor` | Warehouse/building interior | UGV navigation |
| `obstacle-course` | Gates, walls, narrow gaps | Flight validation |

## Architecture

```
ceradon-sim/
├── cli/                    # CLI tool (ceradon-sim command)
├── docker/                 # Docker configs for SITL + Gazebo
│   ├── Dockerfile.sitl     # ArduPilot SITL
│   ├── Dockerfile.gazebo   # Gazebo + worlds + models
│   └── docker-compose.yml  # One-command launch
├── vehicles/               # Vehicle physics profiles
│   ├── copter-5inch.json
│   ├── copter-10inch.json
│   ├── rover-ugv.json
│   └── plane-fixed.json
├── worlds/                 # Gazebo world files
│   ├── empty.sdf
│   ├── urban-search.sdf
│   └── open-field.sdf
├── bridge/                 # Companion computer bridge
│   ├── camera_bridge.py    # Simulated camera → RTSP/OpenCV
│   ├── mavlink_proxy.py    # MAVLink routing
│   └── param_export.py     # Sim → real param conversion
├── scenarios/              # Scripted test scenarios
│   ├── basic_hover.yaml
│   ├── target_track.yaml
│   └── waypoint_mission.yaml
├── models/                 # 3D models for targets/objects
└── docs/                   # Documentation
```

## Roadmap

### Phase 1: Foundation (Current)
- [ ] Docker-based SITL + Gazebo launch
- [ ] Copter and Rover vehicle profiles
- [ ] Simulated camera feed (RTSP output)
- [ ] MAVLink companion computer bridge
- [ ] Basic CLI (`up`, `down`, `status`)

### Phase 2: AI Integration
- [ ] RAPTOR integration guide + example
- [ ] Phantom-Scout integration
- [ ] Target placement and scenario scripting
- [ ] Autonomous behavior validation framework

### Phase 3: Sim-to-Real
- [ ] Parameter export (ArduPilot `.param` format)
- [ ] PID tuning workflow
- [ ] Regression test runner
- [ ] Hardware-in-the-loop mode (real FC + simulated world)

### Phase 4: Product
- [ ] Desktop GUI (Electron or web-based)
- [ ] Vehicle profile editor
- [ ] World editor
- [ ] Telemetry recording and replay
- [ ] Multi-vehicle simulation

## Ceradon Product Integration

Ceradon Sim is designed to work with the full Ceradon Systems edge AI stack:

| Product | Integration | Status |
|---------|------------|--------|
| [RAPTOR](https://github.com/nbschultz97/sorcc-raptor) | Detection/tracking on simulated camera feed | Planned |
| [Phantom-Scout](https://github.com/nbschultz97/Tactical-App) | MAVLink AI copilot testing | Planned |
| [Ceradon Edge](https://github.com/nbschultz97/ceradon-edge) | Full edge appliance simulation | Future |
| [DroneDetect](https://github.com/nbschultz97/DroneDetectAndroid) | C-UAS detection training | Future |

## License

Proprietary — Ceradon Systems, LLC

## About

Built by [Ceradon Systems](https://ceradonsystems.com) — defense technology for the warfighter.
