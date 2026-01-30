
import os
from pathlib import Path

def get_run_ids(runs_dir='runs'):
    run_ids = []
    for p in Path(runs_dir).iterdir():
        if p.is_dir() and len(p.name) == 16:
            try:
                int(p.name, 16)
                run_ids.append(p.name)
            except ValueError:
                pass
    return run_ids

if __name__ == '__main__':
    for run_id in get_run_ids():
        print(run_id)
