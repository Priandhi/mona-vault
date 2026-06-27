#!/bin/bash
# Modal Mining Watchdog — auto-restart container if it dies
# CRITICAL: Prevents duplicate containers (learned from 7-container burn incident)
# Usage: nohup bash watchdog.sh &
source ~/modal-env/bin/activate
cd /path/to/app  # CHANGE THIS

APP_NAME="keryx-mining"  # CHANGE THIS
MAX_CONTAINERS=1  # Never exceed this

while true; do
    # Count ALL ephemeral apps for this miner
    RUNNING=$(modal app list 2>&1 | grep "$APP_NAME" | grep -c "ephemeral")
    
    if [ "$RUNNING" -eq 0 ]; then
        echo "[$(date)] Container dead — restarting..."
        modal run --detach app.py 2>&1 &
        sleep 30
    elif [ "$RUNNING" -gt "$MAX_CONTAINERS" ]; then
        echo "[$(date)] WARNING: $RUNNING containers running! Killing duplicates..."
        # Keep newest, kill the rest
        KEEP=$(modal app list 2>&1 | grep "$APP_NAME" | grep "ephemeral" | awk '{print $2}' | head -1)
        for app_id in $(modal app list 2>&1 | grep "$APP_NAME" | grep "ephemeral" | awk '{print $2}'); do
            if [ "$app_id" != "$KEEP" ]; then
                echo "[$(date)] Killing duplicate: $app_id"
                modal app stop "$app_id" --yes 2>&1
            fi
        done
    else
        APP_ID=$(modal app list 2>&1 | grep "$APP_NAME" | grep "ephemeral" | awk '{print $2}' | head -1)
        echo "[$(date)] Container alive: $APP_ID ($RUNNING running)"
    fi
    
    sleep 300  # Check every 5 minutes
done
