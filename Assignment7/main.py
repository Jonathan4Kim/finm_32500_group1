import os
import matplotlib.pyplot as plt
import json

from data_loader import load_data_pandas
from portfolio import compare_modes
from metrics import benchmark_functions
from reporting import ingestion_time_comp, rolling_metrics_comp, parallel_computing_comp

def main():

    results = benchmark_functions()

    df = load_data_pandas()
    pf_path = os.path.join(os.path.dirname(__file__), "portfolio_structure-1.json")
    if not os.path.exists(pf_path):
        raise SystemExit(f"Missing portfolio file: {pf_path}")

    with open(pf_path) as f:
        portfolio = json.load(f)

    workers = min(4, max(1, (df["symbol"].nunique() if "symbol" in df.columns else 1)))
    comp = compare_modes(portfolio, df, workers=workers)

    print(f"\nSequential: {comp['sequential_time']:.4f}s | Parallel: {comp['parallel_time']:.4f}s | Speedup: {comp['speedup']:.2f}x\n")
    res = comp["result"]
    print(f"{res['name']}: Value=${res['total_value']:,.2f}, Vol={res['aggregate_volatility']:.4f}, MaxDD={res['max_drawdown']:.2%}\n")

    for p in res["positions"]:
        print(f"  {p['symbol']} x{p['quantity']}: ${p['value']:,.2f}, vol={p['volatility']:.4f}, dd={p['drawdown']:.2%}")

    for s in res["sub_portfolios"]:
        print(f"  Sub '{s['name']}': ${s['total_value']:,.2f}, vol={s['aggregate_volatility']:.4f}, dd={s['max_drawdown']:.2%}")

    with open("portfolio_results.json", "w") as f:
        json.dump(res, f, indent=2)

    print("\nSaved portfolio_results.json")

    ingestion_times = ingestion_time_comp()
    print(f"\n*** Ingestion Time Comparison ***")
    print(ingestion_times.to_string(index=False))

    df, fig, NUMBER = rolling_metrics_comp()

    print(f"\n*** Benchmark Computation Time (trails={NUMBER})***")
    print(df.to_string(index=False))
    plt.show()

    print(f"\n*** Threading and Multiprocessing ***")
    parallel_computing_comp()

if __name__ == "__main__":
    main()