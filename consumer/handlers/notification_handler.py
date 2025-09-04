import json
from consumer.pg_client import get_pg_connection
from consumer.logger import logger

pg_conn = get_pg_connection()
logger.info("알림 DB 연결 성공")


def process_notification_message(data):
    """
    data 예시:
    {
        "url": "123-hello-world",
        "title": "새 글입니다",
        "author_email": "writer@test.com",
        "noti_type": "create_post",
    }
    """
    try:
        with pg_conn.cursor() as cur:
            insert_query = """
                INSERT INTO user_notifications (user_email, noti_type, payload)
                SELECT uf.following_email, %(noti_type)s, %(payload)s
                FROM user_follows uf
                WHERE uf.follower_email = %(author_email)s
            """
            cur.execute(
                insert_query,
                {
                    "noti_type": data["noti_type"],
                    "payload": json.dumps(data),
                    "author_email": data["author_email"],
                },
            )

        pg_conn.commit()
        logger.info(f"알림 처리 완료 (DB 한방): {data}")

    except Exception as e:
        logger.error(f"알림 처리 실패: {e}")
        pg_conn.rollback()
