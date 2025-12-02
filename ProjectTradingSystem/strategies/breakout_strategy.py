from strategy import MarketDataPoint, Signal, SignalType
from strategy_class import Strategy
from indicator_engine import IndicatorEngine

class BreakoutStrategy(Strategy):
    """
    Strategy for BREAKOUT regime:
      - Trade momentum during ATR expansion + range breakouts.
    """

    def generate_signal(self, mdp: MarketDataPoint, engine: IndicatorEngine) -> Signal:
        high20 = engine.high_n(20)
        low20 = engine.low_n(20)

        if high20 is None or low20 is None:
            return None

        atr = engine.atr14
        if atr is None:
            return None

        # ---- Bullish Breakout ----
        if mdp.price > high20 and engine.atr14 > engine.atr14_history_mean * 1.3:
            return Signal(
                timestamp=mdp.timestamp,
                signal=SignalType.BUY,
                symbol=mdp.symbol,
                price = mdp.price,
                reason="Bullish breakout: range break + ATR expansion"
            )

        # ---- Bearish Breakout ----
        if mdp.price < low20 and engine.atr14 > engine.atr14_history_mean * 1.3:
            return Signal(
                timestamp=mdp.timestamp,
                signal=SignalType.SELL,
                symbol=mdp.symbol,
                price = mdp.price,
                reason="Bullish breakout: range break + ATR expansion"
            )

        return None
    
