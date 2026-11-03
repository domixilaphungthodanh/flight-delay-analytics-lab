import argparse,os
from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from .db import ROOT,DEFAULT_DB
def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default=str(DEFAULT_DB));a=p.parse_args()
    os.environ['FLIGHT_LAB_DB']=str(Path(a.db).resolve())
    out=ROOT/'notebooks/executed';out.mkdir(parents=True,exist_ok=True)
    paths=[ROOT/'notebooks/02_analysis.ipynb',*sorted((ROOT/'notebooks/lessons').glob('*.ipynb'))]
    assert len(paths)==9
    for path in paths:
        nb=nbformat.read(path,as_version=4);ExecutePreprocessor(timeout=180,kernel_name='python3').preprocess(nb,{'metadata':{'path':str(ROOT)}})
        nbformat.write(nb,out/path.name);print(path.name,flush=True)
if __name__=='__main__':main()
