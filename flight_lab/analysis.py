"""SQL aggregates reconciled against independently chunked raw BTS CSV."""
from pathlib import Path
from datetime import date
import pandas as pd
from .db import connect,day
from .source import open_csv,manifest,ZIP
COUNTS=['total','cancelled','diverted','unknown_arrival','eligible','delayed','delay_sum']
RATE_COLUMNS=['delay_rate_pct','cancel_rate_pct','mean_arrival_delay_min','flights_per_day']
def scope(start=None,end=None):
    a=day(start or '2025-01-01');b=day(end or '2025-01-31')
    if not '2025-01-01'<=a<=b<='2025-01-31':raise ValueError('Chọn ngày trong tháng 01/2025, ngày đầu không sau ngày cuối')
    return a,b
def quality(db):
    with connect(db) as c:
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or c.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('Database không toàn vẹn')
        n=c.execute('SELECT COUNT(*) FROM flights').fetchone()[0]
        meta=dict(c.execute('SELECT key,value FROM metadata').fetchall());sources=c.execute('SELECT csv_sha256,row_count FROM source_files').fetchall()
        if len(sources)!=1 or sources[0][1]!=n:raise ValueError('Số dòng nguồn/nhập không khớp')
        if meta.get('data_kind')=='real':
            s=manifest()
            if sources[0][0]!=s['csv_sha256'] or n!=s['expected_rows']:raise ValueError('Database khác snapshot thật đã chốt')
        elif meta.get('data_kind')!='synthetic_fixture':raise ValueError('Thiếu nhãn nguồn')
        bad=c.execute("""SELECT COUNT(*) FROM flights WHERE flight_date<'2025-01-01' OR flight_date>'2025-01-31'
        OR cancelled+diverted>1 OR (cancelled=0 AND diverted=0 AND arr_delay IS NOT NULL AND arr_del15 IS NOT NULL AND arr_del15<>(arr_delay>=15))""").fetchone()[0]
        if bad:raise ValueError('Ngày/cờ trạng thái không hợp lệ')
        counts=dict(c.execute('SELECT status,COUNT(*) FROM flight_status GROUP BY status'))
        if sum(counts.values())!=n:raise ValueError('Nhóm trạng thái không phủ hết nguồn')
        rows=[{'check':'source_rows','value':n},{'check':'imported_rows','value':n},{'check':'rejected_rows','value':0},{'check':'duplicate_natural_key','value':0},{'check':'foreign_key_errors','value':0}]
        rows.extend({'check':k,'value':counts.get(k,0)} for k in ['on_time','delayed','cancelled','diverted','unknown_arrival'])
        for label,col in [('carrier_count','carriers'),('airport_count','airports')]:rows.append({'check':label,'value':c.execute('SELECT COUNT(*) FROM '+col).fetchone()[0]})
        rows.append({'check':'scheduled_2400_count','value':c.execute("SELECT COUNT(*) FROM flights WHERE crs_dep_time='2400'").fetchone()[0]})
    return pd.DataFrame(rows)
def metrics(frame):
    df=frame.copy()
    for col in COUNTS:df[col]=pd.to_numeric(df[col],errors='raise').fillna(0).astype('int64')
    den=df.eligible.where(df.eligible>0)
    df['delay_rate_pct']=df.delayed*100.0/den
    df['cancel_rate_pct']=df.cancelled*100.0/df.total.where(df.total>0)
    df['mean_arrival_delay_min']=df.delay_sum/den
    if 'reporting_code' in df or 'airport_id' in df:df['rank_eligible']=df.eligible.ge(1000)
    return df
def queries(db,start=None,end=None):
    start,end=scope(start,end);p={'start':start,'end':end}
    # Each aggregation reads exactly one row per flight, never joins detailed histories.
    sums="""COUNT(f.flight_id) total,COALESCE(SUM(f.cancelled),0) cancelled,COALESCE(SUM(f.diverted),0) diverted,
    COALESCE(SUM(f.status='unknown_arrival'),0) unknown_arrival,COALESCE(SUM(f.eligible),0) eligible,
    COALESCE(SUM(f.status='delayed'),0) delayed,COALESCE(SUM(CASE WHEN f.eligible=1 THEN f.arr_delay ELSE 0 END),0) delay_sum"""
    with connect(db) as c:
        airlines=pd.read_sql_query('SELECT a.carrier_id,a.reporting_code,'+sums+" FROM carriers a LEFT JOIN flight_status f ON a.carrier_id=f.carrier_id AND f.flight_date BETWEEN :start AND :end GROUP BY a.carrier_id,a.reporting_code ORDER BY a.carrier_id",c,params=p)
        airports=pd.read_sql_query('SELECT a.airport_id,a.code,a.city,'+sums+" FROM airports a LEFT JOIN flight_status f ON a.airport_id=f.origin_id AND f.flight_date BETWEEN :start AND :end GROUP BY a.airport_id,a.code,a.city ORDER BY a.airport_id",c,params=p)
        daily=pd.read_sql_query('SELECT flight_date,'+sums+' FROM flight_status f WHERE flight_date BETWEEN :start AND :end GROUP BY flight_date ORDER BY flight_date',c,params=p)
        hourly=pd.read_sql_query("SELECT (CAST(strftime('%w',flight_date) AS INTEGER)+6)%7 weekday,scheduled_hour hour,"+sums+' FROM flight_status f WHERE flight_date BETWEEN :start AND :end GROUP BY weekday,hour ORDER BY weekday,hour',c,params=p)
        daytype=pd.read_sql_query("SELECT CASE WHEN strftime('%w',flight_date) IN('0','6') THEN 'weekend' ELSE 'weekday' END day_type,"+sums+' FROM flight_status f WHERE flight_date BETWEEN :start AND :end GROUP BY day_type ORDER BY day_type',c,params=p)
    daily=pd.DataFrame({'flight_date':pd.date_range(start,end).strftime('%Y-%m-%d')}).merge(daily,on='flight_date',how='left')
    hourly=pd.MultiIndex.from_product([range(7),range(24)],names=['weekday','hour']).to_frame(index=False).merge(hourly,on=['weekday','hour'],how='left')
    daytype=calendar_types(start,end).merge(daytype,on='day_type',how='left')
    result={'airline_summary':metrics(airlines),'airport_summary':metrics(airports),'daily_summary':metrics(daily),'hourly_summary':metrics(hourly),'day_type_summary':metrics(daytype)}
    result['day_type_summary']['flights_per_day']=result['day_type_summary'].total/result['day_type_summary'].calendar_days.where(result['day_type_summary'].calendar_days>0)
    return result
def calendar_types(start,end):
    idx=pd.date_range(start,end);counts=pd.Series(['weekend' if d.weekday()>=5 else 'weekday' for d in idx]).value_counts()
    return pd.DataFrame({'day_type':['weekday','weekend'],'calendar_days':[int(counts.get('weekday',0)),int(counts.get('weekend',0))]})
def pandas_tables(source,start=None,end=None):
    start,end=scope(start,end);parts={key:[] for key in ['airline_summary','airport_summary','daily_summary','hourly_summary','day_type_summary']};carriers={};airports={};plot=[]
    fields=['FlightDate','DOT_ID_Reporting_Airline','Reporting_Airline','OriginAirportID','Origin','OriginCityName','DestAirportID','Dest','DestCityName','CRSDepTime','ArrDelay','Cancelled','Diverted']
    with open_csv(source) as stream:
        for raw in pd.read_csv(stream,usecols=fields,dtype=str,keep_default_na=False,chunksize=50000):
            # Independent conversion/grouping from raw CSV, not SQL views or imported normalized values.
            for row in raw[['DOT_ID_Reporting_Airline','Reporting_Airline']].drop_duplicates().itertuples(index=False,name=None):carriers[int(row[0])]=row[1]
            for prefix in ['Origin','Dest']:
                for i,code,city in raw[[prefix+'AirportID',prefix,prefix+'CityName']].drop_duplicates().itertuples(index=False,name=None):airports[int(i)]=(code,city)
            raw=raw[raw.FlightDate.between(start,end)].copy()
            if raw.empty:continue
            dates=pd.to_datetime(raw.FlightDate,format='%Y-%m-%d')
            arr=pd.to_numeric(raw.ArrDelay.replace('',None),errors='raise')
            cancel=pd.to_numeric(raw.Cancelled,errors='raise').eq(1);divert=pd.to_numeric(raw.Diverted,errors='raise').eq(1)
            known=(~cancel)&(~divert)&arr.notna();unknown=(~cancel)&(~divert)&arr.isna()
            df=pd.DataFrame({'carrier_id':raw.DOT_ID_Reporting_Airline.astype(int),'reporting_code':raw.Reporting_Airline,'airport_id':raw.OriginAirportID.astype(int),'code':raw.Origin,'city':raw.OriginCityName,'flight_date':raw.FlightDate,'weekday':dates.dt.weekday,'hour':raw.CRSDepTime.astype(int).floordiv(100).mod(24),'day_type':dates.dt.weekday.map(lambda d:'weekend' if d>=5 else 'weekday'),'total':1,'cancelled':cancel.astype(int),'diverted':divert.astype(int),'unknown_arrival':unknown.astype(int),'eligible':known.astype(int),'delayed':(known&arr.ge(15)).astype(int),'delay_sum':arr.where(known,0).fillna(0).astype('int64')})
            groups={'airline_summary':['carrier_id','reporting_code'],'airport_summary':['airport_id','code','city'],'daily_summary':['flight_date'],'hourly_summary':['weekday','hour'],'day_type_summary':['day_type']}
            for name,keys in groups.items():parts[name].append(df.groupby(keys,as_index=False)[COUNTS].sum())
            plot.append(pd.DataFrame({'carrier_id':df.loc[known,'carrier_id'],'arr_delay':arr[known]}))
    catalogs={'airline_summary':pd.DataFrame([(i,n) for i,n in sorted(carriers.items())],columns=['carrier_id','reporting_code']),'airport_summary':pd.DataFrame([(i,*v) for i,v in sorted(airports.items())],columns=['airport_id','code','city']),'daily_summary':pd.DataFrame({'flight_date':pd.date_range(start,end).strftime('%Y-%m-%d')}),'hourly_summary':pd.MultiIndex.from_product([range(7),range(24)],names=['weekday','hour']).to_frame(index=False),'day_type_summary':calendar_types(start,end)}
    keys={'airline_summary':['carrier_id','reporting_code'],'airport_summary':['airport_id','code','city'],'daily_summary':['flight_date'],'hourly_summary':['weekday','hour'],'day_type_summary':['day_type']};result={}
    for name,frames in parts.items():
        summed=pd.concat(frames,ignore_index=True).groupby(keys[name],as_index=False)[COUNTS].sum() if frames else pd.DataFrame(columns=keys[name]+COUNTS)
        result[name]=metrics(catalogs[name].merge(summed,on=keys[name],how='left'))
    result['day_type_summary']['flights_per_day']=result['day_type_summary'].total/result['day_type_summary'].calendar_days.where(result['day_type_summary'].calendar_days>0)
    return result,pd.concat(plot,ignore_index=True) if plot else pd.DataFrame(columns=['carrier_id','arr_delay'])
def source_for(db,source=None):
    if source is not None:return Path(source)
    with connect(db) as c:r=c.execute("SELECT value FROM metadata WHERE key='input_path'").fetchone()
    path=Path(r[0]) if r else ZIP
    if path.exists():return path
    if ZIP.exists():return ZIP
    raise FileNotFoundError('Cần ZIP/CSV gốc để đối chiếu pandas. Dùng analyze --input đường_dẫn hoặc tải lại nguồn; không thay bằng fixture.')
def reconcile(db,start=None,end=None,source=None):
    checks=quality(db);sql=queries(db,start,end);other,plot=pandas_tables(source_for(db,source),start,end)
    for name,a in sql.items():
        a=a.reset_index(drop=True);b=other[name][a.columns].reset_index(drop=True)
        ratios=[x for x in a if x in RATE_COLUMNS]
        pd.testing.assert_frame_equal(a.drop(columns=ratios),b.drop(columns=ratios),check_dtype=False,check_exact=True)
        pd.testing.assert_frame_equal(a[ratios].astype(float),b[ratios].astype(float),check_dtype=False,check_exact=False,rtol=0,atol=1e-10)
    total=int(sql['airline_summary'].total.sum())
    if total!=int(sql['daily_summary'].total.sum()) or total!=int(sql['airport_summary'].total.sum()):raise ValueError('Tổng nguồn bị nhân hoặc mất qua JOIN')
    return sql,checks,plot
