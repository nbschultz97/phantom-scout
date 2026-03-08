#!/bin/bash
# Ceradon Sim — SITL Entrypoint
# Launches ArduPilot SITL with the specified vehicle type and parameters

set -e

VEHICLE="${VEHICLE:-copter}"
VEHICLE_FRAME="${VEHICLE_FRAME:-quad}"
SPEEDUP="${SPEEDUP:-1}"
HOME_LAT="${SIM_HOME_LAT:-40.7608}"
HOME_LON="${SIM_HOME_LON:--111.8910}"
HOME_ALT="${SIM_HOME_ALT:-1288}"
HOME_HDG="${SIM_HOME_HDG:-0}"

# Map vehicle type to ArduPilot vehicle
case "$VEHICLE" in
    copter|quad|copter-5inch|copter-10inch)
        AP_VEHICLE="ArduCopter"
        ;;
    rover|ugv|rover-ugv)
        AP_VEHICLE="Rover"
        ;;
    plane|fixed|plane-fixed)
        AP_VEHICLE="ArduPlane"
        ;;
    *)
        echo "Unknown vehicle type: $VEHICLE"
        echo "Supported: copter, rover, plane (or aliases)"
        exit 1
        ;;
esac

# Load custom params if vehicle profile exists
PARAM_FILE=""
if [ -f "/vehicles/${VEHICLE}.param" ]; then
    PARAM_FILE="--add-param-file=/vehicles/${VEHICLE}.param"
    echo "Loading vehicle profile: /vehicles/${VEHICLE}.param"
fi

echo "=========================================="
echo "  Ceradon Sim — SITL"
echo "  Vehicle: $AP_VEHICLE ($VEHICLE)"
echo "  Frame: $VEHICLE_FRAME"
echo "  Home: $HOME_LAT, $HOME_LON, ${HOME_ALT}m"
echo "  Speed: ${SPEEDUP}x"
echo "=========================================="

# Launch SITL
# --out: MAVLink output endpoints for companion computer + GCS
# -S: simulation speedup
# --model JSON: use JSON-based physics (compatible with Gazebo)
cd /ardupilot/Tools/autotest

python3 sim_vehicle.py \
    -v "$AP_VEHICLE" \
    -f "$VEHICLE_FRAME" \
    --model JSON \
    --no-rebuild \
    -S "$SPEEDUP" \
    -l "${HOME_LAT},${HOME_LON},${HOME_ALT},${HOME_HDG}" \
    --out "0.0.0.0:14550" \
    --out "0.0.0.0:14551" \
    --out "0.0.0.0:5762" \
    $PARAM_FILE \
    --map --console 2>&1
