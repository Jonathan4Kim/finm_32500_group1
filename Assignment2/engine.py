
"""
market_simulation.py

This module defines the `MarketSimulation` class, which simulates the execution of trading strategies
over historical market data.

The simulator:
- Loads price and volume data using `load_data()` from the data_loader module
- Runs through each time step in the data
- Calls one or more strategy objects to generate trading signals (BUY, SELL, HOLD)
- Aggregates signals to decide on a final action
- Creates and executes simulated orders
- Tracks a portfolio and cash balance over time
- Records Net Asset Value (NAV) at each step

Class:
    MarketSimulation
        Simulates a portfolio given starting cash, strategies, and historical market data.

Key Methods:
    - run_simulation(): Executes the full backtest over all timestamps in the data
    - execute_order(order): Processes a simulated order, updates cash and portfolio
    - calc_position_size(timestamp, symbol, price, action): Computes the appropriate trade size
    - NAV_series: A pandas Series of the portfolio NAV over time

Dependencies:
    - pandas
    - numpy
    - logging
    - data_loader.load_data: loads price and volume market data
    - models.Order, OrderError, ExecutionError, MarketDataPoint

Example usage:
    from market_simulation import MarketSimulation
    from strategy import MyStrategy

    strategy = MyStrategy()
    sim = MarketSimulation(cash_balance=1_000_000, strategies=[strategy], symbols=["AAPL", "MSFT"])
    sim.run_simulation()
    sim.NAV_series.plot()  # Visualize NAV over time

Notes:
- The simulator respects a volume cap (ADV_limit) to restrict order sizes.
- Orders are retried in case of simulated execution errors (up to `order_retries` times).
- The simulation assumes trades are filled at historical closing prices.
"""
from data_loader import load_data
from models import Order, OrderError, ExecutionError, MarketDataPoint
import logging
import pandas as pd
import time

class MarketSimulation:
    def __init__(self, cash_balance, strategies, symbols=None, order_retries=5, adv_limit=0.10, transaction_cost=0.00):
        logging.basicConfig(filename='simulation.log', encoding='utf-8')
        self.cash_balance = cash_balance
        self.NAV_series = pd.Series()
        self.strategies = strategies
        self.signals = {}
        self.__order_retries = order_retries
        self.__adv_limit = adv_limit
        self.__transaction_cost = transaction_cost
        self.cur_portfolio = {}
        self.portfolio_history = []
        self.cash_history = []

        # Loads market data
        raw_market_data = load_data(tickers=symbols)
        self.__price_data_df = raw_market_data["Close"]
        self.__volume_data_df = raw_market_data["Volume"]

        # Removes special characters from column names
        self.__price_data_df.columns = self.__price_data_df.columns.str.replace('.', '_')
        self.__volume_data_df.columns = self.__volume_data_df.columns.str.replace('.', '_')


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
        current_position = self.cur_portfolio.get(symbol, {"quantity": 0, "avg_price": 0.0, "orders": []})
        net_quantity = current_position["quantity"] + quantity
        current_position["avg_price"] = (current_position["avg_price"] * current_position["quantity"] + price * quantity) / (current_position["quantity"] + quantity) if net_quantity != 0 else 0
        current_position["quantity"] += quantity
        current_position["orders"].append(order)

        # Update portfolio and simulate occasional order submission failures
        for num_try in range(self.__order_retries):
            try:
                self.cur_portfolio[symbol] = current_position
                self.cash_balance -= quantity * price + self.__transaction_cost * abs(quantity * price)
                order.status = "FILLED"
                return
            except ExecutionError as e:
                logging.exception("ExecutionError thrown")


    def run_simulation(self):
        start = time.time()
        # Gets markestart = time.time()t data for simulation
        print("Running simulation...")
        nav_history = []    # store NAV over time
        for i, market_data in enumerate(self.__price_data_df.itertuples()):
            if i % (self.__price_data_df.shape[0] // 10) == 0:
                print(f"Simulation {i / self.__price_data_df.shape[0]:.1%} complete...")
            for symbol in self.__price_data_df.columns:
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
                size = self.calc_position_size(data_point.timestamp, data_point.symbol, data_point.price, combined_action)
                final_signal = {"action": combined_action, "symbol": data_point.symbol, "size": size, "price": data_point.price}
                self.signals[market_data.Index] = self.signals.get(market_data.Index, []) + [final_signal]
                if size == 0:
                    continue
                if combined_action == "BUY":
                    self.execute_order(Order(final_signal["symbol"], final_signal["size"], final_signal["price"], "OPEN"))
                # make sure we don't sell when we have no position
                elif combined_action == "SELL" and self.cur_portfolio.get(data_point.symbol, {"quantity": 0})["quantity"] > 0:
                    self.execute_order(Order(final_signal["symbol"], -1*final_signal["size"], final_signal["price"], "OPEN"))

            # Adds NAV for current timestamp to history
            # TODO could calculate NAV in post to increase speed of sim
            portfolio_value = sum(position['quantity'] * getattr(market_data, symbol) for symbol, position in self.cur_portfolio.items())
            nav_history.append((market_data.Index, self.cash_balance + portfolio_value))
            self.portfolio_history.append(self.cur_portfolio)
            self.cash_history.append(self.cash_balance)

        # Packages simulation NAV
        self.NAV_series = pd.Series([v for t, v in nav_history],index=[pd.to_datetime(t) for t, v in nav_history])  # ensure datetime index

        print(f"Simulation took {(time.time() - start)/60:.2f} minutes")


    def calc_position_size(self, timestamp, symbol, price, action):
        # Limits buy size based on ADV or maximum possible size
        if action == "BUY":
            max_size = int(self.__adv_limit * self.__volume_data_df.loc[timestamp, symbol])
            possible_size = self.cash_balance // (price * (1+self.__transaction_cost))
            return min(max_size, possible_size)
        # Sells total position if possible
        elif action == "SELL" and self.cur_portfolio.get(symbol, {"quantity": 0})["quantity"] > 0:
            return self.cur_portfolio[symbol]["quantity"]
        return 0


    def calc_nav(self):
        nav_history = []
        for i, market_data in enumerate(self.__price_data_df.itertuples()):
            portfolio_value = sum(position['quantity'] * getattr(market_data, symbol) for symbol, position in self.portfolio_history[i].items())
            nav_history.append((market_data.Index, self.cash_history[i] + portfolio_value))

        return pd.Series([v for t, v in nav_history],index=[pd.to_datetime(t) for t, v in nav_history])