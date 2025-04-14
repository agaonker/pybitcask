import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import platform
import psutil
import os

def get_system_info():
    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'memory': f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
        'cpu_cores': psutil.cpu_count(logical=False),
        'cpu_threads': psutil.cpu_count(logical=True)
    }

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
            'delete_time': metrics['delete_times_avg'],
            'write_std': metrics['write_times_std'],
            'read_std': metrics['sequential_read_times_std'],
            'random_read_std': metrics['random_read_times_std'],
            'batch_write_std': metrics['batch_write_times_std'],
            'delete_std': metrics['delete_times_std']
        }
        rows.append(row)
    return pd.DataFrame(rows)

def plot_operation_times(df, operation, title):
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")
    
    for value_size in df['value_size'].unique():
        data = df[df['value_size'] == value_size]
        std_col = f"{operation.split('_')[0]}_std"
        if std_col in data.columns:
            plt.errorbar(data['data_size'], data[operation] * 1e6, 
                        yerr=data[std_col] * 1e6,
                        marker='o', label=f'Value Size: {value_size} bytes',
                        capsize=5)
        else:
            plt.plot(data['data_size'], data[operation] * 1e6, 
                    marker='o', label=f'Value Size: {value_size} bytes')
    
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Data Size (number of entries)')
    plt.ylabel('Time (microseconds)')
    plt.title(title)
    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend()
    return plt.gcf()

def plot_operation_comparison(df):
    plt.figure(figsize=(15, 8))
    sns.set_style("whitegrid")
    
    # Prepare data for comparison
    operations = ['write_time', 'read_time', 'random_read_time', 'batch_write_time', 'delete_time']
    data = []
    for op in operations:
        for _, row in df.iterrows():
            data.append({
                'Operation': op.replace('_', ' ').title(),
                'Time (μs)': row[op] * 1e6,
                'Value Size': f"{row['value_size']}B",
                'Data Size': row['data_size']
            })
    
    comparison_df = pd.DataFrame(data)
    
    # Create box plot
    sns.boxplot(x='Operation', y='Time (μs)', data=comparison_df)
    plt.title('Operation Performance Comparison')
    plt.xticks(rotation=45)
    plt.tight_layout()
    return plt.gcf()

def plot_value_size_impact(df):
    plt.figure(figsize=(15, 8))
    sns.set_style("whitegrid")
    
    operations = ['write_time', 'read_time', 'random_read_time', 'batch_write_time', 'delete_time']
    data = []
    for op in operations:
        for _, row in df.iterrows():
            data.append({
                'Operation': op.replace('_', ' ').title(),
                'Time (μs)': row[op] * 1e6,
                'Value Size': f"{row['value_size']}B"
            })
    
    impact_df = pd.DataFrame(data)
    
    # Create violin plot
    sns.violinplot(x='Operation', y='Time (μs)', hue='Value Size', data=impact_df)
    plt.title('Impact of Value Size on Operation Performance')
    plt.xticks(rotation=45)
    plt.tight_layout()
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
    
    # Add comparison plots
    plots['operation_comparison'] = plot_operation_comparison(df)
    plots['value_size_impact'] = plot_value_size_impact(df)
    
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

def generate_benchmark_report(system_info, df):
    report = "# Benchmark Report\n\n"
    report += "## System Configuration\n\n"
    report += "| Parameter | Value |\n"
    report += "|-----------|-------|\n"
    for key, value in system_info.items():
        report += f"| {key.replace('_', ' ').title()} | {value} |\n"
    
    report += "\n## Benchmark Results\n\n"
    report += "Times are in microseconds (μs)\n\n"
    report += generate_markdown_table(df)
    
    return report

def main():
    # Get system information
    system_info = get_system_info()
    
    # Load results
    results = load_results()
    
    # Create DataFrame
    df = create_dataframe(results)
    
    # Generate plots
    plots = generate_plots(df)
    
    # Save plots
    Path('benchmarks/plots').mkdir(parents=True, exist_ok=True)
    for name, fig in plots.items():
        fig.savefig(f'benchmarks/plots/{name}.png', dpi=300, bbox_inches='tight')
        plt.close(fig)
    
    # Generate and save report
    report = generate_benchmark_report(system_info, df)
    with open('benchmarks/results/benchmark_report.md', 'w') as f:
        f.write(report)

if __name__ == "__main__":
    main() 