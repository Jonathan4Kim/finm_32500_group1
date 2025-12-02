from breakout_strategy import BreakoutStrategy
from trend_strategy import TrendStrategy
from strategies.reversal_strategy import ReversalStrategy
from strategy import Signal, SignalType

class StrategyRouter:
    """
    Routes to the correct strategy based on the active market regime.
    Each strategy is state-independent; all state is passed in externally.
    """

    def __init__(self):
        self.breakout = BreakoutStrategy()
        self.trend = TrendStrategy()
        self.reversal = ReversalStrategy()

    def route(
        self,
        regime: str,
        price: float,
        engine,
        prev_ema9: float,
        prev_ema21: float
    ) -> Signal:

        # --- BREAKOUT REGIME ---
        if regime == "BREAKOUT":
            return self.breakout.generate_signal(price, engine)

        # --- TREND REGIME ---
        if regime == "TREND":
            return self.trend.generate_signal(price, engine)

        # --- REVERSAL REGIME ---
        if regime == "REVERSAL":
            return self.reversal.generate_signal(
                price=price,
                engine=engine,
                prev_ema9=prev_ema9,
                prev_ema21=prev_ema21,
            )

        # --- NEUTRAL / UNKNOWN ---
        return None
