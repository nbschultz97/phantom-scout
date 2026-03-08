#!/bin/bash
# Ceradon Sim — Gazebo Entrypoint
# Launches Gazebo with the specified world and vehicle model

set -e

WORLD="${WORLD:-empty}"
VEHICLE_MODEL="${VEHICLE_MODEL:-iris}"

# Resolve world file
WORLD_FILE="/worlds/${WORLD}.sdf"
if [ ! -f "$WORLD_FILE" ]; then
    echo "World file not found: $WORLD_FILE"
    echo "Available worlds:"
    ls /worlds/*.sdf 2>/dev/null || echo "  (none)"
    echo "Falling back to empty world"
    WORLD_FILE="/worlds/empty.sdf"
fi

echo "=========================================="
echo "  Ceradon Sim — Gazebo"
echo "  World: $WORLD"
echo "  Vehicle Model: $VEHICLE_MODEL"
echo "=========================================="

# Launch Gazebo
gz sim -v 4 -r "$WORLD_FILE" 2>&1
