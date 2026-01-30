
import matplotlib.pyplot as plt
import numpy as np
import os

def create_visualizations(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Data from STATISTICS.md and findings
    categories = [
        "Medial", 
        "Self-Distributive", 
        "Symmetric/Flexible", 
        "Idempotent", 
        "Associative", 
        "Novel/Weird"
    ]
    counts = [125, 112, 143, 74, 61, 32]
    colors = ['#00E5FF', '#FF00FF', '#7C4DFF', '#448AFF', '#B2FF59', '#FFAB40']

    # 1. Bar Chart of Property Distribution
    plt.figure(figsize=(12, 7))
    plt.style.use('dark_background')
    bars = plt.bar(categories, counts, color=colors, alpha=0.8)
    plt.title("Axiom Property Distribution (Raw Counts)", fontsize=16, pad=20)
    plt.ylabel("Number of Unique Axioms", fontsize=12)
    plt.xticks(rotation=15, ha='right')
    
    # Add counts on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2, yval, ha='center', va='bottom', color='white', fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "property_distribution_bar.png"), dpi=300)
    plt.close()

    # 2. Donut Chart of Proportions
    plt.figure(figsize=(10, 8))
    plt.pie(counts, labels=categories, colors=colors, autopct='%1.1f%%', startangle=140, pctdistance=0.85, 
            wedgeprops={'alpha': 0.8, 'edgecolor': 'black'})
    
    # Draw a circle at the center to make it a donut
    centre_circle = plt.Circle((0,0), 0.70, fc='#121212')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    
    plt.title("Relative Frequency of Confirmed Properties", fontsize=16)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "property_proportions_donut.png"), dpi=300)
    plt.close()

    # 3. Exploration Progress Gauge (Horizontal Bar)
    plt.figure(figsize=(10, 3))
    total_universe = 484
    explored = 186
    remaining = total_universe - explored
    
    plt.barh(["Exploration Progress"], [explored], color='#00E5FF', label='Explored (186)')
    plt.barh(["Exploration Progress"], [remaining], left=[explored], color='#333333', label='Remaining (298)')
    
    plt.xlim(0, total_universe)
    plt.title(f"Universe Coverage: {explored/total_universe*100:.1f}%", fontsize=14)
    plt.legend(loc='lower center', bbox_to_anchor=(0.5, -0.6), ncol=2)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "coverage_progress.png"), dpi=300)
    plt.close()

    print(f"Visualizations saved to {output_dir}")

if __name__ == "__main__":
    reports_dir = "/Volumes/Crucial X6/MacBook/Code/axioms/reports"
    create_visualizations(reports_dir)
