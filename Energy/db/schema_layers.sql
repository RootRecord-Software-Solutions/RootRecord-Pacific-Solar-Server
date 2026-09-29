PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS aggregation_run (
    aggregation_run_id INTEGER PRIMARY KEY,
    layer TEXT NOT NULL CHECK (layer IN ('1sec','1min','5min','15min','1hour','day','7days','month','year')),
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    source_layer TEXT,
    status TEXT NOT NULL CHECK (status IN ('running','complete','failed')),
    started_at TEXT NOT NULL,
    completed_at TEXT,
    source_watermark TEXT,
    row_count INTEGER,
    UNIQUE(layer, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS aggregate_measurement (
    aggregate_measurement_id INTEGER PRIMARY KEY,
    aggregation_run_id INTEGER NOT NULL,
    subject_type TEXT NOT NULL CHECK (subject_type IN ('device','battery','port')),
    subject_id INTEGER NOT NULL,
    metric_key TEXT NOT NULL,
    unit TEXT,
    sample_count INTEGER NOT NULL DEFAULT 0,
    valid_sample_count INTEGER NOT NULL DEFAULT 0,
    expected_sample_count INTEGER,
    coverage_pct REAL,
    observed_span_s REAL,
    valid_duration_s REAL,
    value_avg REAL,
    value_min REAL,
    value_max REAL,
    value_sum REAL,
    value_delta REAL,
    energy_wh REAL,
    state TEXT NOT NULL CHECK (state IN ('measured','missing','not_applicable')),
    FOREIGN KEY(aggregation_run_id) REFERENCES aggregation_run(aggregation_run_id) ON DELETE CASCADE,
    UNIQUE(aggregation_run_id, subject_type, subject_id, metric_key)
);

CREATE INDEX IF NOT EXISTS idx_aggregation_layer_period
    ON aggregation_run(layer, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_aggregate_metric
    ON aggregate_measurement(subject_type, subject_id, metric_key, aggregation_run_id);
