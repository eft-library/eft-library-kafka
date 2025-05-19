import os
import logging
import json
import psycopg2
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError

load_dotenv()

# 로그 설정
LOG_DIR = os.getenv("LOG_DIR", "./logs")
LOG_FILE = os.path.join(LOG_DIR, "consumer.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)


# PostgreSQL 연결 함수
def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


# 메시지 DB 저장 함수
def save_to_postgresql(conn, data):
    with conn.cursor() as cur:
        insert_query = """
        INSERT INTO user_footprint (request, link, footprint_time)
        VALUES (%s, %s, %s)
        """
        cur.execute(
            insert_query, (data["method"], data["link"], data["footprint_time"])
        )
    conn.commit()


def main():
    conf = {
        "bootstrap.servers": os.getenv("BOOTSTRAP_SERVER"),
        "group.id": os.getenv("GROUP_ID"),
        "auto.offset.reset": os.getenv("OFFSET_RESET_CONFIG"),
    }

    consumer = Consumer(conf)
    topic = os.getenv("TOPIC")
    consumer.subscribe([topic])

    logging.info(f"Subscribed to topic: {topic}")

    # PostgreSQL 연결
    pg_conn = get_pg_connection()
    logging.info("PostgreSQL 연결 성공")

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
                    logging.error(f"Kafka error: {msg.error().str()}")
                continue

            try:
                # 메시지 JSON 디코딩
                data = json.loads(msg.value().decode("utf-8"))
                logging.info(f"Received message JSON: {data}")

                # DB 저장
                save_to_postgresql(pg_conn, data)
                logging.info("데이터 PostgreSQL 저장 완료")

            except json.JSONDecodeError as e:
                logging.error(f"JSON 디코딩 실패: {e}")
            except psycopg2.Error as e:
                logging.error(f"PostgreSQL 저장 실패: {e}")

    except KeyboardInterrupt:
        logging.info("Consumer interrupted by user")

    finally:
        consumer.close()
        pg_conn.close()
        logging.info("Consumer 및 PostgreSQL 연결 종료")


if __name__ == "__main__":
    main()
