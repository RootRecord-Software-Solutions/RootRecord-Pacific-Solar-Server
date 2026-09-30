# ==============================================================================
# FILE: Energy/db/test_aggregate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Focused regression tests for the RootRecord condensation engine (split db layout)."""  # info: """Focused regression tests for the RootRecord condensation engine (split db layout)."""
from __future__ import annotations  # info: from __future__ import annotations

import shutil  # info: import shutil
import tempfile  # info: import tempfile
import unittest  # info: import unittest
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

from Energy.db.aggregate import aggregate_at  # info: from Energy . db . aggregate import aggregate_at
from Energy.db.condense import condense_closed_periods  # info: from Energy . db . condense import condense_closed_periods
from Energy.db.store import (  # info: from Energy . db . store import (
    add_device_measurement,  # info: add_device_measurement ,
    add_port_measurement,  # info: add_port_measurement ,
    connect,  # info: connect ,
    connect_layer,  # info: connect_layer ,
    create_observation,  # info: create_observation ,
    initialize_schema,  # info: initialize_schema ,
    upsert_device,  # info: upsert_device ,
)  # info: )


# ====================================================
# SECTION: class AggregateRegressionTests
# What it does: AggregateRegressionTests.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class AggregateRegressionTests(unittest.TestCase):  # info: class AggregateRegressionTests
    def setUp(self):  # info: def setUp
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)  # info: self . tmp = tempfile . NamedTemporaryFile (
        self.tmp.close()  # info: self . tmp . close ( )
        self.db = Path(self.tmp.name)  # info: self . db = Path ( self .
        self.layers_dir = Path(tempfile.mkdtemp(prefix="rootrecord-layers-"))  # info: self . layers_dir = Path ( tempfile .
        self._layer_conns = []  # info: self . _layer_conns = [ ]

        self.conn = connect(self.db)  # info: self . conn = connect ( self .
        initialize_schema(self.conn)  # info: call initialize_schema
        self.device = upsert_device(  # info: self . device = upsert_device (
            self.conn,  # info: self . conn ,
            serial_number="TEST-SERIAL",  # info: set serial_number
            model="Test Device",  # info: set model
            alias="test",  # info: set alias
            observed_at="2026-09-24T22:00:00.000Z",  # info: set observed_at
        )  # info: )
        self.source = self.conn.execute(  # info: self . source = self . conn .
            """INSERT INTO observation_source
               (source_type,source_name,parser_name,parser_version,created_at)
               VALUES ('test','aggregate-regression','unittest','1',
                       '2026-09-24T22:00:00.000Z')"""
        ).lastrowid  # info: ) . lastrowid

    def tearDown(self):  # info: def tearDown
        for lc in self._layer_conns:  # info: for lc in self . _layer_conns :
            lc.close()  # info: lc . close ( )
        self.conn.close()  # info: self . conn . close ( )
        self.db.unlink(missing_ok=True)  # info: self . db . unlink ( missing_ok =
        for suffix in ("-wal", "-shm"):  # info: for suffix in ( "-wal" , "-shm" )
            Path(str(self.db) + suffix).unlink(missing_ok=True)  # info: call Path
        shutil.rmtree(self.layers_dir, ignore_errors=True)  # info: shutil . rmtree ( self . layers_dir ,

    def open_layer(self, layer):  # info: def open_layer
        lc = connect_layer(layer, self.db, self.layers_dir)  # info: set lc
        self._layer_conns.append(lc)  # info: self . _layer_conns . append ( lc )
        return lc  # info: return lc

    def observation(self, stamp, power=None):  # info: def observation
        obs = create_observation(  # info: set obs
            self.conn,  # info: self . conn ,
            device_id=self.device,  # info: set device_id
            observed_at=stamp,  # info: set observed_at
            source_id=self.source,  # info: set source_id
            online=True,  # info: set online
        )  # info: )
        if power is not None:  # info: if power is not None :
            add_device_measurement(  # info: call add_device_measurement
                self.conn,  # info: self . conn ,
                observation_id=obs,  # info: set observation_id
                metric_key="input_power",  # info: set metric_key
                value=power,  # info: set value
                unit="W",  # info: set unit
                state="measured",  # info: set state
            )  # info: )
        return obs  # info: return obs

    def test_sequence_less_observation_is_idempotent(self):  # info: def test_sequence_less_observation_is_idempotent
        first = create_observation(  # info: set first
            self.conn,  # info: self . conn ,
            device_id=self.device,  # info: set device_id
            observed_at="2026-09-24T22:00:00.000Z",  # info: set observed_at
            source_id=self.source,  # info: set source_id
            online=True,  # info: set online
        )  # info: )
        second = create_observation(  # info: set second
            self.conn,  # info: self . conn ,
            device_id=self.device,  # info: set device_id
            observed_at="2026-09-24T22:00:00.000Z",  # info: set observed_at
            source_id=self.source,  # info: set source_id
            online=False,  # info: set online
        )  # info: )
        count = self.conn.execute(  # info: set count
            "SELECT COUNT(*) FROM observation WHERE device_id=? AND observed_at=? AND source_id=?",  # info: "SELECT COUNT(*) FROM observation WHERE device_id=? AND observed_at=? AND source_id=?" ,
            (self.device, "2026-09-24T22:00:00.000Z", self.source),  # info: call (
        ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
        self.assertEqual(first, second)  # info: self . assertEqual ( first , second )
        self.assertEqual(count, 1)  # info: self . assertEqual ( count , 1 )

    def test_text_port_metadata_is_not_numeric_aggregate_data(self):  # info: def test_text_port_metadata_is_not_numeric_aggregate_data
        obs = self.observation("2026-09-24T22:00:05.000Z")  # info: set obs
        self.conn.execute(  # info: self . conn . execute (
            "INSERT INTO device_port(device_id,port_type,port_index) VALUES (?,?,?)",  # info: "INSERT INTO device_port(device_id,port_type,port_index) VALUES (?,?,?)" ,
            (self.device, "usb", 1),  # info: call (
        )  # info: )
        port = self.conn.execute(  # info: set port
            "SELECT port_id FROM device_port WHERE device_id=? AND port_type='usb' AND port_index=1",  # info: "SELECT port_id FROM device_port WHERE device_id=? AND port_type='usb' AND port_index=1" ,
            (self.device,),  # info: call (
        ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
        add_port_measurement(  # info: call add_port_measurement
            self.conn,  # info: self . conn ,
            observation_id=obs,  # info: set observation_id
            port_id=port,  # info: set port_id
            metric_key="label",  # info: set metric_key
            value="USB-A",  # info: set value
            state="measured",  # info: set state
        )  # info: )
        self.conn.commit()  # info: self . conn . commit ( )

        lc = self.open_layer("1min")  # info: set lc
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))  # info: call aggregate_at
        row = lc.execute(  # info: set row
            """SELECT COUNT(*) FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min' AND am.subject_type='port'
                 AND am.subject_id=? AND am.metric_key='label'""",
            (port,),  # info: call (
        ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
        self.assertEqual(row, 0)  # info: self . assertEqual ( row , 0 )

    def test_power_crosses_period_boundary_without_losing_edge_energy(self):  # info: def test_power_crosses_period_boundary_without_losing_edge_energy
        self.observation("2026-09-24T21:59:30.000Z", 100)  # info: self . observation ( "2026-09-24T21:59:30.000Z" , 100 )
        self.observation("2026-09-24T22:00:30.000Z", 100)  # info: self . observation ( "2026-09-24T22:00:30.000Z" , 100 )
        self.observation("2026-09-24T22:01:30.000Z", 100)  # info: self . observation ( "2026-09-24T22:01:30.000Z" , 100 )
        self.conn.commit()  # info: self . conn . commit ( )

        lc = self.open_layer("1min")  # info: set lc
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))  # info: call aggregate_at

        row = lc.execute(  # info: set row
            """SELECT sample_count,coverage_pct,energy_wh
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min'
                 AND ar.period_start='2026-09-24T22:00:00.000Z'
                 AND am.metric_key='input_power'"""
        ).fetchone()  # info: ) . fetchone ( )

        self.assertEqual(row["sample_count"], 1)  # info: self . assertEqual ( row [ "sample_count" ]
        self.assertAlmostEqual(row["coverage_pct"], 100.0, places=6)  # info: self . assertAlmostEqual ( row [ "coverage_pct" ]
        self.assertAlmostEqual(row["energy_wh"], 100 / 60, places=6)  # info: self . assertAlmostEqual ( row [ "energy_wh" ]

    def test_measured_zero_is_not_missing(self):  # info: def test_measured_zero_is_not_missing
        self.observation("2026-09-24T22:00:05.000Z", 0)  # info: self . observation ( "2026-09-24T22:00:05.000Z" , 0 )
        self.conn.commit()  # info: self . conn . commit ( )

        lc = self.open_layer("1min")  # info: set lc
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))  # info: call aggregate_at

        row = lc.execute(  # info: set row
            """SELECT value_avg,state
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min'
                 AND am.metric_key='input_power'"""
        ).fetchone()  # info: ) . fetchone ( )

        self.assertEqual(row["value_avg"], 0.0)  # info: self . assertEqual ( row [ "value_avg" ]
        self.assertEqual(row["state"], "measured")  # info: self . assertEqual ( row [ "state" ]

    def test_port_measurements_are_aggregated(self):  # info: def test_port_measurements_are_aggregated
        obs = self.observation("2026-09-24T22:00:05.000Z")  # info: set obs
        self.conn.execute(  # info: self . conn . execute (
            """INSERT INTO device_port(device_id,port_type,port_index)
               VALUES (?,?,?)""",
            (self.device, "usb", 0),  # info: call (
        )  # info: )
        port = self.conn.execute(  # info: set port
            """SELECT port_id FROM device_port
               WHERE device_id=? AND port_type='usb' AND port_index=0""",
            (self.device,),  # info: call (
        ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
        add_port_measurement(  # info: call add_port_measurement
            self.conn,  # info: self . conn ,
            observation_id=obs,  # info: set observation_id
            port_id=port,  # info: set port_id
            metric_key="enabled",  # info: set metric_key
            value=True,  # info: set value
            state="measured",  # info: set state
        )  # info: )
        self.conn.commit()  # info: self . conn . commit ( )

        lc = self.open_layer("1min")  # info: set lc
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))  # info: call aggregate_at

        row = lc.execute(  # info: set row
            """SELECT subject_type,subject_id,metric_key,value_avg,state
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min' AND am.subject_type='port'"""
        ).fetchone()  # info: ) . fetchone ( )

        self.assertEqual(row["subject_type"], "port")  # info: self . assertEqual ( row [ "subject_type" ]
        self.assertEqual(row["subject_id"], port)  # info: self . assertEqual ( row [ "subject_id" ]
        self.assertEqual(row["metric_key"], "enabled")  # info: self . assertEqual ( row [ "metric_key" ]
        self.assertEqual(row["value_avg"], 1.0)  # info: self . assertEqual ( row [ "value_avg" ]
        self.assertEqual(row["state"], "measured")  # info: self . assertEqual ( row [ "state" ]

    def test_power_records_duration_fields(self):  # info: def test_power_records_duration_fields
        self.observation("2026-09-24T22:00:00.000Z", 100)  # info: self . observation ( "2026-09-24T22:00:00.000Z" , 100 )
        self.observation("2026-09-24T22:00:30.000Z", 100)  # info: self . observation ( "2026-09-24T22:00:30.000Z" , 100 )
        self.conn.commit()  # info: self . conn . commit ( )

        lc = self.open_layer("1min")  # info: set lc
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))  # info: call aggregate_at

        row = lc.execute(  # info: set row
            """SELECT observed_span_s,valid_duration_s,coverage_pct
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min' AND am.metric_key='input_power'"""
        ).fetchone()  # info: ) . fetchone ( )
        self.assertAlmostEqual(row["observed_span_s"], 30.0)  # info: self . assertAlmostEqual ( row [ "observed_span_s" ]
        self.assertAlmostEqual(row["valid_duration_s"], 30.0)  # info: self . assertAlmostEqual ( row [ "valid_duration_s" ]
        self.assertAlmostEqual(row["coverage_pct"], 50.0)  # info: self . assertAlmostEqual ( row [ "coverage_pct" ]

    def test_aggregation_is_idempotent(self):  # info: def test_aggregation_is_idempotent
        self.observation("2026-09-24T22:00:00.000Z", 100)  # info: self . observation ( "2026-09-24T22:00:00.000Z" , 100 )
        self.observation("2026-09-24T22:00:30.000Z", 100)  # info: self . observation ( "2026-09-24T22:00:30.000Z" , 100 )
        self.conn.commit()  # info: self . conn . commit ( )

        at = datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc)  # info: set at
        lc = self.open_layer("1min")  # info: set lc
        aggregate_at(lc, "1min", at)  # info: call aggregate_at
        first = lc.execute(  # info: set first
            """SELECT COUNT(*),SUM(energy_wh)
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min'"""
        ).fetchone()  # info: ) . fetchone ( )
        aggregate_at(lc, "1min", at)  # info: call aggregate_at
        second = lc.execute(  # info: set second
            """SELECT COUNT(*),SUM(energy_wh)
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min'"""
        ).fetchone()  # info: ) . fetchone ( )
        self.assertEqual(first[0], second[0])  # info: self . assertEqual ( first [ 0 ]
        self.assertAlmostEqual(first[1], second[1])  # info: self . assertAlmostEqual ( first [ 1 ]

    def test_gap_over_interpolation_limit_does_not_claim_coverage(self):  # info: def test_gap_over_interpolation_limit_does_not_claim_coverage
        self.observation("2026-09-24T22:00:00.000Z", 100)  # info: self . observation ( "2026-09-24T22:00:00.000Z" , 100 )
        self.observation("2026-09-24T22:01:01.000Z", 100)  # info: self . observation ( "2026-09-24T22:01:01.000Z" , 100 )
        self.conn.commit()  # info: self . conn . commit ( )

        lc = self.open_layer("1min")  # info: set lc
        aggregate_at(lc, "1min", datetime(2026, 9, 24, 22, 0, tzinfo=timezone.utc))  # info: call aggregate_at
        row = lc.execute(  # info: set row
            """SELECT coverage_pct,energy_wh
               FROM aggregate_measurement am
               JOIN aggregation_run ar ON ar.aggregation_run_id=am.aggregation_run_id
               WHERE ar.layer='1min' AND am.metric_key='input_power'"""
        ).fetchone()  # info: ) . fetchone ( )
        self.assertEqual(row["coverage_pct"], 0.0)  # info: self . assertEqual ( row [ "coverage_pct" ]
        self.assertIsNone(row["energy_wh"])  # info: self . assertIsNone ( row [ "energy_wh" ]

    def test_condensation_skips_open_period_and_backfills_closed_period(self):  # info: def test_condensation_skips_open_period_and_backfills_closed_period
        self.observation("2026-09-24T21:59:30.000Z", 100)  # info: self . observation ( "2026-09-24T21:59:30.000Z" , 100 )
        self.observation("2026-09-24T22:00:30.000Z", 100)  # info: self . observation ( "2026-09-24T22:00:30.000Z" , 100 )
        self.observation("2026-09-24T22:01:30.000Z", 100)  # info: self . observation ( "2026-09-24T22:01:30.000Z" , 100 )
        self.conn.commit()  # info: self . conn . commit ( )

        total = condense_closed_periods(self.db, layers_dir=self.layers_dir)  # info: set total
        self.assertGreater(total, 0)  # info: self . assertGreater ( total , 0 )

        lc = self.open_layer("1min")  # info: set lc
        complete = lc.execute(  # info: set complete
            """SELECT COUNT(*) FROM aggregation_run
               WHERE layer='1min' AND status='complete'"""
        ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
        self.assertEqual(complete, 1)  # info: self . assertEqual ( complete , 1 )

        second = condense_closed_periods(self.db, layers_dir=self.layers_dir)  # info: set second
        self.assertEqual(second, 0)  # info: self . assertEqual ( second , 0 )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    unittest.main()  # info: unittest . main ( )
