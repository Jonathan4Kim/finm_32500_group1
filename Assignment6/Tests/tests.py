import unittest
from collections import deque
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
import numpy as np
from Assignment6.data_loader import load_data
from Assignment6.models import MarketDataPoint, PortfolioGroup, build_portfolio, Position
from Assignment6.patterns.factory import Stock, Bond, ETF, InstrumentFactory
from Assignment6.patterns.singleton import Config
from Assignment6.patterns.builder import Portfolio, PortfolioBuilder
from Assignment6.analytics import VolatilityDecorator, BetaDecorator, DrawdownDecorator
from Assignment6.patterns.observer import SignalPublisher, LoggerObserver, AlertObserver
from Assignment6.patterns.command import ExecuteOrderCommand, UndoOrderCommand, CommandInvoker
from Assignment6.patterns.strategy import BreakoutStrategy, MeanReversionStrategy


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
        np.random.seed(42)
        prices = (100 + np.cumsum(np.random.randn(252))).tolist()
        self.stock_data = {"symbol": "AAPL", "type": "Stock", "prices": prices, "sector": "Tech", "issuer": "Apple"}
        self.bond_data = {"symbol": "US10Y", "type": "Bond", "prices": prices, "sector": "Govt", "issuer": "US Treasury", "maturity": "2035-10-01"}
        self.etf_data = {"symbol": "SPY", "type": "ETF", "prices": prices, "sector": "Index", "issuer": "State Street"}

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


# Builder Pattern Tests

class TestPortfolioBuilder(unittest.TestCase):

    def setUp(self):
        """Create a clean builder for each test."""
        self.builder = PortfolioBuilder("Main Portfolio")

    def test_add_position(self):
        """Ensure positions are added correctly."""
        self.builder.add_position("AAPL", 10, 150.0)
        self.builder.add_position("MSFT", 5, 320.0)
        self.assertEqual(len(self.builder.positions), 2)
        self.assertEqual(self.builder.positions[0]["symbol"], "AAPL")
        self.assertEqual(self.builder.positions[1]["price"], 320.0)

    def test_set_owner(self):
        """Ensure owner is correctly set."""
        self.builder.set_owner("Cole")
        self.assertEqual(self.builder.owner, "Cole")

    def test_build_creates_portfolio(self):
        """Ensure build() produces a Portfolio with correct attributes."""
        self.builder.add_position("AAPL", 10, 150.0)
        self.builder.set_owner("Cole")

        portfolio = self.builder.build()

        self.assertIsInstance(portfolio, Portfolio)
        self.assertEqual(portfolio.name, "Main Portfolio")
        self.assertEqual(portfolio.owner, "Cole")
        self.assertEqual(len(portfolio.positions), 1)
        self.assertEqual(portfolio.positions[0]["symbol"], "AAPL")
        self.assertEqual(portfolio.positions[0]["quantity"], 10)
        self.assertEqual(portfolio.sub_portfolios, [])

    def test_nested_sub_portfolios(self):
        """Ensure nested sub-portfolios are built correctly."""
        # Create main builder
        self.builder.set_owner("Cole")
        self.builder.add_position("AAPL", 10, 150.0)

        # Create sub-portfolio
        sub_builder = PortfolioBuilder("Sub Portfolio 1")
        sub_builder.add_position("TSLA", 3, 700.0)
        sub_builder.set_owner("Hudson")

        # Add subportfolio and build
        self.builder.add_subportfolio(sub_builder)
        portfolio = self.builder.build()

        # Assertions on main portfolio
        self.assertEqual(portfolio.name, "Main Portfolio")
        self.assertEqual(portfolio.owner, "Cole")
        self.assertEqual(len(portfolio.sub_portfolios), 1)

        # Assertions on sub-portfolio
        sub = portfolio.sub_portfolios[0]
        self.assertIsInstance(sub, Portfolio)
        self.assertEqual(sub.name, "Sub Portfolio 1")
        self.assertEqual(sub.owner, "Hudson")
        self.assertEqual(sub.positions[0]["symbol"], "TSLA")

    def test_empty_subportfolio_list(self):
        """Ensure build() works even with no sub-portfolios."""
        self.builder.add_position("GOOGL", 8, 2800.0)
        portfolio = self.builder.build()
        self.assertEqual(portfolio.sub_portfolios, [])
        self.assertEqual(len(portfolio.positions), 1)


# Decorator Pattern Tests

class TestInstrumentDecorators(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        factory = InstrumentFactory()
        self.prices = 100 + np.cumsum(np.random.randn(252))
        self.benchmark = 100 + np.cumsum(np.random.randn(252))
        self.stock_data = {"symbol": "AAPL", "type": "Stock", "prices": self.prices, "sector": "Tech", "issuer": "Apple"}
        self.stock = factory.create_instrument(self.stock_data)

    def test_volatility_decorator(self):
        decorated = VolatilityDecorator(self.stock)
        metrics = decorated.get_metrics()
        self.assertIn("volatility", metrics)
        self.assertGreaterEqual(metrics["volatility"], 0.0)
        self.assertAlmostEqual(metrics["symbol"], "AAPL")

    def test_beta_decorator_with_benchmark(self):
        decorated = BetaDecorator(self.stock, benchmark_prices=self.benchmark.tolist())
        metrics = decorated.get_metrics()
        self.assertIn("beta", metrics)
        self.assertIsInstance(metrics["beta"], float)

    def test_beta_decorator_without_benchmark(self):
        decorated = BetaDecorator(self.stock)
        metrics = decorated.get_metrics()
        self.assertEqual(metrics["beta"], "N/A")

    def test_drawdown_decorator(self):
        decorated = DrawdownDecorator(self.stock)
        metrics = decorated.get_metrics()
        self.assertIn("max_drawdown", metrics)
        self.assertLessEqual(metrics["max_drawdown"], 0.0)

    def test_stacked_decorators(self):
        decorated = DrawdownDecorator(
            BetaDecorator(
                VolatilityDecorator(self.stock),
                benchmark_prices=self.benchmark.tolist()
            )
        )
        metrics = decorated.get_metrics()

        # Check all layers contributed
        self.assertIn("volatility", metrics)
        self.assertIn("beta", metrics)
        self.assertIn("max_drawdown", metrics)

        # Check sensible ranges
        self.assertGreaterEqual(metrics["volatility"], 0)
        self.assertLessEqual(metrics["max_drawdown"], 0)
        self.assertTrue(isinstance(metrics["beta"], float) or metrics["beta"] == "N/A")


# Data Loader Tests (Adapter)

class TestDataLoader(unittest.TestCase):

    @patch("Assignment6.data_loader.YahooFinanceAdapter")
    @patch("Assignment6.data_loader.BloombergXMLAdapter")
    def test_load_data_returns_list(self, mock_bloomberg, mock_yahoo):
        mock_yahoo.return_value.get_data.return_value = {"symbol": "AAPL", "price": 150}
        mock_bloomberg.return_value.get_data.return_value = {"symbol": "MSFT", "price": 320}

        data = load_data()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["symbol"], "AAPL")
        self.assertEqual(data[1]["symbol"], "MSFT")


# Composite Pattern Tests

class TestPortfolioSystem(unittest.TestCase):
    def setUp(self):
        # Basic sample data
        self.ts = datetime(2025, 1, 1, 9, 30)
        self.position_a = Position(symbol="AAPL", quantity=10, price=150.0)
        self.position_b = Position(symbol="MSFT", quantity=5, price=300.0)

        # Portfolio with positions
        self.portfolio = PortfolioGroup(name="Main", owner="Cole")
        self.portfolio.add_position(self.position_a)
        self.portfolio.add_position(self.position_b)

    # ---------- Test Data Classes ----------
    def test_market_data_point(self):
        md = MarketDataPoint(timestamp=self.ts, symbol="AAPL", price=155.25)
        self.assertEqual(md.symbol, "AAPL")
        self.assertEqual(md.price, 155.25)
        self.assertIsInstance(md.timestamp, datetime)

    def test_position_value(self):
        self.assertAlmostEqual(self.position_a.get_value(), 1500.0)
        self.assertEqual(self.position_b.get_positions(), ["MSFT"])

    # ---------- Test PortfolioGroup ----------
    def test_portfolio_value(self):
        total_value = self.portfolio.get_value()
        self.assertAlmostEqual(total_value, 1500 + 1500)  # 3000
        self.assertIn("AAPL", self.portfolio.get_positions())
        self.assertIn("MSFT", self.portfolio.get_positions())

    def test_add_and_remove_position_full(self):
        # Remove full quantity of AAPL
        result = self.portfolio.remove_position("AAPL", 10)
        self.assertTrue(result)
        self.assertNotIn("AAPL", self.portfolio.get_positions())

    def test_remove_partial_position(self):
        result = self.portfolio.remove_position("MSFT", 2)
        self.assertTrue(result)
        for p in self.portfolio.positions:
            if p.symbol == "MSFT":
                self.assertEqual(p.quantity, 3.0)

    def test_remove_nonexistent_symbol(self):
        result = self.portfolio.remove_position("GOOG", 5)
        self.assertFalse(result)

    def test_nested_sub_portfolio_value(self):
        sub_portfolio = PortfolioGroup(name="Sub1")
        sub_portfolio.add_position(Position("TSLA", 2, 400.0))
        self.portfolio.add_sub_portfolio(sub_portfolio)

        total = self.portfolio.get_value()
        # 3000 from main + 800 from sub
        self.assertAlmostEqual(total, 3800.0)
        self.assertIn("TSLA", self.portfolio.get_positions())

    # ---------- Test build_portfolio Factory ----------
    def test_build_portfolio_from_dict(self):
        data = {
            "name": "Parent",
            "owner": "Seb",
            "positions": [
                {"symbol": "AAPL", "quantity": 5, "price": 100},
                {"symbol": "MSFT", "quantity": 2, "price": 200}
            ],
            "sub_portfolios": [
                {
                    "name": "Child",
                    "positions": [
                        {"symbol": "GOOG", "quantity": 1, "price": 1000}
                    ]
                }
            ]
        }

        built = build_portfolio(data)
        self.assertIsInstance(built, PortfolioGroup)
        self.assertAlmostEqual(built.get_value(), 5*100 + 2*200 + 1*1000)
        self.assertIn("GOOG", built.get_positions())
        self.assertIn("MSFT", built.get_positions())
        self.assertIn("Child", [sp.name for sp in built.sub_portfolios])


# Strategy Pattern Tests

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
        self.portfolio = PortfolioGroup(name="TestPortfolio")
        self.invoker = CommandInvoker()

    def test_execute_undo_redo(self):
        # BUY command
        signal = {"action": "BUY", "symbol": "AAPL", "quantity": 40, "price": 100}
        cmd = ExecuteOrderCommand(self.portfolio, signal)
        self.invoker.execute_command(cmd)
        self.assertEqual(self.portfolio.get_positions(), ["AAPL"])

        # Undo
        self.invoker.undo()
        self.assertEqual(self.portfolio.get_positions(), [])

        # Redo
        self.invoker.redo()
        self.assertEqual(self.portfolio.get_positions(), ["AAPL"])



if __name__ == "__main__":
    unittest.main()

#  Composite