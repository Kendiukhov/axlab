
import subprocess
from get_run_ids import get_run_ids
from pathlib import Path

def main():
    run_ids = get_run_ids()
    run_paths = [str(Path('runs') / run_id) for run_id in run_ids]
    run_paths.append('battery_run')
    summary_file = 'interesting_axioms.txt'

    with open(summary_file, 'w') as f_out:
        for run_path in run_paths:
            print(f"Processing run: {run_path}")
            
            # Interpret all axioms in the run
            print("  Interpreting axioms...")
            subprocess.run(['python3', 'interpret_all.py', run_path])

            dossiers_path = Path(run_path) / 'dossiers.jsonl'
            if dossiers_path.exists() and dossiers_path.stat().st_size > 0:
                # Analyze the dossiers to find interesting axioms
                print("  Analyzing dossiers...")
                result = subprocess.run(
                    ['python3', 'analyze_dossiers.py', run_path],
                    capture_output=True,
                    text=True
                )
                
                print(f"  Analysis output for {run_path}:")
                print(result.stdout)
                
                # Write the analysis output to the summary file
                f_out.write(result.stdout)
                f_out.write("-" * 80 + "\n")
            else:
                print(f"  Skipping analysis for {run_path} because dossiers.jsonl is empty or does not exist.")

    print(f"Analysis complete. Results saved to {summary_file}")

if __name__ == '__main__':
    main()
