from confluent_kafka import Consumer, KafkaError
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    conf = {
        "bootstrap.servers": os.getenv("BOOTSTAP_SERVER"),  # Kafka 브로커 주소
        "group.id": os.getenv("GROUP_ID"),  # Consumer 그룹명
        "auto.offset.reset": os.getenv("OFFSET_RESET_CONFIG"),  # 처음부터 읽기
    }

    consumer = Consumer(conf)

    topic = "test-topics"
    consumer.subscribe([topic])

    print(f"Subscribed to topic: {topic}")

    try:
        while True:
            msg = consumer.poll(1.0)  # 1초 대기
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # 파티션 끝에 도달한 경우
                    print(f"End of partition reached {msg.topic()} [{msg.partition()}]")
                else:
                    print(f"Error occurred: {msg.error().str()}")
            else:
                # 메시지 수신
                print(f"Received message: {msg.value().decode('utf-8')}")
                # 여기서 ClickHouse/PostgreSQL 저장 로직 추가 가능

    except KeyboardInterrupt:
        print("Consumer stopped by user")

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
