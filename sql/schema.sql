PRAGMA foreign_keys=ON;
CREATE TABLE carriers(carrier_id INTEGER PRIMARY KEY,reporting_code TEXT NOT NULL CHECK(length(reporting_code)>0));
CREATE TABLE airports(airport_id INTEGER PRIMARY KEY,code TEXT NOT NULL,city TEXT NOT NULL);
CREATE TABLE source_files(source_id INTEGER PRIMARY KEY,url TEXT NOT NULL,csv_name TEXT NOT NULL,csv_sha256 TEXT NOT NULL UNIQUE,input_sha256 TEXT NOT NULL,imported_at TEXT NOT NULL,row_count INTEGER NOT NULL);
CREATE TABLE flights(
 flight_id INTEGER PRIMARY KEY,source_id INTEGER NOT NULL REFERENCES source_files,source_row INTEGER NOT NULL,
 flight_date TEXT NOT NULL,carrier_id INTEGER NOT NULL REFERENCES carriers,flight_number TEXT NOT NULL,
 origin_id INTEGER NOT NULL REFERENCES airports,dest_id INTEGER NOT NULL REFERENCES airports,
 crs_dep_time TEXT NOT NULL,scheduled_hour INTEGER NOT NULL CHECK(scheduled_hour BETWEEN 0 AND 23),
 dep_time TEXT,crs_arr_time TEXT NOT NULL,arr_time TEXT,
 dep_delay INTEGER,arr_delay INTEGER,arr_del15 INTEGER CHECK(arr_del15 IN(0,1)),
 cancelled INTEGER NOT NULL CHECK(cancelled IN(0,1)),diverted INTEGER NOT NULL CHECK(diverted IN(0,1)),
 cancellation_code TEXT,distance_miles INTEGER NOT NULL CHECK(distance_miles>0),
 CHECK(cancelled+diverted<=1),CHECK(origin_id<>dest_id),
 UNIQUE(source_id,source_row),UNIQUE(flight_date,carrier_id,flight_number,origin_id,dest_id,crs_dep_time));
CREATE INDEX flights_date ON flights(flight_date);
CREATE INDEX flights_carrier ON flights(carrier_id);
CREATE INDEX flights_origin ON flights(origin_id);
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE VIEW flight_status AS SELECT *,
 CASE WHEN cancelled=1 THEN 'cancelled' WHEN diverted=1 THEN 'diverted'
 WHEN arr_delay IS NULL THEN 'unknown_arrival' WHEN arr_delay>=15 THEN 'delayed' ELSE 'on_time' END status,
 CASE WHEN cancelled=0 AND diverted=0 AND arr_delay IS NOT NULL THEN 1 ELSE 0 END eligible
 FROM flights;
