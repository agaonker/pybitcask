import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

def load_results():
    with open('benchmarks/results/benchmark_results.json', 'r') as f:
        return json.load(f)

def create_comparison_charts(results):
    # Convert results to DataFrame
    data = []
    for engine, stats in results.items():
        data.append({
            'Engine': engine,
            'Operation': 'Write',
            'Time (s)': stats['write_avg'],
            'Std Dev': stats['write_std']
        })
        data.append({
            'Engine': engine,
            'Operation': 'Read',
            'Time (s)': stats['read_avg'],
            'Std Dev': stats['read_std']
        })
        data.append({
            'Engine': engine,
            'Operation': 'Delete',
            'Time (s)': stats['delete_avg'],
            'Std Dev': stats['delete_std']
        })
    
    df = pd.DataFrame(data)
    
    # Set style
    plt.style.use('seaborn')
    sns.set_palette("husl")
    
    # Create bar plot
    plt.figure(figsize=(12, 6))
    ax = sns.barplot(x='Operation', y='Time (s)', hue='Engine', data=df)
    
    # Add error bars
    for i, bar in enumerate(ax.patches):
        x = bar.get_x() + bar.get_width() / 2
        y = bar.get_height()
        std = df['Std Dev'].iloc[i]
        plt.errorbar(x, y, yerr=std, fmt='none', color='black', capsize=5)
    
    plt.title('Storage Engine Performance Comparison')
    plt.ylabel('Average Time (seconds)')
    plt.xlabel('Operation')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save plot
    plt.savefig('benchmarks/results/performance_comparison.png')
    plt.close()
    
    # Create table
    table = df.pivot(index='Engine', columns='Operation', values='Time (s)')
    table.to_csv('benchmarks/results/performance_table.csv')
    
    # Print results
    print("\nPerformance Comparison Table:")
    print(table)

def main():
    # Create results directory if it doesn't exist
    Path('benchmarks/results').mkdir(parents=True, exist_ok=True)
    
    # Load and visualize results
    results = load_results()
    create_comparison_charts(results)

if __name__ == "__main__":
    main() 