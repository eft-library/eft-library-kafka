import os
import logging
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError

load_dotenv()

# 로그 설정
LOG_DIR = os.getenv("LOG_DIR", "./logs")  # .env 파일에서 경로 설정 가능, 기본은 ./logs
LOG_FILE = os.path.join(LOG_DIR, "consumer.log")
os.makedirs(LOG_DIR, exist_ok=True)  # 디렉토리 없으면 생성

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),  # 터미널에도 출력 (원하면 제거 가능)
    ],
)


def main():
    conf = {
        "bootstrap.servers": os.getenv("BOOTSTRAP_SERVER"),
        "group.id": os.getenv("TOPIC"),
        "auto.offset.reset": os.getenv("OFFSET_RESET_CONFIG"),
    }

    consumer = Consumer(conf)
    topic = os.getenv("TOPIC")
    consumer.subscribe([topic])

    logging.info(f"Subscribed to topic: {topic}")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logging.warning(
                        f"End of partition: {msg.topic()} [{msg.partition()}]"
                    )
                else:
                    logging.error(f"Error: {msg.error().str()}")
            else:
                value = msg.value().decode("utf-8")
                logging.info(f"Received message: {value}")
                # → ClickHouse/PostgreSQL 저장 로직 삽입 가능

    except KeyboardInterrupt:
        logging.info("Consumer interrupted by user")

    finally:
        consumer.close()
        logging.info("Consumer closed")


if __name__ == "__main__":
    main()
