import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import re
from pathlib import Path

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

def generate_frontier_map(root_dir, log_path, output_path):
    root_dir = Path(root_dir)
    log_path = Path(log_path)
    
    can_to_idx = {}
    total_axioms = 10404 # Known for Size-7
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("event") == "enumerate":
                        offset = data["offset"]
                        for i, ax in enumerate(data["axioms"]):
                            idx = offset + i
                            if idx < total_axioms:
                                can_to_idx[canonicalize_eq(ax["left"], ax["right"])] = idx
                except: continue

    grid = np.zeros(total_axioms)
    for res_path in root_dir.glob("**/results.jsonl"):
        with open(res_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line); d = data.get("dossier", data)
                    can = canonicalize_eq(d["axiom"]["left"], d["axiom"]["right"])
                    if can in can_to_idx:
                        idx = can_to_idx[can]
                        
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
                                val = 3 # Other Law (Lime)
                            else:
                                # Unified Weak Category
                                val = 8 # Weak Non-Trivial
                        
                        if grid[idx] < val:
                            grid[idx] = val
                except: continue

    colors = ["black", "#7F7F7F", "#FFD700", "#32CD32", "#1E90FF", "#00FFFF", "#FF1493", "#8A2BE2", "#C0C0C0"]
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(np.arange(len(colors)+1)-0.5, len(colors))
    
    side = 102 
    matrix = grid.reshape((side, side))
    fig, ax = plt.subplots(figsize=(10, 10), facecolor='black')
    ax.imshow(matrix, cmap=cmap, norm=norm, interpolation='nearest')
    ax.set_title(f"Size-7 Frontier Map: Structural Growth", color='white', fontsize=18)
    
    labels = ["Gap", "Trivial", "Strong Novelty", "Other Laws", "Idempotent", "Medial", "Self-Dist", "Associative", "Weak Non-Trivial"]
    patches = [plt.Rectangle((0,0),1,1, color=c) for c in colors]
    ax.legend(patches, labels, loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=3, frameon=False, labelcolor='white')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)

if __name__ == "__main__":
    import sys
    generate_frontier_map(sys.argv[1], sys.argv[2], sys.argv[3])
