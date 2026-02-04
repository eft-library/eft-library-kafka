import logging
import os
from logging.handlers import TimedRotatingFileHandler
from consumer.config import LOG_DIR, LOG_FILE

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("consumer")
logger.setLevel(logging.INFO)
logger.propagate = False  # root logger 전파 방지

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # 🔹 매일 새로운 파일로 롤링
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d.log"  # 기존 로그에 날짜 붙이기
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
