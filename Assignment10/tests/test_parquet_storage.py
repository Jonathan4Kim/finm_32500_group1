import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure the Assignment10 modules are importable when running pytest from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from data_loader import DataLoader
from parquet_storage import ParquetStorage


@pytest.fixture(autouse=True)
def _set_workdir(monkeypatch):
    """Run tests from Assignment10 root so relative data paths resolve."""
    monkeypatch.chdir(PROJECT_ROOT)


@pytest.fixture()
def parquet_root(tmp_path):
    """Temporary location for parquet output to keep tests isolated."""
    return tmp_path / "parquet_out"


def write_parquet_dataset(dest):
    """Helper to materialize the dataset at a temporary location."""
    ParquetStorage.convert_to_parquet(save_root=str(dest))
    return DataLoader.load_from_csv()


def test_convert_to_parquet_overwrites_partitions(parquet_root):
    source_df = write_parquet_dataset(parquet_root)

    # Running twice should not duplicate rows because existing partitions are replaced
    ParquetStorage.convert_to_parquet(save_root=str(parquet_root))
    dataset = pd.read_parquet(parquet_root)

    assert len(dataset) == len(source_df)
    assert set(dataset["ticker"]) == set(source_df["ticker"])
    partition_dirs = {p.name for p in parquet_root.glob("ticker=*")}
    assert partition_dirs == {f"ticker={ticker}" for ticker in source_df["ticker"].unique()}


def test_load_ticker_parquet_filters_by_date_range(parquet_root):
    write_parquet_dataset(parquet_root)
    start = "2025-11-17 09:31:00"
    end = "2025-11-17 09:32:00"

    df = ParquetStorage.load_ticker_parquet("AAPL", start=start, end=end, root=str(parquet_root))

    assert not df.empty
    # Partition column is encoded in the directory name, so dataframe lacks a ticker column
    expected_cols = {"timestamp", "open", "high", "low", "close", "volume"}
    assert set(df.columns) == expected_cols
    assert df["timestamp"].min() >= pd.to_datetime(start)
    assert df["timestamp"].max() <= pd.to_datetime(end)


def test_compute_rolling_volatility_uses_partitioned_data(monkeypatch, parquet_root):
    write_parquet_dataset(parquet_root)
    original_loader = ParquetStorage.load_ticker_parquet

    def _load_with_tmp_root(ticker, start=None, end=None, root=None):
        return original_loader(ticker, start=start, end=end, root=str(parquet_root))

    # Point compute_rolling_volatility at the temporary parquet dataset
    monkeypatch.setattr(ParquetStorage, "load_ticker_parquet", staticmethod(_load_with_tmp_root))

    result = ParquetStorage.compute_rolling_volatility("AAPL")

    assert "vol_5" in result.columns
    assert result["timestamp"].is_monotonic_increasing
    # At least one non-NaN rolling volatility value after enough rows
    assert result["vol_5"].notna().any()


def test_compute_rolling_close_avg(monkeypatch, parquet_root):
    write_parquet_dataset(parquet_root)
    original_loader = ParquetStorage.load_ticker_parquet

    def _load_with_tmp_root(ticker, start=None, end=None, root=None):
        return original_loader(ticker, start=start, end=end, root=str(parquet_root))

    monkeypatch.setattr(ParquetStorage, "load_ticker_parquet", staticmethod(_load_with_tmp_root))

    result = ParquetStorage.compute_rolling_close_avg("AAPL")

    assert {"timestamp", "close", "close_5min_avg"} <= set(result.columns)
    assert result["timestamp"].is_monotonic_increasing
    assert result["close_5min_avg"].notna().any()
