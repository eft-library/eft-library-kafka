from consumer.pg_client import get_pg_connection, save_log_to_postgresql
from consumer.ch_client import get_clickhouse_client, save_log_to_clickhouse
from consumer.logger import logger

pg_conn = get_pg_connection()
ch_client = get_clickhouse_client()
logger.info("로그 DB 연결 성공")


def process_log_message(data):
    save_log_to_postgresql(pg_conn, data)
    save_log_to_clickhouse(ch_client, data)
