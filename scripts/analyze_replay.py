
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np
try:
    from sklearn.cluster import KMeans
    from sklearn.manifold import TSNE
    import matplotlib.pyplot as plt
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "scikit-learn", "matplotlib", "--break-system-packages"])
    from sklearn.cluster import KMeans
    from sklearn.manifold import TSNE
    import matplotlib.pyplot as plt

def main():
    """
    Analyzes a given axiom exploration run.

    This script replays a run, filters for "interesting" axioms (those with both
    confirmed and refuted properties), clusters them based on their properties,
    and generates a visualization of the clusters.
    """
    parser = argparse.ArgumentParser(description="Analyze a run from a replay.")
    parser.add_argument("run_path", help="The path to the run directory.")
    parser.add_argument("--output-dir", default="analysis_results",
                        help="The directory to save analysis results.")
    parser.add_argument("--n-clusters", type=int, default=5,
                        help="The number of clusters to create.")
    args = parser.parse_args()

    run_path = Path(args.run_path)
    output_dir = Path(args.output_dir)
    n_clusters = args.n_clusters

    if not run_path.is_dir():
        print(f"Error: Run directory not found at {run_path}")
        return

    output_dir.mkdir(exist_ok=True)
    clusters_dir = output_dir / "clusters"
    clusters_dir.mkdir(exist_ok=True)

    # Replay the run to get the data
    print(f"Replaying run from {run_path}...")
    replay_command = [
        'python3',
        'axlab/cli/replay_run.py',
        '--run-dir',
        str(run_path),
    ]
    replay_process = subprocess.run(
        replay_command,
        capture_output=True,
        text=True,
        env={'PYTHONPATH': '.'},
    )

    if replay_process.returncode != 0:
        print(f"Error replaying run: {run_path}")
        print(replay_process.stderr)
        return

    run_data = json.loads(replay_process.stdout)
    results = run_data['results']
    
    # Filter for interesting axioms
    print("Filtering for interesting axioms...")
    interesting_axioms = []
    for result in results:
        properties = result.get('implications', [])
        confirmed = [prop['theory'] for prop in properties if prop.get('status') == 'confirmed']
        refuted = [prop['theory'] for prop in properties if prop.get('status') == 'counterexample']
        if confirmed and refuted:
            interesting_axioms.append({
                "axiom": result['axiom'],
                "confirmed": confirmed,
                "refuted": refuted,
            })

    if not interesting_axioms:
        print("No interesting axioms found in this run.")
        return
    
    print(f"Found {len(interesting_axioms)} interesting axioms.")
        
    # Create a vocabulary of all properties
    all_properties = set()
    for axiom in interesting_axioms:
        all_properties.update(axiom['confirmed'])
        all_properties.update(axiom['refuted'])
    
    vocabulary = sorted(list(all_properties))
    
    # Create feature vectors
    feature_vectors = []
    for axiom in interesting_axioms:
        vector = []
        for prop in vocabulary:
            if prop in axiom['confirmed']:
                vector.append(1)
            elif prop in axiom['refuted']:
                vector.append(-1)
            else:
                vector.append(0)
        feature_vectors.append(vector)
        
    # Perform clustering
    n_clusters = min(n_clusters, len(interesting_axioms))
    print(f"Performing clustering into {n_clusters} clusters...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
    clusters = kmeans.fit_predict(feature_vectors)
    
    # Analyze and print clusters
    for i in range(n_clusters):
        cluster_filename = clusters_dir / f"cluster_{i+1}.txt"
        with open(cluster_filename, "w") as f:
            print(f"Cluster {i+1}:", file=f)
            cluster_axioms_indices = [j for j, label in enumerate(clusters) if label == i]
            
            if not cluster_axioms_indices:
                print("  No axioms in this cluster.", file=f)
                continue

            # Find common properties
            first_axiom_vector = feature_vectors[cluster_axioms_indices[0]]
            common_properties = np.array(first_axiom_vector)
            for axiom_index in cluster_axioms_indices[1:]:
                common_properties = np.minimum(common_properties, np.array(feature_vectors[axiom_index]))

            confirmed_common = [vocabulary[k] for k, val in enumerate(common_properties) if val == 1]
            refuted_common = [vocabulary[k] for k, val in enumerate(common_properties) if val == -1]

            if confirmed_common:
                print(f"  Common Confirmed Properties: {', '.join(confirmed_common)}", file=f)
            if refuted_common:
                print(f"  Common Refuted Properties: {', '.join(refuted_common)}", file=f)
            
            print("  Axioms:", file=f)
            for axiom_index in cluster_axioms_indices:
                axiom = interesting_axioms[axiom_index]
                print(f"    {axiom['axiom']['left']} = {axiom['axiom']['right']}", file=f)
    print(f"Cluster information saved in {clusters_dir}")


    # Visualize the clusters
    if len(interesting_axioms) > 1:
        print("Generating cluster visualization...")
        tsne = TSNE(n_components=2, random_state=0, perplexity=min(30, len(feature_vectors) - 1))
        transformed_vectors = tsne.fit_transform(np.array(feature_vectors))
        
        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(transformed_vectors[:, 0], transformed_vectors[:, 1], c=clusters, cmap='viridis')
        plt.title('Axiom Clusters (t-SNE)')
        plt.xlabel('t-SNE component 1')
        plt.ylabel('t-SNE component 2')
        plt.legend(handles=scatter.legend_elements()[0], labels=[f'Cluster {i+1}' for i in range(n_clusters)])
        
        plot_filename = output_dir / 'axiom_clusters.png'
        plt.savefig(plot_filename)
        print(f"Cluster visualization saved to {plot_filename}")
    else:
        print("Skipping visualization because there is only one interesting axiom.")

if __name__ == '__main__':
    main()
