from collections import deque
from typing import Optional

from strategy import MarketDataPoint
from indicator_engine import IndicatorEngine

class RegimeDetector:
    def __init__(self):
        self.prev_ema9 = None
        self.prev_ema21 = None
        self.prev_atr14 = None
        self.atr_history = deque(maxlen=50)


    def detect(self, price: float, engine: IndicatorEngine):

        if engine.ema9 is None or engine.ema21 is None or engine.ema50 is None:
            return None

        # Store previous
        prev_ema9 = self.prev_ema9
        prev_ema21 = self.prev_ema21
        prev_atr14 = self.prev_atr14

        # Update history
        if engine.atr14:
            self.atr_history.append(engine.atr14)
        atr_mean = sum(self.atr_history) / len(self.atr_history) if self.atr_history else None

        # ----- BREAKOUT -----
        atr_exploding = atr_mean and engine.atr14 > atr_mean * 1.5
        range_break = (
            (engine.high_n(20) and price > engine.high_n(20)) or
            (engine.low_n(20) and price > engine.low_n(20))
        )

        ema_spread_widening = (
            prev_ema9 is not None and 
            abs(engine.ema9 - engine.ema21) > abs(prev_ema9 - prev_ema21)
        )

        breakout_score = 0
        if atr_exploding: breakout_score += 3
        if range_break: breakout_score += 3
        if ema_spread_widening: breakout_score += 2
        is_breakout = breakout_score >= 5

        # ----- TREND -----
        ema_bull = engine.ema9 > engine.ema21 > engine.ema50
        ema_bear = engine.ema9 < engine.ema21 < engine.ema50
        atr_rising = prev_atr14 and engine.atr14 > prev_atr14
        not_breakout_vol = atr_mean and engine.atr14 < atr_mean * 1.5

        price_ago_5 = engine.prices[-5] if len(engine.prices) >= 5 else price
        directional_up = price > price_ago_5
        directional_down = price < price_ago_5

        trend_score = 0
        if ema_bull or ema_bear: trend_score += 4
        if atr_rising and not_breakout_vol: trend_score += 2
        if directional_up or directional_down: trend_score += 1

        is_trend = trend_score >= 5

        # ----- REVERSAL -----
        ema_cross_bull = prev_ema9 and prev_ema21 and prev_ema9 < prev_ema21 and engine.ema9 > engine.ema21
        ema_cross_bear = prev_ema9 and prev_ema21 and prev_ema9 > prev_ema21 and engine.ema9 < engine.ema21

        swing_break = (
            (engine.high_n(20) and price > engine.high_n(20)) or
            (engine.low_n(20) and price < engine.low_n(20))
        )

        atr_spike = atr_mean and engine.atr14 > atr_mean * 1.3
        atr_drop = prev_atr14 and engine.atr14 < prev_atr14

        reversal_score = 0
        if ema_cross_bull or ema_cross_bear: reversal_score += 3
        if swing_break: reversal_score += 2
        if atr_spike and atr_drop: reversal_score += 2

        is_reversal = reversal_score >= 5

        # ----- PRIORITY -----
        if is_breakout:
            regime = "BREAKOUT"
        elif is_reversal:
            regime = "REVERSAL"
        elif is_trend:
            regime = "TREND"
        else:
            regime = "NEUTRAL"

        # save for next tick
        self.prev_ema9 = engine.ema9
        self.prev_ema21 = engine.ema21
        self.prev_atr14 = engine.atr14

        return regime
