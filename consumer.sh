#!/bin/bash

APP_DIR="/home/kafka/eft-library-kafka"
VENV_DIR="$APP_DIR/venv"
APP_NAME="main.py"
PID_FILE="$APP_DIR/consumer.pid"

LOG_DIR="$APP_DIR/logs"
LOG_FILE="$LOG_DIR/consumer.log"

mkdir -p "$LOG_DIR"

start() {
  if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "Consumer is already running (PID: $(cat $PID_FILE))"
    exit 1
  fi
  echo "Starting consumer..."
  source "$VENV_DIR/bin/activate"
  nohup python3 "$APP_DIR/$APP_NAME" > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  deactivate
  echo "Consumer started with PID $(cat $PID_FILE)"
}

stop() {
  if [ ! -f "$PID_FILE" ]; then
    echo "Consumer is not running (no PID file)"
    exit 1
  fi
  PID=$(cat "$PID_FILE")
  if kill -0 $PID 2>/dev/null; then
    echo "Stopping consumer (PID: $PID)..."
    kill $PID
    rm -f "$PID_FILE"
    echo "Consumer stopped."
  else
    echo "Process not running but PID file exists. Cleaning up."
    rm -f "$PID_FILE"
  fi
}

restart() {
  stop
  sleep 1
  start
}

case "$1" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  *) echo "Usage: $0 {start|stop|restart}" ;;
esac
