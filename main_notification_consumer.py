from consumer.config import NOTIFICATION_KAFKA_CONFIG
from consumer.consumer_base import run_consumer
from consumer.handlers.notification_handler import process_notification_message

if __name__ == "__main__":
    run_consumer(NOTIFICATION_KAFKA_CONFIG, process_notification_message)
