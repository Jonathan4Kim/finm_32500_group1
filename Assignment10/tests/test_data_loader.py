import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from data_loader import DataLoader


def test_load_from_csv_drops_rows_with_missing_required_fields(tmp_path):
    market_path = tmp_path / "market.csv"
    tickers_path = tmp_path / "tickers.csv"

    # One complete row and one with missing close price that should be dropped
    market_df = pd.DataFrame(
        [
            {"timestamp": "2025-11-17 09:30:00", "ticker": "AAPL", "open": 1, "high": 2, "low": 1, "close": 1.5, "volume": 10},
            {"timestamp": "2025-11-17 09:31:00", "ticker": "AAPL", "open": 1, "high": 2, "low": 1, "close": None, "volume": 10},
        ]
    )
    market_df.to_csv(market_path, index=False)
    pd.DataFrame({"symbol": ["AAPL"]}).to_csv(tickers_path, index=False)

    result = DataLoader.load_from_csv(market_data_path=str(market_path), tickers_path=str(tickers_path))

    assert len(result) == 1
    assert result["close"].isna().sum() == 0
    assert result["timestamp"].isna().sum() == 0


def test_load_from_csv_raises_when_ticker_missing(tmp_path):
    market_path = tmp_path / "market.csv"
    tickers_path = tmp_path / "tickers.csv"

    pd.DataFrame(
        [{"timestamp": "2025-11-17 09:30:00", "ticker": "AAPL", "open": 1, "high": 2, "low": 1, "close": 1.5, "volume": 10}]
    ).to_csv(market_path, index=False)
    pd.DataFrame({"symbol": ["AAPL", "MSFT"]}).to_csv(tickers_path, index=False)

    with pytest.raises(ValueError, match="Ticker \"MSFT\" is not available"):
        DataLoader.load_from_csv(market_data_path=str(market_path), tickers_path=str(tickers_path))
