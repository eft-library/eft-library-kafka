# Kafka 경로 설정
KAFKA_DIR="/home/kafka/kafka_2.13-3.9.0"  # Kafka 설치 경로로 변경
KAFKA_CONFIG="$KAFKA_DIR/config/kraft/server.properties"  # Kafka 설정 파일 경로

# 로그 파일 경로
LOG_FILE="$KAFKA_DIR/kafka.log"

# Kafka 프로세스 찾기
KAFKA_PID_FILE="$KAFKA_DIR/kafka.pid"

start_kafka() {
    # Kafka가 이미 실행 중인 경우
    if [ -f "$KAFKA_PID_FILE" ]; then
        echo "Kafka is already running (PID file exists)."
        return
    fi

    echo "Starting Kafka..."

    # Kafka를 nohup으로 백그라운드에서 실행
    nohup $KAFKA_DIR/bin/kafka-server-start.sh $KAFKA_CONFIG > $LOG_FILE 2>&1 &

    # Kafka 프로세스 PID 저장
    echo $! > "$KAFKA_PID_FILE"

    echo "Kafka started with PID $(cat $KAFKA_PID_FILE)"
}

stop_kafka() {
    # Kafka가 실행 중인지 확인
    if [ ! -f "$KAFKA_PID_FILE" ]; then
        echo "Kafka is not running (PID file not found)."
        return
    fi

    # Kafka 종료
    PID=$(cat $KAFKA_PID_FILE)
    echo "Stopping Kafka (PID $PID)..."
    kill $PID

    # PID 파일 삭제
    rm -f "$KAFKA_PID_FILE"

    echo "Kafka stopped."
}

restart_kafka() {
    stop_kafka
    start_kafka
}

status_kafka() {
    # Kafka가 실행 중인지 확인
    if [ -f "$KAFKA_PID_FILE" ]; then
        echo "Kafka is running (PID $(cat $KAFKA_PID_FILE))."
    else
        echo "Kafka is not running."
    fi
}

# 인수에 따라 함수 실행
case "$1" in
    start)
        start_kafka
        ;;
    stop)
        stop_kafka
        ;;
    restart)
        restart_kafka
        ;;
    status)
        status_kafka
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac