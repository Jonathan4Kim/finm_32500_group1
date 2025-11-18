# order_manager.py
import csv
import json
import socket
import threading
import time
from dataclasses import dataclass, asdict
from itertools import count
from typing import Optional, Dict, Any

from order import Order
from risk_engine import RiskEngine
from logger import Logger
from matching_engine import MatchingEngine as me


HOST = "127.0.0.1"
PORT = 62000
BACKLOG = 10
RECV_BYTES = 4096
MESSAGE_DELIMITER = b"*"


class OrderManagerServer:
    """
    TCP server that accepts Order messages over a socket.
    Each message is a JSON object terminated by MESSAGE_DELIMITER (b"*").
    """

    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self._srv_sock: Optional[socket.socket] = None
        self._stop_event = threading.Event()
        self._threads = []
        self._order_id_counter = count(1)  # server-side order ids
        self._order_id_lock = threading.Lock()
        self._risk_engine = RiskEngine()
        self.orders = []


    # Public API
    def start(self):
        self._srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv_sock.bind((self.host, self.port))
        self._srv_sock.listen(BACKLOG)
        Logger().log(
            "OrderManager",
            {"reason": f"listening on {self.host}:{self.port}"}
        )

        try:
            while not self._stop_event.is_set():
                self._srv_sock.settimeout(1.0)
                try:
                    conn, addr = self._srv_sock.accept()
                except socket.timeout:
                    continue
                t = threading.Thread(
                    target=self._handle_client, args=(conn, addr), daemon=True
                )
                t.start()
                self._threads.append(t)
        except KeyboardInterrupt:
            Logger().log(
                "KeyboardInterrupt",
                {"reason": f"stopping OrderManager..."}
            )
        finally:
            self.stop()

    def stop(self):
        self._stop_event.set()
        if self._srv_sock:
            try:
                self._srv_sock.close()
            except Exception:
                pass
            self._srv_sock = None
        for t in self._threads:
            t.join(timeout=1.0)
        Logger().log(
            "OrderManager",
            {"reason": f"OrderManager stopped"}
        )

    # Internals
    def _handle_client(self, conn: socket.socket, addr):
        name = f"{addr[0]}:{addr[1]}"
        Logger().log(
            "OrderManager",
            {"reason": f"Client connected: {name}"}
        )
        buffer = b""
        try:
            with conn:
                conn.settimeout(2.0)
                while not self._stop_event.is_set():
                    try:
                        chunk = conn.recv(RECV_BYTES)
                    except socket.timeout:
                        continue
                    if not chunk:
                        break
                    buffer += chunk

                    # Process all complete frames in buffer
                    while True:
                        idx = buffer.find(MESSAGE_DELIMITER)
                        if idx == -1:
                            break  # no full frame yet
                        frame = buffer[:idx]
                        buffer = buffer[idx + len(MESSAGE_DELIMITER):]
                        if not frame.strip():
                            continue
                        self._process_order_frame(frame, conn)
        except Exception as e:
            Logger().log(
                "OrderManager",
                {"reason": f"Client {name} error: {e}"}
            )
        finally:
            Logger().log(
                "OrderManager",
                {"reason": f"Client disconnected: {name}"}
            )

    def _process_order_frame(self, frame: bytes, conn: socket.socket):
        # Decode JSON
        try:
            payload = json.loads(frame.decode("utf-8"))
        except json.JSONDecodeError as e:
            Logger().log(
                "OrderManager",
                {"reason": f"Bad JSON payload: {e} | raw={frame!r}"}
            )
            self._send_ack(conn, ok=False, msg="bad_json")
            return

        # Validate and normalize
        try:
            order = Order.from_dict(payload)
        except ValueError as e:
            Logger().log(
                "OrderManager",
                {"reason": f"Invalid order: {e} | payload={payload}"}
            )
            self._send_ack(conn, ok=False, msg=str(e))
            return

        # Assign server-side order id if missing
        if order.id is None:
            with self._order_id_lock:
                order.id = next(self._order_id_counter)

        # Check if order passes checks
        if self._risk_engine.check(order):
            self._risk_engine.update_position(order)
        else:
            Logger().log(
                "OrderManager",
                {"reason": f"Order failed risk checks | payload={payload}"}
            )
            self._send_ack(conn, ok=False)
            return

        # "Execute" the order (here we just log it)
        Logger().log(
            "OrderManager",
            {"reason": f"Sending Order {order.id}: {order.side} {order.qty} {order.symbol} @ {order.price:.2f}"}
        )
        response = me.simulate_execution(order)
        if response["status"] == "CANCELLED":
            Logger().log(
                "OrderManager",
                {"reason": f"Order Cancelled {order.id}: {order.side} {order.qty} {order.symbol} @ {order.price:.2f}"}
            )
        elif response["status"] == "PARTIAL":
            self.orders.append(order)
            Logger().log(
                "OrderManager",
                {"reason": f"Order Partially Filled {order.id}: {order.side} {response['qty']} {order.symbol} @ {order.price:.2f}"}
            )
        elif response["status"] == "FILLED":
            self.orders.append(order)
            Logger().log(
                "OrderManager",
                {"reason": f"Order Filled {order.id}: {order.side} {order.qty} {order.symbol} @ {order.price:.2f}"}
            )

        # Send ACK back
        self._send_ack(conn, ok=True, order=order)


    def _send_ack(self, conn: socket.socket, ok: bool, order: Optional[Order] = None, msg: str = ""):
        ack = {"ok": ok}
        if order is not None:
            ack["order"] = asdict(order)
        if msg:
            ack["msg"] = msg
        try:
            conn.sendall(json.dumps(ack).encode("utf-8") + MESSAGE_DELIMITER)
        except Exception:
            pass

    def save_orders_to_csv(self, filepath: str = "order_log.csv"):
        """
        Save a list of Order objects to a CSV file.

        CSV columns:
            id, side, symbol, qty, price, ts
        """

        # Choose column order
        fieldnames = ["id", "side", "symbol", "qty", "price", "ts"]

        # Check if file exists to determine if we should write the header
        try:
            file_exists = open(filepath).close() is None
        except FileNotFoundError:
            file_exists = False

        with open(filepath, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # If file doesn't exist, write header first
            if not file_exists:
                writer.writeheader()

            # Write each order
            for i, order in enumerate(self.orders):
                row = {
                    "id": order.id if order.id is not None else i,
                    "side": order.side,
                    "symbol": order.symbol,
                    "qty": order.qty,
                    "price": order.price,
                    "ts": order.ts if order.ts is not None else None,
                }
                writer.writerow(row)



def run_ordermanager(host: str = HOST, port: int = PORT):
    server = OrderManagerServer(host, port)
    server.start()
    Logger().save("order_manager_events.json")
    server.save_orders_to_csv()


if __name__ == "__main__":
    run_ordermanager()