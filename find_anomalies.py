
import json
from pathlib import Path

def find_anomalies(dossiers_dir):
    dossiers_path = Path(dossiers_dir)
    anomalies = []

    for dossier_file in dossiers_path.glob("*.json"):
        try:
            with open(dossier_file, 'r') as f:
                data = json.load(f)
                dossier = data.get('dossier', data)
                
                # Check for spectrum gaps
                spectrum = {s['size']: s['status'] for s in dossier.get('model_spectrum', [])}
                if 1 in spectrum and 2 in spectrum and 3 in spectrum:
                    if spectrum[1] == 'found' and spectrum[2] == 'not_found' and spectrum[3] == 'found':
                        anomalies.append({
                            'axiom': f"{dossier['axiom']['left']} = {dossier['axiom']['right']}",
                            'type': 'Spectrum Gap (1, 3 found; 2 missing)',
                            'file': dossier_file.name
                        })
                
                # Check for "Weird" axioms: non-degenerate but 0 confirmed properties
                confirmed = []
                if 'properties' in dossier:
                    confirmed = [p['name'] for p in dossier['properties'] if p.get('status') == 'confirmed']
                
                is_degenerate = any(dossier.get('degeneracy', {}).values())
                
                if not confirmed and not is_degenerate:
                    anomalies.append({
                        'axiom': f"{dossier['axiom']['left']} = {dossier['axiom']['right']}",
                        'type': 'Weird: Non-degenerate but 0 confirmed properties',
                        'file': dossier_file.name
                    })

                # Check for "Rare" property combinations (e.g. Associative but NOT Medial)
                if 'associative' in confirmed and 'medial' not in confirmed:
                     anomalies.append({
                            'axiom': f"{dossier['axiom']['left']} = {dossier['axiom']['right']}",
                            'type': 'Rare: Associative but NOT Medial',
                            'file': dossier_file.name
                        })

        except:
            continue

    return anomalies

if __name__ == "__main__":
    anomalies = find_anomalies("/Volumes/Crucial X6/MacBook/Code/axioms/runs/dossiers")
    if not anomalies:
        print("No obvious anomalies found in the current subset.")
    for a in anomalies:
        print(f"Anomaly: {a['type']} in {a['axiom']} ({a['file']})")
