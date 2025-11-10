import json
import socket
import threading
import time
import pytest

from order_manager import OrderManagerServer, MESSAGE_DELIMITER

HOST = "127.0.0.1"
PORT = 65000  # use a test port


@pytest.fixture(scope="module")
def order_manager_server():
    """Start the OrderManager server in a background thread for testing."""
    server = OrderManagerServer(host=HOST, port=PORT)
    t = threading.Thread(target=server.start, daemon=True)
    t.start()
    # Give the server a moment to start listening
    time.sleep(0.5)
    yield server
    server.stop()


def send_order(order_dict):
    """Utility: send a single order and return the server's ACK."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        payload = json.dumps(order_dict).encode("utf-8") + MESSAGE_DELIMITER
        s.sendall(payload)

        # Receive until delimiter
        data = b""
        while MESSAGE_DELIMITER not in data:
            chunk = s.recv(1024)
            if not chunk:
                break
            data += chunk
        frame, *_ = data.split(MESSAGE_DELIMITER, 1)
        return json.loads(frame.decode("utf-8"))


# Core functional tests

def test_valid_buy_order_ack(order_manager_server):
    """Server should accept a valid BUY order and return ok=True."""
    order = {"side": "BUY", "symbol": "AAPL", "qty": 10, "price": 172.5}
    ack = send_order(order)
    assert ack["ok"] is True
    assert "order" in ack
    assert ack["order"]["symbol"] == "AAPL"
    assert ack["order"]["side"] == "BUY"
    assert ack["order"]["qty"] == 10
    assert ack["order"]["price"] == 172.5
    assert isinstance(ack["order"]["id"], int)


def test_valid_sell_order_ack(order_manager_server):
    """Server should accept a valid SELL order."""
    order = {"side": "SELL", "symbol": "MSFT", "qty": 5, "price": 320.1}
    ack = send_order(order)
    assert ack["ok"] is True
    assert ack["order"]["side"] == "SELL"


def test_invalid_order_missing_field(order_manager_server):
    """Missing required fields should result in ok=False."""
    bad_order = {"side": "BUY", "qty": 10, "price": 100.0}  # missing symbol
    ack = send_order(bad_order)
    assert ack["ok"] is False
    assert "msg" in ack
    assert "symbol" in ack["msg"]


def test_invalid_json_payload(order_manager_server):
    """Non-JSON data should trigger ok=False."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b"not-json*" )
        data = b""
        while MESSAGE_DELIMITER not in data:
            data += s.recv(1024)
        frame, *_ = data.split(MESSAGE_DELIMITER, 1)
        ack = json.loads(frame.decode("utf-8"))
        assert ack["ok"] is False
        assert ack["msg"] == "bad_json"


def test_multiple_clients_concurrent(order_manager_server):
    """Simulate multiple strategy clients sending orders concurrently."""
    orders = [
        {"side": "BUY", "symbol": "AAPL", "qty": 10, "price": 170.0},
        {"side": "SELL", "symbol": "TSLA", "qty": 4, "price": 250.5},
        {"side": "BUY", "symbol": "MSFT", "qty": 8, "price": 330.2},
    ]

    results = []

    def worker(order):
        ack = send_order(order)
        results.append(ack)

    threads = [threading.Thread(target=worker, args=(o,)) for o in orders]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == len(orders)
    for ack in results:
        assert ack["ok"] is True
        assert "order" in ack
        assert ack["order"]["id"] is not None


def test_order_ids_unique_and_incrementing(order_manager_server):
    """Order IDs should be unique and monotonic across clients."""
    ids = []
    for _ in range(3):
        ack = send_order({"side": "BUY", "symbol": "GOOG", "qty": 1, "price": 1000.0})
        ids.append(ack["order"]["id"])
    assert ids == sorted(set(ids)), "Order IDs should be unique and increasing"
