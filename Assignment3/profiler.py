from Assignment3.data_loader import load_data
import matplotlib.pyplot as plt
from Assignment3.strategies import Strategy, NaiveMovingAverageStrategy, WindowedMovingAverageStrategy
import time
import tracemalloc
import os


def get_runtime_and_memory(strategy: Strategy, ticks: list[int]):
    runtime, memory = [], []
    data = load_data()
    for tick in ticks:
        curr_data = data[:tick]
        tracemalloc.start()
        start = time.time()
        for data_point in curr_data: 
            strategy.generate_signals(data_point)
        end = time.time()
        _, peak = tracemalloc.get_traced_memory()
        memory.append(peak)
        runtime.append(end - start)

    return runtime, memory


def plot_strategy_performance(ticks: list[int], values, name, is_runtime=True):
    # Convert memory from bytes to MB for readability
    if not is_runtime:
        values = [v / 1_000_000 for v in values]
    
    print(f"{name} - {'Runtime' if is_runtime else 'Memory'}: {values}")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Bar plot with evenly spaced bars
    x_positions = range(len(ticks))  # Use indices: 0, 1, 2, ...
    bars = ax.bar(x_positions, values, color="skyblue", width=0.6)
    
    # Add value labels on top of bars
    ax.bar_label(bars, fmt='%.4f' if is_runtime else '%.2f', padding=3)
    
    ax.set_xlabel("# of Market Data Points", fontsize=12)
    ax.set_xticks(x_positions)  # Set ticks at the bar positions
    ax.set_xticklabels([f"{t:,}" for t in ticks])  # Label with actual tick values
    
    if is_runtime:
        ax.set_title(f"{name}'s Runtime Performance", fontsize=14)
        ax.set_ylabel("Runtime (seconds)", fontsize=12)
    else:
        ax.set_title(f"{name}'s Memory Performance", fontsize=14)
        ax.set_ylabel("Memory (MB)", fontsize=12)
    
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    # Save plot
    if not os.path.exists("plots"):
        os.mkdir("plots")
    
    filename = f"plots/{name.replace(' ', '_')}_{'runtime' if is_runtime else 'memory'}_plot.png"
    fig.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    
    plt.show()
    plt.close()


def main():
    ticks = [1_000, 10_000, 100_000]
    naive = NaiveMovingAverageStrategy(2, 5)
    window = WindowedMovingAverageStrategy(2, 5)
    strategies = [(naive, "Naive MAC"), (window, "Windowed MAC")]
    for strategy, name in strategies:
        runtime, memory = get_runtime_and_memory(strategy, ticks)
        print(name)
        print(runtime)
        print(memory)
        plot_strategy_performance(ticks, runtime, name, is_runtime=True)
        plot_strategy_performance(ticks, memory, name, is_runtime=False)


if __name__ == "__main__":
    main()