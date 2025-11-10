"""Connectivity-related tests for gateway helpers."""

import csv

import pytest
from gateway import send_symbol_list, load_data


class DummyClient:
    """Simple socket stand-in that records bytes sent."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent_data = []

    def send(self, payload: bytes):
        if self.should_fail:
            raise OSError("simulated failure")
        self.sent_data.append(payload)
        return len(payload)


def test_send_symbol_list_formats_payload_with_delimiter():
    client = DummyClient()
    symbols = ["AAPL", "MSFT", "SPY"]
    success = send_symbol_list(client, symbols, delimiter=b"*")
    assert success is True
    assert client.sent_data == [b"SYMBOLS|AAPL,MSFT,SPY*"]


def test_send_symbol_list_returns_false_when_socket_errors():
    client = DummyClient(should_fail=True)
    success = send_symbol_list(client, ["AAPL"], delimiter=b"*")
    assert success is False
    assert client.sent_data == []


def test_load_data_returns_unique_symbols_in_file_order():
    data_points, symbols, sent_points = load_data()
    assert len(data_points) == len(sent_points) and len(data_points) > 0

    expected_symbols = []
    seen = set()
    first_row = None
    with open("market_data.csv", newline="") as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # skip header
        for row in reader:
            if first_row is None:
                first_row = row
            symbol = row[1]
            if symbol not in seen:
                expected_symbols.append(symbol)
                seen.add(symbol)

    assert symbols == expected_symbols
    price_fields = data_points[0].decode().split("*")
    assert price_fields[0] == first_row[0]
    assert price_fields[1] == first_row[1]
    assert price_fields[2] == first_row[2]

    sent_fields = sent_points[0].decode().split("*")
    assert sent_fields[:2] == price_fields[:2]
    assert len(sent_fields[2]) > 0
