
import subprocess
from pathlib import Path

def main():
    """
    Runs the battery for all spec files in the 'specs' directory.
    """
    specs_dir = Path("specs")
    runs_dir = Path("runs")
    
    for spec_file in sorted(specs_dir.glob("*.json")):
        run_name = spec_file.stem
        run_dir = runs_dir / run_name
        
        if run_dir.exists():
            print(f"Skipping {run_name}, directory already exists.")
            continue
            
        print(f"Running battery for {spec_file.name}...")
        
        command = [
            'python3',
            '-m',
            'axlab.cli.run_battery',
            '--spec',
            str(spec_file),
            '--output',
            str(run_dir),
        ]
        
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env={'PYTHONPATH': '.'},
        )
        
        if process.returncode != 0:
            print(f"Error running battery for {spec_file.name}:")
            print(process.stderr)
        else:
            print(f"Finished run for {spec_file.name}, results in {run_dir}")

if __name__ == "__main__":
    main()
