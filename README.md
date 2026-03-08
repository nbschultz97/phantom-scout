# Phantom-Scout

**MAVLink AI Copilot for autonomous vehicles.**

Companion to Mission Planner/QGC — not a replacement. Natural language mission planning, telemetry diagnosis, anomaly detection, and mission debrief from .bin logs. Runs offline on Jetson/laptop for DDIL environments.

## Philosophy

> Mission Planner is the steering wheel. Phantom-Scout is the copilot riding shotgun.

Doesn't ask operators to learn new tools. Makes them faster, catches what they'd miss. Works offline, no reachback needed.

## Features (Planned)

- **NL Mission Planning** — "Set up a search pattern over this grid, avoid the ridgeline" → MAVLink waypoints
- **Telemetry Diagnosis** — "Why is my drone yawing left?" → Motor 3 ESC desync (2 seconds vs 20 min log diving)
- **Anomaly Detection** — Real-time telemetry monitoring, catches failures before the operator notices
- **Mission Debrief** — Plain English summary from .bin flight logs
- **Field Troubleshooting** — "Lost GPS, what are my options?" → context-aware suggestions

## Architecture

Works with any MAVLink vehicle (ArduPilot, PX4) — drones, UGVs, USVs.

```
Mission Planner/QGC ←→ MAVLink ←→ Flight Controller
                                        ↕
                              Phantom-Scout (AI Copilot)
                              Jetson / Laptop / Edge
                              Phi-4 + Qwen + Moondream
```

## Part of the Ceradon Stack

| Product | Role |
|---------|------|
| [RAPTOR](https://github.com/nbschultz97/sorcc-raptor) | Detection/tracking/targeting |
| **Phantom-Scout** | MAVLink AI copilot |
| [Ceradon Sim](https://github.com/nbschultz97/ceradon-sim) | Virtual testbench |
| [Ceradon Edge](https://github.com/nbschultz97/ceradon-edge) | Edge compute platform |

## Status

Early development. Scaffold incoming.

## License

Proprietary — Ceradon Systems, LLC
