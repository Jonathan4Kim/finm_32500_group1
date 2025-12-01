import asyncio
import csv
from dataclasses import dataclass
from datetime import datetime
from queue import Queue
from threading import Thread
from typing import Generator

from alpaca.data.live import StockDataStream, CryptoDataStream
from alpaca.data.enums import DataFeed

from strategy import MarketDataPoint


class LiveMarketDataSource:
    """
    Streams live market data bars from Alpaca using WebSockets.
    - Writes each FULL bar to a CSV file
    - Yields simplified MarketDataPoint objects (timestamp, symbol, price)
      for feeding into your trading engine.
    """

    def __init__(self, api_key: str, api_secret: str,
                 symbol: str = "AAPL",
                 csv_path: str = "streamed_data.csv"):

        self.api_key = api_key
        self.api_secret = api_secret
        self.symbol = symbol
        self.csv_path = csv_path

        # Thread-safe queue for MDPs
        self.queue: Queue[MarketDataPoint] = Queue()

    # -------- Conversion Helpers -------- #

    @staticmethod
    def bar_to_mdp(bar) -> MarketDataPoint:
        """Convert Alpaca streaming bar to MarketDataPoint."""
        return MarketDataPoint(
            timestamp=bar.timestamp,
            symbol=bar.symbol,
            price=bar.close
        )

    @staticmethod
    def bar_to_csv_row(bar):
        """Convert Alpaca bar to a CSV row with full OHLCV data."""
        return [
            bar.timestamp.isoformat(),
            bar.symbol,
            bar.open,
            bar.high,
            bar.low,
            bar.close,
            bar.volume,
            bar.trade_count,
            bar.vwap,
        ]

    # -------- Internal Streaming Logic -------- #

    async def _on_bar(self, bar):
        """Internal async callback triggered by Alpaca on each bar."""
        # 1. Convert to MarketDataPoint
        mdp = self.bar_to_mdp(bar)

        # 2. Push MarketDataPoint into queue for synchronous consumption
        self.queue.put(mdp)

        # 3. Append full bar to CSV
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.bar_to_csv_row(bar))

    async def _run_stream(self):
        """Run the Alpaca websocket streaming forever."""
        # stream = StockDataStream(
        #     self.api_key,
        #     self.api_secret,
        #     feed=DataFeed.IEX  # REQUIRED for paper accounts
        # )
        stream = CryptoDataStream(
            self.api_key,
            self.api_secret
        )

        stream.subscribe_bars(self._on_bar, self.symbol)

        await stream._run_forever()  # safe for any environment

    def _start_async_loop(self):
        """Start asyncio event loop in background thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_stream())

    # -------- Public API: Generator -------- #

    def stream(self) -> Generator[MarketDataPoint, None, None]:
        """
        Yields MarketDataPoint objects in real time.
        This can be consumed by your trading engine.
        """

        # Launch WebSocket in background thread
        t = Thread(target=self._start_async_loop, daemon=True)
        t.start()

        # Yield MDPs as they arrive
        while True:
            mdp = self.queue.get()    # blocking call
            if mdp:
                print(mdp)
            else:
                print("None type")
            yield mdp