import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def load_results():
    with open('benchmarks/results/benchmark_results.json', 'r') as f:
        return json.load(f)

def create_dataframe(results):
    rows = []
    for config, data in results.items():
        metrics = data['metrics']
        row = {
            'data_size': data['data_size'],
            'value_size': data['value_size'],
            'write_time': metrics['write_times_avg'],
            'read_time': metrics['sequential_read_times_avg'],
            'random_read_time': metrics['random_read_times_avg'],
            'batch_write_time': metrics['batch_write_times_avg'],
            'delete_time': metrics['delete_times_avg']
        }
        rows.append(row)
    return pd.DataFrame(rows)

def plot_operation_times(df, operation, title):
    plt.figure(figsize=(10, 6))
    for value_size in df['value_size'].unique():
        data = df[df['value_size'] == value_size]
        plt.plot(data['data_size'], data[operation], 
                marker='o', label=f'Value Size: {value_size} bytes')
    
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Data Size (number of entries)')
    plt.ylabel('Time (seconds)')
    plt.title(title)
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend()
    return plt.gcf()

def generate_plots(df):
    operations = {
        'write_time': 'Sequential Write Performance',
        'read_time': 'Sequential Read Performance',
        'random_read_time': 'Random Read Performance',
        'batch_write_time': 'Batch Write Performance',
        'delete_time': 'Delete Performance'
    }
    
    plots = {}
    for op, title in operations.items():
        fig = plot_operation_times(df, op, title)
        plots[op] = fig
        
    return plots

def generate_markdown_table(df):
    # Create a pivot table for better visualization
    table = pd.pivot_table(
        df,
        values=['write_time', 'read_time', 'random_read_time', 'batch_write_time', 'delete_time'],
        index=['data_size', 'value_size'],
        aggfunc='mean'
    )
    
    # Format the times to be more readable (microseconds)
    for col in table.columns:
        table[col] = table[col].apply(lambda x: f"{x*1e6:.2f}")
    
    # Convert to markdown
    return table.to_markdown()

def main():
    # Load results
    results = load_results()
    
    # Create DataFrame
    df = create_dataframe(results)
    
    # Generate plots
    plots = generate_plots(df)
    
    # Save plots
    Path('benchmarks/plots').mkdir(parents=True, exist_ok=True)
    for op, fig in plots.items():
        fig.savefig(f'benchmarks/plots/{op}.png')
        plt.close(fig)
    
    # Generate markdown table
    table = generate_markdown_table(df)
    
    # Save table
    with open('benchmarks/results/benchmark_table.md', 'w') as f:
        f.write("# Benchmark Results\n\n")
        f.write("Times are in microseconds (μs)\n\n")
        f.write(table)

if __name__ == "__main__":
    main() 