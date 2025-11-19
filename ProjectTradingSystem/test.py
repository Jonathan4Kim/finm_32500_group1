"""
Standalone test for strategies - no dependencies on OrderManager, etc.
Tests if strategies can load data and generate signals correctly.
"""

import os
from strategy import MAStrategy, MomentumStrategy, StatisticalSignalStrategy


def test_strategy(strategy_class, strategy_name, symbol, csv_file):
    """Test a single strategy."""
    print(f"\n{'='*70}")
    print(f"Testing: {strategy_name}")
    print(f"{'='*70}")
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"ERROR: File not found - {csv_file}")
        return False
    
    try:
        # Instantiate strategy
        strategy = strategy_class(symbol=symbol, position_size=100)
        print(f"✓ Strategy instantiated")
        
        # Load data
        data = strategy.load_data(csv_file)
        print(f"✓ Data loaded: {len(data)} rows")
        print(f"  Columns: {list(data.columns)}")
        
        # Generate signals
        signals = strategy.generate_signals()
        print(f"✓ Signals generated: {len(signals)} total")
        
        # Print summary
        summary = strategy.summary()
        print(f"\nStrategy Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Show sample signals
        if signals:
            print(f"\nFirst 5 signals:")
            for i, sig in enumerate(signals[:5], 1):
                print(f"  {i}. {sig.timestamp} | {sig.signal.value} @ {sig.price:.2f} | {sig.reason}")
        else:
            print(f"WARNING: No signals generated")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("STRATEGY TESTING - STANDALONE")
    print(f"{'='*70}\n")
    
    # Configuration
    data_dir = "cleaned_data"
    test_symbol = "AAPL"
    test_file = f"{data_dir}/{test_symbol}_cleaned.csv"
    
    # Test all three strategies
    strategies = [
        (MAStrategy, "MA Crossover Strategy"),
        (MomentumStrategy, "Momentum Strategy"),
        (StatisticalSignalStrategy, "Statistical Signal Strategy"),
    ]
    
    results = []
    for strategy_class, strategy_name in strategies:
        success = test_strategy(strategy_class, strategy_name, test_symbol, test_file)
        results.append((strategy_name, success))
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    for name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n✓ All strategies working correctly!")
    else:
        print("\n✗ Some strategies failed")
    
    return all_passed


if __name__ == "__main__":
    main()