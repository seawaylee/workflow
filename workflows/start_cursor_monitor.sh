#!/bin/bash
# Cursor Session 监测系统启动脚本
# 用于开机自启动持续监测

# 日志文件路径
LOG_FILE="/tmp/cursor_session_monitor.log"
PID_FILE="/tmp/cursor_session_monitor.pid"

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "$(date): Cursor session monitor already running with PID $PID" | tee -a "$LOG_FILE"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# 启动监测进程
echo "$(date): Starting Cursor session monitor..." | tee -a "$LOG_FILE"

# 设置环境变量禁用Python缓冲
export PYTHONUNBUFFERED=1

# 使用nohup在后台运行持续监测，确保实时输出
nohup /opt/homebrew/opt/python@3.9/bin/python3.9 -u /Users/NikoBelic/Documents/IdeaProjects/pythonDemo/workflows/cursor_session_scheduler.py seconds 30 --strict >> "$LOG_FILE" 2>&1 &

# 保存进程ID
echo $! > "$PID_FILE"

echo "$(date): Cursor session monitor started with PID $!" | tee -a "$LOG_FILE"
echo "$(date): Monitor will check every 10 seconds in strict mode" | tee -a "$LOG_FILE"
echo "$(date): Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "$(date): Use 'tail -f $LOG_FILE' to monitor in real-time" | tee -a "$LOG_FILE"
