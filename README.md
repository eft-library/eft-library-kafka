
- [eft-library-kafka](#eft-library-kafka)
- [구조](#구조)
- [ClickHouse](#clickhouse)
- [ClickHouse VS PostgreSQL](#clickhouse-vs-postgresql)
- [환경](#환경)
- [개발 내용](#개발-내용)
- [PostgreSQL 테이블 생성](#postgresql-테이블-생성)
- [ClickHouse 테이블 생성](#clickhouse-테이블-생성)
- [FastAPI의 Middleware 설정 및 Kafka Producer 서비스 구현](#fastapi의-middleware-설정-및-kafka-producer-서비스-구현)
- [테스트 결과 및 성능 비교 (1만, 10만, 100만)](#테스트-결과-및-성능-비교-1만-10만-100만)
- [내구내적(내가 직접 구축해서 직접 적용해봄) ClickHouse의 단점](#내구내적내가-직접-구축해서-직접-적용해봄-clickhouse의-단점)
- [번외: 서버에 구축하기](#번외-서버에-구축하기)
- [번외: Kafka 코드](#번외-kafka-코드)


# eft-library-kafka

> EFT Library의 실시간 데이터를 처리하는 부분입니다.
> 
> FastAPI의 Middleware를 사용해서 요청이 오는 경우 페이지 주소, 통신 방식, 요청 시간을 Kafka에 넘겨줍니다.
> 
> Kafka에서 이를 받아 Postgresql, ClickHouse에 적재를 진행하고, 웹에서 통계를 보여주고 있습니다.
> 
> PostgreSQL과 ClickHouse 두 저장소에 적재하는 이유는 성능 비교를 해보기 위함입니다.

# 구조
![architecture](https://github.com/user-attachments/assets/11fc955e-0516-4dd7-8863-92f4ebb249af)

# ClickHouse 
ClickHouse는 Yandex에서 개발한 **오픈소스 컬럼 지향(column-oriented) 데이터베이스 관리 시스템(DBMS)** 입니다.

**OLAP(Online Analytical Processing) 용도로 설계**되어, 대용량 데이터의 빠른 집계 및 분석에 특화되어 있습니다.
- 데이터는 컬럼 단위로 저장됨
- 실시간 분석 쿼리 성능에 강점
- 분산 처리 및 병렬 쿼리에 최적화
- SQL 지원 (표준 SQL과 유사)
- Druid와 유사한 분산처리 구조, Shard와 Replica 구조로 노드를 나눌 수 있음
- Distributed Table을 사용하면 여러 Shard에 분산된 테이블을 추상적으로 하나로 보이게 할 수 있음

특징은 아래와 같습니다.

| 특징        | 설명                                                  |
|-----------|-----------------------------------------------------|
| 컬럼 기반 저장  | 필요한 컬럼만 읽기 때문에 대용량 데이터에서도 빠름                        |
| 고속 집계     | 수십억 행의 데이터도 매우 빠르게 집계 가능                            |
| 분산 구조     | 수평 확장이 용이하고 클러스터링 지원                                |
| 실시간 분석    | 로그/이벤트 데이터를 빠르게 분석 가능                               |
| 압축 효율     | 높은 압축률로 디스크 공간 절약 가능                                |
| 다양한 엔진 지원 | MergeTree, SummingMergeTree, AggregatingMergeTree 등 |


# ClickHouse VS PostgreSQL

Kafka를 통해서 페이지 방문 History 관련 대시보드와 통계를 표현할 것이기에 해당 관점에서 비교한 내용입니다.

| 항목      | **ClickHouse**             | **PostgreSQL**                  |
|---------|----------------------------|---------------------------------|
| 처리 시간   | 0.3 \~ 2초 (분산 환경일 경우 더 빠름) | 5 \~ 30초 (인덱스 최적화 되어 있어도 느림)    |
| CPU 사용량 | 높음 (멀티코어 활용)               | 보통 (싱글 프로세스 위주)                 |
| RAM 사용량 | 비교적 효율적                    | 집계 시 메모리 사용 많음                  |
| 병렬 처리   | 자동 병렬 실행                   | 병렬 처리 옵션 제한적 (`parallel` 설정 필요) |
| I/O 처리  | 컬럼만 디스크에서 읽음               | 전체 행 읽기 필요                      |
| 확장성     | 노드 추가 시 성능 향상              | 수직 확장에 의존                       |



# 환경

**자원이 한정적이어서 하나의 서버에 Stand-alone으로 동시에 구축했습니다.**

| 항목         | 정보                                        |
|------------|-------------------------------------------|
| Kafka      | kafka_2.13-4.0.0 (KRaft 모드, Zookeeper 제거) |
| PostgreSQL | PostgreSQL 17.4                           |
| ClickHouse | 25.4.4.25                                 |


# 개발 내용

FastAPI 애플리케이션에 **Middleware를 적용하여 Kafka와 연동**하였습니다.

Middleware에서는 사용자 요청에 대해 **접속한 페이지 주소, 방문 시간, 요청 타입 등의 정보를 Kafka로 전송(Produce)**합니다.

이후 Kafka Consumer를 통해 해당 데이터를 PostgreSQL과 ClickHouse에 동시에 적재한 뒤,

이 데이터를 기반으로 통계 쿼리를 수행하여 **두 데이터베이스 간 성능을 비교**하고자 합니다.

    1. 시스템 구성
    FastAPI에 Middleware를 구현하여 Kafka 연동, 사용자 요청 시 아래의 정보를 Kafka에 Produce
    data = {
        "method": HTTP 요청 방식,
        "link": 접속한 페이지 주소,
        "footprint_time": 요청 시간,
    }
    
    2. 데이터 파이프라인
    Kafka Consumer는 메시지를 수신하여 PostgreSQL, ClickHouse 두 데이터베이스에 동시에 데이터를 저장
    
    3. 분석 및 실험 목적
    동일한 데이터셋에 대해 통계 쿼리를 수행, PostgreSQL과 ClickHouse의 집계 쿼리 처리 성능을 비교 분석

# PostgreSQL 테이블 생성

PostgreSQL USER_FOOTPRINT 테이블 생성

```sql
CREATE TABLE USER_FOOTPRINT
(
  ID SERIAL PRIMARY KEY,
  LINK TEXT,
  REQUEST TEXT,
  FOOTPRINT_TIME timestamp with time zone,
  EXECUTE_TIME timestamp with time zone default now()
);
COMMENT ON COLUMN USER_FOOTPRINT.ID IS '사용자 기록 아이디';
COMMENT ON COLUMN USER_FOOTPRINT.REQUEST IS '사용자 기록 요청 타입';
COMMENT ON COLUMN USER_FOOTPRINT.LINK IS '사용자 기록 주소';
COMMENT ON COLUMN USER_FOOTPRINT.FOOTPRINT_TIME IS '사용자 기록 전송 시간';
COMMENT ON COLUMN USER_FOOTPRINT.EXECUTE_TIME IS '사용자 기록 적재 시간';
```

**TMI**

PostgreSQL에서 VARCHAR가 아닌 TEXT 타입의 장점

    1. 길이 제한의 실효성 부족
    대부분 VARCHAR(n)의 n은 "어림짐작"으로 정함. (예: VARCHAR(255))
    실질적으로는 대부분의 경우 그 제한이 논리적인 필요가 아닌 습관
    → 나중에 값이 초과되면 불필요한 에러 유발

    2. 성능은 사실상 동일
    PostgreSQL 내부에서는 TEXT, VARCHAR(n), VARCHAR 모두 동일한 방식(TOAST) 으로 처리
    심지어 PostgreSQL에서는 VARCHAR(n)도 내부적으로 TEXT + CHECK(length <= n)으로 처리
    
    3. 더 간결한 스키마 설계
    TEXT는 길이 제한이 없어서 유연하게 사용할 수 있고, 추후 변경이 필요 없움
    스키마를 간단하게 유지할 수 있음

# ClickHouse 테이블 생성

ClickHouse USER_FOOTPRINT 테이블 생성

**ClickHouse는 PostgreSQL과 다르게 Serial로 자동 생성을 할 수 없고 UUID로 해야 합니다.**

```sql
CREATE TABLE user_footprint
(
    id UUID DEFAULT generateUUIDv4(),
    link String,
    request String,
    footprint_time DateTime64(3),
    execute_time DateTime64(3) DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(footprint_time)
ORDER BY (footprint_time);
```

# FastAPI의 Middleware 설정 및 Kafka Producer 서비스 구현

**main.py**

```python
@app.middleware("http")
async def kafka_producer_middleware(request: Request, call_next):
    now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
    footprint_time = now_kst.isoformat()
    data = {
        "method": request.method,
        "link": request.url.path,
        "footprint_time": footprint_time,
    }
    json_str = json.dumps(data)
    produce_message(json_str)
    response = await call_next(request)
    return response
```

**kafka_producer.py**

```python
BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER")
TOPIC = os.getenv("TOPIC")

producer_conf = {"bootstrap.servers": BOOTSTRAP_SERVER, "client.id": "fastapi-producer"}
producer = Producer(producer_conf)


def delivery_report(err, msg):
    if err:
        logging.error(f"Delivery failed: {err}")
    else:
        logging.info(f"Delivered message to {msg.topic()} [{msg.partition()}]")


def produce_message(value: str):
    producer.produce(TOPIC, value=value.encode("utf-8"), callback=delivery_report)
    producer.poll(0)
```

# 테스트 결과 및 성능 비교 (1만, 10만, 100만)

대시보드 통계 정보

    1. 기간별 상위 10개 Request 타입 및 엔드포인트별 요청 수 => BarChart
    2. 기간별 총 요청수 => 상단 중앙에 큰 숫자
    3. 기간별 요청 시간대별 분포 => Heatmap / Histogram (01:15 ~ 01:17 집중됨)

아직 데이터가 많이 쌓이지 않음

# 내구내적(내가 직접 구축해서 직접 적용해봄) ClickHouse의 단점

매초 데이터를 실시간으로 넣으면 내부에서 쓰기 병합(Merge) 지연 발생 가능, **삽입 속도가 좀 느림.**

예: 초당 많은 데이터가 Kafka에서 들어오면 → 내부 병합이 쌓이고 → 대시보드에서 2 ~ 5초 이상 늦게 보일 수 있음


# 번외: 서버에 구축하기
PostgreSQL은 이미 설치되어 있어야 하고, Kafka와 ClickHouse를 구축하고, 연동하는 과정 입니다.

**Stand-alone으로 구성**, 자원이 없습니다;;;

구축하기에 앞서 **Ubuntu 커널 매개변수를 활성화 하는 이유**

    Delay accounting은 Linux 커널에서 프로세스가 I/O, 스케줄링 지연, 대기 등으로 인해 실제로 실행되지 못한 시간을 측정하는 기능입니다.
    OSIOWaitMicroseconds는 ClickHouse가 내부적으로 프로세스 지연 시간(특히 I/O 대기 시간)을 수집하기 위해 필요한 데이터입니다.
    이 기능이 켜져 있지 않으면, ClickHouse가 지연 관련 통계를 정확히 수집하지 못해서 성능 진단 등에 제한이 생길 수 있습니다.

**구축 과정**

```shell
# java 21 설치
apt install openjdk-21-jre-headless

# kafka 4.0.0 다운로드 및 압축해제
wget https://downloads.apache.org/kafka/4.0.0/kafka_2.13-4.0.0.tgz
tar -xzf kafka_2.13-4.0.0.tgz

# 외부에서 접근할 수 있게 방화벽 해제
ufw allow 8123
ufw allow 9232 # 기본 port는 9000임, 현재 환경에서는 겹치기에 9232로 변경해서 사용

# 로그 디렉토리 초기화 (메타 데이터 설정)
bin/kafka-storage.sh format --config config/server.properties --cluster-id $(bin/kafka-storage.sh random-uuid) --standalone

# Kafka Stand-alone 구동 테스트
# 토픽 생성
/home/kafka/kafka_2.13-4.0.0/bin/kafka-topics.sh --create --topic web-logs-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

# 토픽 리스트 확인
/home/kafka/kafka_2.13-4.0.0/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# 메시지 Producer
/home/kafka/kafka_2.13-4.0.0/bin/kafka-console-producer.sh --topic web-logs-topic --bootstrap-server localhost:9092

# 메시지 Consume
/home/kafka/kafka_2.13-4.0.0/bin/kafka-console-consumer.sh --topic web-logs-topic --from-beginning --bootstrap-server localhost:9092

# 이전에 작성한 FastAPI를 사용해서 Middleware Producer 개발

# 이전에 작성한 PostgreSQL 테이블 생성

# ClickHouse Stand-alone
# Ubuntu 커널 매개변수 활성화 - 재부팅해도 적용되게 설정
echo 1 | sudo tee /proc/sys/kernel/task_delayacct
sudo sh -c 'echo "kernel.task_delayacct=1" >> /etc/sysctl.conf'
sudo sysctl -p

# ClickHouse Package 설정 및 설치 - 설치 할 때 default 계정 비밀번호 입력하라고 나오면 입력
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

ARCH=$(dpkg --print-architecture)

echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main" | sudo tee /etc/apt/sources.list.d/clickhouse.list

sudo apt install clickhouse-server clickhouse-client -y

# ClickHouse 설정 수정
sudo vi /etc/clickhouse-server/config.xml

# 이미 사용중인 port가 있어서 안겹치게 수정
tcp port 9000 => 9232

# 외부에서도 접속할 수 있게 0.0.0.0으로 변경
<listen_host>0.0.0.0</listen_host>

# 저장
:w!

# ClickHouse 실행 및 접속 - 설치할 때 입력한 default 계정의 비밀번호 입력 필요
sudo clickhouse start
clickhouse-client --port 9232 # port가 달라서 부여한 값

# ClickHouse 사용자, DB 생성 및 권한 부여
create database prd;
create user test IDENTIFIED With plaintext_password by 'password';
GRANT SELECT, INSERT, CREATE, UPDATE, DELETE, TRUNCATE, DROP ON prd.* TO test;

# 이전에 작성한 ClickHouse 테이블 생성
```

# 번외: Kafka 코드

초창기에 작성하여 적용한 버전입니다.

**config.py**
```python
import os
from dotenv import load_dotenv

load_dotenv()

LOG_DIR = os.getenv("LOG_DIR", "./logs")
LOG_FILE = os.path.join(LOG_DIR, "consumer.log")

# PostgreSQL
PG_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# ClickHouse
CH_CONFIG = {
    "host": os.getenv("CH_HOST", "localhost"),
    "port": int(os.getenv("CH_PORT", "8123")),
    "username": os.getenv("CH_USER", "default"),
    "password": os.getenv("CH_PASSWORD", ""),
}

# Kafka
KAFKA_CONFIG = {
    "bootstrap.servers": os.getenv("BOOTSTRAP_SERVER"),
    "group.id": os.getenv("GROUP_ID"),
    "auto.offset.reset": os.getenv("OFFSET_RESET_CONFIG"),
    "topic": os.getenv("TOPIC"),
}
```

**ch_client.py**
```python
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

    client.command(query, params)
    logger.info("데이터 ClickHouse 저장 완료")
```

**pg_client.py**
```python
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

```

**main.py**
```python
import json
from confluent_kafka import Consumer, KafkaError
from consumer.logger import logger
from consumer.config import KAFKA_CONFIG
from consumer.pg_client import get_pg_connection, save_to_postgresql
from consumer.ch_client import get_clickhouse_client, save_to_clickhouse


def main():
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_CONFIG["bootstrap.servers"],
            "group.id": KAFKA_CONFIG["group.id"],
            "auto.offset.reset": KAFKA_CONFIG["auto.offset.reset"],
        }
    )
    topic = KAFKA_CONFIG["topic"]
    consumer.subscribe([topic])
    logger.info(f"Subscribed to topic: {topic}")

    pg_conn = get_pg_connection()
    ch_client = get_clickhouse_client()
    logger.info("DB 연결 성공")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.warning(
                        f"End of partition: {msg.topic()} [{msg.partition()}]"
                    )
                else:
                    logger.error(f"Kafka error: {msg.error().str()}")
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                logger.info(f"Received message JSON: {data}")

                save_to_postgresql(pg_conn, data)
                save_to_clickhouse(ch_client, data)

            except json.JSONDecodeError as e:
                logger.error(f"JSON 디코딩 실패: {e}")
            except Exception as e:
                logger.error(f"DB 저장 실패: {e}")

    except KeyboardInterrupt:
        logger.info("Consumer 종료됨")

    finally:
        consumer.close()
        pg_conn.close()
        logger.info("Consumer 및 PostgreSQL 연결 종료")


if __name__ == "__main__":
    main()
```

<!--
```shell
./kafka.sh start      # 시작
./kafka.sh stop       # 종료
./kafka.sh restart    # 재시작
./kafka.sh status     # 상태 확인

./consumer.sh start
./consumer.sh stop
./consumer.sh restart
./consumer.sh status
```


```
pip install confluent-kafka
pip install python-dotenv
pip install psycopg2-binary
pip install clickhouse-connect
```
-->
