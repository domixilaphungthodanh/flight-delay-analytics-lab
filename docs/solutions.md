# Lời giải — thử làm trước

1. `SELECT COUNT(*) FROM flights` →539747 ở snapshot thật.
2. ORDER BY flight_date,crs_dep_time,flight_id LIMIT10.
3. SELECT carrier_id,reporting_code FROM carriers ORDER BY reporting_code.
4. WHERE code LIKE ? OR city LIKE ?, truyền tham số.
5–6. Xem sql/analysis.sql; JOIN carriers một lần, airports hai alias; số dòng bằng nguồn.
7. GROUP BY carrier_id; COUNT(flight_id) khi LEFT JOIN, không dùng COUNT(*) cho catalog rỗng.
8. SUM(eligible)>=1000; giữ cột mẫu số. Ngưỡng này là bài học, không tiêu chuẩn ngành.
9. -5sớm,14vẫn on_time theo ngưỡng,15delayed; không phải “trên15”.
10. WHERE cancelled=0 AND diverted=0 AND arr_delay IS NULL. Snapshot thật0dòng vẫn đúng.
11. SUM(status='delayed')*100.0/NULLIF(SUM(eligible),0).
12. SUM(cancelled)*100.0/NULLIF(COUNT(*),0).
13. LEFT JOIN, điều kiện ngày trong ON để không loại catalog rỗng.
14. Tạo lịch bằng pandas date_range rồi LEFT JOIN/merge counts, fill0cho count; tỷ lệ0mẫu số đểNULL.
15. weekday tháng1/2025có23ngày, weekend8ngày; chia số ngày lịch theo khoảng chọn, không chỉ ngày có chuyến.
16. HHMM không có ngày và múi giờ; dùng ArrDelay nguồn. Không suy độ trễ bằng phép trừ HHMM.
17. Tổng hợp ngày trước, LAG(total) OVER(ORDER BY flight_date). Tính trên lịch đầy đủ nếu muốn ngày lịch liền trước.
18. Bảng tạm, BEGIN/INSERT/ROLLBACK rồi COUNT0; không ghi DB thật.
19. `reconcile(db)` đọc lại rawZIPqua pandas theo khối; so các tổng, nhóm và tỷ lệ.
20. Tổng/chuyến đủ mẫu và mẫu số; hãng kèm tỷ lệ+n; giới hạn một tháng/chưa điều chỉnh tuyến/thời tiết. Không kết luận nguyên nhân.
