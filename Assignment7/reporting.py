import pandas as pd
import matplotlib.pyplot as plt

import timeit

import psutil
from memory_profiler import memory_usage

from data_loader import load_data_pandas, load_data_polars, load_data_pandas_memory_test, load_data_polars_memory_test
from metrics import benchmark_functions, plot_benchmark
from parallel import compare_parallel_approaches, analyze_gil_impact

def ingestion_time_comp():

    pandas_time = timeit.timeit(load_data_pandas, number=1)
    polars_time = timeit.timeit(load_data_polars, number=1)

    pandas_mem = memory_usage(load_data_pandas_memory_test)
    polars_mem = memory_usage(load_data_polars_memory_test)

    ingestion_times = pd.DataFrame({
        'Package': ['Pandas', 'Polars'],
        'Ingestion Time': [pandas_time, polars_time],
        'Relative Speed': ['1', f'{pandas_time/polars_time:.2f}x'],
        'Peak Memory (MB)': [f'{max(pandas_mem):.2f} MB',f'{max(polars_mem):.2f} MB']
    })

    return ingestion_times

def rolling_metrics_comp(NUMBER=20):
    results = benchmark_functions()

    df = pd.DataFrame({
        'Package': ['Pandas', 'Polars'],
        'Rolling Mean': [results['Rolling Mean']['Pandas'], results['Rolling Mean']['Polars']],
        'Rolling Std': [results['Rolling Std']['Pandas'], results['Rolling Std']['Polars']],
        'Rolling Sharpe': [results['Rolling Sharpe']['Pandas'], results['Rolling Sharpe']['Polars']]
    })
    
    fig = plot_benchmark(results)

    return df, fig, NUMBER

def parallel_computing_comp():
    
    df = load_data_pandas()

    # Performance comparison
    workers = min(4, max(1, psutil.cpu_count(logical=False) or 1))
    print(f"\n1. Performance Comparison (using {workers} workers):\n")
    summary = compare_parallel_approaches(df, max_workers=workers)
    print(summary.to_string(index=False))

    # GIL impact
    print(f"\n2. GIL Impact Analysis:\n")
    worker_list = [1, 2, 4, min(8, max(1, psutil.cpu_count(logical=False) or 1))]
    gil_df = analyze_gil_impact(df, worker_counts=worker_list)
    print(gil_df.to_string(index=False))

    # Chart 1: Execution Time Comparison
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    colors = ['#1f77b4', '#2ca02c', '#d62728']
    bars1 = ax1.bar(summary['Approach'], summary['Execution Time (s)'], color=colors)
    ax1.set_ylabel('Time (seconds)', fontsize=12)
    ax1.set_title('Execution Time by Approach (4 workers)', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', linestyle='--', alpha=0.6)
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.4f}s', ha='center', va='bottom', fontsize=11)
    plt.tight_layout()
    plt.savefig('1_execution_time.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Chart 2: Speedup Comparison
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    bars2 = ax2.bar(summary['Approach'], summary['Speedup vs Sequential'], color=colors)
    ax2.set_ylabel('Speedup Factor', fontsize=12)
    ax2.set_title('Speedup vs Sequential', fontsize=14, fontweight='bold')
    ax2.axhline(y=1, color='gray', linestyle='--', alpha=0.5)
    ax2.grid(axis='y', linestyle='--', alpha=0.6)
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}x', ha='center', va='bottom', fontsize=11)
    plt.tight_layout()
    plt.savefig('2_speedup.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Chart 3: Memory Usage
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    bars3 = ax3.bar(summary['Approach'], summary['Memory Δ (MB)'], color=colors)
    ax3.set_ylabel('Memory Delta (MB)', fontsize=12)
    ax3.set_title('Memory Usage Difference', fontsize=14, fontweight='bold')
    ax3.grid(axis='y', linestyle='--', alpha=0.6)
    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}', ha='center', va='bottom', fontsize=11)
    plt.tight_layout()
    plt.savefig('3_memory_usage.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Chart 4: Threading vs Multiprocessing (GIL Impact)
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    x = range(len(gil_df['Workers']))
    width = 0.35
    bars_threading = ax4.bar([i - width/2 for i in x], gil_df['Threading (s)'], width, 
                            label='Threading', color='#2ca02c')
    bars_mp = ax4.bar([i + width/2 for i in x], gil_df['Multiprocessing (s)'], width,
                    label='Multiprocessing', color='#d62728')
    ax4.set_xlabel('Number of Workers', fontsize=12)
    ax4.set_ylabel('Time (seconds)', fontsize=12)
    ax4.set_title('GIL Impact Analysis', fontsize=14, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(gil_df['Workers'])
    ax4.legend(fontsize=11)
    ax4.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig('4_gil_impact.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    ingestion_times = ingestion_time_comp()
    print(f"\n*** Ingestion Time Comparison ***")
    print(ingestion_times.to_string(index=False))

    df, fig, NUMBER = rolling_metrics_comp()

    print(f"\n*** Benchmark Computation Time (trails={NUMBER})***")
    print(df.to_string(index=False))
    plt.show()

    print(f"\n*** Threading and Multiprocessing ***")
    parallel_computing_comp()