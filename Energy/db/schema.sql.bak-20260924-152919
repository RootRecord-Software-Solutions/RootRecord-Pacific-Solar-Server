PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS device (
    device_id INTEGER PRIMARY KEY,
    serial_number TEXT NOT NULL UNIQUE,
    model TEXT NOT NULL,
    alias TEXT,
    role TEXT,
    ble_address TEXT,
    manufacturer TEXT NOT NULL DEFAULT 'EcoFlow',
    first_seen_at TEXT,
    last_seen_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS battery (
    battery_id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    battery_role TEXT NOT NULL CHECK (battery_role IN ('primary','expansion')),
    battery_slot INTEGER,
    serial_number TEXT,
    enabled INTEGER CHECK (enabled IN (0,1)),
    first_seen_at TEXT,
    last_seen_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(device_id, battery_role, battery_slot),
    FOREIGN KEY(device_id) REFERENCES device(device_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS device_port (
    port_id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    port_type TEXT NOT NULL,
    port_index INTEGER,
    label TEXT,
    first_seen_at TEXT,
    last_seen_at TEXT,
    UNIQUE(device_id, port_type, port_index),
    FOREIGN KEY(device_id) REFERENCES device(device_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS observation_source (
    source_id INTEGER PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_name TEXT,
    source_version TEXT,
    parser_name TEXT,
    parser_version TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observation (
    observation_id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL,
    observed_at TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    online INTEGER CHECK (online IN (0,1)),
    connection_state TEXT,
    source_sequence INTEGER,
    quality TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(device_id, observed_at, source_id, source_sequence),
    FOREIGN KEY(device_id) REFERENCES device(device_id) ON DELETE CASCADE,
    FOREIGN KEY(source_id) REFERENCES observation_source(source_id)
);

CREATE TABLE IF NOT EXISTS device_measurement (
    device_measurement_id INTEGER PRIMARY KEY,
    observation_id INTEGER NOT NULL,
    metric_key TEXT NOT NULL,
    value_num REAL,
    value_text TEXT,
    value_bool INTEGER CHECK (value_bool IN (0,1)),
    unit TEXT,
    state TEXT NOT NULL CHECK (state IN ('measured','defaulted','missing','not_applicable')),
    FOREIGN KEY(observation_id) REFERENCES observation(observation_id) ON DELETE CASCADE,
    CHECK (
        (state IN ('missing','not_applicable') AND value_num IS NULL AND value_text IS NULL AND value_bool IS NULL)
        OR
        (state IN ('measured','defaulted') AND
            ((value_num IS NOT NULL) + (value_text IS NOT NULL) + (value_bool IS NOT NULL)) = 1)
    ),
    UNIQUE(observation_id, metric_key)
);

CREATE TABLE IF NOT EXISTS battery_measurement (
    battery_measurement_id INTEGER PRIMARY KEY,
    observation_id INTEGER NOT NULL,
    battery_id INTEGER NOT NULL,
    metric_key TEXT NOT NULL,
    value_num REAL,
    value_text TEXT,
    value_bool INTEGER CHECK (value_bool IN (0,1)),
    unit TEXT,
    state TEXT NOT NULL CHECK (state IN ('measured','defaulted','missing','not_applicable')),
    FOREIGN KEY(observation_id) REFERENCES observation(observation_id) ON DELETE CASCADE,
    FOREIGN KEY(battery_id) REFERENCES battery(battery_id) ON DELETE CASCADE,
    CHECK (
        (state IN ('missing','not_applicable') AND value_num IS NULL AND value_text IS NULL AND value_bool IS NULL)
        OR
        (state IN ('measured','defaulted') AND
            ((value_num IS NOT NULL) + (value_text IS NOT NULL) + (value_bool IS NOT NULL)) = 1)
    ),
    UNIQUE(observation_id, battery_id, metric_key)
);

CREATE TABLE IF NOT EXISTS electrical_measurement (
    electrical_measurement_id INTEGER PRIMARY KEY,
    observation_id INTEGER NOT NULL,
    channel TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    value_num REAL,
    unit TEXT,
    state TEXT NOT NULL CHECK (state IN ('measured','defaulted','missing','not_applicable')),
    FOREIGN KEY(observation_id) REFERENCES observation(observation_id) ON DELETE CASCADE,
    CHECK (
        (state IN ('missing','not_applicable') AND value_num IS NULL)
        OR
        (state IN ('measured','defaulted') AND value_num IS NOT NULL)
    ),
    UNIQUE(observation_id, channel, metric_key)
);

CREATE TABLE IF NOT EXISTS port_measurement (
    port_measurement_id INTEGER PRIMARY KEY,
    observation_id INTEGER NOT NULL,
    port_id INTEGER NOT NULL,
    metric_key TEXT NOT NULL,
    value_num REAL,
    value_text TEXT,
    value_bool INTEGER CHECK (value_bool IN (0,1)),
    unit TEXT,
    state TEXT NOT NULL CHECK (state IN ('measured','defaulted','missing','not_applicable')),
    FOREIGN KEY(observation_id) REFERENCES observation(observation_id) ON DELETE CASCADE,
    FOREIGN KEY(port_id) REFERENCES device_port(port_id) ON DELETE CASCADE,
    CHECK (
        (state IN ('missing','not_applicable') AND value_num IS NULL AND value_text IS NULL AND value_bool IS NULL)
        OR
        (state IN ('measured','defaulted') AND
            ((value_num IS NOT NULL) + (value_text IS NOT NULL) + (value_bool IS NOT NULL)) = 1)
    ),
    UNIQUE(observation_id, port_id, metric_key)
);

CREATE TABLE IF NOT EXISTS observation_raw (
    observation_id INTEGER PRIMARY KEY,
    payload_format TEXT NOT NULL,
    payload TEXT NOT NULL,
    parser_name TEXT,
    parser_version TEXT,
    FOREIGN KEY(observation_id) REFERENCES observation(observation_id) ON DELETE CASCADE
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

CREATE UNIQUE INDEX IF NOT EXISTS uq_observation_identity_without_sequence
    ON observation(device_id, observed_at, source_id)
    WHERE source_sequence IS NULL;

CREATE INDEX IF NOT EXISTS idx_observation_device_time
    ON observation(device_id, observed_at);

CREATE INDEX IF NOT EXISTS idx_battery_device
    ON battery(device_id);

CREATE INDEX IF NOT EXISTS idx_battery_measurement_time
    ON battery_measurement(battery_id, observation_id);

CREATE INDEX IF NOT EXISTS idx_device_measurement_time
    ON device_measurement(observation_id, metric_key);

CREATE INDEX IF NOT EXISTS idx_electrical_measurement_channel
    ON electrical_measurement(observation_id, channel, metric_key);

CREATE INDEX IF NOT EXISTS idx_port_measurement_time
    ON port_measurement(port_id, observation_id);

CREATE INDEX IF NOT EXISTS idx_aggregation_layer_period
    ON aggregation_run(layer, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_aggregate_metric
    ON aggregate_measurement(subject_type, subject_id, metric_key, aggregation_run_id);
