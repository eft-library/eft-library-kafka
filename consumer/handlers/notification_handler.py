import json
import redis
from consumer.pg_client import get_pg_connection
from consumer.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()
# PostgreSQL 연결
pg_conn = get_pg_connection()
logger.info("알림 DB 연결 성공")

# Redis 연결
redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    db=int(os.getenv("REDIS_DB")),
    decode_responses=True,
)
logger.info("Redis 연결 성공")


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
                RETURNING user_email
            """
            cur.execute(
                insert_query,
                {
                    "noti_type": data["noti_type"],
                    "payload": json.dumps(data),
                    "author_email": data["author_email"],
                },
            )

            # DB에 들어간 user_email 목록 가져오기
            notified_users = [row[0] for row in cur.fetchall()]

        pg_conn.commit()

        # Redis에 알림 데이터 저장

        for user_email in notified_users:
            redis_key = f"notifications:{user_email}"
            redis_client.lpush(redis_key, json.dumps(data))
            # 필요하다면 TTL도 설정 가능 (예: 7일)
            redis_client.expire(redis_key, 60 * 60 * 24 * 7)

        logger.info(f"알림 처리 완료: {data} (Redis에도 저장됨)")

    except Exception as e:
        logger.error(f"알림 처리 실패: {e}")
        pg_conn.rollback()
