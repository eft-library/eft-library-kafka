import psycopg2
from consumer.config import PG_CONFIG
from consumer.logger import logger


def get_pg_connection():
    return psycopg2.connect(**PG_CONFIG)


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
    logger.info("데이터 PostgreSQL 저장 완료")
