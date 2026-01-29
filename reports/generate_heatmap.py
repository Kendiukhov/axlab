import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import re
from pathlib import Path

def get_can(ax):
    return '='.join(sorted([ax['left'].replace(' ',''), ax['right'].replace(' ','')]))

def canonicalize_eq(left, right):
    s = f"{left}={right}".replace(" ", "")
    vars_found = re.findall(r'x\d+', s)
    vmap = {}
    for v in vars_found:
        if v not in vmap:
            vmap[v] = f"x{len(vmap)}"
    
    # Use a single-pass replacement to avoid double-substitution bugs
    if vmap:
        pattern = re.compile("|".join(re.escape(k) for k in vmap.keys()))
        s = pattern.sub(lambda m: vmap[m.group(0)], s)
    
    parts = s.split('=')
    if len(parts) == 2:
        return "=".join(sorted(parts))
    return s

def generate_heatmap(root_dir, output_path):
    root_dir = Path(root_dir)
    log_path = root_dir / "agent_log.jsonl"
    
    idx_to_can = {}
    if log_path.exists():
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("event") == "enumerate":
                        offset = data["offset"]
                        for i, ax in enumerate(data["axioms"]):
                            idx = offset + i
                            if idx < 484:
                                idx_to_can[idx] = canonicalize_eq(ax["left"], ax["right"])
                except: continue

    # PRIORITY: Higher value is plotted.
    # 0: Gap (Black)
    # 1: Trivial (Gray)
    # 2: Novel/Interesting (Gold)
    # 3: Other Laws (Lime)
    # 4: Idempotent (Blue)
    # 5: Medial (Cyan)
    # 6: Self-Distributive (Pink)
    # 7: Associative (Purple)
    
    can_to_data = {}
    for res_path in root_dir.glob("**/results.jsonl"):
        with open(res_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    d = data.get("dossier", data)
                    can = canonicalize_eq(d["axiom"]["left"], d["axiom"]["right"])
                    
                    val = 1 # Trivial
                    degen = d.get("degeneracy", {})
                    if not (degen.get("trivial_identity") or degen.get("projection_collapse") or degen.get("constant_collapse")):
                        props = [p["name"] for p in d.get("properties", []) if p.get("status") == "confirmed"]
                        if not props:
                            props = [i["theory"] for i in d.get("implications", []) if i.get("status") == "confirmed"]
                        
                        if props:
                            if "associative" in props: val = 7
                            elif any(x in props for x in ["left_self_distributive", "right_self_distributive"]): val = 6
                            elif "medial" in props: val = 5
                            elif "idempotent" in props: val = 4
                            else: val = 3 # Other Law
                        else:
                            val = 2 # Novel Discovery
                    
                    if can not in can_to_data or val > can_to_data[can]:
                        can_to_data[can] = val
                except: continue

    grid = np.zeros(484)
    for idx, can in idx_to_can.items():
        if can in can_to_data:
            grid[idx] = can_to_data[can]
    
    # NEW VIBRANT COLORS WITH CORRECT PRIORITY
    # 0: Black, 1: Gray, 2: Gold, 3: Lime, 4: DodgerBlue, 5: Cyan, 6: DeepPink, 7: BlueViolet
    colors = ["black", "#7F7F7F", "#FFD700", "#32CD32", "#1E90FF", "#00FFFF", "#FF1493", "#8A2BE2"]
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(np.arange(len(colors) + 1) - 0.5, len(colors))

    matrix = grid.reshape((22, 22))
    fig, ax = plt.subplots(figsize=(10, 10), facecolor='black')
    ax.imshow(matrix, cmap=cmap, norm=norm)
    ax.set_title("Axiom Discovery Catalog: Structural Distribution", color='white', fontsize=18)
    
    labels = ["Gap", "Trivial", "Discovery", "Other Laws", "Idempotent", "Medial", "Self-Dist", "Associative"]
    patches = [plt.Rectangle((0,0),1,1, color=c) for c in colors]
    ax.legend(patches, labels, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4, frameon=False, labelcolor='white')

    plt.tight_layout()
    plt.savefig(output_path, dpi=120)

if __name__ == "__main__":
    generate_heatmap("/Volumes/Crucial X6/MacBook/Code/axioms/runs", "/Volumes/Crucial X6/MacBook/Code/axioms/reports/exploration_heatmap.png")
