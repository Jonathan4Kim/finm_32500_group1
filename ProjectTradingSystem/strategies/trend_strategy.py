from strategy import MarketDataPoint, Signal, SignalType
from strategy_class import Strategy
from indicator_engine import IndicatorEngine

class TrendStrategy(Strategy):
    """
    Strategy for TREND regime:
      - Ride established direction using EMA alignment.
    """

    def generate_signal(self, mdp: MarketDataPoint, engine: IndicatorEngine) -> Signal:
        ema9 = engine.ema9
        ema21 = engine.ema21
        ema50 = engine.ema50

        if not ema9 or not ema21 or not ema50:
            return None

        # ---- Bull Trend ----
        if ema9 > ema21 > ema50:
            # Buy dips toward EMA21
            if mdp.price >= ema9:            
                return Signal(
                    timestamp=mdp.timestamp,
                    signal=SignalType.BUY,
                    symbol=mdp.symbol,
                    price = mdp.price,
                    reason="Bullish trend continuation"
                )

        # ---- Bear Trend ----
        if ema9 < ema21 < ema50:
            # Sell rallies up toward EMA21
            if mdp.price <= ema9:
                return Signal(
                    timestamp=mdp.timestamp,
                    signal=SignalType.BUY,
                    symbol=mdp.symbol,
                    price = mdp.price,
                    reason="Bearish trend continuation"
                )
            
        return None