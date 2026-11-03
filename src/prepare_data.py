import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
if __name__=='__main__':
    from run_flights import prepare_environment,run
    python=prepare_environment()
    run([python,'-m','flight_lab.prepare_data',*sys.argv[1:]])
