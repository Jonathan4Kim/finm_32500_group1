import unittest
import sys
from data_loader import load_data
from strategies import NaiveMovingAverageStrategy, WindowedMovingAverageStrategy
from models import MarketDataPoint
from datetime import datetime
from models import MarketDataPoint
import time
import tracemalloc
import cProfile
import io
import pstats



class NaiveMACTestCase(unittest.TestCase):
    strategy = NaiveMovingAverageStrategy(2, 5)

    def test_holding_before_long(self):
        strategy = NaiveMovingAverageStrategy(2, 5)
        mdp = MarketDataPoint("2025-10-07T17:32:58.016406", "AAPL", 204.0)
        # ensure that anything before long average is computed returns hold
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
    
    def test_buy_signal(self):
        # create strategy and prices that are oriented towards buy signal
        strategy = NaiveMovingAverageStrategy(2, 5)
        prices = [10.0, 20.0, 30.0, 40.0, 100.0, 100.0]
        # generate signals from strategy
        for price in prices:
            mdp = MarketDataPoint(datetime.now(), "MSFT", price)
            signal = strategy.generate_signals(mdp)
        self.assertEqual(signal, ["BUY"])
    
    def test_sell_signal(self):
        # get strategy, prices, and reverse
        strategy = NaiveMovingAverageStrategy(2, 5)
        prices = [10.0, 20.0, 30.0, 40.0, 100.0, 100.0]
        prices.reverse()
        # generate signals from strategy
        for price in prices:
            mdp = MarketDataPoint(datetime.now(), "MSFT", price)
            signal = strategy.generate_signals(mdp)
        self.assertEqual(signal, ["SELL"])

class WindowedMACTestCase(unittest.TestCase):

    def test_holding_before_long(self):
        # just create one data point to make sure holding is happening
        strategy = WindowedMovingAverageStrategy(2, 5)
        mdp = MarketDataPoint("2025-10-07T17:32:58.016406", "AAPL", 204.0)
        # ensure that anything before long average is computed returns hold
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
        self.assertTrue(strategy.generate_signals(mdp), ["HOLD"])
    
    def test_buy_signal(self):
        # create strategy and prices that are oriented towards buy signal
        strategy = WindowedMovingAverageStrategy(2, 5)
        prices = [10.0, 20.0, 30.0, 40.0, 100.0, 100.0]
        # generate signals from strategy
        for price in prices:
            mdp = MarketDataPoint(datetime.now(), "MSFT", price)
            signal = strategy.generate_signals(mdp)
        self.assertEqual(signal, ["BUY"])
    
    def test_sell_signal(self):
        # create strategy and prices that are oriented towards sel signal
        strategy = WindowedMovingAverageStrategy(2, 5)
        prices = [10.0, 20.0, 30.0, 40.0, 100.0, 100.0]
        prices.reverse()
        # generate signals from strategy
        for price in prices:
            mdp = MarketDataPoint(datetime.now(), "MSFT", price)
            signal = strategy.generate_signals(mdp)
        self.assertEqual(signal, ["SELL"])

    def test_speed_100k(self):
        # create strategy and load data
        strategy = WindowedMovingAverageStrategy(2, 5)
        data = load_data()
        
        # time hwo long it takes to generate signals
        start = time.time()
        # generate signals from strategy
        for mdp in data:
            strategy.generate_signals(mdp)
        end = time.time()
        
        # get actual time for execution and test
        total_time = end - start
        self.assertTrue(total_time < 1.0)
    
    def test_memory_100k(self):
        # create strategy and load data
        strategy = WindowedMovingAverageStrategy(2, 5)
        tracemalloc.start()
        data = load_data()
        # generate signals from strategy
        for mdp in data: 
            strategy.generate_signals(mdp)
        _, peak = tracemalloc.get_traced_memory()
        self.assertTrue(peak / 10**6 < 100)
        
    def test_profiling_hotspots(self):
        # create strategy and load data
        strategy = WindowedMovingAverageStrategy(2, 5)
        data = load_data()
        
        profiler = cProfile.Profile()
        profiler.enable()
        # generate signals from strategy
        for mdp in data:
            strategy.generate_signals(mdp)
        profiler.disable()
        
        # ensure that pstats, based on cumulative factors, have generate_signals in profiling hotspots
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        stats.print_stats(10)
        output = s.getvalue()
        
        self.assertIn("generate_signals", output)
    
    def test_profiling_memory_peaks(self):
        # get strategy and load data
        strategy = WindowedMovingAverageStrategy(2, 5)
        data = load_data()
        
        # begin tracemalloc and generate signals
        tracemalloc.start()
        for mdp in data:
            strategy.generate_signals(mdp)
        # after generating 100k signals, take teh snapshot and get statistics
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")
        
        # stop tracemallorc after getting the top 10 memory peaks
        files = "\n".join(str(stat.traceback[0]) for stat in top_stats[:10])
        tracemalloc.stop()

        # ensure strategies isn't in there (data mostly allocated to data_loader.py)
        self.assertFalse(
        any("strategies.py" in f for f in files),
        f"strategies.py not found in top memory allocations. Got: {files}"
        )


if __name__ == "__main__":
    unittest.main()