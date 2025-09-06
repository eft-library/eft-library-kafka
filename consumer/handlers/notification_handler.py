import json
import redis
from consumer.pg_client import get_pg_connection
from consumer.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()
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


def save_notifications_and_push_to_redis(cur, query, params, data):
    """
    공통 함수: DB에 알림 저장 후 Redis에 push
    """
    cur.execute(query, params)
    notified_users = [row[0] for row in cur.fetchall()]
    pg_conn.commit()

    for user_email in notified_users:
        redis_key = f"notifications:{user_email}"
        redis_client.lpush(redis_key, json.dumps(data))
        redis_client.expire(redis_key, 60 * 60 * 24 * 7)  # TTL 7일

    return notified_users


def process_notification_message(data):
    """
    알림 처리하기
    """
    try:
        with pg_conn.cursor() as cur:
            if data["noti_type"] == "create_post":
                # 팔로우한 사용자에게 알림
                insert_query = """
                    INSERT INTO user_notifications (user_email, noti_type, payload)
                    SELECT uf.following_email, %(noti_type)s, %(payload)s
                    FROM user_follows uf
                    WHERE uf.follower_email = %(author_email)s
                    RETURNING user_email
                """
                params = {
                    "noti_type": data["noti_type"],
                    "payload": json.dumps(data),
                    "author_email": data["author_email"],
                }
                save_notifications_and_push_to_redis(cur, insert_query, params, data)

            elif data["noti_type"] == "create_parent_comment":
                # 게시글 작성자에게 알림
                insert_query = """
                    INSERT INTO user_notifications (user_email, noti_type, payload)
                    SELECT cp.user_email, %(noti_type)s, %(payload)s
                    FROM community_posts cp
                    WHERE cp.id = %(post_id)s
                    RETURNING user_email
                """
                params = {
                    "noti_type": data["noti_type"],
                    "payload": json.dumps(data),
                    "post_id": data["post_id"],
                }
                save_notifications_and_push_to_redis(cur, insert_query, params, data)
            elif data["noti_type"] == "create_child_comment":
                # 부모 댓글에 알림
                insert_query = """
                    INSERT INTO user_notifications (user_email, noti_type, payload)
                    SELECT cc.user_email, %(noti_type)s, %(payload)s
                    FROM community_comments cc
                    WHERE cc.id = %(parent_comment_id)s
                    RETURNING user_email
                """
                params = {
                    "noti_type": data["noti_type"],
                    "payload": json.dumps(data),
                    "parent_comment_id": data["parent_comment_id"],
                }
                save_notifications_and_push_to_redis(cur, insert_query, params, data)

        logger.info(f"알림 처리 완료: {data} (Redis Save)")

    except Exception as e:
        logger.error(f"알림 처리 실패: {e}")
        pg_conn.rollback()
