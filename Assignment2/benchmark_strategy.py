from strategies import Strategy

class BenchmarkStrategy(Strategy):

    def __init__(self):
        self.name = "benchmark"
        self.isFirstDay = True
        
    def generate_signals(self, tick):
        """
        Generates first signal to buy
        on first date. Then hold otherwise

        Args:
            tick (MarketDataPoint): one day adjusted
            closing price of (tick.symbol) on day (tick.timestamp)

        Returns:
            _type_: _description_
        """
        if self.isFirstDay:
            self.isFirstDay = False
            return ["BUY"]
        return ["HOLD"]
    