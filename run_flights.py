"""Portable stdlib bootstrap; launch modules directly, never Jupyter .exe wrappers."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parent

def environment_directory(root=ROOT):
    # Jedi/Jupyter include deeply nested files; avoid Windows MAX_PATH failures.
    if sys.platform=='win32' and len(str(root))>80:
        cache=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'FlightLab/venvs'
        key=hashlib.sha256(str(root.resolve()).casefold().encode('utf-8')).hexdigest()[:12]
        return cache/key
    return root/'.venv'

ENV=environment_directory()
DB=ROOT/'database/flights.db'
for stream in (sys.stdout,sys.stderr):
    if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')

def environment_python():return ENV/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')

def run(command,db=None):
    env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PIP_PROGRESS_BAR='off')
    if db is not None:env['FLIGHT_LAB_DB']=str(db)
    subprocess.run([str(value) for value in command],cwd=ROOT,env=env,check=True)

def digest(notebook):
    requirements=ROOT/('requirements.txt' if notebook else 'requirements-app.txt')
    return hashlib.sha256(requirements.read_bytes()+(ROOT/'requirements-app.txt').read_bytes()+str(sys.version_info[:2]).encode()).hexdigest()

def prepare_environment(notebook=False):
    python=environment_python()
    if not python.is_file():
        print('Dang tao moi truong Python rieng:',ENV,flush=True)
        venv.EnvBuilder(with_pip=True).create(ENV)
    marker=ENV/('flight_notebook.sha256' if notebook else 'flight_app.sha256')
    ready=marker.is_file() and marker.read_text().strip()==digest(notebook)
    imports='import pandas,seaborn,matplotlib,requests'+(',notebook,nbconvert,ipykernel' if notebook else '')
    if ready:ready=subprocess.run([str(python),'-c',imports],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
    if not ready:
        print('Lan dau can Internet cai thu vien; khong can Git hoac Administrator.',flush=True)
        run([python,'-m','pip','install','-r',ROOT/('requirements.txt' if notebook else 'requirements-app.txt')])
        marker.write_text(digest(notebook)+'\n')
        if notebook:(ENV/'flight_app.sha256').write_text(digest(False)+'\n')
    return python

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--notebook',action='store_true');parser.add_argument('--setup-only',action='store_true');parser.add_argument('--db')
    args=parser.parse_args(argv)
    if sys.version_info[:2]!=(3,12):
        print('Can Python 3.12; cai Python 3.12, chon Add python.exe to PATH roi mo lai.');return 1
    db=Path(args.db) if args.db else DB
    if not db.is_absolute():db=ROOT/db
    try:
        python=prepare_environment(args.notebook)
        if not db.exists():
            print('Đang tải/nhập dữ liệu chuyến bay thật BTS tháng 01/2025. Lần đầu có thể mất vài phút.',flush=True)
            run([python,'-m','flight_lab.prepare_data','--db',db])
        else:print('Dung tiep database hien co, khong ghi de.',flush=True)
        if not args.setup_only:
            if args.notebook:
                # The server and kernel both use this environment's Python interpreter.
                print('Mở 02_analysis.ipynb; nếu thấy trang quản lý, chọn Files > notebooks > 02_analysis.ipynb.',flush=True)
                run([python,'-m','notebook','--notebook-dir',ROOT,ROOT/'notebooks/02_analysis.ipynb'],db=db)
            else:run([python,'-m','flight_lab.cli','--db',db])
        return 0
    except (OSError,ValueError,subprocess.CalledProcessError,EOFError,KeyboardInterrupt) as exc:
        print('Chua mo duoc:',exc)
        print('Giai nen toan bo ZIP vao Documents; kiem tra Python 3.12 va Internet lan dau. Khong tat chinh sach bao mat Windows.');return 1

if __name__=='__main__':raise SystemExit(main())
