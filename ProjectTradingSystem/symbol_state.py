from indicator_engine import IndicatorEngine
from regime_detector import RegimeDetector
from strategies.strategy_router import StrategyRouter

class SymbolState:

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.indicators = IndicatorEngine()
        self.regime_detector = RegimeDetector()
        self.router = StrategyRouter()
        self.prev_ema9 = None
        self.prev_ema21 = None
        self.current_regime = "NEUTRAL"

    def update_state(self, price: float):
        """
        Called for each new price for this symbol.
        Updates indicators, detects regime, routes strategy, and
        then updates previous indicator values.
        """

        # STEP 1 — Update Indicators for This Symbol
        self.indicators.on_price(price)

        # STEP 2 — Detect Regime
        regime = self.regime_detector.detect(
            price=price,
            engine=self.indicators
        )
        self.current_regime = regime

        # STEP 3 — Route Appropriate Strategy
        signal = self.router.route(
            regime=regime,
            price=price,
            engine=self.indicators,
            prev_ema9=self.prev_ema9,
            prev_ema21=self.prev_ema21
        )

        # STEP 4 — Store this bar’s EMAs for next bar’s reversal logic
        self.prev_ema9 = self.indicators.ema9
        self.prev_ema21 = self.indicators.ema21
        self.prev_atr14 = self.indicators.atr14

        return regime, signal