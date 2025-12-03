from logging_utils.logger import setup_logger

trade_logger = setup_logger("Trading", "trading.log")
regime_logger = setup_logger("Regime", "regime.log")
signal_logger = setup_logger("Signal", "signal.log")

def log_regime(symbol, timestamp, regime, price, ema9=None, ema21=None, ema50=None):
    regime_logger.info(
        f"{timestamp} | {symbol} | Regime: {regime} | Price={price:.2f} "
        f"| EMA9={ema9} EMA21={ema21} EMA50={ema50}"
    )

def log_signal(symbol, timestamp, signal):
    if signal is None:
        return
    
    signal_logger.info(
        f"{timestamp} | {symbol} | Signal={signal.side.value} "
        f"| Confidence={signal.confidence:.2f} | Reason={signal.reason}"
    )
