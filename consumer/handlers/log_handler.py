from consumer.pg_client import get_pg_connection, save_log_to_postgresql
from consumer.logger import logger

pg_conn = get_pg_connection()
logger.info("로그 DB 연결 성공")


def process_log_message(data):
    save_log_to_postgresql(pg_conn, data)
