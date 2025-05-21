
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
- [개발 History](#개발-history)


# eft-library-kafka

> EFT Library의 실시간 데이터를 처리하는 부분입니다.     
> FastAPI의 Middleware를 사용해서 요청이 오는 경우 페이지 주소, 통신 방식, 요청 시간을 Kafka에 넘겨줍니다.       
> Kafka에서 이를 받아 Postgresql, ClickHouse에 적재를 진행하고, 웹에서 통계를 보여주고 있습니다.    
> PostgreSQL과 ClickHouse 두 저장소에 적재하는 이유는 성능 비교를 해보기 위함입니다.

# 구조
![architecture](https://github.com/user-attachments/assets/11fc955e-0516-4dd7-8863-92f4ebb249af)

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

# 개발 History
- 🛠️ [Kafka 환경 구축](https://github.com/eft-library/eft-library-history/main/kafka/kafka_system_development.md)
- 🚀 [ClickHouse와 PostgreSQL 비교 및 테이블 설계](https://github.com/eft-library/eft-library-history/main/kafka/clickhouse_postgresql.md)
- 📊 [대시보드 성능 테스트](https://github.com/eft-library/eft-library-history/main/kafka/dashboard.md)