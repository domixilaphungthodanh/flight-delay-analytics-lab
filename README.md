# Flight Delay Analytics Lab ✈️

Học SQL qua **dữ liệu chuyến bay thật BTS tháng 01/2025**, theo bố cục Sales Analysis Lab. Python 3.12 · SQLite · pandas · Seaborn · Matplotlib · Jupyter. Repo **Public**, mã MIT.

## PowerShell — bắt đầu tại đây

Tải [ZIP trong Releases](https://github.com/domixilaphungthodanh/flight-delay-analytics-lab/releases/latest), giải nén toàn bộ. Trong File Explorer mở thư mục dự án, gõ `powershell` vào thanh địa chỉ rồi Enter. Kiểm tra có `run_flights.py`, `src`, `requirements.txt`:

```powershell
Get-Location
Get-ChildItem
python --version
python src/prepare_data.py
python src/analyze.py
python run_flights.py --notebook
```

**Không chạy từ system32 hoặc C:\Users\tên_bạn khi file nằm ở thư mục khác.** Đổi thư mục bằng `cd "đường dẫn thư mục dự án"`, không dùng `/d` trong PowerShell.

Launcher cần Python **3.12**, tự chuẩn bị môi trường riêng. Lần đầu cần mạng cài thư viện và tải **một ZIP khoảng 27 MB**; CSV bên trong khoảng243MB nhưng được đọc trực tiếp theo khối, không bắt buộc giải nén ra đĩa. Nên dự phòng2GB trống cho môi trường/database/kết quả; đây không phải dung lượng tải. Lần sau giữ DB và ZIP để học offline. Không cần Git; chưa phải EXE độc lập. Có `START_WINDOWS.cmd`, `START_NOTEBOOK.cmd`; hỗ trợ thư mục có dấu/khoảng trắng, dùng môi trường ngắn khi đường dẫn Windows sâu. Không tắt chính sách bảo mật.

Notebook mở bài **`notebooks/02_analysis.ipynb`**. Nếu chỉ thấy trang quản lý, chọn **Files → notebooks → 02_analysis.ipynb**. Tab Running trống chỉ có nghĩa chưa có kernel chạy. Nhấn **Shift+Enter** từng ô từ trên xuống, giữ PowerShell mở.

Menu đọc dữ liệu, không sửa chuyến bay thật:

```powershell
python run_flights.py
```

Chọn số chức năng ở menu, sau đó chọn số đứng trước kết quả, không phải mã hãng/sân bay. Nhập sai có thể thử lại; `q` quay lại khi chọn danh mục. Mục **8** giải thích các chỉ số.

## Dữ liệu thật và phạm vi

Nguồn chính thức: [BTS On-Time Performance](https://www.bts.gov/explore-topics-and-geography/topics/airline-time-performance-and-causes-flight-delays), bảng **Reporting Carrier On-Time Performance (1987–present)**. [ZIP tháng1/2025](https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_1.zip). Tên và giải thích trường còn có trong `readme.html` đi kèm ZIP.

Snapshot kiểm tra **03/11/2026**, chốt URL, SHA256 ZIP/CSV và kích thước trong [manifest](docs/source_manifest.json). Không tự cập nhật checksum khi nguồn thay đổi; báo lỗi và yêu cầu kiểm tra phiên bản.

| Kết quả kiểm tra toàn tháng | Số bản ghi |
|---|---:|
| Tổng | 539.747 |
| Không hủy/không chuyển hướng, có ArrDelay | 522.269 |
| Đến trễ ít nhất15phút trong nhóm trên | 98.130 |
| Hủy | 16.312 |
| Chuyển hướng | 1.166 |
| Không hủy/không chuyển hướng nhưng thiếu ArrDelay | 0 |

Có **14 mã hãng báo cáo**, **329 sân bay**. Đây là các chuyến nội địa Mỹ được báo cáo trong bộ nguồn, **không phải tất cả chuyến bay trên thế giới hoặc mọi hãng Mỹ**. Hãng hiển thị bằng mã `Reporting_Airline` và định danh DOT; không gộp hãng vận hành với mạng hãng tiếp thị. Không suy tên hiện tại của hãng từ mã lịch sử. Tên thành phố và mã sân bay là nhãn của snapshot, không phải danh mục sân bay cập nhật hôm nay.

ZIP thật và database không nằm trong Git/ZIP phát hành. Dữ liệu BTS giữ điều kiện/ghi nhận nguồn của BTS; giấy phép MIT áp dụng cho mã nguồn dự án, không tự gán lại giấy phép dữ liệu bên thứ ba.

Nếu nguồn tải tự động tạm lỗi, tải thủ công **cùng ZIP hoặc CSV đã chốt**, rồi:

```powershell
python src/prepare_data.py --input "C:\Users\Dell XPS\Downloads\On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_1.zip"
```

Không yêu cầu token, API key hoặc tài khoản Kaggle. Không tự thay bằng fixture. Nhập vào DB tạm, kiểm tra xong mới công bố file đích. Lỗi thì không để DB hoàn thành giả, không nhập một phần. Giữ mọi dòng hợp lệ của snapshot, không tự bỏ chuyến hủy/trễ dài hoặc tự loại dòng trùng; mã tự nhiên trùng làm dừng nhập để kiểm tra.

## Hiểu mẫu số trước khi đọc biểu đồ

| Chỉ số | Định nghĩa |
|---|---|
| Tổng chuyến | Tất cả bản ghi trong khoảng ngày chọn |
| Đủ điều kiện (`eligible`) | Không hủy, không chuyển hướng, có ArrDelay |
| Đến trễ | Đủ điều kiện và ArrDelay **>=15 phút**; đúng15phút cũng trễ |
| Tỷ lệ đến trễ | Số đến trễ / số đủ điều kiện ×100% |
| Tỷ lệ hủy | Số hủy / tổng chuyến ×100% |
| Trung bình ArrDelay | Trung bình **có dấu** của chuyến đủ điều kiện; âm là đến sớm |
| Chuyến/ngày theo loại ngày | Tổng chuyến / số ngày lịch thuộc loại đó, gồm ngày0chuyến |

Không có mẫu số → để trống, không gán0%. Chuyến hủy/chuyển hướng/thiếu ArrDelay không biến thành đúng giờ. Tháng nguồn có0chuyến unknown nhưng ứng dụng vẫn xử lý và kiểm thử trường hợp này. Năm nhóm trạng thái rời nhau: on_time, delayed, cancelled, diverted, unknown_arrival.

**Thời gian:** dùng FlightDate nguồn và giờ khởi hành **dự kiến địa phương tại sân bay đi**. Không đổi sang giờ Việt Nam. Không lấy ArrTime − DepTime để tính thời lượng vì có múi giờ và chuyến qua ngày. Dùng ArrDelay do BTS cung cấp. Giữ HHMM dạng chuỗi để không mất số0đầu; 2400 nếu gặp được giữ nhãn nguồn và nhóm vào giờ00 (snapshot này không có CRSDepTime=2400). Heatmap không phải giờ đến hoặc giờ UTC.

**Sân bay:** bảng nhóm theo sân bay **xuất phát**, đo kết quả đến của các chuyến rời sân bay đó; không chứng minh sân bay đó gây trễ. Ngày thường/cuối tuần chưa xử lý ngày lễ. Không suy hành vi hiện tại, cả năm, nguyên nhân thời tiết hay chất lượng tổng thể từ một tháng dữ liệu quan sát.

## Kết quả phân tích

**4 PNG:**
1. Thanh ngang: tỷ lệ đến trễ theo hãng, kèm mẫu số; chỉ xếp hạng hãng có >=1.000 chuyến đủ điều kiện (ngưỡng học tập).
2. Đường: tổng chuyến và số đến trễ theo ngày, bổ sung ngày0chuyến.
3. Heatmap7×24: tỷ lệ đến trễ theo thứ và giờ khởi hành dự kiến; ô dưới30chuyến hợp lệ để trống.
4. Boxplot: số phút đến trễ/sớm theo hãng, chỉ nhóm đủ điều kiện. Ẩn dấu chấm ngoại lệ để dễ đọc; **không xóa ngoại lệ khỏi bảng hoặc thống kê**.

**6 CSV:** airline_summary, airport_summary, daily_summary, hourly_summary, day_type_summary, data_quality. Bảng giữ cả nhóm dưới ngưỡng, có `rank_eligible` cho hãng/sân bay. Báo cáo Markdown có3nhận xét định lượng và giới hạn. Không có dữ liệu phù hợp thì hình có thông báo.

SQL tính một dòng/mỗi chuyến trước khi tổng hợp. pandas **đọc lại ZIP/CSV nguồn theo khối50.000dòng**, tự chuyển kiểu và nhóm độc lập; không dùng bảng tổng hợp SQL để “đối chiếu”. Các tổng/số đếm phải khớp chính xác, tỷ lệ cho sai số số thực rất nhỏ. Chỉ xuất sau khi kiểm tra đạt. Giữ ZIP/CSV gốc để tái đối chiếu offline; nếu di chuyển nguồn, truyền `--input` khi phân tích.

```powershell
python src/analyze.py --start 2025-01-01 --end 2025-01-15 --out outputs/first_half
python src/prepare_data.py --db database/practice.db
python run_flights.py --notebook --db database/practice.db
```

Chỉ nhận khoảng ngày trong tháng01/2025, bao gồm hai đầu. `prepare_data.py` chạy lại **không xóa database**, chỉ kiểm tra và xuất3CSV danh mục/nguồn (không nhân bản toàn bộ CSV chuyến bay). Import trực tiếp chặn DB tồn tại. `--db` tạo bản thực hành khác. Dữ liệu giữa các máy không tự đồng bộ.

## Cấu trúc và lệnh thủ công

```text
src/prepare_data.py         Tải/kiểm tra/nhập nếu chưa có DB
src/analyze.py              Đối chiếu và xuất kết quả
data/raw/                  ZIP nguồn và CSV danh mục sinh ra
database/flights.db         SQLite sinh ra
sql/schema.sql             Bảng, khóa, indexes và view trạng thái
sql/analysis.sql            SQL mẫu
notebooks/02_analysis.ipynb Bài tổng hợp học trước
notebooks/lessons/         Tám bài chuyên sâu
flight_lab/                Logic dùng chung
docs/                      Từ điển, sơ đồ, bài tập/lời giải
tests/                     Fixture nhỏ ghi rõ giả lập
outputs/                   CSV, PNG, báo cáo sinh ra
```

```powershell
python -m pip install -r requirements.txt
python -m flight_lab.source
python -m flight_lab.import_data
python -m flight_lab.cli
python -m flight_lab.analyze
python -m notebook
```

`python -m` chạy module; `--input` chọn ZIP/CSV; `--db` chọn SQLite; `--start`/`--end` chọn ngày; `--out` chọn thư mục kết quả. Launcher nhận `--db`, `--notebook`, `--setup-only`. `Get-Location` xem vị trí, `Get-ChildItem` xem file, `cd` đổi thư mục. Trong menu chỉ nhập số; SQL chạy trong chuỗi Python của notebook qua `read_sql()`.

## Học SQL và Git

[Tám buổi học](docs/learning_path.md), [20bài tập](docs/exercises.md), [lời giải riêng](docs/solutions.md), [từ điển/sơ đồ](docs/data_dictionary.md). Notebook đọc DB chỉ đọc; INSERT/ROLLBACK dùng database tạm giả lập. Bài Git chưa làm sẵn: lọc chuyến theo **số phút đến trễ tối thiểu** trong menu. Tạo Issue → đặt tiêu chí → kiểm thử → diff → commit → push.

```powershell
python -m unittest discover -s tests -v
python -m flight_lab.execute_notebooks
```

Actions kiểm thử Windows/Linux bằng fixture nhỏ, không thay dữ liệu thật. Workflow thủ công tải snapshot thật, phân tích, chạy chín notebook; lưu bảng/hình/notebook14ngày, không lưu rawZIP/CSV hoặc database. Bản phát hành không chứa môi trường, database, nguồn thật hoặc notebook đã chạy.
