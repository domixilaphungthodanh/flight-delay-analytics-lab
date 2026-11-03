from pathlib import Path
from datetime import date
import sqlite3
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/'database/flights.db'
class Connection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
def connect(db=DEFAULT_DB,readonly=True):
    p=Path(db).resolve()
    c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,factory=Connection) if readonly else sqlite3.connect(p,factory=Connection)
    c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=30000')
    return c
def day(value):
    parsed=date.fromisoformat(value)
    if parsed.isoformat()!=value:raise ValueError('Ngày cần YYYY-MM-DD')
    return value
