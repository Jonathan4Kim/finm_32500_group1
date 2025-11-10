"""
Unit Tests for Trading System - Assignment 8
Covers:
1. Shared memory functionality
2. Strategy signal generation
3. Message serialization/deserialization
4. Socket connectivity
5. Data correctness
"""

import unittest
import json
import socket
import numpy as np
from datetime import datetime
from shared_memory_utils import SharedPriceBook


# Only import strategies if they exist
try:
    from strategy import WindowedMovingAverageStrategy, SentimentStrategy, MarketDataPoint
    STRATEGY_AVAILABLE = True
except ImportError:
    STRATEGY_AVAILABLE = False


class TestSharedMemory(unittest.TestCase):
    """Test suite for SharedPriceBook (shared memory utilities)."""

    def setUp(self):
        self.test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        self.test_name = 'test_prices'

    def tearDown(self):
        from multiprocessing import shared_memory
        try:
            shm = shared_memory.SharedMemory(name=self.test_name)
            shm.close()
            shm.unlink()
        except:
            pass

    def test_create_shared_memory(self):
        """Create and verify shared memory block."""
        book = SharedPriceBook(self.test_symbols, name=self.test_name, create=True)
        self.assertEqual(book.get_symbols(), self.test_symbols)
        book.close()
        book.unlink()

    def test_update_and_read_price(self):
        """Update and read price correctly."""
        book = SharedPriceBook(self.test_symbols, name=self.test_name, create=True)
        symbol, price = 'AAPL', 172.53
        book.update(symbol, price)
        idx = book.symbol_to_index[symbol]
        retrieved_price = float(book.prices[idx]['price'])
        self.assertAlmostEqual(retrieved_price, price, places=2)
        book.close()
        book.unlink()

    def test_update_multiple_prices(self):
        """Update multiple prices and verify."""
        book = SharedPriceBook(self.test_symbols, name=self.test_name, create=True)
        prices = {'AAPL': 172.53, 'MSFT': 325.20, 'GOOGL': 2850.75}
        book.update_multiple(prices)
        for sym, val in prices.items():
            idx = book.symbol_to_index[sym]
            self.assertAlmostEqual(float(book.prices[idx]['price']), val, places=2)
        book.close()
        book.unlink()

    def test_shared_memory_propagates(self):
        """Shared memory updates propagate between instances."""
        book1 = SharedPriceBook(self.test_symbols, name=self.test_name, create=True)
        book1.update('AAPL', 150.0)
        book2 = SharedPriceBook(self.test_symbols, name=self.test_name, create=False)
        idx = book2.symbol_to_index['AAPL']
        self.assertAlmostEqual(float(book2.prices[idx]['price']), 150.0, places=2)
        book1.close()
        book2.close()
        book1.unlink()

    def test_data_persistence(self):
        """Data persists correctly."""
        book = SharedPriceBook(['TEST'], name='test_persist', create=True)
        for i in range(10):
            book.update('TEST', 100.0 + i)
        idx = book.symbol_to_index['TEST']
        final_price = float(book.prices[idx]['price'])
        self.assertAlmostEqual(final_price, 109.0, places=2)
        book.close()
        book.unlink()


@unittest.skipUnless(STRATEGY_AVAILABLE, "Strategy module not available")
class TestStrategySignals(unittest.TestCase):
    """Tests for trading strategy signal generation."""

    def test_moving_average_buy_signal(self):
        strategy = WindowedMovingAverageStrategy(s=2, l=5)
        prices = [100, 101, 102, 103, 104, 110]
        for p in prices:
            tick = MarketDataPoint(datetime.now(), 'AAPL', p)
            signal = strategy.generate_signals(tick)
        self.assertEqual(signal[0], "BUY")

    def test_moving_average_sell_signal(self):
        strategy = WindowedMovingAverageStrategy(s=2, l=5)
        prices = [110, 109, 108, 107, 106, 100]
        for p in prices:
            tick = MarketDataPoint(datetime.now(), 'AAPL', p)
            signal = strategy.generate_signals(tick)
        self.assertEqual(signal[0], "SELL")

    def test_sentiment_signals(self):
        s = SentimentStrategy(60, 40)
        self.assertEqual(s.generate_signals(75)[0], "BUY")
        self.assertEqual(s.generate_signals(25)[0], "SELL")
        self.assertEqual(s.generate_signals(50)[0], "HOLD")


class TestMessageSerialization(unittest.TestCase):
    """Tests for message serialization/deserialization."""

    def test_price_message_format(self):
        message = "AAPL,172.53*"
        parts = message.rstrip('*').split(',')
        self.assertEqual(parts[0], "AAPL")
        self.assertAlmostEqual(float(parts[1]), 172.53, places=2)

    def test_order_serialization(self):
        order = {'order_id': 12, 'action': 'BUY', 'symbol': 'AAPL', 'quantity': 10, 'price': 173.20}
        serialized = json.dumps(order) + '*'
        deserialized = json.loads(serialized.rstrip('*'))
        self.assertEqual(deserialized['action'], 'BUY')
        self.assertEqual(deserialized['symbol'], 'AAPL')
        self.assertAlmostEqual(deserialized['price'], 173.20, places=2)


class TestSocketConnectivity(unittest.TestCase):
    """Test socket connection establishment."""

    def test_socket_server_creation(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(('localhost', 9999))
            server.listen(1)
            success = True
        except Exception:
            success = False
        finally:
            server.close()
        self.assertTrue(success, "Socket server creation failed")


def run_all_tests():
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='test_shared_memory.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    ok = run_all_tests()
    exit(0 if ok else 1)
