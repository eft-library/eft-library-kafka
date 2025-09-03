from consumer.config import LOG_KAFKA_CONFIG
from consumer.consumer_base import run_consumer
from consumer.handlers.log_handler import process_log_message

if __name__ == "__main__":
    run_consumer(LOG_KAFKA_CONFIG, process_log_message)
