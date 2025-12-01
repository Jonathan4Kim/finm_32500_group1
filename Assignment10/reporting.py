import os
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Callable, Dict, Tuple

import pandas as pd

from data_loader import DataLoader
from sqlite_storage import SQLiteStorage
from parquet_storage import ParquetStorage


AssignmentRoot = Path(__file__).resolve().parent
ReportsDir = AssignmentRoot / "reports"


def _ensure_workdir() -> Path:
    """
    The storage modules expect to run with Assignment10 as the working directory
    because they rely on relative paths (for example ``data/schema.sql``).
    """
    os.chdir(AssignmentRoot)
    return AssignmentRoot


def _timed_call(func: Callable, *args, **kwargs) -> Tuple[object, float]:
    start = perf_counter()
    result = func(*args, **kwargs)
    return result, perf_counter() - start


def _format_df(df: pd.DataFrame, max_rows: int = 5) -> str:
    if df.empty:
        return "(no rows returned)"
    if len(df) <= max_rows:
        return df.to_string(index=False)
    head = df.head(max_rows).to_string(index=False)
    return f"{head}\n... (showing first {max_rows} of {len(df)} rows)"


def _dir_size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if not path.exists():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def _human_bytes(num: int) -> str:
    step = 1024.0
    for unit in ["B", "KB", "MB", "GB"]:
        if num < step:
            return f"{num:.2f} {unit}"
        num /= step
    return f"{num:.2f} TB"


def _parquet_avg_daily_volume(root: str) -> pd.DataFrame:
    df = pd.read_parquet(root)
    grouped = (
        df.groupby("ticker")["volume"]
        .mean()
        .reset_index(name="avg_daily_volume")
        .sort_values("ticker")
    )
    return grouped


def _parquet_vol_summary(tickers) -> pd.DataFrame:
    rows = []
    for ticker in tickers:
        vol_df = ParquetStorage.compute_rolling_volatility(ticker)
        latest = vol_df["vol_5"].dropna().iloc[-1] if vol_df["vol_5"].notna().any() else float("nan")
        rows.append({"ticker": ticker, "latest_vol_5": latest})
    return pd.DataFrame(rows)


def build_report() -> Dict[str, pd.DataFrame]:
    """
    Run the ingestion + storage pipeline and capture result dataframes for downstream use.
    """
    _ensure_workdir()
    root = AssignmentRoot
    db_path = root / "market_data.db"
    schema_path = root / "data" / "schema.sql"
    parquet_root = root / "market_data"

    market_df = DataLoader.load_from_csv(
        market_data_path=str(root / "data" / "market_data_multi.csv"),
        tickers_path=str(root / "data" / "tickers.csv"),
    )
    tickers = market_df["ticker"].sort_values().unique().tolist()

    SQLiteStorage.create_database(db_path=str(db_path), schema_path=str(schema_path))
    SQLiteStorage.insert_data(df=market_df, db_path=str(db_path))

    tsla_start = "2025-11-17 00:00:00"
    tsla_end = "2025-11-18 23:59:59"

    sqlite_tsla_df, sqlite_tsla_time = _timed_call(
        SQLiteStorage.query_tsla_date_range,
        tsla_start,
        tsla_end,
        db_path=str(db_path),
    )
    sqlite_avg_vol_df, sqlite_avg_time = _timed_call(
        SQLiteStorage.query_avg_daily_volume, db_path=str(db_path)
    )
    sqlite_top_returns_df = SQLiteStorage.query_top_3_tickers_by_return(db_path=str(db_path))
    sqlite_first_last_df = SQLiteStorage.query_first_last_price_per_day(db_path=str(db_path))

    ParquetStorage.convert_to_parquet(save_root=str(parquet_root))

    parquet_tsla_df, parquet_tsla_time = _timed_call(
        ParquetStorage.load_ticker_parquet,
        "TSLA",
        tsla_start,
        tsla_end,
        root=str(parquet_root),
    )
    parquet_avg_vol_df, parquet_avg_time = _timed_call(
        _parquet_avg_daily_volume,
        str(parquet_root),
    )
    parquet_volatility_df = _parquet_vol_summary(tickers)

    comparison_df = pd.DataFrame(
        [
            {
                "format": "SQLite",
                "artifact": db_path.name,
                "size": _human_bytes(_dir_size_bytes(db_path)),
                "TSLA range query": f"{sqlite_tsla_time * 1000:.2f} ms",
                "Avg volume query": f"{sqlite_avg_time * 1000:.2f} ms",
            },
            {
                "format": "Parquet",
                "artifact": "market_data/",
                "size": _human_bytes(_dir_size_bytes(parquet_root)),
                "TSLA range query": f"{parquet_tsla_time * 1000:.2f} ms",
                "Avg volume query": f"{parquet_avg_time * 1000:.2f} ms",
            },
        ]
    )

    return {
        "market": market_df,
        "sqlite_tsla": sqlite_tsla_df,
        "sqlite_avg_vol": sqlite_avg_vol_df,
        "sqlite_top_returns": sqlite_top_returns_df,
        "sqlite_first_last": sqlite_first_last_df,
        "parquet_tsla": parquet_tsla_df,
        "parquet_avg_vol": parquet_avg_vol_df,
        "parquet_volatility": parquet_volatility_df,
        "comparison": comparison_df,
    }


def main() -> None:
    report = build_report()
    market_df = report["market"]
    ReportsDir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_sections = []

    text_sections.append(
        "=== Data Validation ===\n"
        f"Rows loaded: {len(market_df)}\n"
        f"Date range: {market_df['timestamp'].min()} to {market_df['timestamp'].max()}\n"
        f"Tickers: {', '.join(sorted(market_df['ticker'].unique()))}"
    )

    text_sections.append(
        "=== SQLite Queries ===\n"
        "TSLA 2025-11-17 to 2025-11-18\n"
        f"{_format_df(report['sqlite_tsla'])}\n\n"
        "Average daily volume per ticker\n"
        f"{_format_df(report['sqlite_avg_vol'])}\n\n"
        "Top 3 tickers by return\n"
        f"{_format_df(report['sqlite_top_returns'])}\n\n"
        "First/last trade price per day\n"
        f"{_format_df(report['sqlite_first_last'])}"
    )

    text_sections.append(
        "=== Parquet Analytics ===\n"
        "TSLA partition data\n"
        f"{_format_df(report['parquet_tsla'])}\n\n"
        "Average daily volume from Parquet\n"
        f"{_format_df(report['parquet_avg_vol'])}\n\n"
        "Latest 5-day rolling volatility\n"
        f"{_format_df(report['parquet_volatility'])}"
    )

    text_sections.append(
        "=== Storage Comparison ===\n"
        f"{report['comparison'].to_string(index=False)}"
    )

    summary_path = ReportsDir / f"summary_{timestamp}.txt"
    summary_path.write_text("\n\n".join(text_sections))

    csv_exports = {
        "sqlite_tsla": report["sqlite_tsla"],
        "sqlite_avg_volume": report["sqlite_avg_vol"],
        "sqlite_top_returns": report["sqlite_top_returns"],
        "sqlite_first_last": report["sqlite_first_last"],
        "parquet_tsla": report["parquet_tsla"],
        "parquet_avg_volume": report["parquet_avg_vol"],
        "parquet_volatility": report["parquet_volatility"],
        "comparison": report["comparison"],
    }

    for name, df in csv_exports.items():
        csv_path = ReportsDir / f"{name}_{timestamp}.csv"
        df.to_csv(csv_path, index=False)

    print(f"Report summary saved to {summary_path}")
    print(f"Detailed CSV outputs available in {ReportsDir}")


if __name__ == "__main__":
    main()
