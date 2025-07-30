#!/bin/bash
# Cursor Session 监测系统停止脚本

LOG_FILE="/tmp/cursor_session_monitor.log"
PID_FILE="/tmp/cursor_session_monitor.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "$(date): Stopping Cursor session monitor (PID: $PID)..." >> "$LOG_FILE"
        kill "$PID"
        sleep 2
        if kill -0 "$PID" 2>/dev/null; then
            echo "$(date): Force stopping Cursor session monitor..." >> "$LOG_FILE"
            kill -9 "$PID"
        fi
        rm -f "$PID_FILE"
        echo "$(date): Cursor session monitor stopped" >> "$LOG_FILE"
        echo "Cursor session monitor stopped"
    else
        echo "Cursor session monitor not running"
        rm -f "$PID_FILE"
    fi
else
    echo "Cursor session monitor not running (no PID file)"
fi