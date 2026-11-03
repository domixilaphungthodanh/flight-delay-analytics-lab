"""All fixtures are SYNTHETIC; no network and no real flight records in unit tests."""
import csv,hashlib,io,sqlite3,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import requests
from flight_lab.db import ROOT,connect
from flight_lab.import_data import FIELDS,parse_row,records,ingest,integer,clock,import_data
from flight_lab.analysis import scope,queries,reconcile,quality
def row(**changes):
    x=dict(zip(FIELDS,['2025-01-01','3','AA','1','1','1001','AAA','Alpha, Test','1002','BBB','Beta, Test','0800','0800','1000','1000','0.00','-5.00','0.00','0.00','0.00','','100.00']))
    x.update(changes);return x
def csv_text(rows):
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows);return s.getvalue()
def fixture_rows():return [
    row(Flight_Number_Reporting_Airline='1'),
    row(Flight_Number_Reporting_Airline='2',ArrDelay='14.00'),
    row(Flight_Number_Reporting_Airline='3',ArrDelay='15.00',ArrDel15='1.00'),
    row(Flight_Number_Reporting_Airline='4',DOT_ID_Reporting_Airline='2',Reporting_Airline='ZZ',Cancelled='1.00',ArrDelay='',ArrDel15='',DepTime='',ArrTime=''),
    row(Flight_Number_Reporting_Airline='5',FlightDate='2025-01-02',DayOfWeek='4',OriginAirportID='1003',Origin='CCC',OriginCityName='Gamma, Test',Diverted='1.00',ArrDelay='',ArrDel15=''),
    row(Flight_Number_Reporting_Airline='6',FlightDate='2025-01-02',DayOfWeek='4',ArrDelay='',ArrDel15='',ArrTime='')]
def fixture(directory):
    p=Path(directory)/'fixture.csv';p.write_text(csv_text(fixture_rows()),encoding='utf-8');db=Path(directory)/'fixture.db'
    with connect(db,False) as c:
        c.executescript((ROOT/'sql/schema.sql').read_text(encoding='utf-8'))
        c.execute("INSERT INTO source_files VALUES(1,'SYNTHETIC','fixture.csv','fixture','fixture','2026-01-01',0)")
        with p.open(encoding='utf-8',newline='') as f:n=ingest(f,c)
        c.execute('UPDATE source_files SET row_count=?',(n,))
        c.executemany('INSERT INTO metadata VALUES(?,?)',[('data_kind','synthetic_fixture'),('input_path',str(p))])
    return db,p
class ParserTests(unittest.TestCase):
    def test_valid_signed_minutes(self):self.assertEqual(parse_row(row(),2)[0][13],-5)
    def test_row_provenance(self):self.assertEqual(parse_row(row(),42)[0][1],42)
    def test_missing_delay_preserved(self):self.assertIsNone(parse_row(row(ArrDelay='',ArrDel15=''),2)[0][13])
    def test_wrong_weekday(self):
        with self.assertRaises(ValueError):parse_row(row(DayOfWeek='1'),2)
    def test_wrong_month(self):
        with self.assertRaises(ValueError):parse_row(row(FlightDate='2025-02-01'),2)
    def test_wrong_date(self):
        with self.assertRaises(ValueError):parse_row(row(FlightDate='2025-01-32'),2)
    def test_bad_flag(self):
        with self.assertRaises(ValueError):parse_row(row(Cancelled='2'),2)
    def test_both_cancelled_diverted(self):
        with self.assertRaises(ValueError):parse_row(row(Cancelled='1',Diverted='1'),2)
    def test_conflicting_arrival_flag(self):
        with self.assertRaises(ValueError):parse_row(row(ArrDelay='15',ArrDel15='0'),2)
    def test_15_minutes_is_late(self):self.assertEqual(parse_row(row(ArrDelay='15',ArrDel15='1'),2)[0][14],1)
    def test_hour_2400_kept_and_binned_zero(self):
        v=parse_row(row(CRSDepTime='2400'),2)[0];self.assertEqual(v[7],'2400');self.assertEqual(v[8],0)
    def test_hour_0000(self):self.assertEqual(clock('0000'),'0000')
    def test_invalid_hhmm(self):
        for x in ['2560','1260','2401','800','abcd']:
            with self.assertRaises(ValueError):clock(x)
    def test_zero_distance(self):
        with self.assertRaises(ValueError):parse_row(row(Distance='0'),2)
    def test_same_airport(self):
        with self.assertRaises(ValueError):parse_row(row(DestAirportID='1001'),2)
    def test_empty_flight_number(self):
        with self.assertRaises(ValueError):parse_row(row(Flight_Number_Reporting_Airline=''),2)
    def test_decimal_not_silently_rounded(self):
        with self.assertRaises(ValueError):integer('1.5')
    def test_missing_header(self):
        with self.assertRaises(ValueError):list(records(io.StringIO('FlightDate\n2025-01-01\n')))
    def test_bad_column_count(self):
        with self.assertRaises(ValueError):list(records(io.StringIO(csv_text([row()])+','.join(['extra']*(len(FIELDS)+1))+'\n')))
class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db,self.source=fixture(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def test_quality_partition(self):
        q=quality(self.db).set_index('check').value;self.assertEqual(q['imported_rows'],6);self.assertEqual(sum(q[k] for k in ['on_time','delayed','cancelled','diverted','unknown_arrival']),6)
    def test_eligible_and_rate(self):
        t=queries(self.db)['airline_summary'].set_index('reporting_code').loc['AA'];self.assertEqual(t.eligible,3);self.assertEqual(t.delayed,1);self.assertAlmostEqual(t.delay_rate_pct,100/3)
    def test_negative_mean_preserved(self):
        t=queries(self.db)['airline_summary'].set_index('reporting_code').loc['AA'];self.assertEqual(t.mean_arrival_delay_min,8)
    def test_cancelled_only_rate_null(self):
        t=queries(self.db)['airline_summary'].set_index('reporting_code').loc['ZZ'];self.assertTrue(pd.isna(t.delay_rate_pct));self.assertEqual(t.cancel_rate_pct,100)
    def test_status_counts(self):
        with connect(self.db) as c:x=dict(c.execute('SELECT status,COUNT(*) FROM flight_status GROUP BY status'))
        self.assertEqual(x,{'on_time':2,'delayed':1,'cancelled':1,'diverted':1,'unknown_arrival':1})
    def test_calendar_days(self):
        t=queries(self.db)['day_type_summary'].set_index('day_type');self.assertEqual(t.loc['weekday','calendar_days'],23);self.assertEqual(t.loc['weekend','calendar_days'],8);self.assertAlmostEqual(t.loc['weekday','flights_per_day'],6/23)
    def test_calendar_zero_days_and_heat_grid(self):
        t=queries(self.db);self.assertEqual(len(t['daily_summary']),31);self.assertEqual(len(t['hourly_summary']),168);self.assertEqual(t['daily_summary'].total.iloc[-1],0)
    def test_both_airport_joins_keep_count(self):
        with connect(self.db) as c:n=c.execute('SELECT COUNT(*) FROM flights f JOIN airports o ON o.airport_id=f.origin_id JOIN airports d ON d.airport_id=f.dest_id').fetchone()[0]
        self.assertEqual(n,6)
    def test_zero_origin_airport_kept(self):
        a=queries(self.db)['airport_summary'].set_index('code').loc['BBB'];self.assertEqual(a.total,0);self.assertTrue(pd.isna(a.delay_rate_pct))
    def test_subrange_filters(self):self.assertEqual(queries(self.db,'2025-01-01','2025-01-01')['airline_summary'].total.sum(),4)
    def test_empty_range_preserves_catalogs(self):
        t=queries(self.db,'2025-01-31','2025-01-31');self.assertEqual(len(t['airline_summary']),2);self.assertTrue(t['airline_summary'].delay_rate_pct.isna().all())
    def test_bad_range(self):
        for a,b in [('2025-01-03','2025-01-01'),('2024-12-31','2025-01-01'),('2025-01-01','2025-02-01')]:
            with self.assertRaises(ValueError):scope(a,b)
    def test_ranking_999_1000_boundary(self):
        from flight_lab.analysis import metrics,COUNTS
        frame=pd.DataFrame([dict(carrier_id=i,reporting_code=f'T{i}',**{k:(n if k in ['total','eligible'] else 0) for k in COUNTS}) for i,n in [(1,999),(2,1000)]])
        self.assertEqual(metrics(frame).rank_eligible.tolist(),[False,True])
    def test_pandas_sql_independent(self):
        with patch('flight_lab.analysis.open_csv',side_effect=lambda p:Path(p).open(encoding='utf-8',newline='')):reconcile(self.db)
    def test_empty_pandas_sql(self):
        with patch('flight_lab.analysis.open_csv',side_effect=lambda p:Path(p).open(encoding='utf-8',newline='')):reconcile(self.db,'2025-01-31','2025-01-31')
    def test_existing_db_not_overwritten(self):
        h=hashlib.sha256(self.db.read_bytes()).hexdigest()
        with self.assertRaises(FileExistsError):import_data('missing.csv',self.db)
        self.assertEqual(h,hashlib.sha256(self.db.read_bytes()).hexdigest())
    def test_failed_import_not_published(self):
        bad=Path(self.tmp.name)/'bad.csv';bad.write_text(csv_text([row(),row(ArrDel15='1')]),encoding='utf-8');dest=Path(self.tmp.name)/'bad.db'
        with patch('flight_lab.import_data.open_csv',side_effect=lambda p:Path(p).open(encoding='utf-8',newline='')):
            with self.assertRaises(ValueError):import_data(bad,dest)
        self.assertFalse(dest.exists());self.assertFalse(list(Path(self.tmp.name).glob('*.sqlite.tmp')))
    def test_readonly(self):
        with connect(self.db) as c:
            with self.assertRaises(sqlite3.OperationalError):c.execute("INSERT INTO carriers VALUES(3,'NO')")
    def test_foreign_key(self):
        with connect(self.db,False) as c:
            self.assertEqual(c.execute('PRAGMA foreign_keys').fetchone()[0],1)
            with self.assertRaises(sqlite3.IntegrityError):c.execute('UPDATE flights SET carrier_id=99 WHERE flight_id=1')
    def test_natural_duplicate_rejected(self):
        with connect(self.db,False) as c:
            with self.assertRaises(sqlite3.IntegrityError):c.execute('INSERT INTO flights(source_id,source_row,flight_date,carrier_id,flight_number,origin_id,dest_id,crs_dep_time,scheduled_hour,crs_arr_time,cancelled,diverted,distance_miles) SELECT source_id,999,flight_date,carrier_id,flight_number,origin_id,dest_id,crs_dep_time,scheduled_hour,crs_arr_time,cancelled,diverted,distance_miles FROM flights WHERE flight_id=1')
    def test_empty_report_outputs(self):
        from flight_lab.analyze import analyze
        with patch('flight_lab.analysis.open_csv',side_effect=lambda p:Path(p).open(encoding='utf-8',newline='')):out=analyze(self.db,'2025-01-31','2025-01-31',Path(self.tmp.name)/'out')
        self.assertEqual(len(list(out.glob('*.png'))),4);self.assertEqual(len(list(out.glob('*.csv'))),6);self.assertIn('GIẢ LẬP KIỂM THỬ',(out/'report.md').read_text(encoding='utf-8'))
    def test_menu_exit(self):
        from flight_lab.cli import main
        with patch('sys.argv',['cli','--db',str(self.db)]),patch('builtins.input',return_value='0'),patch('builtins.print'):main()
    def test_selector_retry(self):
        from flight_lab.cli import choose
        with patch('builtins.input',side_effect=['AA','bad','999','1']),patch('builtins.print'):self.assertEqual(choose(self.db,'carriers','carrier_id','reporting_code'),1)
    def test_selector_cancel(self):
        from flight_lab.cli import choose
        with patch('builtins.input',side_effect=['','q']),patch('builtins.print'):self.assertIsNone(choose(self.db,'carriers','carrier_id','reporting_code'))
class DownloadTests(unittest.TestCase):
    def test_network_error_no_partial_file(self):
        from flight_lab.source import download
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.zip'
            with patch('flight_lab.source.requests.get',side_effect=requests.ConnectionError('fixture')):
                with self.assertRaises(requests.ConnectionError):download(p)
            self.assertFalse(p.exists());self.assertFalse(list(Path(d).glob('*.part')))
    def test_existing_bad_zip_not_overwritten(self):
        from flight_lab.source import download
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.zip';p.write_bytes(b'fixture')
            with self.assertRaises(ValueError):download(p)
            self.assertEqual(p.read_bytes(),b'fixture')
if __name__=='__main__':unittest.main()
