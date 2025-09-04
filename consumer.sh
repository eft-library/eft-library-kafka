#!/bin/bash

APP_DIR="/home/kafka/eft-library-kafka"
VENV_DIR="$APP_DIR/venv"

SERVICES=("log" "notification")
LOG_DIR="$APP_DIR/logs"
mkdir -p "$LOG_DIR"

start_service() {
  SERVICE=$1
  MAIN_FILE="$APP_DIR/main_${SERVICE}_consumer.py"
  PID_FILE="$APP_DIR/${SERVICE}.pid"
  LOG_FILE="$LOG_DIR/${SERVICE}.log"

  if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "$SERVICE consumer is already running (PID: $(cat $PID_FILE))"
    return
  fi

  echo "Starting $SERVICE consumer..."
  source "$VENV_DIR/bin/activate"
  nohup python3 "$MAIN_FILE" > "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  deactivate
  echo "$SERVICE consumer started with PID $(cat $PID_FILE)"
}

stop_service() {
  SERVICE=$1
  PID_FILE="$APP_DIR/${SERVICE}.pid"

  if [ ! -f "$PID_FILE" ]; then
    echo "$SERVICE consumer is not running (no PID file)"
    return
  fi

  PID=$(cat "$PID_FILE")
  if kill -0 $PID 2>/dev/null; then
    echo "Stopping $SERVICE consumer (PID: $PID)..."
    kill $PID
    rm -f "$PID_FILE"
    echo "$SERVICE consumer stopped."
  else
    echo "Process not running but PID file exists. Cleaning up."
    rm -f "$PID_FILE"
  fi
}

case "$1" in
  start)
    for svc in "${SERVICES[@]}"; do
      start_service "$svc"
    done
    ;;
  stop)
    for svc in "${SERVICES[@]}"; do
      stop_service "$svc"
    done
    ;;
  restart)
    for svc in "${SERVICES[@]}"; do
      stop_service "$svc"
    done
    sleep 1
    for svc in "${SERVICES[@]}"; do
      start_service "$svc"
    done
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}"
    ;;
esac
