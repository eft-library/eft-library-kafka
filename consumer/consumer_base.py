import json
from confluent_kafka import Consumer, KafkaError
from consumer.logger import logger


def run_consumer(kafka_config, process_message_callback):
    consumer = Consumer(
        {
            "bootstrap.servers": kafka_config["bootstrap.servers"],
            "group.id": kafka_config["group.id"],
            "auto.offset.reset": kafka_config["auto.offset.reset"],
        }
    )
    topic = kafka_config["topic"]
    consumer.subscribe([topic])
    logger.info(f"Subscribed to topic: {topic}")

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

                process_message_callback(data)

            except json.JSONDecodeError as e:
                logger.error(f"JSON 디코딩 실패: {e}")
            except Exception as e:
                logger.error(f"메시지 처리 실패: {e}")

    except KeyboardInterrupt:
        logger.info("Consumer 종료됨")
    finally:
        consumer.close()
        logger.info("Consumer 연결 종료")
