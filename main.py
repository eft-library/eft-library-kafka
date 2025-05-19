import json
from confluent_kafka import Consumer, KafkaError
from logger import logger
from config import KAFKA_CONFIG
from pg_client import get_pg_connection, save_to_postgresql
from ch_client import get_clickhouse_client, save_to_clickhouse


def main():
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_CONFIG["bootstrap.servers"],
            "group.id": KAFKA_CONFIG["group.id"],
            "auto.offset.reset": KAFKA_CONFIG["auto.offset.reset"],
        }
    )
    topic = KAFKA_CONFIG["topic"]
    consumer.subscribe([topic])
    logger.info(f"Subscribed to topic: {topic}")

    pg_conn = get_pg_connection()
    ch_client = get_clickhouse_client()
    logger.info("DB 연결 성공")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.warning(
                        f"End of partition: {msg.topic()} [{msg.partition()}]"
                    )
                else:
                    logger.error(f"Kafka error: {msg.error().str()}")
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                logger.info(f"Received message JSON: {data}")

                save_to_postgresql(pg_conn, data)
                save_to_clickhouse(ch_client, data)

            except json.JSONDecodeError as e:
                logger.error(f"JSON 디코딩 실패: {e}")
            except Exception as e:
                logger.error(f"DB 저장 실패: {e}")

    except KeyboardInterrupt:
        logger.info("Consumer 종료됨")

    finally:
        consumer.close()
        pg_conn.close()
        logger.info("Consumer 및 PostgreSQL 연결 종료")


if __name__ == "__main__":
    main()
