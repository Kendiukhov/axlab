import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Analyze the dossiers for a run.")
    parser.add_argument("run_path", help="The path to the run directory.")
    args = parser.parse_args()
    run_path = Path(args.run_path)
    dossiers_path = run_path / 'dossiers.jsonl'

    print(f"Analyzing dossiers for run: {run_path}")
    print("Axioms with both confirmed and refuted properties:")

    found_any = False
    with dossiers_path.open('r') as f_in:
        for line in f_in:
            dossier_data = json.loads(line)
            dossier = dossier_data['dossier']
            
            confirmed = []
            refuted = []
            if 'properties' in dossier:
                for prop in dossier['properties']:
                    if prop.get('status') == 'counterexample':
                        refuted.append(prop['name'])
                    elif prop.get('status') == 'confirmed':
                        confirmed.append(prop['name'])
            
            if confirmed and refuted:
                found_any = True
                axiom = dossier['axiom']
                print(f"  Axiom: {axiom['left']} = {axiom['right']}")
                print(f"    Confirmed: {', '.join(confirmed)}")
                print(f"    Refuted: {', '.join(refuted)}")

    if not found_any:
        print(f"No axioms with a mix of confirmed and refuted properties found in {run_path}")

if __name__ == '__main__':
    main()
