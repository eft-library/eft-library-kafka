import clickhouse_connect
from consumer.config import CH_CONFIG
from consumer.logger import logger
from datetime import datetime, timezone, timedelta
import re


def parse_timestamptz(dt_str):
    # ISO 8601 포맷 맞춰서 초 단위 이하 자릿수 정리 (필요시)
    # '2025-05-19T13:45:30.123+09:00' 같은 문자열을 datetime 객체로 변환

    # 타임존 오프셋 포함된 부분 분리
    match = re.match(r"(.*)([+-]\d{2}):(\d{2})$", dt_str)
    if match:
        dt_without_tz = match.group(1)
        tz_hours = int(match.group(2))
        tz_minutes = int(match.group(3))
        tz_delta = timezone(timedelta(hours=tz_hours, minutes=tz_minutes))
        dt = datetime.strptime(dt_without_tz, "%Y-%m-%dT%H:%M:%S.%f")
        dt = dt.replace(tzinfo=tz_delta)
    else:
        # 타임존이 Z(UTC)일 경우 처리
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        dt = dt.replace(tzinfo=timezone.utc)

    # UTC로 변환 후 tzinfo 제거
    dt_utc = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt_utc


def get_clickhouse_client():
    return clickhouse_connect.get_client(**CH_CONFIG)


def save_to_clickhouse(client, data):
    query = """
    INSERT INTO prd.user_footprint (link, request, footprint_time)
    VALUES (%(link)s, %(request)s, %(footprint_time)s)
    """

    params = {
        "link": data["link"],
        "request": data["method"],
        "footprint_time": parse_timestamptz(data["footprint_time"]),
    }

    client.execute(query, params)
    logger.info("데이터 ClickHouse 저장 완료")
