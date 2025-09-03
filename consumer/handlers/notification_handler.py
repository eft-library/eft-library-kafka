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
        "author_email": "writer@test.com"
    }
    """
    try:
        # DB 저장
        # follow 한 사람들을 먼저 찾고 저장해야 함
        with pg_conn.cursor() as cur:
            cur.execute(
                """
                insert into user_notifications (user_email, noti_type, payload)
                values ()
                """,
                (data["title"], data["url"], data["author_email"]),
            )
        pg_conn.commit()

        # redis에 알림 보내기
        # fastapi websocket이 redis를 subscribe 하고, 온 게 있으면 바로 발송
        # 데이터는 게시글, 알림 대상 사용자 같이 보내기

        logger.info(f"알림 처리 완료: {data}")

    except Exception as e:
        logger.error(f"알림 처리 실패: {e}")
