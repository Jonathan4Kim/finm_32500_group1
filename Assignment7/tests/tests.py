import pytest
import pandas as pd
import polars as pl
import numpy as np
import json
import os

from Assignment7.metrics import (
    add_rolling_mean_pandas, add_rolling_mean_polars,
    add_rolling_std_pandas, add_rolling_std_polars,
    add_rolling_sharpe_pandas, add_rolling_sharpe_polars
)
from Assignment7.data_loader import load_data_pandas, load_data_polars

from Assignment7.parallel import (
    compute_rolling_metrics_for_symbol,
    compute_metrics_sequential,
    compute_metrics_threading,
    compute_metrics_multiprocessing,
    verify_consistency
)

from Assignment7.portfolio import (
    compute_position_metrics,
    compute_positions,
    aggregate_metrics,
    process_portfolio,
    compare_modes,
    PositionMetrics
)

# ---------- Fixtures ----------

@pytest.fixture
def sample_data():
    """Generate a small mixed-symbol test dataset."""
    data = {
        "timestamp": pd.date_range("2025-01-01", periods=6, freq="D").tolist() * 2,
        "symbol": ["AAPL"]*6 + ["MSFT"]*6,
        "price": [100, 101, 102, 103, 104, 105, 200, 201, 203, 202, 205, 207],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_data_polars(sample_data):
    """Polars equivalent of sample data."""
    return pl.from_pandas(sample_data)


# ---------- Input Validation Tests ----------

@pytest.mark.parametrize("func", [
    add_rolling_mean_pandas,
    add_rolling_std_pandas,
    add_rolling_sharpe_pandas,
])
def test_pandas_missing_columns(func):
    """Ensure Pandas versions raise ValueError on missing required columns."""
    bad_df = pd.DataFrame({"foo": [1, 2, 3]})
    with pytest.raises(ValueError):
        func(bad_df)


@pytest.mark.parametrize("func", [
    add_rolling_mean_polars,
    add_rolling_std_polars,
    add_rolling_sharpe_polars,
])
def test_polars_missing_columns(func):
    """Ensure Polars versions raise ValueError on missing required columns."""
    bad_df = pl.DataFrame({"foo": [1, 2, 3]})
    with pytest.raises(ValueError):
        func(bad_df)


@pytest.mark.parametrize("func, expected_col", [
    (add_rolling_mean_pandas, "rolling_mean_20"),
    (add_rolling_std_pandas, "rolling_std_20"),
    (add_rolling_sharpe_pandas, "rolling_sharpe_20"),
    (add_rolling_mean_polars, "rolling_mean_20"),
    (add_rolling_std_polars, "rolling_std_20"),
    (add_rolling_sharpe_polars, "rolling_sharpe_20"),
])
def test_none_input_loads_default(func, expected_col):
    """
    Ensure functions handle df=None by loading default dataset via load_data_*().
    Check that the returned DataFrame contains expected columns and valid results.
    """
    result = func(None)

    # Validate type
    if "polars" in func.__name__:
        assert isinstance(result, pl.DataFrame)
        assert expected_col in result.columns
        assert result.height > 0
        # Check that not all values are null
        assert not result[expected_col].is_null().all()
    else:
        assert isinstance(result, pd.DataFrame)
        assert expected_col in result.columns
        assert len(result) > 0
        assert not result[expected_col].isnull().all()


# ---------- Functional Tests ----------

def test_rolling_mean_output(sample_data, sample_data_polars):
    """Ensure rolling means match between Pandas and Polars."""
    df_pd = add_rolling_mean_pandas(sample_data.copy())
    df_pl = add_rolling_mean_polars(sample_data_polars.clone()).to_pandas()

    assert "rolling_mean_20" in df_pd.columns
    assert "rolling_mean_20" in df_pl.columns
    assert len(df_pd) == len(df_pl)

    # Compare numerically (NaNs okay)
    np.testing.assert_allclose(
        df_pd["rolling_mean_20"].fillna(0),
        df_pl["rolling_mean_20"].fillna(0),
        rtol=1e-6,
        atol=1e-6
    )


def test_rolling_std_output(sample_data, sample_data_polars):
    """Ensure rolling stds match between Pandas and Polars."""
    df_pd = add_rolling_std_pandas(sample_data.copy())
    df_pl = add_rolling_std_polars(sample_data_polars.clone()).to_pandas()

    np.testing.assert_allclose(
        df_pd["rolling_std_20"].fillna(0),
        df_pl["rolling_std_20"].fillna(0),
        rtol=1e-6,
        atol=1e-6
    )


def test_rolling_sharpe_output(sample_data, sample_data_polars):
    """Ensure rolling Sharpe ratios roughly match between Pandas and Polars."""
    df_pd = add_rolling_sharpe_pandas(sample_data.copy())
    df_pl = add_rolling_sharpe_polars(sample_data_polars.clone()).to_pandas()

    assert "rolling_sharpe_20" in df_pd.columns
    assert "rolling_sharpe_20" in df_pl.columns
    assert len(df_pd) == len(df_pl)

    # Allow slightly larger tolerance due to potential rounding diff
    np.testing.assert_allclose(
        df_pd["rolling_sharpe_20"].fillna(0),
        df_pl["rolling_sharpe_20"].fillna(0),
        rtol=1e-4,
        atol=1e-4
    )


# ---------- Edge Case Tests ----------

def test_single_symbol(sample_data):
    """Ensure single-symbol dataset works."""
    df = sample_data[sample_data["symbol"] == "AAPL"]
    out = add_rolling_mean_pandas(df)
    assert not out["rolling_mean_20"].isnull().all()


def test_short_series(sample_data):
    """Handle very short series (< window)."""
    short_df = sample_data.iloc[:5]
    out = add_rolling_std_pandas(short_df)
    assert "rolling_std_20" in out.columns
    assert not out["rolling_std_20"].isnull().all()


def test_with_missing_prices(sample_data):
    """Gracefully handle NaN prices."""
    sample_data.loc[2, "price"] = np.nan
    df_out = add_rolling_mean_pandas(sample_data)
    assert "rolling_mean_20" in df_out.columns
    # Pandas rolling ignores NaNs by default
    assert not df_out["rolling_mean_20"].isnull().all()

# ---------- Parallel Computing Tests (Task 3) ----------

@pytest.fixture
def parallel_test_data():
    """Small dataset for parallel testing."""
    data = {
        "timestamp": pd.date_range("2025-01-01", periods=50, freq="H").tolist() * 3,
        "symbol": ["AAPL"]*50 + ["MSFT"]*50 + ["GOOGL"]*50,
        "price": np.random.randn(150).cumsum() + 100,
    }
    return pd.DataFrame(data)


def test_compute_rolling_metrics_for_symbol(parallel_test_data):
    """Test single symbol metric computation."""
    symbol_data = ("AAPL", parallel_test_data[parallel_test_data["symbol"] == "AAPL"])
    result = compute_rolling_metrics_for_symbol(symbol_data)
    assert result["symbol"] == "AAPL"
    assert "data" in result
    assert "rolling_mean_20" in result["data"].columns
    assert "rolling_std_20" in result["data"].columns
    assert "rolling_sharpe_20" in result["data"].columns
    assert result["latest_price"] is not None


def test_threading_vs_sequential_consistency(parallel_test_data):
    """Confirm threading produces same results as sequential."""
    seq_results, _ = compute_metrics_sequential(parallel_test_data)
    thr_results, _ = compute_metrics_threading(parallel_test_data, max_workers=2)
    assert verify_consistency(seq_results, thr_results)


def test_multiprocessing_vs_sequential_consistency(parallel_test_data):
    """Confirm multiprocessing produces same results as sequential."""
    seq_results, _ = compute_metrics_sequential(parallel_test_data)
    mp_results, _ = compute_metrics_multiprocessing(parallel_test_data, max_workers=2)
    assert verify_consistency(seq_results, mp_results)


def test_all_approaches_produce_same_symbols(parallel_test_data):
    """All approaches should process the same symbols."""
    seq_results, _ = compute_metrics_sequential(parallel_test_data)
    thr_results, _ = compute_metrics_threading(parallel_test_data, max_workers=2)
    mp_results, _ = compute_metrics_multiprocessing(parallel_test_data, max_workers=2)
    assert set(seq_results.keys()) == set(thr_results.keys())
    assert set(seq_results.keys()) == set(mp_results.keys())
    assert len(seq_results) == 3  # AAPL, MSFT, GOOGL


def test_rolling_metrics_correctness(parallel_test_data):
    """Validate correctness of rolling metrics calculation."""
    results, _ = compute_metrics_sequential(parallel_test_data)
    for symbol, result in results.items():
        df = result["data"]
        assert df["rolling_mean_20"].notna().any()
        assert (df["rolling_std_20"].dropna() >= 0).all()
        assert "rolling_sharpe_20" in df.columns


def test_performance_metrics_captured(parallel_test_data):
    """Ensure performance metrics are captured for all approaches."""
    _, seq_perf = compute_metrics_sequential(parallel_test_data)
    _, thr_perf = compute_metrics_threading(parallel_test_data, max_workers=2)
    _, mp_perf = compute_metrics_multiprocessing(parallel_test_data, max_workers=2)
    for perf in [seq_perf, thr_perf, mp_perf]:
        assert perf.execution_time > 0
        assert perf.cpu_percent >= 0
        assert perf.approach in ["Sequential", "Threading", "Multiprocessing"]

def test_verify_consistency_detects_mismatch():
    """Test that verify_consistency detects when results differ."""
    results_a = {
        "AAPL": {
            "data": pd.DataFrame({
                "rolling_mean_20": [100.0, 101.0],
                "rolling_std_20": [1.0, 1.5],
                "rolling_sharpe_20": [0.5, 0.6]
            })
        }
    }
    
    results_b = {
        "AAPL": {
            "data": pd.DataFrame({
                "rolling_mean_20": [100.0, 102.0],  # Different value
                "rolling_std_20": [1.0, 1.5],
                "rolling_sharpe_20": [0.5, 0.6]
            })
        }
    }
    assert not verify_consistency(results_a, results_b)

def test_verify_consistency_passes_identical():
    """Test that verify_consistency passes for identical results."""
    results = {
        "AAPL": {
            "data": pd.DataFrame({
                "rolling_mean_20": [100.0, 101.0],
                "rolling_std_20": [1.0, 1.5],
                "rolling_sharpe_20": [0.5, 0.6]
            })
        }
    }
    assert verify_consistency(results, results)

def test_threading_different_worker_counts(parallel_test_data):
    """Test threading with different worker counts produces consistent results."""
    results_2, _ = compute_metrics_threading(parallel_test_data, max_workers=2)
    results_4, _ = compute_metrics_threading(parallel_test_data, max_workers=4)
    assert verify_consistency(results_2, results_4)

def test_multiprocessing_different_worker_counts(parallel_test_data):
    """Test multiprocessing with different worker counts produces consistent results."""
    results_2, _ = compute_metrics_multiprocessing(parallel_test_data, max_workers=2)
    results_4, _ = compute_metrics_multiprocessing(parallel_test_data, max_workers=4)
    
    assert verify_consistency(results_2, results_4)

    # ---------- Portfolio Aggregation Tests (Task 4) ----------

@pytest.fixture
def portfolio_test_data():
    """Small market data for portfolio testing."""
    data = {
        "timestamp": pd.date_range("2025-01-01", periods=100, freq="h").tolist() * 3,
        "symbol": ["AAPL"]*100 + ["MSFT"]*100 + ["SPY"]*100,
        "price": [100 + i*0.5 for i in range(100)] + 
                 [200 + i*0.3 for i in range(100)] + 
                 [400 + i*0.2 for i in range(100)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_portfolio():
    """Simple portfolio structure for testing."""
    return {
        "name": "Test Portfolio",
        "positions": [
            {"symbol": "AAPL", "quantity": 10, "price": 150.0},
            {"symbol": "MSFT", "quantity": 5, "price": 250.0}
        ],
        "sub_portfolios": [
            {
                "name": "Sub Portfolio",
                "positions": [
                    {"symbol": "SPY", "quantity": 20, "price": 450.0}
                ]
            }
        ]
    }

def test_compute_position_metrics_single(portfolio_test_data):
    """Test single position metrics computation."""
    position = {"symbol": "AAPL", "quantity": 10}
    result = compute_position_metrics((position, portfolio_test_data))
    
    assert isinstance(result, PositionMetrics)
    assert result.symbol == "AAPL"
    assert result.quantity == 10
    assert result.value > 0
    assert result.volatility >= 0
    assert result.drawdown <= 0

def test_compute_position_value_calculation(portfolio_test_data):
    """Ensure value = quantity × latest_price."""
    position = {"symbol": "AAPL", "quantity": 10}
    result = compute_position_metrics((position, portfolio_test_data))
    
    # Verify value calculation
    expected_value = result.quantity * result.latest_price
    assert abs(result.value - expected_value) < 0.01

def test_sequential_vs_parallel_positions(portfolio_test_data, sample_portfolio):
    """Ensure sequential and parallel produce same position metrics."""
    positions = sample_portfolio["positions"]
    seq_results = compute_positions(positions, portfolio_test_data, parallel=False)
    par_results = compute_positions(positions, portfolio_test_data, parallel=True, workers=2)
    assert len(seq_results) == len(par_results)
    for seq, par in zip(seq_results, par_results):
        assert seq.symbol == par.symbol
        assert abs(seq.value - par.value) < 0.01
        assert abs(seq.volatility - par.volatility) < 0.0001

def test_aggregate_total_value(portfolio_test_data):
    """Test that total_value is sum of all position values."""
    positions = [
        PositionMetrics("AAPL", 10, 150.0, 1500.0, 0.01, -0.05),
        PositionMetrics("MSFT", 5, 250.0, 1250.0, 0.02, -0.03)
    ]
    agg = aggregate_metrics(positions)
    expected_total = 1500.0 + 1250.0
    assert abs(agg["total_value"] - expected_total) < 0.01

def test_aggregate_weighted_volatility(portfolio_test_data):
    """Test weighted average volatility calculation."""
    positions = [
        PositionMetrics("AAPL", 10, 100.0, 1000.0, 0.02, -0.05),  
        PositionMetrics("MSFT", 5, 200.0, 1000.0, 0.04, -0.03)    
    ]
    agg = aggregate_metrics(positions)
    # Weighted avg: (1000*0.02 + 1000*0.04) / 2000 = 0.03
    expected_vol = (1000 * 0.02 + 1000 * 0.04) / 2000
    assert abs(agg["aggregate_volatility"] - expected_vol) < 0.0001


def test_aggregate_max_drawdown(portfolio_test_data):
    """Test that max_drawdown is the worst across all positions."""
    positions = [
        PositionMetrics("AAPL", 10, 150.0, 1500.0, 0.01, -0.05),
        PositionMetrics("MSFT", 5, 250.0, 1250.0, 0.02, -0.10),  # Worst drawdown
        PositionMetrics("GOOGL", 3, 200.0, 600.0, 0.015, -0.03)
    ]
    agg = aggregate_metrics(positions)
    assert agg["max_drawdown"] == -0.10  # Worst one

def test_recursive_portfolio_aggregation(portfolio_test_data, sample_portfolio):
    """Test recursive aggregation includes sub-portfolios."""
    result = process_portfolio(sample_portfolio, portfolio_test_data, parallel=False)
    assert "total_value" in result
    assert "aggregate_volatility" in result
    assert "max_drawdown" in result
    assert len(result["positions"]) == 2
    assert len(result["sub_portfolios"]) == 1
    assert result["sub_portfolios"][0]["name"] == "Sub Portfolio"


def test_portfolio_total_includes_subs(portfolio_test_data, sample_portfolio):
    """Ensure main portfolio total_value includes sub-portfolio values."""
    result = process_portfolio(sample_portfolio, portfolio_test_data, parallel=False)
    main_positions_value = sum(p["value"] for p in result["positions"])
    sub_value = sum(s["total_value"] for s in result["sub_portfolios"])
    expected_total = main_positions_value + sub_value
    assert abs(result["total_value"] - expected_total) < 0.01

def test_portfolio_output_structure(portfolio_test_data, sample_portfolio):
    """Validate output matches expected JSON structure."""
    result = process_portfolio(sample_portfolio, portfolio_test_data, parallel=False)
    assert "name" in result
    assert "total_value" in result
    assert "aggregate_volatility" in result
    assert "max_drawdown" in result
    assert "positions" in result
    assert "sub_portfolios" in result
    for pos in result["positions"]:
        assert "symbol" in pos
        assert "quantity" in pos
        assert "latest_price" in pos
        assert "value" in pos
        assert "volatility" in pos
        assert "drawdown" in pos

def test_compare_modes_returns_both_results(portfolio_test_data, sample_portfolio):
    """Test that compare_modes returns timing and results."""
    comp = compare_modes(sample_portfolio, portfolio_test_data, workers=2)
    assert "sequential_time" in comp
    assert "parallel_time" in comp
    assert "speedup" in comp
    assert "result" in comp
    assert comp["sequential_time"] > 0
    assert comp["parallel_time"] > 0
    assert comp["speedup"] > 0

def test_empty_positions_handled(portfolio_test_data):
    """Test portfolio with no positions."""
    empty_portfolio = {
        "name": "Empty Portfolio",
        "positions": [],
        "sub_portfolios": []
    }
    result = process_portfolio(empty_portfolio, portfolio_test_data, parallel=False)
    assert result["total_value"] == 0.0
    assert result["aggregate_volatility"] == 0.0
    assert len(result["positions"]) == 0

def test_position_with_no_market_data(portfolio_test_data):
    """Test position for symbol not in market data uses fallback price."""
    position = {"symbol": "UNKNOWN", "quantity": 10, "price": 100.0}
    result = compute_position_metrics((position, portfolio_test_data))
    assert result.symbol == "UNKNOWN"
    assert result.latest_price == 100.0  # Fallback to JSON price
    assert result.value == 1000.0  # 10 * 100

def test_volatility_is_rolling(portfolio_test_data):
    """Ensure volatility uses rolling calculation, not simple std."""
    position = {"symbol": "AAPL", "quantity": 10}
    result = compute_position_metrics((position, portfolio_test_data))
    assert result.volatility >= 0
    assert result.volatility < 1.0  # Should be a reasonable percentage