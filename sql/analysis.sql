-- Một dòng mỗi chuyến; airports cần hai alias.
SELECT f.flight_date,c.reporting_code,f.flight_number,o.code origin,d.code destination,f.arr_delay,f.status
FROM flight_status f JOIN carriers c USING(carrier_id)
JOIN airports o ON o.airport_id=f.origin_id JOIN airports d ON d.airport_id=f.dest_id
ORDER BY f.flight_date,f.crs_dep_time,f.flight_id LIMIT 20;

-- Mẫu số là eligible, không phải tổng chuyến.
SELECT c.reporting_code,COUNT(*) total,SUM(f.eligible) eligible,
SUM(f.status='delayed') delayed,
100.0*SUM(f.status='delayed')/NULLIF(SUM(f.eligible),0) delay_rate_pct
FROM flight_status f JOIN carriers c USING(carrier_id)
GROUP BY c.carrier_id,c.reporting_code ORDER BY delay_rate_pct DESC;

-- Các nhóm loại trừ nhau; tổng phải bằng số dòng nguồn.
SELECT status,COUNT(*) flights FROM flight_status GROUP BY status;
