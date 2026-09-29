# RootRecord SQLite Data Layer

This directory is the canonical persistence and condensation layer for Energy/EcoFlow telemetry.

## Runtime path

EcoFlow BLE -> EFLIB -> read_runner -> SQLite observation/measurement rows -> closed-period condensation -> nine reporting layers.

Legacy JSON remains a compatibility/output layer during migration.

## Files

- `schema.sql` — canonical relational schema.
- `store.py` — transactional persistence primitives.
- `ingest.py` — EFLIB snapshot ingestion bridge.
- `aggregate.py` — nine-layer condensation engine.
- `condense.py` — runtime hook that only processes newly closed periods.
- `MIGRATION-SPEC.md` — data-model and migration semantics.
- `MIGRATION-RUNBOOK.md` — legacy import verification procedure.
- `OPERATIONAL-DATA-LAYER.md` — runtime data flow.
- `../scripts/init_rootrecord_db.py` — explicit schema initializer.
- `../scripts/migrate_json.py` — additive legacy JSON importer.
- `../scripts/condense_closed_periods.py` — explicit condensation runner.
- `../scripts/verify_rootrecord_db.py` — integrity verifier.

## Database

Target production path:

`/home/rootrecord/Database/ROOTRECORD/rootrecord.db`

Importing modules does not create telemetry. Live ingestion explicitly initializes the schema on first persistence.

## Model

A device has exactly one modeled primary battery and zero or more expansion batteries.

- B1 = River 2 Pro.
- B2 = Delta 2.
- B3 = Delta 2 expansion battery under B2; it is not a third device.

Battery observations are separate from device, electrical, and port measurements.

## State semantics

- `measured` — source supplied a real value, including measured zero.
- `defaulted` — EFLIB explicitly supplied a configured default.
- `missing` — source did not provide a value.
- `not_applicable` — metric does not apply to the hardware.

Never convert missing/not-applicable into numeric zero.

## Time layers

`1sec -> 1min -> 5min -> 15min -> 1hour -> day -> 7days -> month -> year`

Observation timestamps are canonical UTC ISO-8601 with `Z`. Reporting boundaries use Pacific/Honolulu time.

Power energy is integrated from elapsed valid measurements and bounded interpolation gaps; it is not calculated by assuming a full-period average.

Aggregation runs are persisted and idempotent. Closed periods are not repeatedly rebuilt by the live runtime once marked complete.


## Schema v2 duration semantics

Aggregate rows also persist:
- `observed_span_s`: elapsed time between the first and last valid in-period samples.
- `valid_duration_s`: elapsed duration actually covered by bounded power integration.
- `coverage_pct`: for power metrics, valid duration divided by the reporting-period duration; for non-power metrics, valid in-period samples divided by in-period samples.

A power gap greater than 60 seconds is not interpolated. Measured zero remains measured zero; missing and not-applicable remain distinct.
