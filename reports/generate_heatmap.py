
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os

def generate_heatmap(root_dir, output_path):
    # 1. Build Axiom -> Index mapping from agent_log
    axiom_to_index = {}
    explored_indices = set()
    
    log_path = Path(root_dir) / "agent_log.jsonl"
    if log_path.exists():
        with open(log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('event') == 'enumerate':
                        offset = data['offset']
                        for i, ax in enumerate(data['axioms']):
                            ax_str = f"{ax['left']} = {ax['right']}"
                            idx = offset + i
                            axiom_to_index[ax_str] = idx
                            explored_indices.add(idx)
                except:
                    continue

    # 2. Identify Non-Trivial Axioms from results.jsonl
    interesting_indices = set()
    root_path = Path(root_dir)
    for res_file in root_path.glob("**/results.jsonl"):
        with open(res_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    dossier = data.get('dossier', data)
                    ax_str = f"{dossier['axiom']['left']} = {dossier['axiom']['right']}"
                    
                    # Extract confirmed properties
                    confirmed = []
                    if 'properties' in dossier:
                        confirmed = [p['name'] for p in dossier['properties'] if p.get('status') == 'confirmed']
                    elif 'implications' in dossier:
                        confirmed = [i['theory'] for i in dossier['implications'] if i.get('status') == 'confirmed']
                    
                    if confirmed and ax_str in axiom_to_index:
                        interesting_indices.add(axiom_to_index[ax_str])
                except:
                    continue

    # 3. Construct 22x22 Grid
    # 0 = Unexplored, 1 = Explored (Trivial), 2 = Interesting
    grid = np.zeros((22, 22))
    for idx in range(484):
        r, c = divmod(idx, 22)
        if idx in interesting_indices:
            grid[r, c] = 2
        elif idx in explored_indices:
            grid[r, c] = 1
        else:
            grid[r, c] = 0

    # 4. Plot Heatmap
    plt.figure(figsize=(10, 10))
    plt.style.use('dark_background')
    
    # Custom colormap: Black (Unexplored), Gray (Trivial), Cyan (Interesting)
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(['#121212', '#333333', '#00E5FF'])
    
    plt.imshow(grid, cmap=cmap, interpolation='nearest')
    
    # Add title and labels
    plt.title("Axiom Universe Exploration Heatmap (22x22)", fontsize=16, pad=20)
    plt.xlabel("Offset % 22", fontsize=12)
    plt.ylabel("Offset // 22", fontsize=12)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#121212', edgecolor='white', label='Unexplored'),
        Patch(facecolor='#333333', edgecolor='white', label='Explored (Degenerate)'),
        Patch(facecolor='#00E5FF', edgecolor='white', label='Non-Trivial (Interesting)')
    ]
    plt.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Heatmap saved to {output_path}")

if __name__ == "__main__":
    generate_heatmap("/Volumes/Crucial X6/MacBook/Code/axioms/runs", "/Volumes/Crucial X6/MacBook/Code/axioms/reports/exploration_heatmap.png")
