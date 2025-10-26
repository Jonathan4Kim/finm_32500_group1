import sys
import os
import unittest
from collections import deque
from unittest.mock import patch, mock_open, MagicMock

# Add Assignment6 top-level folder to path
sys.path.append(os.path.abspath("."))

# Correct imports
from data_loader import load_data
from models import MarketDataPoint
from patterns.factory import Stock, Bond, ETF, InstrumentFactory
from patterns.singleton import Config
from patterns.observer import SignalPublisher, LoggerObserver, AlertObserver
from patterns.command import Portfolio, ExecuteOrderCommand, UndoOrderCommand, CommandInvoker
from patterns.strategy import BreakoutStrategy, MeanReversionStrategy


# Mock classes for testing

class MockTick:
    def __init__(self, symbol, price):
        self.symbol = symbol
        self.price = price


# Factory pattern tests

class TestInstrumentFactory(unittest.TestCase):

    def setUp(self):
        self.factory = InstrumentFactory()
        # Sample instrument dictionaries
        self.stock_data = {"symbol": "AAPL", "type": "Stock", "price": 172.35, "sector": "Tech", "issuer": "Apple"}
        self.bond_data = {"symbol": "US10Y", "type": "Bond", "price": 100.0, "sector": "Govt", "issuer": "US Treasury", "maturity": "2035-10-01"}
        self.etf_data = {"symbol": "SPY", "type": "ETF", "price": 430.50, "sector": "Index", "issuer": "State Street"}

    def test_factory_creates_correct_types(self):
        stock = self.factory.create_instrument(self.stock_data)
        bond = self.factory.create_instrument(self.bond_data)
        etf = self.factory.create_instrument(self.etf_data)

        self.assertIsInstance(stock, Stock)
        self.assertIsInstance(bond, Bond)
        self.assertIsInstance(etf, ETF)
        self.assertEqual(bond.maturity, "2035-10-01")


# Singleton Pattern Tests

class TestSingleton(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{"log_level":"INFO","data_path":"./data/","report_path":"./reports/","default_strategy":"MeanReversionStrategy"}')
    def test_singleton_reads_config(self, mock_file):
        c1 = Config()
        c2 = Config()
        self.assertIs(c1, c2)
        self.assertEqual(c1.log_level, "INFO")
        self.assertEqual(c1.data_path, "./data/")
        self.assertEqual(c1.report_path, "./reports/")
        self.assertEqual(c1.default_strategy, "MeanReversionStrategy")


# Observer Pattern Tests 

class TestObserverPattern(unittest.TestCase):

    def setUp(self):
        self.publisher = SignalPublisher()
        self.logger = LoggerObserver()
        self.alert = AlertObserver(quantity_threshold=50)
        self.publisher.attach(self.logger)
        self.publisher.attach(self.alert)

    def test_notify_all_observers(self):
        signal = {"action": "BUY", "symbol": "AAPL", "quantity": 10}
        try:
            self.publisher.notify(signal)
        except Exception as e:
            self.fail(f"Notify raised exception: {e}")

    def test_large_trade_alert(self):
        signal = {"action": "SELL", "symbol": "TSLA", "quantity": 100}
        try:
            self.publisher.notify(signal)
        except Exception as e:
            self.fail(f"Alert raised exception: {e}")

    def test_attach_detach_observer(self):
        self.publisher.detach(self.logger)
        self.assertNotIn(self.logger, self.publisher._observers)
        self.assertIn(self.alert, self.publisher._observers)


# Command Pattern Tests

class TestCommandPattern(unittest.TestCase):

    def setUp(self):
        self.portfolio = Portfolio()
        self.invoker = CommandInvoker()

    def test_execute_undo_redo(self):
        # BUY command
        signal = {"action": "BUY", "symbol": "AAPL", "quantity": 40}
        cmd = ExecuteOrderCommand(self.portfolio, signal)
        self.invoker.execute_command(cmd)
        self.assertEqual(self.portfolio.get_position("AAPL"), 40)

        # Undo
        self.invoker.undo()
        self.assertEqual(self.portfolio.get_position("AAPL"), 0)

        # Redo
        self.invoker.redo()
        self.assertEqual(self.portfolio.get_position("AAPL"), 40)


# Strategy Patern Tests

class TestStrategyPattern(unittest.TestCase):

    def test_mean_reversion_signals(self):
        params = {"lookback_window": 3, "threshold": 0.02}
        strategy = MeanReversionStrategy(params)
        symbol = "AAPL"

        strategy.price_history[symbol] = deque([100, 101, 102], maxlen=3)
        tick = MockTick(symbol, 95)
        signals = strategy.generate_signals(tick)
        self.assertEqual(signals[0]["action"], "BUY")

        strategy.price_history[symbol] = deque([100, 101, 102], maxlen=3)
        tick = MockTick(symbol, 105)
        signals = strategy.generate_signals(tick)
        self.assertEqual(signals[0]["action"], "SELL")

    def test_breakout_signals(self):
        params = {"lookback_window": 3, "threshold": 0.03}
        strategy = BreakoutStrategy(params)
        symbol = "TSLA"

        strategy.price_history[symbol] = deque([100, 101, 102], maxlen=3)
        tick = MockTick(symbol, 106)
        signals = strategy.generate_signals(tick)
        self.assertEqual(signals[0]["action"], "BUY")

        strategy.price_history[symbol] = deque([100, 101, 102], maxlen=3)
        tick = MockTick(symbol, 90)
        signals = strategy.generate_signals(tick)
        self.assertEqual(signals[0]["action"], "SELL")


# Data Loader Tests

class TestDataLoader(unittest.TestCase):

    @patch("data_loader.YahooFinanceAdapter")
    @patch("data_loader.BloombergXMLAdapter")
    def test_load_data_returns_list(self, mock_bloomberg, mock_yahoo):
        mock_yahoo.return_value.get_data.return_value = {"symbol": "AAPL", "price": 150}
        mock_bloomberg.return_value.get_data.return_value = {"symbol": "MSFT", "price": 320}

        data = load_data()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["symbol"], "AAPL")
        self.assertEqual(data[1]["symbol"], "MSFT")


if __name__ == "__main__":
    unittest.main()