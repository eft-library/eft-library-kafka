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