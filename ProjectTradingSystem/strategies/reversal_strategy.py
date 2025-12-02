from strategy import MarketDataPoint, Signal, SignalType
from strategy_class import Strategy
from indicator_engine import IndicatorEngine

class ReversalStrategy(Strategy):
    """
    Strategy for REVERSAL regime:
      - Trade opposite when trend fails (EMA cross + swing break).
    """

    def generate_signal(self, mdp: MarketDataPoint, engine: IndicatorEngine, prev_ema9, prev_ema21) -> Signal:
        ema9 = engine.ema9
        ema21 = engine.ema21

        high20 = engine.high_n(20)
        low20 = engine.low_n(20)

        if not ema9 or not ema21 or high20 is None or low20 is None:
            return None

        # ---- Bullish Reversal (from bear to bull) ----
        if prev_ema9 < prev_ema21 and ema9 > ema21 and mdp.price > high20:
            return Signal(
                        timestamp=mdp.timestamp,
                        signal=SignalType.BUY,
                        symbol=mdp.symbol,
                        price = mdp.price,
                        reason="Bullish reversal: EMA cross + swing break"
                    )

        # ---- Bearish Reversal (from bull to bear) ----
        if prev_ema9 > prev_ema21 and ema9 < ema21 and mdp.price < low20:
            return Signal(
                        timestamp=mdp.timestamp,
                        signal=SignalType.BUY,
                        symbol=mdp.symbol,
                        price = mdp.price,
                        reason="Bearish reversal: EMA cross + swing break"
                    )

        return None