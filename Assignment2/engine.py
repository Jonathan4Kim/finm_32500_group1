import random
import re
from data_loader import load_data
from models import Order, OrderError, ExecutionError, MarketDataPoint
import logging
import pandas as pd

class MarketSimulation:
    def __init__(self, cash_balance, strategies, order_retries=5, symbols=None):
        logging.basicConfig(filename='simulation.log', encoding='utf-8')
        self.cash_balance = cash_balance
        self.NAV_series = pd.Series()
        self.strategies = strategies
        self.signals = []
        self.__order_retries = order_retries
        self.portfolio = {}

        # Loads market data
        self.__market_data_df = load_data(symbols)
        # Removes special characters from column names
        self.__market_data_df.columns = self.__market_data_df.columns.str.replace('.', '_')


    def execute_order(self, order):
        # Check for order errors
        try:
            if order.quantity == 0 or order.quantity != int(order.quantity):
                raise OrderError(f"Order quantity must be a non-zero integer, order = {order}")
            elif not (order.symbol and order.quantity and order.price and order.status):
                raise OrderError(f"Order is missing attributes, order = {order}")
        except OrderError as e:
            logging.exception("OrderError thrown")
            order.symbol = "CANCELLED"
            return

        # Gets order details and updates portfolio
        symbol = order.symbol
        quantity = order.quantity
        price = order.price
        current_position = self.portfolio.get(symbol, {"quantity": 0, "avg_price": 0.0, "orders": []})
        current_position["avg_price"] = (current_position["avg_price"] * current_position["quantity"] + price * quantity) / (current_position["quantity"] + 1)
        current_position["quantity"] += quantity
        current_position["orders"].append(order)

        # Update portfolio and simulate occasional order submission failures
        for num_try in range(self.__order_retries):
            try:
                self.portfolio[symbol] = current_position
                self.cash_balance -= quantity * price
                order.status = "FILLED"
                break
            except ExecutionError as e:
                logging.exception("ExecutionError thrown")


    def run_simulation(self):
        # Gets market data for simulation
        print("Running simulation...")
        nav_history = []    # store NAV over time
        for i, market_data in enumerate(self.__market_data_df.itertuples()):
            if i % 100 == 0:
                print(f"Now processing timestamp #{i}: {market_data}")
            for symbol in self.__market_data_df.columns:
                # Skips symbols that have no data for timestamp
                if pd.isna(getattr(market_data, symbol)):
                    continue

                # Creates new MarketDataPoint
                data_point = MarketDataPoint(market_data.Index, symbol, getattr(market_data, symbol))

                # Generate all raw signals from strategies
                raw_signals = []
                for strategy in self.strategies:
                    raw_signals.append(strategy.generate_signals(data_point))

                # Find combined action
                action_count = {"BUY": 0, "SELL": 0, "HOLD": 0}
                for raw_signal in raw_signals:
                    action_count[raw_signal[0]] += 1
                sorted_counts = sorted(action_count, key=action_count.get, reverse=True)
                if action_count[sorted_counts[0]] != action_count[sorted_counts[1]]:
                    combined_action = sorted_counts[0]
                else:
                    combined_action = "HOLD"

                # Generate final signal and order object
                new_order = None
                if combined_action == "BUY":
                    size = 0.10 * self.cash_balance // data_point.price
                    final_signal = (combined_action, data_point.symbol, size, data_point.price)
                    self.signals.append(final_signal)
                    new_order = Order(final_signal[1], final_signal[2], final_signal[3], "OPEN")
                    self.execute_order(new_order)
                # make sure we don't sell when we have no position
                elif combined_action == "SELL" and self.portfolio.get(data_point.symbol, {"quantity": 0})["quantity"] > 0:
                    size = self.portfolio[data_point.symbol]["quantity"]
                    final_signal = (combined_action, data_point.symbol, size, data_point.price)
                    self.signals.append(final_signal)
                    new_order = Order(final_signal[1], -1*final_signal[2], final_signal[3], "OPEN")
                    self.execute_order(new_order)
                elif combined_action == "HOLD":
                    final_signal = (combined_action, data_point.symbol, 0, data_point.price)
                    self.signals.append(final_signal)

            # Adds NAV for current timestamp to history
            portfolio_value = sum(position['quantity'] * getattr(market_data, symbol) for symbol, position in self.portfolio.items())
            nav_history.append((market_data.Index, self.cash_balance + portfolio_value))

        # Packages and returns simulation NAV
        self.NAV_series = pd.Series([v for t, v in nav_history],index=[pd.to_datetime(t) for t, v in nav_history])  # ensure datetime index