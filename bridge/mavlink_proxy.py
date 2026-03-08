#!/usr/bin/env python3
"""
Ceradon Sim — MAVLink Proxy

Routes MAVLink messages between SITL and companion computer(s).
Handles:
- Multiple companion computer connections
- Message filtering and logging
- Telemetry recording for replay
- Parameter bridging for sim-to-real export

Your companion computer connects here the same way it would connect
to a real flight controller over serial/UDP.
"""

import os
import sys
import time
import json
import signal
import threading
from datetime import datetime
from pathlib import Path

try:
    from pymavlink import mavutil
except ImportError:
    print("ERROR: pymavlink not installed. Run: pip install pymavlink")
    sys.exit(1)

# Configuration
SITL_HOST = os.environ.get("SITL_HOST", "sitl")
SITL_PORT = int(os.environ.get("SITL_PORT", "5760"))
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "14550"))
LOG_DIR = os.environ.get("LOG_DIR", "/logs")
RECORD = os.environ.get("RECORD", "true").lower() == "true"


class MAVLinkProxy:
    """Proxy MAVLink between SITL and companion computers."""

    def __init__(self):
        self.running = True
        self.sitl_conn = None
        self.companion_conns = []
        self.params = {}
        self.telemetry_log = []
        self.msg_count = 0

        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, signum, frame):
        print("[MAVProxy] Shutting down...")
        self.running = False
        if RECORD:
            self._save_telemetry_log()

    def connect_sitl(self):
        """Connect to ArduPilot SITL."""
        conn_str = f"tcp:{SITL_HOST}:{SITL_PORT}"
        print(f"[MAVProxy] Connecting to SITL at {conn_str}...")

        retries = 0
        while self.running and retries < 30:
            try:
                self.sitl_conn = mavutil.mavlink_connection(conn_str)
                self.sitl_conn.wait_heartbeat(timeout=10)
                print(f"[MAVProxy] Connected to SITL (system {self.sitl_conn.target_system})")
                return True
            except Exception as e:
                retries += 1
                print(f"[MAVProxy] SITL not ready (attempt {retries}/30): {e}")
                time.sleep(2)

        print("[MAVProxy] Failed to connect to SITL")
        return False

    def listen_companion(self):
        """Listen for companion computer connections."""
        listen_str = f"udpin:0.0.0.0:{LISTEN_PORT}"
        print(f"[MAVProxy] Listening for companion on {listen_str}")
        conn = mavutil.mavlink_connection(listen_str)
        self.companion_conns.append(conn)
        return conn

    def forward_messages(self):
        """Forward messages between SITL and companion computers."""
        companion = self.listen_companion()

        while self.running:
            # SITL → Companion (telemetry, heartbeat, etc.)
            msg = self.sitl_conn.recv_match(blocking=False)
            if msg:
                msg_type = msg.get_type()
                self.msg_count += 1

                # Record telemetry
                if RECORD and msg_type in [
                    "HEARTBEAT", "GLOBAL_POSITION_INT", "ATTITUDE",
                    "VFR_HUD", "SYS_STATUS", "GPS_RAW_INT",
                    "BATTERY_STATUS", "RC_CHANNELS"
                ]:
                    self.telemetry_log.append({
                        "t": time.time(),
                        "type": msg_type,
                        "data": msg.to_dict()
                    })

                # Track parameters
                if msg_type == "PARAM_VALUE":
                    self.params[msg.param_id.rstrip('\x00')] = {
                        "value": msg.param_value,
                        "type": msg.param_type,
                        "index": msg.param_index,
                        "count": msg.param_count
                    }

                # Forward to companion
                try:
                    companion.mav.send(msg)
                except Exception:
                    pass

            # Companion → SITL (commands, parameter changes)
            msg = companion.recv_match(blocking=False)
            if msg:
                try:
                    self.sitl_conn.mav.send(msg)
                except Exception:
                    pass

            # Don't spin too fast
            time.sleep(0.001)

    def export_params(self, output_path: str = None):
        """Export current parameters as ArduPilot .param file."""
        if not self.params:
            print("[MAVProxy] No parameters captured yet")
            return

        if output_path is None:
            output_path = os.path.join(LOG_DIR, "exported.param")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(f"# Ceradon Sim — Exported Parameters\n")
            f.write(f"# Date: {datetime.now().isoformat()}\n")
            f.write(f"# Parameters: {len(self.params)}\n\n")

            for name, info in sorted(self.params.items()):
                f.write(f"{name},{info['value']}\n")

        print(f"[MAVProxy] Exported {len(self.params)} parameters to {output_path}")

    def _save_telemetry_log(self):
        """Save telemetry log for replay/analysis."""
        if not self.telemetry_log:
            return

        Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(LOG_DIR, f"telemetry_{timestamp}.json")

        with open(log_path, "w") as f:
            json.dump(self.telemetry_log, f)

        print(f"[MAVProxy] Saved {len(self.telemetry_log)} telemetry records to {log_path}")

    def run(self):
        """Main entry point."""
        print("=" * 50)
        print("  Ceradon Sim — MAVLink Proxy")
        print(f"  SITL: {SITL_HOST}:{SITL_PORT}")
        print(f"  Companion Port: {LISTEN_PORT}")
        print(f"  Recording: {RECORD}")
        print("=" * 50)

        if not self.connect_sitl():
            sys.exit(1)

        try:
            self.forward_messages()
        finally:
            if RECORD:
                self._save_telemetry_log()
            self.export_params()


if __name__ == "__main__":
    proxy = MAVLinkProxy()
    proxy.run()
