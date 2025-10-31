import pytest
import pandas as pd
import polars as pl
import numpy as np

from Assignment7.metrics import (
    add_rolling_mean_pandas, add_rolling_mean_polars,
    add_rolling_std_pandas, add_rolling_std_polars,
    add_rolling_sharpe_pandas, add_rolling_sharpe_polars
)
from Assignment7.data_loader import load_data_pandas, load_data_polars

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
