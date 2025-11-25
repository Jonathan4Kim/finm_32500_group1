# ProjectTradingSystem

A modular algorithmic trading system designed for both simulated and live execution. This framework supports market data ingestion, order management, backtesting, risk evaluation, and execution routing — using a clean architecture optimized for quantitative trading research and real-time deployment.

---

## 🔄 System Flow (Live Trading Pipeline)

This is the real execution flow used in live trading mode:

1. Pulls live market data from Alpaca
2. Saves each received bar to CSV in `/data`
3. Converts each bar into MDP (internal Model Data Protocol)
4. Streams MDP objects to the Strategy module
5. Strategy generates an order signal
6. Order is passed to Order Manager
7. Order Manager converts to an Alpaca order format
8. Order Manager submits as a `LimitOrder`
9. Order executes in the Alpaca paper trading account

This architecture provides realistic market conditions with controlled execution transparency.

---

## 🚀 Features

* Real-time & historical market data support
* Simulated and live trading modes
* CSV data archiving
* Standardized internal MDP data format
* Modular strategy and execution logic
* Full lifecycle order tracking
* Integrated risk control

---

## 📦 Repository Structure

```
ProjectTradingSystem/
│
├── data/                
├── reports/             
├── tests/               
│
├── alpaca_env_util.py    
├── backtester.py         
├── data_client.py        
├── events.json           
├── gateway.py            
├── logger.py             
├── main.py               
├── main_simulated.py     
├── matching_engine.py    
├── order.py              
├── order_manager.py      
├── orderbook.py          
├── risk_engine.py        
└── strategy.py           
```

---

## 🔧 Setup Instructions

### Clone repository

```
git clone https://github.com/Jonathan4Kim/finm_32500_group1.git
cd finm_32500_group1/ProjectTradingSystem
```

### Create environment

```
python3 -m venv env
source env/bin/activate       # Mac/Linux
env\Scripts\activate          # Windows
```

### Install dependencies

```
pip install -r requirements.txt
```

---

## 🔑 Alpaca API Configuration

```
export APCA_API_KEY_ID=your_key
export APCA_API_SECRET_KEY=your_secret
export APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

Used by `alpaca_env_util.py`.

---

## 🏃 Running the System

### Simulated trading mode:

```
python main_simulated.py
```

### Live paper-trading mode:

```
python main.py
```

---

## 📜 Module Descriptions

### `data_client.py`

* Connects to Alpaca data feed
* Saves raw bars to CSV
* Converts to MDP format

### `strategy.py`

* Receives MDP
* Computes trading signal
* Creates Order object

### `order_manager.py`

* Takes internal order
* Converts to Alpaca order format
* Submits Limit Order to Alpaca

### `matching_engine.py`

* (Simulated mode)
* Emulates exchange execution
* Maintains orderbook

### `risk_engine.py`

* Validates orders
* Exposure limits / risk checks

### `gateway.py`

* Routes orders to:

  * Alpaca (live)
  * MatchingEngine (simulated)

---

## 🧪 Running Tests

```
pytest
```

---

## 🛡️ Disclaimer

This system is intended for academic and research use only and should not be used for production financial trading without appropriate validation, supervision, and regulatory compliance.
