import argparse,contextlib,hashlib,io,json,os,tempfile,zipfile
from pathlib import Path
import requests
from .db import ROOT
MANIFEST=ROOT/'docs/source_manifest.json'
ZIP=ROOT/'data/raw/bts-2025-01.zip'
def manifest():return json.loads(MANIFEST.read_text(encoding='utf-8'))
def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()
def download(target=ZIP):
    p=Path(target);s=manifest();p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        if sha256(p)!=s['zip_sha256']:raise ValueError('ZIP có sẵn khác SHA256 đã chốt; không ghi đè.')
        return p
    print('Tải BTS tháng 01/2025: khoảng 27 MB; không tải cả năm.',flush=True)
    fd,tmp=tempfile.mkstemp(dir=p.parent,suffix='.part');h=hashlib.sha256()
    try:
        with os.fdopen(fd,'wb') as f,requests.get(s['url'],stream=True,timeout=(20,90)) as response:
            response.raise_for_status()
            for b in response.iter_content(1024*1024):f.write(b);h.update(b)
        if h.hexdigest()!=s['zip_sha256']:raise ValueError('Nguồn đã đổi hoặc tải không đầy đủ; không tự đổi checksum/nguồn.')
        os.link(tmp,p)
    finally:Path(tmp).unlink(missing_ok=True)
    return p
@contextlib.contextmanager
def open_csv(path):
    p=Path(path);s=manifest()
    if p.suffix.lower()=='.zip':
        if sha256(p)!=s['zip_sha256']:raise ValueError('ZIP không khớp snapshot đã kiểm tra')
        with zipfile.ZipFile(p) as z:
            if s['csv_name'] not in z.namelist():raise ValueError('ZIP thiếu CSV đã chốt')
            with z.open(s['csv_name']) as b,io.TextIOWrapper(b,encoding='utf-8-sig',newline='') as f:yield f
    else:
        if sha256(p)!=s['csv_sha256']:raise ValueError('CSV không khớp snapshot đã kiểm tra')
        with p.open(encoding='utf-8-sig',newline='') as f:yield f
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default=str(ZIP));a=p.parse_args()
    try:print(download(a.out))
    except (ValueError,OSError,requests.RequestException) as e:p.exit(1,str(e)+'\nNếu BTS tạm lỗi, tải thủ công cùng URL rồi dùng --input. Không thay bằng dữ liệu giả lập.\n')
if __name__=='__main__':main()
