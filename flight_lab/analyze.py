import argparse
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from .db import ROOT,DEFAULT_DB,connect
from .analysis import reconcile,scope
from .source import manifest
def analyze(db=DEFAULT_DB,start=None,end=None,out=None,source=None):
    start,end=scope(start,end);tables,checks,plot=reconcile(db,start,end,source)
    out=Path(out or ROOT/'outputs'/f'{start}_{end}');out.mkdir(parents=True,exist_ok=True)
    tables['data_quality']=checks
    for name,df in tables.items():df.to_csv(out/(name+'.csv'),index=False,encoding='utf-8-sig')
    sns.set_theme(style='whitegrid')
    def draw(name,title,fn,empty=False,foot=''):
        fig,ax=plt.subplots(figsize=(11,7))
        if empty:ax.text(.5,.5,'Not enough eligible data',ha='center',transform=ax.transAxes);ax.axis('off')
        else:fn(ax)
        ax.set_title(title+f' | {start} to {end}');fig.text(.01,.01,foot,fontsize=9);fig.tight_layout(rect=(0,.04,1,1));fig.savefig(out/name,dpi=150);plt.close(fig)
    a=tables['airline_summary'];rank=a[a.rank_eligible].sort_values(['delay_rate_pct','reporting_code'],ascending=[False,True]).copy()
    rank['label']=rank.reporting_code+' (n='+rank.eligible.astype(str)+')'
    def airline(ax):
        sns.barplot(data=rank,x='delay_rate_pct',y='label',color='#3188a4',ax=ax);ax.set_xlabel('Late arrival rate (%)');ax.set_ylabel('Reporting carrier (eligible flights)')
    draw('01_airline_delay_rate.png','Arrival delay >=15 min by reporting carrier',airline,rank.empty,'Rate denominator: non-cancelled, non-diverted flights with known arrival delay; n>=1,000 (learning rule).')
    d=tables['daily_summary']
    def daily(ax):
        tidy=d[['flight_date','total','delayed']].melt('flight_date',var_name='series',value_name='flights');sns.lineplot(data=tidy,x='flight_date',y='flights',hue='series',ax=ax)
        ticks=list(range(0,len(d),3));ax.set_xticks(ticks,labels=d.flight_date.iloc[ticks].tolist());ax.tick_params(axis='x',rotation=45);ax.set_xlabel('Flight date');ax.set_ylabel('Flights')
    draw('02_daily_flights.png','Scheduled flights and late arrivals by flight date',daily,int(a.total.sum())==0,'Date is the BTS flight date, not actual arrival date. Includes zero-flight calendar days.')
    h=tables['hourly_summary'].copy();h.loc[h.eligible<30,'delay_rate_pct']=float('nan')
    def heat(ax):
        pivot=h.pivot(index='weekday',columns='hour',values='delay_rate_pct');pivot.index=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];sns.heatmap(pivot,ax=ax,cmap='YlOrRd',vmin=0,vmax=100,cbar_kws={'label':'Late arrival rate (%)'})
        ax.set_xticklabels([f'{x:02}' for x in range(24)],rotation=0,fontsize=9);ax.set_xlabel('Scheduled departure hour (origin local)')
    draw('03_weekday_hour.png','Arrival delay rate by scheduled departure weekday/hour',heat,h.delay_rate_pct.isna().all(),'Origin-local scheduled departure hour; blank cells have fewer than 30 eligible flights. Not a causal claim.')
    def box(ax):
        lookup=a.set_index('carrier_id').reporting_code;values=plot.assign(carrier=plot.carrier_id.map(lookup));sns.boxplot(data=values,x='carrier',y='arr_delay',showfliers=False,ax=ax,color='#80b7d0');ax.axhline(15,color='firebrick',linestyle='--');ax.set_ylabel('Signed arrival delay (minutes; negative = early)')
    draw('04_delay_distribution.png','Arrival delay distribution by reporting carrier',box,plot.empty,'Eligible flights only. Outlier dots are hidden, not removed from tables/statistics. No cancelled/diverted flights assigned zero.')
    total=int(a.total.sum());eligible=int(a.eligible.sum());late=int(a.delayed.sum());cancelled=int(a.cancelled.sum());diverted=int(a.diverted.sum());unknown=int(a.unknown_arrival.sum())
    with connect(db) as c:kind=c.execute("SELECT value FROM metadata WHERE key='data_kind'").fetchone()[0]
    label='DỮ LIỆU THẬT BTS' if kind=='real' else 'GIẢ LẬP KIỂM THỬ — KHÔNG PHẢI KẾT QUẢ THẬT'
    notes=[f'Có **{total:,} chuyến** thuộc phạm vi; **{eligible:,}** chuyến đủ điều kiện tính tỷ lệ đến trễ. Hủy **{cancelled:,}**, chuyển hướng **{diverted:,}**, thiếu ArrDelay ở chuyến không hủy/không chuyển hướng **{unknown:,}**.']
    notes.append(f'Có **{late:,}/{eligible:,}** chuyến đến trễ ít nhất 15 phút (**{late/eligible*100:.2f}%**).' if eligible else 'Không có mẫu số hợp lệ; tỷ lệ để trống, không gán 0%.')
    if not rank.empty:
        r=rank.iloc[0];notes.append(f'Trong hãng đủ ngưỡng 1.000 chuyến hợp lệ, mã **{r.reporting_code}** có tỷ lệ đến trễ cao nhất trong nhóm: **{r.delay_rate_pct:.2f}%**, mẫu số **{int(r.eligible):,}**. Chưa điều chỉnh tuyến, thời tiết hoặc lịch bay; không kết luận hãng kém hơn do riêng chỉ số này.')
    else:notes.append('Chưa đủ mẫu để xếp hạng hãng; vẫn giữ mọi hãng trong bảng CSV.')
    text=f'# Flight Delay Analytics Lab\n\n**{label}** — {start} đến {end}.\n\n'+'\n\n'.join(f'{i}. {n}' for i,n in enumerate(notes,1))
    s=manifest();text+='\n\n## Định nghĩa và giới hạn\n\nĐến trễ: ArrDelay >= 15 phút, tính ở cổng đến. Mẫu số là chuyến không hủy, không chuyển hướng, có ArrDelay. Chuyến đến sớm giữ số phút âm; trung bình là trung bình có dấu. Số chuyến không phải số hành khách. Tỷ lệ hủy dùng tổng chuyến. Hủy/chuyển hướng/không rõ/đúng giờ/trễ là các nhóm rời nhau.\n\nSân bay trong airport_summary là **sân bay xuất phát**, đo kết quả đến của các chuyến xuất phát tại đó; không phải chẩn đoán lỗi vận hành sân bay. Heatmap dựa trên ngày chuyến và giờ khởi hành dự kiến địa phương ở sân bay đi; không đổi sang giờ Việt Nam. Không trừ trực tiếp hai giờ HHMM để suy thời lượng, vì khác múi giờ và có chuyến qua ngày. 2400, nếu có, giữ nguyên nhãn nguồn và được nhóm vào giờ 00, không tự suy ngày đến.\n\nNgày thường/cuối tuần tính theo lịch, chưa xử lý ngày lễ. Số chuyến/ngày chia số ngày lịch của từng loại, gồm ngày 0 chuyến. Một tháng của các hãng báo cáo không đại diện cả năm, toàn bộ hãng Mỹ hoặc thế giới. Không có điểm số tổng hợp, khuyến nghị mua vé hoặc kết luận nguyên nhân.\n\nSQL đã đối chiếu độc lập với pandas đọc lại ZIP/CSV nguồn theo khối. Chỉ xuất sau khi kiểm tra đạt.\n\nNguồn BTS: '+s['url']+'\n\nĐịnh nghĩa: '+s['definitions_url']+'\n\nCSV SHA256: `'+s['csv_sha256']+'`\n'
    (out/'report.md').write_text(text,encoding='utf-8');return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default=str(DEFAULT_DB));p.add_argument('--start');p.add_argument('--end');p.add_argument('--out');p.add_argument('--input');a=p.parse_args()
    try:print(analyze(a.db,a.start,a.end,a.out,a.input))
    except (ValueError,OSError,AssertionError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
