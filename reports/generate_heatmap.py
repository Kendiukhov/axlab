
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os

def generate_heatmap(root_dir, output_path):
    # 1. Build Axiom -> Index mapping from agent_log
    axiom_to_index = {}
    
    log_path = Path(root_dir) / "agent_log.jsonl"
    if log_path.exists():
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('event') == 'enumerate':
                        offset = data['offset']
                        for i, ax in enumerate(data['axioms']):
                            idx = offset + i
                            if idx < 484:
                                ax_str = f"{ax['left']} = {ax['right']}"
                                axiom_to_index[ax_str] = idx
                except:
                    continue

    # 2. Identify Explored and Categorize Interesting Indices
    # 0: Unexplored, 1: Trivial/Degenerate, 2: Associative, 3: Self-Dist, 4: Medial, 5: Idempotent, 6: Other
    grid_data = np.zeros(484)
    explored_indices = set()
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('event') == 'select':
                        for ax in data['axioms']:
                            ax_str = f"{ax['left']} = {ax['right']}"
                            if ax_str in axiom_to_index:
                                grid_data[axiom_to_index[ax_str]] = 1
                    if data.get('event') == 'interpret':
                        ax = data['axiom']
                        ax_str = f"{ax['left']} = {ax['right']}"
                        if ax_str in axiom_to_index:
                            grid_data[axiom_to_index[ax_str]] = 1
                except:
                    continue

    root_path = Path(root_dir)
    for res_file in root_path.glob("**/results.jsonl"):
        with open(res_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    dossier = data.get('dossier', data)
                    ax = dossier['axiom']
                    ax_str = f"{ax['left']} = {ax['right']}"
                    
                    if ax_str not in axiom_to_index: continue
                    idx = axiom_to_index[ax_str]

                    confirmed = []
                    if 'properties' in dossier:
                        confirmed = [p['name'] for p in dossier['properties'] if p.get('status') == 'confirmed']
                    elif 'implications' in dossier:
                        confirmed = [i['theory'] for i in dossier['implications'] if i.get('status') == 'confirmed']
                    
                    if not confirmed:
                        grid_data[idx] = 1 # Mark as trivial
                        continue

                    # Precedence: Associative > Self-Dist > Medial > Idempotent > Other
                    if 'associative' in confirmed: grid_data[idx] = 2
                    elif 'left_self_distributive' in confirmed or 'right_self_distributive' in confirmed: grid_data[idx] = 3
                    elif 'medial' in confirmed: grid_data[idx] = 4
                    elif 'idempotent' in confirmed: grid_data[idx] = 5
                    else: grid_data[idx] = 6
                except:
                    continue

    # 3. Construct 22x22 Grid
    grid = grid_data.reshape((22, 22))

    # 4. Plot Heatmap
    plt.figure(figsize=(11, 11))
    plt.style.use('dark_background')
    
    from matplotlib.colors import ListedColormap
    # Colors: Black, Gray, Purple (Assoc), Magenta (Dist), Cyan (Medial), Blue (Idem), Green (Other)
    colors = ['#000000', '#333333', '#7C4DFF', '#FF00FF', '#00E5FF', '#448AFF', '#B2FF59']
    cmap = ListedColormap(colors)
    
    plt.imshow(grid, cmap=cmap, interpolation='nearest')
    
    plt.title("Spatial Distribution of Axiom Properties (22x22 Universe)", fontsize=16, pad=20)
    plt.xlabel("Offset % 22 (Complexity Sub-cycle)", fontsize=12)
    plt.ylabel("Offset // 22 (Complexity Group)", fontsize=12)
    
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#000000', label='Unexplored'),
        Patch(facecolor='#333333', label='Trivial/Degenerate'),
        Patch(facecolor='#7C4DFF', label='Associative'),
        Patch(facecolor='#FF00FF', label='Self-Distributive'),
        Patch(facecolor='#00E5FF', label='Medial (Entropic)'),
        Patch(facecolor='#448AFF', label='Idempotent'),
        Patch(facecolor='#B2FF59', label='Other Interesting')
    ]
    plt.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Enhanced Heatmap saved to {output_path}")

if __name__ == "__main__":
    generate_heatmap("/Volumes/Crucial X6/MacBook/Code/axioms/runs", "/Volumes/Crucial X6/MacBook/Code/axioms/reports/exploration_heatmap.png")
