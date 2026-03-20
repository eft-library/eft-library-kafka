- [타르코프 도서관의 운영 방식](#타르코프-도서관의-운영-방식)
  * [주요 사항](#주요-사항)
  * [환경 및 패키지 정보](#환경-및-패키지-정보)
  * [개발 내용](#개발-내용)
  * [개발 History](#개발-history)


# 타르코프 도서관의 운영 방식

타르코프 도서관의 실시간 데이터를 처리하는 부분입니다.        

<img width="1314" height="1275" alt="arch_v4" src="https://github.com/user-attachments/assets/0392b55e-14b0-45d8-9aa6-4b83a9cd640f" />

## 주요 사항

- FastAPI의 Middleware를 사용해서 요청이 오는 경우 페이지 주소, 통신 방식, 요청 시간을 Kafka에 넘겨줍니다.          
- Kafka에서 이를 받아 Postgresql에 적재를 진행하고, 웹에서 통계를 보여주고 있습니다.      
- Redis를 사용하여 WebSocket에 사용자 알림 데이터를 연결하고 있습니다.

# 패키지 정보

**자원이 한정적이어서 하나의 서버에 Stand-alone으로 동시에 구축했습니다.**

| 패키지명         | 버전               |
|------------|------------------|
| Kafka      | kafka_2.13-4.1.1 |
| PostgreSQL | PostgreSQL 17.7  |
| Redis      | remi-8.4         |


# 개발 내용

FastAPI 애플리케이션에 **Middleware를 적용하여 Kafka와 연동**하였습니다.

Middleware에서는 사용자 요청에 대해 **접속한 페이지 주소, 방문 시간, 요청 타입 등의 정보를 Kafka로 전송(Produce)**합니다.

사용자 알림 데이터의 경우는 Redis에 저장한 뒤 FastAPI에서 Listen 하고 있다가 Front로 찔러 줍니다.

    1. 시스템 구성
    FastAPI에 Middleware를 구현하여 Kafka 연동, 사용자 요청 시 아래의 정보를 Kafka에 Produce
    data = {
        "method": HTTP 요청 방식,
        "link": 접속한 페이지 주소,
        "footprint_time": 요청 시간,
    }
    
    2. 데이터 파이프라인
    Kafka Consumer는 메시지를 수신하여 PostgreSQL에 데이터를 저장
    
    3. 웹 로그와 사용자 알람정보를 처리
    별도의 프로세스로 분리되어 실행, 개별 동작

## 개발 History

여기에서 확인해 주세요!

[velog 바로가기](https://github.com/eft-library/eft-library-history/blob/main/kafka/user_footprint.md)

<!--
pip install --upgrade pip
pip install redis psycopg2-binary python-dotenv clickhouse-connect confluent-kafka
-->
