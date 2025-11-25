import sys
from pathlib import Path
import pandas as pd
import pytest
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from data_loader import DataLoader
from sqlite_storage import SQLiteStorage


@pytest.fixture(autouse=True)
def _set_workdir(monkeypatch):
    """Run tests from Assignment10 root so relative paths resolve."""
    monkeypatch.chdir(PROJECT_ROOT)

@pytest.fixture()
def test_db(tmp_path):
    """Temporary SQLite database for testing."""
    db_path = tmp_path / "test_market_data.db"
    SQLiteStorage.create_database(db_path=str(db_path))
    return str(db_path)

@pytest.fixture()
def populated_db(test_db):
    """Create and populate test database with sample data."""
    df = DataLoader.load_from_csv()
    SQLiteStorage.insert_data(df=df, db_path=test_db)
    return test_db

def test_create_database_creates_tables(test_db):
    """Verify schema creation creates required tables."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Check tickers table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tickers'")
    assert cursor.fetchone() is not None
    
    # Check prices table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
    assert cursor.fetchone() is not None
    
    conn.close()


def test_create_database_creates_foreign_key(test_db):
    """Verify foreign key constraint exists between prices and tickers."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_key_list(prices)")
    fks = cursor.fetchall()
    
    assert len(fks) > 0
    assert fks[0][2] == "tickers"  # References tickers table
    assert fks[0][3] == "ticker_id"  # On ticker_id column
    
    conn.close()


def test_insert_data_populates_tickers(populated_db):
    """Verify all unique tickers are inserted into tickers table."""
    conn = sqlite3.connect(populated_db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tickers")
    count = cursor.fetchone()[0]
    
    # Should have 5 tickers: AAPL, MSFT, GOOG, TSLA, AMZN
    assert count == 5
    
    cursor.execute("SELECT symbol FROM tickers ORDER BY symbol")
    symbols = [row[0] for row in cursor.fetchall()]
    assert symbols == ["AAPL", "AMZN", "GOOG", "MSFT", "TSLA"]
    
    conn.close()


def test_insert_data_populates_prices(populated_db):
    """Verify price data is inserted correctly."""
    conn = sqlite3.connect(populated_db)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM prices")
    count = cursor.fetchone()[0]
    
    # Should match the loaded CSV data
    assert count > 0
    
    # Verify required columns exist and have data
    cursor.execute("SELECT open, high, low, close, volume FROM prices LIMIT 1")
    row = cursor.fetchone()
    assert all(v is not None for v in row)
    
    conn.close()


def test_query_tsla_date_range_returns_data(populated_db):
    """Verify TSLA date range query returns correct data."""
    df = SQLiteStorage.query_tsla_date_range(
        "2025-11-17", 
        "2025-11-18", 
        db_path=populated_db
    )
    
    # Should return rows
    assert len(df) > 0
    
    # All rows should be TSLA
    assert df["symbol"].unique().tolist() == ["TSLA"]
    
    # All timestamps should be in range
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    assert (df["timestamp"] >= "2025-11-17").all()
    assert (df["timestamp"] <= "2025-11-18").all()


def test_query_avg_daily_volume_returns_all_tickers(populated_db):
    """Verify average volume query includes all tickers."""
    df = SQLiteStorage.query_avg_daily_volume(db_path=populated_db)
    
    # Should have 5 rows (one per ticker)
    assert len(df) == 5
    
    # All expected tickers present
    tickers = set(df["symbol"])
    assert tickers == {"AAPL", "MSFT", "GOOG", "TSLA", "AMZN"}
    
    # All volumes are positive
    assert (df["avg_daily_volume"] > 0).all()


def test_query_top_3_tickers_by_return_returns_three(populated_db):
    """Verify top 3 tickers query returns exactly 3 rows."""
    df = SQLiteStorage.query_top_3_tickers_by_return(db_path=populated_db)
    
    # Should return exactly 3 rows
    assert len(df) == 3
    
    # Required columns present
    assert all(col in df.columns for col in ["symbol", "return_pct", "first_close", "last_close"])
    
    # Returns should be in descending order
    assert (df["return_pct"].iloc[0] >= df["return_pct"].iloc[1] >= df["return_pct"].iloc[2])


def test_query_first_last_price_per_day_returns_data(populated_db):
    """Verify first/last price query returns correct structure."""
    df = SQLiteStorage.query_first_last_price_per_day(db_path=populated_db)
    
    # Should return multiple rows (5 tickers × 5 days)
    assert len(df) > 0
    
    # Required columns present
    assert all(col in df.columns for col in ["symbol", "date", "first_price", "last_price"])
    
    # Sample check: for a given day/ticker, first_price should exist
    sample = df.iloc[0]
    assert sample["first_price"] is not None
    assert sample["last_price"] is not None