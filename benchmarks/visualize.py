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
    for config, result in results.items():
        metrics = result['metrics']
        data_size = result['data_size']
        value_size = result['value_size']
        
        # Add each metric
        data.append({
            'Data Size': data_size,
            'Value Size': value_size,
            'Operation': 'Sequential Write',
            'Time (s)': metrics['write_times_avg'],
            'Std Dev': metrics['write_times_std']
        })
        data.append({
            'Data Size': data_size,
            'Value Size': value_size,
            'Operation': 'Sequential Read',
            'Time (s)': metrics['sequential_read_times_avg'],
            'Std Dev': metrics['sequential_read_times_std']
        })
        data.append({
            'Data Size': data_size,
            'Value Size': value_size,
            'Operation': 'Random Read',
            'Time (s)': metrics['random_read_times_avg'],
            'Std Dev': metrics['random_read_times_std']
        })
        data.append({
            'Data Size': data_size,
            'Value Size': value_size,
            'Operation': 'Batch Write',
            'Time (s)': metrics['batch_write_times_avg'],
            'Std Dev': metrics['batch_write_times_std']
        })
        data.append({
            'Data Size': data_size,
            'Value Size': value_size,
            'Operation': 'Delete',
            'Time (s)': metrics['delete_times_avg'],
            'Std Dev': metrics['delete_times_std']
        })
    
    df = pd.DataFrame(data)
    
    # Create plots for different aspects
    create_operation_comparison(df)
    create_data_size_impact(df)
    create_value_size_impact(df)
    
    # Save detailed results to CSV
    df.to_csv('benchmarks/results/detailed_results.csv', index=False)

def create_operation_comparison(df):
    plt.figure(figsize=(15, 8))
    sns.set_style("whitegrid")
    
    # Group by operation type and calculate mean
    operation_means = df.groupby('Operation')['Time (s)'].mean().reset_index()
    
    # Create bar plot
    ax = sns.barplot(x='Operation', y='Time (s)', data=operation_means, palette='husl')
    
    plt.title('Average Operation Times Across All Configurations')
    plt.ylabel('Average Time (seconds)')
    plt.xlabel('Operation Type')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig('benchmarks/results/operation_comparison.png')
    plt.close()

def create_data_size_impact(df):
    plt.figure(figsize=(15, 8))
    sns.set_style("whitegrid")
    
    # Create line plot
    ax = sns.lineplot(data=df, x='Data Size', y='Time (s)', 
                     hue='Operation', style='Operation', markers=True, dashes=False)
    
    plt.title('Impact of Data Size on Operation Performance')
    plt.ylabel('Average Time (seconds)')
    plt.xlabel('Data Size (number of entries)')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    plt.savefig('benchmarks/results/data_size_impact.png')
    plt.close()

def create_value_size_impact(df):
    plt.figure(figsize=(15, 8))
    sns.set_style("whitegrid")
    
    # Create line plot
    ax = sns.lineplot(data=df, x='Value Size', y='Time (s)', 
                     hue='Operation', style='Operation', markers=True, dashes=False)
    
    plt.title('Impact of Value Size on Operation Performance')
    plt.ylabel('Average Time (seconds)')
    plt.xlabel('Value Size (bytes)')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    plt.savefig('benchmarks/results/value_size_impact.png')
    plt.close()

def main():
    # Create results directory if it doesn't exist
    Path('benchmarks/results').mkdir(parents=True, exist_ok=True)
    
    # Load and visualize results
    results = load_results()
    create_comparison_charts(results)
    
    print("\nVisualization complete! Check the following files:")
    print("1. benchmarks/results/operation_comparison.png")
    print("2. benchmarks/results/data_size_impact.png")
    print("3. benchmarks/results/value_size_impact.png")
    print("4. benchmarks/results/detailed_results.csv")

if __name__ == "__main__":
    main() 