import argparse
import json
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Interpret all axioms in a run.")
    parser.add_argument("run_path", help="The path to the run directory.")
    args = parser.parse_args()
    run_path = Path(args.run_path)
    results_path = run_path / 'results.jsonl'
    output_path = run_path / 'dossiers.jsonl'

    # Determine the command based on the run type
    if run_path.name == 'battery_run':
        base_command = [
            'python3',
            'axlab/cli/interpret.py',
            '--run-dir',
            str(run_path),
        ]
    else:
        with (run_path / 'run.json').open('r') as f:
            run_manifest = json.load(f)
        run_id = run_manifest['run_id']
        base_command = [
            'python3',
            'axlab/cli/interpret.py',
            '--store',
            '../results/runs/store',
            '--run-id',
            run_id,
        ]

    with results_path.open('r') as f_in, output_path.open('w') as f_out:
        for line in f_in:
            result = json.loads(line)
            axiom = result['axiom']
            left = axiom['left']
            right = axiom['right']

            command = base_command + [
                '--axiom-left',
                left,
                '--axiom-right',
                right,
            ]

            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env={'PYTHONPATH': '.'},
            )

            if process.returncode == 0:
                f_out.write(process.stdout)
            else:
                print(f"Error interpreting axiom: {left} = {right}")
                print(process.stderr)

if __name__ == '__main__':
    main()