import argparse
from pathlib import Path
import pandas as pd
from .db import ROOT,DEFAULT_DB,connect
from .source import download
from .import_data import import_data
from .analysis import quality
def prepare(db=DEFAULT_DB,source=None):
    if not Path(db).exists():import_data(source or download(),db)
    else:print('Giữ nguyên database; chỉ kiểm tra và xuất danh mục, không nhập lại.')
    quality(db);out=ROOT/'data/raw';out.mkdir(parents=True,exist_ok=True)
    with connect(db) as c:
        for name in ['carriers','airports','source_files']:pd.read_sql_query('SELECT * FROM '+name,c).to_csv(out/(name+'.csv'),index=False,encoding='utf-8-sig')
    return Path(db)
def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default=str(DEFAULT_DB));p.add_argument('--input');a=p.parse_args();print(prepare(a.db,a.input))
if __name__=='__main__':main()
