import pandas as pd
import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    timestamp: pd.Timestamp
    signal: SignalType
    symbol: str
    price: float
    reason: str


class MAStrategy:
    """
    Moving Average Crossover Strategy
    
    Approach: Trend-following
    Entry: Short MA crosses above long MA (bullish trend)
    Exit: Short MA crosses below long MA (bearish trend)
    Logic: Follows medium-term price trends
    """
    
    def __init__(
        self,
        symbol: str,
        short_ma_window: int = 20,
        long_ma_window: int = 50,
        position_size: int = 100
    ):
        self.symbol = symbol
        self.short_ma_window = short_ma_window
        self.long_ma_window = long_ma_window
        self.position_size = position_size
        self.data = None
        self.signals = []
        self.position = 0
        self.strategy_name = "MA Crossover (Trend-Following)"
    
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        self.data = pd.read_csv(filepath, index_col=0, parse_dates=True)
        if self.data.index.name is None:
            self.data.index.name = 'Datetime'
        return self.data
    
    
    def generate_signals(self) -> List[Signal]:
        if self.data is None or self.data.empty:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if 'MA_20' not in self.data.columns or 'MA_50' not in self.data.columns:
            raise ValueError("Data missing MA_20 or MA_50 columns")
        
        self.signals = []
        
        for i in range(1, len(self.data)):
            prev_row = self.data.iloc[i - 1]
            curr_row = self.data.iloc[i]
            
            prev_ma_short = prev_row['MA_20']
            prev_ma_long = prev_row['MA_50']
            curr_ma_short = curr_row['MA_20']
            curr_ma_long = curr_row['MA_50']
            curr_price = curr_row['Close']
            curr_time = self.data.index[i]
            
            if pd.isna(prev_ma_short) or pd.isna(prev_ma_long) or pd.isna(curr_ma_short) or pd.isna(curr_ma_long):
                continue
            
            if prev_ma_short <= prev_ma_long and curr_ma_short > curr_ma_long and self.position == 0:
                signal = Signal(
                    timestamp=curr_time,
                    signal=SignalType.BUY,
                    symbol=self.symbol,
                    price=curr_price,
                    reason=f"MA_20 crossed above MA_50"
                )
                self.signals.append(signal)
                self.position = 1
            
            elif prev_ma_short >= prev_ma_long and curr_ma_short < curr_ma_long and self.position == 1:
                signal = Signal(
                    timestamp=curr_time,
                    signal=SignalType.SELL,
                    symbol=self.symbol,
                    price=curr_price,
                    reason=f"MA_20 crossed below MA_50"
                )
                self.signals.append(signal)
                self.position = 0
        
        return self.signals
    
    
    def get_signal_at_index(self, index: int) -> Optional[Signal]:
        if index < 1 or index >= len(self.data):
            return None
        
        prev_row = self.data.iloc[index - 1]
        curr_row = self.data.iloc[index]
        
        prev_ma_short = prev_row['MA_20']
        prev_ma_long = prev_row['MA_50']
        curr_ma_short = curr_row['MA_20']
        curr_ma_long = curr_row['MA_50']
        curr_price = curr_row['Close']
        curr_time = self.data.index[index]
        
        if pd.isna(prev_ma_short) or pd.isna(prev_ma_long) or pd.isna(curr_ma_short) or pd.isna(curr_ma_long):
            return None
        
        if prev_ma_short <= prev_ma_long and curr_ma_short > curr_ma_long and self.position == 0:
            self.position = 1
            return Signal(
                timestamp=curr_time,
                signal=SignalType.BUY,
                symbol=self.symbol,
                price=curr_price,
                reason=f"MA_20 crossed above MA_50"
            )
        
        elif prev_ma_short >= prev_ma_long and curr_ma_short < curr_ma_long and self.position == 1:
            self.position = 0
            return Signal(
                timestamp=curr_time,
                signal=SignalType.SELL,
                symbol=self.symbol,
                price=curr_price,
                reason=f"MA_20 crossed below MA_50"
            )
        
        return None
    
    
    def get_position_size(self) -> int:
        return self.position_size
    
    
    def summary(self) -> dict:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "total_signals": len(self.signals),
            "buy_signals": sum(1 for s in self.signals if s.signal == SignalType.BUY),
            "sell_signals": sum(1 for s in self.signals if s.signal == SignalType.SELL),
        }


class MomentumStrategy:
    """
    Momentum Strategy 
    
    Approach: Mean reversion with momentum confirmation
    Entry: Price accelerates upward (positive momentum + positive returns)
    Exit: Momentum fades or reverses (negative momentum)
    Logic: Exploits short-term price acceleration, captures momentum waves
    """
    
    def __init__(
        self,
        symbol: str,
        momentum_window: int = 10,
        momentum_threshold: float = 0.001, # <-- Chnage threshhold for more or less signals
        position_size: int = 100
    ):
        self.symbol = symbol
        self.momentum_window = momentum_window
        self.momentum_threshold = momentum_threshold
        self.position_size = position_size
        self.data = None
        self.signals = []
        self.position = 0
        self.strategy_name = "Momentum (Rate of Change)"
    
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        self.data = pd.read_csv(filepath, index_col='Datetime', parse_dates=True)
        
        # Calculate momentum (ROC)
        self.data['Momentum'] = self.data['Close'].pct_change(self.momentum_window)
        return self.data
    
    
    def generate_signals(self) -> List[Signal]:
        if self.data is None or self.data.empty:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if 'Momentum' not in self.data.columns or 'Returns' not in self.data.columns:
            raise ValueError("Data missing Momentum or Returns columns")
        
        self.signals = []
        
        for i in range(1, len(self.data)):
            prev_row = self.data.iloc[i - 1]
            curr_row = self.data.iloc[i]
            
            prev_momentum = prev_row['Momentum']
            curr_momentum = curr_row['Momentum']
            curr_returns = curr_row['Returns']
            curr_price = curr_row['Close']
            curr_time = self.data.index[i]
            
            if pd.isna(prev_momentum) or pd.isna(curr_momentum) or pd.isna(curr_returns):
                continue
            
            # Buy: Momentum accelerates above threshold and returns are positive
            if (prev_momentum <= self.momentum_threshold and 
                curr_momentum > self.momentum_threshold and 
                curr_returns > 0 and 
                self.position == 0):
                
                signal = Signal(
                    timestamp=curr_time,
                    signal=SignalType.BUY,
                    symbol=self.symbol,
                    price=curr_price,
                    reason=f"Momentum surge: {curr_momentum:.4f} with positive returns"
                )
                self.signals.append(signal)
                self.position = 1
            
            # Sell: Momentum falls below threshold or turns negative
            elif (curr_momentum < -self.momentum_threshold and self.position == 1):
                signal = Signal(
                    timestamp=curr_time,
                    signal=SignalType.SELL,
                    symbol=self.symbol,
                    price=curr_price,
                    reason=f"Momentum collapse: {curr_momentum:.4f}"
                )
                self.signals.append(signal)
                self.position = 0
        
        return self.signals
    
    
    def get_signal_at_index(self, index: int) -> Optional[Signal]:
        if index < self.momentum_window or index >= len(self.data):
            return None
        
        prev_row = self.data.iloc[index - 1]
        curr_row = self.data.iloc[index]
        
        prev_momentum = prev_row['Momentum']
        curr_momentum = curr_row['Momentum']
        curr_returns = curr_row['Returns']
        curr_price = curr_row['Close']
        curr_time = self.data.index[index]
        
        if pd.isna(prev_momentum) or pd.isna(curr_momentum) or pd.isna(curr_returns):
            return None
        
        if (prev_momentum <= self.momentum_threshold and 
            curr_momentum > self.momentum_threshold and 
            curr_returns > 0 and 
            self.position == 0):
            
            self.position = 1
            return Signal(
                timestamp=curr_time,
                signal=SignalType.BUY,
                symbol=self.symbol,
                price=curr_price,
                reason=f"Momentum surge: {curr_momentum:.4f}"
            )
        
        elif curr_momentum < -self.momentum_threshold and self.position == 1:
            self.position = 0
            return Signal(
                timestamp=curr_time,
                signal=SignalType.SELL,
                symbol=self.symbol,
                price=curr_price,
                reason=f"Momentum collapse: {curr_momentum:.4f}"
            )
        
        return None
    
    
    def get_position_size(self) -> int:
        return self.position_size
    
    
    def summary(self) -> dict:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "total_signals": len(self.signals),
            "buy_signals": sum(1 for s in self.signals if s.signal == SignalType.BUY),
            "sell_signals": sum(1 for s in self.signals if s.signal == SignalType.SELL),
        }


class StatisticalSignalStrategy:
    """
    Statistical Signal Generation Model (Z-Score Mean Reversion)
    
    Approach: Statistical mean reversion using z-scores
    Entry: Price deviates significantly from mean (z-score < -1.5 for BUY, > 1.5 for SELL)
    Exit: Price reverts toward mean (z-score crosses zero)
    Logic: Identifies overbought/oversold conditions statistically, trades mean reversion
    """
    
    def __init__(
        self,
        symbol: str,
        lookback_window: int = 20,
        zscore_threshold: float = 1.5,
        position_size: int = 100
    ):
        self.symbol = symbol
        self.lookback_window = lookback_window
        self.zscore_threshold = zscore_threshold
        self.position_size = position_size
        self.data = None
        self.signals = []
        self.position = 0
        self.entry_zscore = None
        self.strategy_name = "Statistical Signal (Z-Score Mean Reversion)"
    
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        self.data = pd.read_csv(filepath, index_col='Datetime', parse_dates=True)
        
        # Calculate rolling mean and standard deviation
        self.data['Price_Mean'] = self.data['Close'].rolling(window=self.lookback_window).mean()
        self.data['Price_Std'] = self.data['Close'].rolling(window=self.lookback_window).std()
        
        # Calculate z-score (statistical deviation from mean)
        self.data['Z_Score'] = (self.data['Close'] - self.data['Price_Mean']) / self.data['Price_Std']
        
        return self.data
    
    
    def generate_signals(self) -> List[Signal]:
        if self.data is None or self.data.empty:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if 'Z_Score' not in self.data.columns:
            raise ValueError("Data missing Z_Score column")
        
        self.signals = []
        
        for i in range(1, len(self.data)):
            prev_row = self.data.iloc[i - 1]
            curr_row = self.data.iloc[i]
            
            prev_zscore = prev_row['Z_Score']
            curr_zscore = curr_row['Z_Score']
            curr_price = curr_row['Close']
            curr_time = self.data.index[i]
            
            if pd.isna(prev_zscore) or pd.isna(curr_zscore):
                continue
            
            # Buy: Price oversold (z-score below -threshold) and position flat
            if curr_zscore < -self.zscore_threshold and self.position == 0:
                self.entry_zscore = curr_zscore
                signal = Signal(
                    timestamp=curr_time,
                    signal=SignalType.BUY,
                    symbol=self.symbol,
                    price=curr_price,
                    reason=f"Oversold signal: z-score {curr_zscore:.2f}"
                )
                self.signals.append(signal)
                self.position = 1
            
            # Sell (long position): Z-score crosses zero (mean reversion)
            elif self.position == 1 and prev_zscore < 0 and curr_zscore >= 0:
                signal = Signal(
                    timestamp=curr_time,
                    signal=SignalType.SELL,
                    symbol=self.symbol,
                    price=curr_price,
                    reason=f"Mean reversion: z-score {curr_zscore:.2f} crossed zero"
                )
                self.signals.append(signal)
                self.position = 0
                self.entry_zscore = None
        
        return self.signals
    
    
    def get_signal_at_index(self, index: int) -> Optional[Signal]:
        if index < self.lookback_window or index >= len(self.data):
            return None
        
        prev_row = self.data.iloc[index - 1]
        curr_row = self.data.iloc[index]
        
        prev_zscore = prev_row['Z_Score']
        curr_zscore = curr_row['Z_Score']
        curr_price = curr_row['Close']
        curr_time = self.data.index[index]
        
        if pd.isna(prev_zscore) or pd.isna(curr_zscore):
            return None
        
        if curr_zscore < -self.zscore_threshold and self.position == 0:
            self.entry_zscore = curr_zscore
            self.position = 1
            return Signal(
                timestamp=curr_time,
                signal=SignalType.BUY,
                symbol=self.symbol,
                price=curr_price,
                reason=f"Oversold: z-score {curr_zscore:.2f}"
            )
        
        elif self.position == 1 and prev_zscore < 0 and curr_zscore >= 0:
            self.position = 0
            return Signal(
                timestamp=curr_time,
                signal=SignalType.SELL,
                symbol=self.symbol,
                price=curr_price,
                reason=f"Mean reversion: z-score {curr_zscore:.2f}"
            )
        
        return None
    
    
    def get_position_size(self) -> int:
        return self.position_size
    
    
    def summary(self) -> dict:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "total_signals": len(self.signals),
            "buy_signals": sum(1 for s in self.signals if s.signal == SignalType.BUY),
            "sell_signals": sum(1 for s in self.signals if s.signal == SignalType.SELL),
        }