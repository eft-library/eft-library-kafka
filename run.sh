#!/bin/bash

KAFKA_DIR="/home/kafka/kafka_2.13-4.0.0"
CONFIG="$KAFKA_DIR/config/kraft/server.properties"
PID_FILE="$KAFKA_DIR/kafka.pid"
LOG_FILE="$KAFKA_DIR/kafka.log"

case "$1" in
  start)
    if [ -f "$PID_FILE" ]; then
      echo "Kafka is already running with PID $(cat $PID_FILE)"
      exit 1
    fi
    echo "Starting Kafka in KRaft mode..."
    nohup $KAFKA_DIR/bin/kafka-server-start.sh $CONFIG > $LOG_FILE 2>&1 &
    echo $! > $PID_FILE
    echo "Kafka started with PID $(cat $PID_FILE)"
    ;;

  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      echo "Stopping Kafka (PID $PID)..."
      kill "$PID"
      rm -f "$PID_FILE"
      echo "Kafka stopped."
    else
      echo "Kafka is not running or PID file not found."
    fi
    ;;

  restart)
    $0 stop
    sleep 2
    $0 start
    ;;

  status)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if ps -p "$PID" > /dev/null; then
        echo "Kafka is running with PID $PID"
      else
        echo "Kafka PID file exists but process not running."
      fi
    else
      echo "Kafka is not running."
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
