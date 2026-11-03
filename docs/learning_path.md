# Tám buổi học SQL, mỗi buổi khoảng60–90phút

1. Bảng/dòng/khóa và PowerShell: phân biệt nguồn CSV, chuyến, hãng, sân bay.
2. SELECT/WHERE/ORDER BY/LIMIT: lọc theo ngày, hãng, tình trạng; số0dòng có thể đúng.
3. JOIN: cùng bảng airports hai lần cho điểm đi và điểm đến; kiểm tra không nhân chuyến.
4. GROUP BY/COUNT/SUM/HAVING: đếm chuyến và chọn nhóm đủ mẫu.
5. NULL/LEFT JOIN/CASE: tách chuyến hủy/chuyển hướng/không rõ; không biến thiếu thành0.
6. CTE và tỷ lệ: xác định mẫu số; ranh giới14/15phút; calendar ngày0chuyến.
7. LAG/RANK và transaction: so ngày trước; thử rollback trong database tạm.
8. pandas/Seaborn/Git: đối chiếu độc lập từ nguồn, viết3nhận xét có giới hạn.

Mỗi notebook: câu hỏi → dự đoán → SQL mẫu → giải thích → tự làm → kiểm tra. SQL nằm trong chuỗi Python, không gõ vào PowerShell. Học notebook tổng hợp trước nếu chưa quen.

## Bài Git chưa làm sẵn

Issue “Lọc chuyến theo số phút đến trễ tối thiểu”. Tiêu chí: nhận số nguyên không âm; chỉ xét eligible; min=0không bao gồm chuyến đến sớm nếu định nghĩa điều kiện là ArrDelay>=0; Enter giữ bộ lọc hiện tại không áp dụng ngưỡng. Chặn chữ/số âm; NULL không so thành0; tôn trọng khoảng ngày/hãng/sân bay đang chọn. Kiểm thử14/15/NULL/hủy/âm và trường hợp không có chuyến.

Tạo nhánh → viết test → sửa `flight_lab/cli.py` → chạy unittest → `git diff` → `git add flight_lab/cli.py tests/` → `git commit -m "Add minimum arrival delay filter"` → `git push` → PR ghi `Closes #...`. Không đóng Issue chỉ vì đã viết mã nếu chưa đạt tiêu chí.
