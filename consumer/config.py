import os
from dotenv import load_dotenv

load_dotenv()

LOG_DIR = os.getenv("LOG_DIR", "./logs")
LOG_FILE = os.path.join(LOG_DIR, "consumer.log")

# PostgreSQL
PG_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# ClickHouse
CH_CONFIG = {
    "host": os.getenv("CH_HOST", "localhost"),
    "port": int(os.getenv("CH_PORT", "8123")),
    "username": os.getenv("CH_USER", "default"),
    "password": os.getenv("CH_PASSWORD", ""),
}

# Kafka
KAFKA_CONFIG = {
    "bootstrap.servers": os.getenv("BOOTSTRAP_SERVER"),
    "group.id": os.getenv("GROUP_ID"),
    "auto.offset.reset": os.getenv("OFFSET_RESET_CONFIG"),
    "topic": os.getenv("TOPIC"),
}
