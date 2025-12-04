import sys
import os

# Add the project root (PTS) to Python path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from strategies.breakout_strategy import BreakoutStrategy
from strategies.trend_strategy import TrendStrategy
from strategies.reversal_strategy import ReversalStrategy
from strategy import Signal, SignalType, MarketDataPoint

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
        mdp: MarketDataPoint,
        engine,
        prev_ema9: float,
        prev_ema21: float
    ) -> Signal:

        # --- BREAKOUT REGIME ---
        if regime == "BREAKOUT":
            return self.breakout.generate_signal(mdp, engine)

        # --- TREND REGIME ---
        if regime == "TREND":
            return self.trend.generate_signal(mdp, engine)

        # --- REVERSAL REGIME ---
        if regime == "REVERSAL":
            return self.reversal.generate_signal(
                mdp=mdp,
                engine=engine,
                prev_ema9=prev_ema9,
                prev_ema21=prev_ema21,
            )

        # --- NEUTRAL / UNKNOWN ---
        return None
