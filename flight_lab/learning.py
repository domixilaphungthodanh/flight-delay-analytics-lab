import os
from pathlib import Path
import pandas as pd
from .db import DEFAULT_DB,connect
def database():
    db=Path(os.environ.get('FLIGHT_LAB_DB',DEFAULT_DB)).resolve()
    if not db.exists():raise FileNotFoundError('Chạy python src/prepare_data.py ở thư mục dự án trước.')
    return db
def read_sql(sql,params=None):
    c=connect(database())
    try:return pd.read_sql_query(sql,c,params=params)
    finally:c.close()
