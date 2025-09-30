from strategies import Strategy

class VolatilityBreakoutStrategy(Strategy):
    def __init__(self):
        # TODO: Intialize
        self.name = "volatility"
        super().__init__()
    
    def generate_signals(self, tick):
        # TODO: Finish Generating Signals
        return super().generate_signals(tick)