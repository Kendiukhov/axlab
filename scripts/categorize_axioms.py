import json
import os
from pathlib import Path
from collections import defaultdict

def scan_for_axioms(root_dir):
    root_path = Path(root_dir)
    unique_axioms = {}

    # Scan for results.jsonl in run directories
    for results_file in root_path.glob("**/results.jsonl"):
        try:
            with open(results_file, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    process_axiom_data(data, unique_axioms)
        except Exception as e:
            print(f"Error parsing {results_file}: {e}")

    # Also scan dossiers directory for individual JSONs
    dossiers_path = root_path / "dossiers"
    if dossiers_path.exists():
        for dossier_file in dossiers_path.glob("*.json"):
            try:
                with open(dossier_file, 'r') as f:
                    data = json.load(f)
                    process_axiom_data(data, unique_axioms)
            except Exception as e:
                print(f"Error parsing {dossier_file}: {e}")

    return unique_axioms

def process_axiom_data(data, unique_axioms):
    # Handle different structures (results.jsonl vs dossiers)
    dossier = data.get('dossier', data)
    
    if 'axiom' not in dossier:
        return
    
    axiom_str = f"{dossier['axiom']['left']} = {dossier['axiom']['right']}"
    
    # Extract confirmed properties (handle nested properties in dossiers vs implications in results.jsonl)
    confirmed = []
    
    # Format 1: 'properties' list (dossiers)
    if 'properties' in dossier:
        for prop in dossier['properties']:
            if prop.get('status') == 'confirmed':
                confirmed.append(prop['name'])
    
    # Format 2: 'implications' list (results.jsonl)
    elif 'implications' in dossier:
        for imp in dossier['implications']:
            if imp.get('status') == 'confirmed':
                confirmed.append(imp['theory'])

    if confirmed:
        if axiom_str not in unique_axioms:
            unique_axioms[axiom_str] = confirmed
        else:
            # Merge confirmed properties if found in multiple places
            unique_axioms[axiom_str] = list(set(unique_axioms[axiom_str] + confirmed))

def categorize_axioms(unique_axioms):
    categories = defaultdict(list)
    
    for axiom_str, confirmed in unique_axioms.items():
        matched = False
        
        if 'associative' in confirmed:
            categories['Associative (Semigroups/Monoids)'].append(axiom_str)
            matched = True
        
        if 'left_self_distributive' in confirmed or 'right_self_distributive' in confirmed:
            categories['Self-Distributive (Shelves/Racks)'].append(axiom_str)
            matched = True
        
        if 'medial' in confirmed:
            categories['Medial (Entropic)'].append(axiom_str)
            matched = True
            
        if 'commutative' in confirmed or 'flexible' in confirmed:
            categories['Symmetric/Flexible (Non-associative)'].append(axiom_str)
            matched = True
            
        if 'idempotent' in confirmed:
            categories['Idempotent'].append(axiom_str)
            matched = True
            
        if not matched:
            categories['Other Interesting'].append(axiom_str)
            
    return categories

def main():
    root_dir = "/Volumes/Crucial X6/MacBook/Code/axioms/runs"
    unique_axioms = scan_for_axioms(root_dir)
    categories = categorize_axioms(unique_axioms)
    
    print(f"Summary of Non-Trivial Axioms Found ({len(unique_axioms)} unique):\n")
    
    for cat, axioms in sorted(categories.items()):
        print(f"### {cat} ({len(axioms)})")
        for ax in sorted(axioms):
            props = unique_axioms[ax]
            print(f"- `{ax}`: confirmed {', '.join(sorted(props))}")
        print()

if __name__ == "__main__":
    main()
