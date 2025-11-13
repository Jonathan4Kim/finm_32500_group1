# main.py
from fix_parser import FixParser as fix
from order import Order, OrderState
from risk_engine import RiskEngine
from logger import Logger

risk = RiskEngine()
log = Logger()

raw = "8=FIX.4.2|35=D|55=AAPL|54=1|38=500|40=2|10=128"
msg = fix.parse(raw)

order = Order(msg["55"], int(msg["38"]), msg["54"])
log.log("OrderCreated", msg)

try:
    risk.check(order)
    order.transition(OrderState.ACKED)
    risk.update_position(order)
    order.transition(OrderState.FILLED)
    log.log("OrderFilled", {"symbol": order.symbol, "qty": order.qty})
except ValueError as e:
    order.transition(OrderState.REJECTED)
    log.log("OrderRejected", {"reason": str(e)})

log.save("events.json")