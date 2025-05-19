import clickhouse_connect
from consumer.config import CH_CONFIG
from consumer.logger import logger


def get_clickhouse_client():
    return clickhouse_connect.get_client(**CH_CONFIG)


def save_to_clickhouse(client, data):
    insert_data = [
        {
            "id": None,  # 서버에서 generateUUIDv4() 자동 생성
            "link": data["link"],
            "request": data["method"],
            "footprint_time": data["footprint_time"],
            "execute_time": None,  # now() 자동
        }
    ]
    client.insert("user_footprint", insert_data)
    logger.info("데이터 ClickHouse 저장 완료")
