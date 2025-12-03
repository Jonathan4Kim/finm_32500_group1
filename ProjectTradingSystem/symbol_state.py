from indicator_engine import IndicatorEngine
from regime_detector import RegimeDetector
from strategies.strategy_router import StrategyRouter
from logging_utils.trading_logger import log_regime, log_signal

class SymbolState:

    def __init__(self, symbol: str, warmup_bars: int = 20):
        self.symbol = symbol

        self.warmup_bars = warmup_bars
        self.bars_seen = 0
        self.is_warm = False

        self.indicators = IndicatorEngine()
        self.regime_detector = RegimeDetector()
        self.router = StrategyRouter()

        self.prev_ema9 = None
        self.prev_ema21 = None
        self.current_regime = None

    def update_state(self, price: float, timestamp=None):
        """
        Called for each new price for this symbol.
        Updates indicators, detects regime, routes strategy, and
        then updates previous indicator values.
        """

        # STEP 1 — Update Indicators for This Symbol
        self.bars_seen += 1
        self.indicators.on_price(price)

        # Check warmup progress
        if not self.is_warm:
            if self.bars_seen < self.warmup_bars:
                log_regime(self.symbol, timestamp, "WARMING", price)
                return "WARMING", None

            # Enough bars — we are now warm
            self.is_warm = True
            log_regime(self.symbol, timestamp, "WARMUP COMPLETE", price)

        # STEP 2 — Detect Regime
        regime = self.regime_detector.detect(
            price=price,
            engine=self.indicators
        )
        self.current_regime = regime

        log_regime(
            self.symbol,
            timestamp,
            regime,
            price,
            self.indicators.ema9,
            self.indicators.ema21,
            self.indicators.ema50
        )

        # STEP 3 — Route Appropriate Strategy
        signal = self.router.route(
            regime=regime,
            price=price,
            engine=self.indicators,
            prev_ema9=self.prev_ema9,
            prev_ema21=self.prev_ema21
        )

        log_signal(self.symbol, timestamp, signal)

        # STEP 4 — Store this bar’s EMAs for next bar’s reversal logic
        self.prev_ema9 = self.indicators.ema9
        self.prev_ema21 = self.indicators.ema21
        self.prev_atr14 = self.indicators.atr14

        return regime, signal