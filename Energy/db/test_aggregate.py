"""Focused regression tests for the RootRecord condensation engine (split db layout)."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from Energy.db.aggregate import aggregate_at
from Energy.db.condense import condense_closed_periods
from Energy.db.store import (
    add_device_measurement,
    add_port_measurement,
    connect,
    connect_layer,
    create_observation,
    initialize_schema,
    upsert_device,
)


class AggregateRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = Path(self.tmp.name)
        self.layers_dir = Path(tempfile.mkdtemp(prefix="rootrecord-layers-"))
        self._layer_conns = []

        self.conn = connect(self.db)
        initialize_schema(self.conn)
        self.device = upsert_device(
            self.conn,
            serial_number="TEST-SERIAL",
            model="Test Device",
            alias="test",
            observed_at="2026-09-24T22:00:00.000Z",
        )
        self.source = self.conn.execute(
            """INSERT INTO observation_source
               (source_type,source_name,parser_name,parser_version,created_at)
               VALUES ('test','aggregate-regression','unittest','1',
                       '2026-09-24T22:00:00.000Z')"""
        ).lastrowid

    def tearDown(self):
        for lc in self._layer_conns:
            lc.close()
        self.conn.close()
        self.db.unlink(missing_ok=True)
        for suffix in ("-wal", "-shm"):
            Path(str(self.db) + suffix).unlink(missing_ok=True)
        shutil.rmtree(self.layers_dir, ignore_errors=True)

    def open_layer(self, layer):
        lc = connect_layer(layer, self.db, self.layers_dir)
        self._layer_conns.append(lc)
        return lc

    def observation(self, stamp, power=None):
        obs = create_observation(
            self.conn,
            device_id=self.device,
            observed_at=stamp,
            source_id=self.source,
            online=True,
        )
        if power is not None:
            add_device_measurement(
                self.conn,
                observation_id=obs,
                metric_key="input_power",
                value=power,
                unit="W",
                state="measured",
            )
        return obs

    def test_sequence_less_observation_is_idempotent(self):
        first = create_observation(
            self.conn,
            device_id=self.device,
            observed_at="2026-09-24T22:00:00.000Z",
            source_id=self.source,
            online=True,
        )
        second = create_observation(
            self.conn,
            device_id=self.device,
            observed_at="2026-09-24T22:00:00.000Z",
            source_id=self.source,
            online=False,
        )
        count = self.conn.execute(
            "SELECT COUNT(*) FROM observation WHERE device_id=? AND observed_at=? AND source_id=?",
            (self.device, "2026-09-24T22:00:00.000Z", self.source),
        ).fetchone()[0]
        self.assertEqual(first, second)
        self.assertEqual(count, 1)

    def test_text_port_metadata_is_not_numeric_aggregate_data(self):
        obs = self.observation("2026-09-24T22:00:05.000Z")
        self.conn.execute(
            "INSERT INTO device_port(device_id,port_type,port_index) VALUES (?,?,?)",
            (self.device, "usb", 1),
        )
        port = self.conn.execute(
            "SELECT port_id FROM device_port WHERE device_id=? AND port_type='usb' AND port_index=1",
            (self.device,),
        ).fetchone()[0]
        add_port_measurement(
            self.conn,
            observation_id=obs,
            port_id=port,
            metric_key="label",
            value="USB-A",
            state="measured",
        )
        self.conn.commit()

        lc = self.open_layer("1min")
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))
        row = lc.execute(
            """SELECT COUNT(*) FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min' AND am.subject_type='port'
                 AND am.subject_id=? AND am.metric_key='label'""",
            (port,),
        ).fetchone()[0]
        self.assertEqual(row, 0)

    def test_power_crosses_period_boundary_without_losing_edge_energy(self):
        self.observation("2026-09-24T21:59:30.000Z", 100)
        self.observation("2026-09-24T22:00:30.000Z", 100)
        self.observation("2026-09-24T22:01:30.000Z", 100)
        self.conn.commit()

        lc = self.open_layer("1min")
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))

        row = lc.execute(
            """SELECT sample_count,coverage_pct,energy_wh
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min'
                 AND ar.period_start='2026-09-24T22:00:00.000Z'
                 AND am.metric_key='input_power'"""
        ).fetchone()

        self.assertEqual(row["sample_count"], 1)
        self.assertAlmostEqual(row["coverage_pct"], 100.0, places=6)
        self.assertAlmostEqual(row["energy_wh"], 100 / 60, places=6)

    def test_measured_zero_is_not_missing(self):
        self.observation("2026-09-24T22:00:05.000Z", 0)
        self.conn.commit()

        lc = self.open_layer("1min")
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))

        row = lc.execute(
            """SELECT value_avg,state
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min'
                 AND am.metric_key='input_power'"""
        ).fetchone()

        self.assertEqual(row["value_avg"], 0.0)
        self.assertEqual(row["state"], "measured")

    def test_port_measurements_are_aggregated(self):
        obs = self.observation("2026-09-24T22:00:05.000Z")
        self.conn.execute(
            """INSERT INTO device_port(device_id,port_type,port_index)
               VALUES (?,?,?)""",
            (self.device, "usb", 0),
        )
        port = self.conn.execute(
            """SELECT port_id FROM device_port
               WHERE device_id=? AND port_type='usb' AND port_index=0""",
            (self.device,),
        ).fetchone()[0]
        add_port_measurement(
            self.conn,
            observation_id=obs,
            port_id=port,
            metric_key="enabled",
            value=True,
            state="measured",
        )
        self.conn.commit()

        lc = self.open_layer("1min")
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))

        row = lc.execute(
            """SELECT subject_type,subject_id,metric_key,value_avg,state
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min' AND am.subject_type='port'"""
        ).fetchone()

        self.assertEqual(row["subject_type"], "port")
        self.assertEqual(row["subject_id"], port)
        self.assertEqual(row["metric_key"], "enabled")
        self.assertEqual(row["value_avg"], 1.0)
        self.assertEqual(row["state"], "measured")

    def test_power_records_duration_fields(self):
        self.observation("2026-09-24T22:00:00.000Z", 100)
        self.observation("2026-09-24T22:00:30.000Z", 100)
        self.conn.commit()

        lc = self.open_layer("1min")
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))

        row = lc.execute(
            """SELECT observed_span_s,valid_duration_s,coverage_pct
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min' AND am.metric_key='input_power'"""
        ).fetchone()
        self.assertAlmostEqual(row["observed_span_s"], 30.0)
        self.assertAlmostEqual(row["valid_duration_s"], 30.0)
        self.assertAlmostEqual(row["coverage_pct"], 50.0)

    def test_aggregation_is_idempotent(self):
        self.observation("2026-09-24T22:00:00.000Z", 100)
        self.observation("2026-09-24T22:00:30.000Z", 100)
        self.conn.commit()

        at = datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc)
        lc = self.open_layer("1min")
        aggregate_at(lc, "1min", at)
        first = lc.execute(
            """SELECT COUNT(*),SUM(energy_wh)
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min'"""
        ).fetchone()
        aggregate_at(lc, "1min", at)
        second = lc.execute(
            """SELECT COUNT(*),SUM(energy_wh)
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min'"""
        ).fetchone()
        self.assertEqual(first[0], second[0])
        self.assertAlmostEqual(first[1], second[1])

    def test_gap_over_interpolation_limit_does_not_claim_coverage(self):
        self.observation("2026-09-24T22:00:00.000Z", 100)
        self.observation("2026-09-24T22:01:01.000Z", 100)
        self.conn.commit()

        lc = self.open_layer("1min")
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))
        row = lc.execute(
            """SELECT coverage_pct,energy_wh
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min' AND am.metric_key='input_power'"""
        ).fetchone()
        self.assertEqual(row["coverage_pct"], 0.0)
        self.assertIsNone(row["energy_wh"])

    def test_condensation_skips_open_period_and_backfills_closed_period(self):
        self.observation("2026-09-24T21:59:30.000Z", 100)
        self.observation("2026-09-24T22:00:30.000Z", 100)
        self.observation("2026-09-24T22:01:30.000Z", 100)
        self.conn.commit()

        total = condense_closed_periods(self.db, layers_dir=self.layers_dir)
        self.assertGreater(total, 0)

        lc = self.open_layer("1min")
        complete = lc.execute(
            """SELECT COUNT(*) FROM aggregation_run
               WHERE layer='1min' AND status='complete'"""
        ).fetchone()[0]
        self.assertEqual(complete, 1)

        second = condense_closed_periods(self.db, layers_dir=self.layers_dir)
        self.assertEqual(second, 0)


if __name__ == "__main__":
    unittest.main()
