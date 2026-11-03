"""Real BTS reporting-carrier flight analysis, January 2025."""
import sys

# Direct `python -m flight_lab...` must also work in Windows CP1252 pipes.
# Notebook/captured streams without reconfigure are left alone.
for _stream in (sys.stdout,sys.stderr):
    if hasattr(_stream,'reconfigure'):
        _stream.reconfigure(encoding='utf-8',errors='backslashreplace')
__version__='1.0.0'
