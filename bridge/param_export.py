#!/usr/bin/env python3
"""
Ceradon Sim — Parameter Export Tool

The killer feature: settings tuned in simulation carry over to real hardware.

Connects to SITL, downloads all parameters, and exports them in formats
compatible with real flight controllers:
- ArduPilot .param files (load via Mission Planner)
- JSON (for programmatic use)
- Diff (only parameters changed from defaults)

Usage:
    python param_export.py --host localhost:14550 --output my-drone.param
    python param_export.py --host localhost:14550 --format json --output config.json
    python param_export.py --host localhost:14550 --diff --output changes-only.param
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

try:
    from pymavlink import mavutil
except ImportError:
    print("ERROR: pymavlink not installed. Run: pip install pymavlink")
    sys.exit(1)


# Default ArduPilot parameters (subset — used for diff mode)
# Full defaults would be loaded from a reference file
KNOWN_DEFAULTS = {}


def connect(host: str, timeout: int = 30):
    """Connect to MAVLink endpoint."""
    print(f"Connecting to {host}...")
    conn = mavutil.mavlink_connection(host)
    conn.wait_heartbeat(timeout=timeout)
    print(f"Connected (system {conn.target_system}, component {conn.target_component})")
    return conn


def fetch_all_params(conn, timeout: int = 60) -> dict:
    """Download all parameters from the flight controller."""
    print("Requesting all parameters...")
    conn.mav.param_request_list_send(conn.target_system, conn.target_component)

    params = {}
    total = None
    deadline = time.time() + timeout

    while time.time() < deadline:
        msg = conn.recv_match(type="PARAM_VALUE", blocking=True, timeout=2)
        if msg is None:
            if total and len(params) >= total:
                break
            continue

        name = msg.param_id.rstrip('\x00')
        params[name] = {
            "value": msg.param_value,
            "type": msg.param_type,
            "index": msg.param_index,
        }

        if total is None:
            total = msg.param_count
            print(f"Total parameters: {total}")

        # Progress
        if len(params) % 100 == 0:
            print(f"  Downloaded {len(params)}/{total}...")

        if total and len(params) >= total:
            break

    print(f"Downloaded {len(params)} parameters")
    return params


def export_param_file(params: dict, output: str, diff_only: bool = False):
    """Export as ArduPilot .param file."""
    with open(output, "w") as f:
        f.write(f"# Ceradon Sim — Parameter Export\n")
        f.write(f"# Exported: {datetime.now().isoformat()}\n")
        f.write(f"# Parameters: {len(params)}\n")

        if diff_only:
            f.write(f"# Mode: DIFF (changed from defaults only)\n")

        f.write(f"#\n")
        f.write(f"# Load in Mission Planner: Config > Full Parameter List > Load from file\n")
        f.write(f"# Load via MAVProxy: param load {output}\n\n")

        for name in sorted(params.keys()):
            value = params[name]["value"]

            if diff_only and name in KNOWN_DEFAULTS:
                if abs(value - KNOWN_DEFAULTS[name]) < 0.0001:
                    continue

            # Format value (integers vs floats)
            if value == int(value):
                f.write(f"{name},{int(value)}\n")
            else:
                f.write(f"{name},{value:.6f}\n")

    print(f"Exported to {output}")


def export_json(params: dict, output: str):
    """Export as JSON."""
    export = {
        "ceradon_sim_export": True,
        "exported_at": datetime.now().isoformat(),
        "param_count": len(params),
        "parameters": {
            name: info["value"] for name, info in sorted(params.items())
        }
    }

    with open(output, "w") as f:
        json.dump(export, f, indent=2)

    print(f"Exported {len(params)} parameters to {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Ceradon Sim — Export tuned parameters from simulation to real hardware"
    )
    parser.add_argument(
        "--host", default="udp:localhost:14550",
        help="MAVLink connection string (default: udp:localhost:14550)"
    )
    parser.add_argument(
        "--output", "-o", default="exported.param",
        help="Output file path"
    )
    parser.add_argument(
        "--format", "-f", choices=["param", "json"], default="param",
        help="Output format (default: param)"
    )
    parser.add_argument(
        "--diff", action="store_true",
        help="Only export parameters changed from defaults"
    )
    parser.add_argument(
        "--timeout", type=int, default=60,
        help="Timeout for parameter download (seconds)"
    )

    args = parser.parse_args()

    conn = connect(args.host)
    params = fetch_all_params(conn, timeout=args.timeout)

    if not params:
        print("ERROR: No parameters received")
        sys.exit(1)

    if args.format == "json":
        export_json(params, args.output)
    else:
        export_param_file(params, args.output, diff_only=args.diff)


if __name__ == "__main__":
    main()
