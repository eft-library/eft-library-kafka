
- [eft-library-kafka](#eft-library-kafka)
- [구조](#구조)
- [환경](#환경)
- [개발 내용](#개발-내용)
- [FastAPI의 Middleware 설정 및 Kafka Producer 서비스 구현](#fastapi의-middleware-설정-및-kafka-producer-서비스-구현)
- [개발 History](#개발-history)


# eft-library-kafka

EFT Library의 실시간 데이터를 처리하는 부분입니다.        
FastAPI의 Middleware를 사용해서 요청이 오는 경우 페이지 주소, 통신 방식, 요청 시간을 Kafka에 넘겨줍니다.          
Kafka에서 이를 받아 Postgresql, ClickHouse에 적재를 진행하고, 웹에서 통계를 보여주고 있습니다.      
PostgreSQL과 ClickHouse 두 저장소에 적재하는 이유는 성능 비교를 해보기 위함입니다.   
Redis를 사용하여 WebSocket에 사용자 알림 데이터를 연결하고 있습니다.

# 구조
![architecture](https://github.com/user-attachments/assets/0aad4cb2-2a18-48e1-832c-436507af67fd)

# 환경

**자원이 한정적이어서 하나의 서버에 Stand-alone으로 동시에 구축했습니다.**

| 항목         | 정보               |
|------------|------------------|
| Kafka      | kafka_2.13-4.1.1 |
| PostgreSQL | PostgreSQL 17.7  |
| ClickHouse | 25.11.2.24       |
| Redis      | remi-8.4         |


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

# 개발 History
- [Kafka 환경 구축](https://github.com/eft-library/eft-library-history/blob/main/kafka/kafka_system_development.md)
- [사용자 방문 통계](https://github.com/eft-library/eft-library-history/blob/main/kafka/user_footprint.md)

<!--
pip install --upgrade pip
pip install redis psycopg2-binary python-dotenv clickhouse-connect confluent-kafka
-->