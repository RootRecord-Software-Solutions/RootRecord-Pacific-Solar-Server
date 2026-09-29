-- RootRecord SYSTEM raw + layer schema (mirrors energy pattern, host metrics only)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS observation (
    observation_id   INTEGER PRIMARY KEY,
    observed_at      TEXT NOT NULL,          -- UTC ISO
    host             TEXT NOT NULL DEFAULT 'host',
    source           TEXT NOT NULL DEFAULT 'proc',
    UNIQUE(observed_at, host, source)
);

CREATE TABLE IF NOT EXISTS measurement (
    measurement_id   INTEGER PRIMARY KEY,
    observation_id   INTEGER NOT NULL REFERENCES observation(observation_id) ON DELETE CASCADE,
    metric_key       TEXT NOT NULL,
    value_num        REAL,
    unit             TEXT,
    state            TEXT NOT NULL CHECK (state IN ('measured','missing','defaulted','not_applicable')),
    UNIQUE(observation_id, metric_key)
);

CREATE INDEX IF NOT EXISTS idx_observation_at ON observation(observed_at);
CREATE INDEX IF NOT EXISTS idx_measurement_obs ON measurement(observation_id);
CREATE INDEX IF NOT EXISTS idx_measurement_key ON measurement(metric_key);

-- Used by every layer file
CREATE TABLE IF NOT EXISTS aggregation_run (
    aggregation_run_id INTEGER PRIMARY KEY,
    layer              TEXT NOT NULL,
    period_start       TEXT NOT NULL,
    period_end         TEXT NOT NULL,
    source_layer       TEXT NOT NULL DEFAULT 'raw',
    status             TEXT NOT NULL CHECK (status IN ('running','complete','failed')),
    started_at         TEXT,
    completed_at       TEXT,
    source_watermark   TEXT,
    row_count          INTEGER,
    UNIQUE(layer, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS aggregate_measurement (
    aggregate_measurement_id INTEGER PRIMARY KEY,
    aggregation_run_id       INTEGER NOT NULL REFERENCES aggregation_run(aggregation_run_id) ON DELETE CASCADE,
    metric_key               TEXT NOT NULL,
    unit                     TEXT,
    sample_count             INTEGER,
    valid_sample_count       INTEGER,
    coverage_pct             REAL,
    observed_span_s          REAL,
    valid_duration_s         REAL,
    value_avg                REAL,
    value_min                REAL,
    value_max                REAL,
    value_sum                REAL,
    value_delta              REAL,
    state                    TEXT,
    UNIQUE(aggregation_run_id, metric_key)
);
