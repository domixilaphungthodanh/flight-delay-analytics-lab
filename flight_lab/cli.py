import argparse
import pandas as pd
from .db import DEFAULT_DB,connect
from .analysis import queries,quality,scope
from .analyze import analyze
def show(df):
    if df.empty:print('Không có kết quả.');return
    for i in range(0,len(df),20):
        print(df.iloc[i:i+20].round(2).fillna('Chưa có').to_string(index=False))
        if i+20<len(df) and input('Enter: trang sau; q: dừng > ').strip().lower()=='q':break
def period():
    return scope(input('Ngày đầu YYYY-MM-DD (Enter: 2025-01-01): ').strip() or None,input('Ngày cuối YYYY-MM-DD (Enter: 2025-01-31): ').strip() or None)
def choose(db,table,key,label):
    with connect(db) as c:rows=c.execute('SELECT '+key+','+label+' FROM '+table+' ORDER BY '+label).fetchall()
    word=input('Từ khóa (Enter: tất cả): ').strip().casefold();found=[r for r in rows if word in str(r[0]).casefold() or word in str(r[1]).casefold()]
    if not found:print('Không tìm thấy.');return None
    show(pd.DataFrame([(i,k,n) for i,(k,n) in enumerate(found,1)],columns=['Số chọn','ID nguồn','Nhãn']))
    while True:
        s=input('Nhập SỐ CHỌN đứng trước kết quả, không phải ID; q: quay lại > ').strip()
        if s.lower()=='q':return None
        if s=='' and len(found)==1:return found[0][0]
        if s.isdigit() and 1<=int(s)<=len(found):return found[int(s)-1][0]
        print(f'Chọn số từ 1 đến {len(found)}; ví dụ kết quả 1. AA thì nhập 1.')
def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default=str(DEFAULT_DB));a=p.parse_args();quality(a.db)
    while True:
        print('\nCHUYẾN BAY THẬT — BTS THÁNG 01/2025\n1. Tổng kết hãng\n2. Tổng kết sân bay xuất phát\n3. Lọc chuyến theo hãng\n4. Lọc chuyến theo sân bay đi\n5. Ngày thường/cuối tuần\n6. Nguồn và chất lượng\n7. Xuất báo cáo\n8. Giải thích chỉ số\n0. Thoát')
        choice=input('Chọn số chức năng: ').strip()
        if choice=='0':return
        try:
            if choice=='8':
                print('Đến trễ: ArrDelay >= 15 phút. eligible: chuyến không hủy/không chuyển hướng, có ArrDelay. delay_rate_pct: trễ/eligible ×100. Tổng chuyến gồm cả hủy/chuyển hướng. Số phút âm là đến sớm. Chưa rõ không phải 0. Giờ là giờ dự kiến địa phương sân bay đi.');continue
            if choice=='6':
                from .source import manifest
                print(manifest()['url']);show(quality(a.db));continue
            if choice not in ['1','2','3','4','5','7']:print('Nhập số 0–8.');continue
            start,end=period()
            if choice=='7':print(analyze(a.db,start,end));continue
            if choice in ['3','4']:
                carrier=choice=='3';selected=choose(a.db,'carriers' if carrier else 'airports','carrier_id' if carrier else 'airport_id','reporting_code' if carrier else 'code')
                if selected is None:continue
                with connect(a.db) as c:
                    query="SELECT f.flight_date,c.reporting_code,f.flight_number,o.code origin,d.code destination,f.crs_dep_time,f.arr_delay,f.status FROM flight_status f JOIN carriers c USING(carrier_id) JOIN airports o ON o.airport_id=f.origin_id JOIN airports d ON d.airport_id=f.dest_id WHERE f.flight_date BETWEEN ? AND ? AND f."+('carrier_id' if carrier else 'origin_id')+'=? ORDER BY flight_date,crs_dep_time,flight_id LIMIT 200'
                    rows=pd.read_sql_query(query,c,params=(start,end,selected))
                show(rows);print('Hiển thị tối đa 200 chuyến đầu; báo cáo dùng toàn bộ phạm vi.');continue
            t=queries(a.db,start,end)
            if choice=='1':show(t['airline_summary'][['reporting_code','total','eligible','delayed','delay_rate_pct','cancelled','diverted','unknown_arrival','rank_eligible']].sort_values('delay_rate_pct',ascending=False))
            elif choice=='2':show(t['airport_summary'][['code','city','total','eligible','delayed','delay_rate_pct','rank_eligible']].sort_values('total',ascending=False))
            elif choice=='5':show(t['day_type_summary'])
        except (ValueError,OSError,AssertionError) as e:print('Chưa thực hiện được:',e)
if __name__=='__main__':main()
