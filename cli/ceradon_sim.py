#!/usr/bin/env python3
"""
Ceradon Sim — CLI

One-command launch for virtual UxS testing.

Usage:
    ceradon-sim up --vehicle copter-10inch --world urban-search
    ceradon-sim down
    ceradon-sim status
    ceradon-sim export-params --output my-drone.param
    ceradon-sim run-scenario --scenario target_track
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Project root
ROOT = Path(__file__).parent.parent
DOCKER_DIR = ROOT / "docker"
VEHICLES_DIR = ROOT / "vehicles"
WORLDS_DIR = ROOT / "worlds"
SCENARIOS_DIR = ROOT / "scenarios"


def cmd_up(args):
    """Start the simulation environment."""
    vehicle = args.vehicle or "copter-10inch"
    world = args.world or "empty"

    # Load vehicle profile
    vehicle_file = VEHICLES_DIR / f"{vehicle}.json"
    if not vehicle_file.exists():
        print(f"ERROR: Vehicle profile not found: {vehicle}")
        print(f"Available: {', '.join(p.stem for p in VEHICLES_DIR.glob('*.json'))}")
        sys.exit(1)

    with open(vehicle_file) as f:
        profile = json.load(f)

    # Check world exists
    world_file = WORLDS_DIR / f"{world}.sdf"
    if not world_file.exists():
        print(f"WARNING: World file not found: {world}, falling back to 'empty'")
        world = "empty"

    print(f"{'=' * 50}")
    print(f"  Ceradon Sim — Starting")
    print(f"  Vehicle: {profile['name']} ({vehicle})")
    print(f"  World: {world}")
    print(f"  Type: {profile['type']}")
    print(f"{'=' * 50}")

    # Set environment variables for docker-compose
    env = os.environ.copy()
    env["VEHICLE"] = profile["type"]
    env["VEHICLE_FRAME"] = profile.get("sitl_frame", "quad")
    env["WORLD"] = world
    env["VEHICLE_MODEL"] = profile.get("gazebo_model", "iris")

    if args.headless:
        env["DISPLAY"] = ""

    if args.speedup:
        env["SPEEDUP"] = str(args.speedup)

    # Camera settings from profile
    if "camera" in profile:
        cam = profile["camera"]
        env["CAMERA_RES"] = cam.get("resolution", "640x480")
        env["CAMERA_FPS"] = str(cam.get("fps", 30))

    # Launch docker-compose
    compose_file = DOCKER_DIR / "docker-compose.yml"
    cmd = ["docker", "compose", "-f", str(compose_file), "up"]

    if args.detach:
        cmd.append("-d")

    if args.build:
        cmd.append("--build")

    print(f"\nConnect your AI to:")
    print(f"  MAVLink: udp:localhost:14550")
    print(f"  Camera:  rtsp://localhost:8554/fpv")
    print(f"  GCS:     tcp:localhost:5762 (Mission Planner)")
    print()

    try:
        subprocess.run(cmd, env=env, cwd=str(DOCKER_DIR))
    except KeyboardInterrupt:
        print("\nShutting down...")
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "down"],
            env=env, cwd=str(DOCKER_DIR)
        )


def cmd_down(args):
    """Stop the simulation environment."""
    compose_file = DOCKER_DIR / "docker-compose.yml"
    subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "down"],
        cwd=str(DOCKER_DIR)
    )
    print("Simulation stopped.")


def cmd_status(args):
    """Show simulation status."""
    compose_file = DOCKER_DIR / "docker-compose.yml"
    subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "ps"],
        cwd=str(DOCKER_DIR)
    )


def cmd_export_params(args):
    """Export parameters from running simulation."""
    from bridge.param_export import connect, fetch_all_params, export_param_file, export_json

    host = args.host or "udp:localhost:14550"
    output = args.output or "exported.param"
    fmt = args.format or "param"

    conn = connect(host)
    params = fetch_all_params(conn)

    if fmt == "json":
        export_json(params, output)
    else:
        export_param_file(params, output, diff_only=args.diff)


def cmd_vehicles(args):
    """List available vehicle profiles."""
    print("Available vehicle profiles:\n")
    for f in sorted(VEHICLES_DIR.glob("*.json")):
        with open(f) as fp:
            profile = json.load(fp)
        print(f"  {f.stem:<20} {profile['name']}")
        print(f"  {'':20} Type: {profile['type']}, {profile.get('description', '')}")
        print()


def cmd_worlds(args):
    """List available worlds."""
    print("Available worlds:\n")
    for f in sorted(WORLDS_DIR.glob("*.sdf")):
        print(f"  {f.stem}")


def main():
    parser = argparse.ArgumentParser(
        prog="ceradon-sim",
        description="Ceradon Sim — Virtual testbench for UxS + edge AI"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # up
    up_parser = subparsers.add_parser("up", help="Start simulation")
    up_parser.add_argument("--vehicle", "-v", help="Vehicle profile (e.g. copter-10inch)")
    up_parser.add_argument("--world", "-w", help="World to load (e.g. urban-search)")
    up_parser.add_argument("--headless", action="store_true", help="No GUI")
    up_parser.add_argument("--detach", "-d", action="store_true", help="Run in background")
    up_parser.add_argument("--build", action="store_true", help="Rebuild containers")
    up_parser.add_argument("--speedup", type=int, help="Simulation speed multiplier")
    up_parser.set_defaults(func=cmd_up)

    # down
    down_parser = subparsers.add_parser("down", help="Stop simulation")
    down_parser.set_defaults(func=cmd_down)

    # status
    status_parser = subparsers.add_parser("status", help="Show status")
    status_parser.set_defaults(func=cmd_status)

    # export-params
    export_parser = subparsers.add_parser("export-params", help="Export tuned parameters")
    export_parser.add_argument("--host", help="MAVLink connection")
    export_parser.add_argument("--output", "-o", help="Output file")
    export_parser.add_argument("--format", "-f", choices=["param", "json"])
    export_parser.add_argument("--diff", action="store_true", help="Only changed params")
    export_parser.set_defaults(func=cmd_export_params)

    # vehicles
    vehicles_parser = subparsers.add_parser("vehicles", help="List vehicle profiles")
    vehicles_parser.set_defaults(func=cmd_vehicles)

    # worlds
    worlds_parser = subparsers.add_parser("worlds", help="List worlds")
    worlds_parser.set_defaults(func=cmd_worlds)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
