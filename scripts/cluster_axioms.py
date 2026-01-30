
import argparse
import re
from pathlib import Path
import json
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
    parser = argparse.ArgumentParser(description="Cluster axioms from a summary file.")
    parser.add_argument("summary_file", help="The path to the summary file.")
    args = parser.parse_args()
    summary_file = Path(args.summary_file)
    
    axioms = []
    current_axiom = None
    
    with summary_file.open('r') as f_in:
        for line in f_in:
            line = line.strip()
            if not line or line.startswith('-') or line.startswith('Analyzing'):
                if current_axiom:
                    axioms.append(current_axiom)
                    current_axiom = None
                continue

            if line.startswith('Axiom:'):
                if current_axiom:
                    axioms.append(current_axiom)
                match = re.search(r'Axiom:\s*(.*)\s*=\s*(.*)', line)
                if match:
                    current_axiom = {
                        'left': match.group(1).strip(),
                        'right': match.group(2).strip(),
                        'confirmed': [],
                        'refuted': [],
                    }
            elif line.startswith('Confirmed:'):
                if current_axiom:
                    props = line.replace('Confirmed:', '').strip().split(', ')
                    current_axiom['confirmed'] = [p for p in props if p]
            elif line.startswith('Refuted:'):
                if current_axiom:
                    props = line.replace('Refuted:', '').strip().split(', ')
                    current_axiom['refuted'] = [p for p in props if p]
    
    if current_axiom:
        axioms.append(current_axiom)

    # Create a vocabulary of all properties
    all_properties = set()
    for axiom in axioms:
        all_properties.update(axiom['confirmed'])
        all_properties.update(axiom['refuted'])
    
    vocabulary = sorted(list(all_properties))
    
    # Create feature vectors
    feature_vectors = []
    for axiom in axioms:
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
    if not feature_vectors:
        print("No axioms to cluster.")
        return

    n_clusters = 5 # Adjust as needed
    kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
    clusters = kmeans.fit_predict(feature_vectors)
    
    # Analyze and print clusters
    for i in range(n_clusters):
        print(f"Cluster {i+1}:")
        cluster_axioms_indices = [j for j, label in enumerate(clusters) if label == i]
        
        if not cluster_axioms_indices:
            print("  No axioms in this cluster.")
            continue

        # Find common properties
        first_axiom_vector = feature_vectors[cluster_axioms_indices[0]]
        common_properties = np.array(first_axiom_vector)
        for axiom_index in cluster_axioms_indices[1:]:
            common_properties = np.minimum(common_properties, np.array(feature_vectors[axiom_index]))

        confirmed_common = [vocabulary[k] for k, val in enumerate(common_properties) if val == 1]
        refuted_common = [vocabulary[k] for k, val in enumerate(common_properties) if val == -1]

        if confirmed_common:
            print(f"  Common Confirmed Properties: {', '.join(confirmed_common)}")
        if refuted_common:
            print(f"  Common Refuted Properties: {', '.join(refuted_common)}")
        
        print("  Axioms:")
        for axiom_index in cluster_axioms_indices:
            axiom = axioms[axiom_index]
            print(f"    {axiom['left']} = {axiom['right']}")

    # Visualize the clusters
    tsne = TSNE(n_components=2, random_state=0, perplexity=min(30, len(feature_vectors) - 1))
    transformed_vectors = tsne.fit_transform(np.array(feature_vectors))
    
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(transformed_vectors[:, 0], transformed_vectors[:, 1], c=clusters, cmap='viridis')
    plt.title('Axiom Clusters (t-SNE)')
    plt.xlabel('t-SNE component 1')
    plt.ylabel('t-SNE component 2')
    plt.legend(handles=scatter.legend_elements()[0], labels=[f'Cluster {i+1}' for i in range(n_clusters)])
    plt.savefig('axiom_clusters.png')
    print("\nCluster visualization saved to axiom_clusters.png")

if __name__ == '__main__':
    main()
