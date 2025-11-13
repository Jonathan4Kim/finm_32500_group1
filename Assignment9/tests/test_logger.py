import json

import pytest

import logger as logger_module
from logger import Logger


@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure each test works with a fresh Logger singleton."""
    Logger._instance = None
    yield
    Logger._instance = None


def test_logger_singleton_reuses_instance(tmp_path):
    Logger._instance = None
    log_path = tmp_path / "events.json"
    first = Logger(log_path)
    second = Logger(log_path)

    assert first is second
    assert first.filename == log_path


def test_log_adds_timestamped_entry(tmp_path, monkeypatch):
    log_path = tmp_path / "events.json"
    logger = Logger(log_path)
    monkeypatch.setattr(
        logger_module.time, "strftime", lambda fmt: "2024-01-01 00:00:00"
    )

    logger.log("TestEvent", {"key": "value"})

    assert logger.entries == [
        {
            "timestamp": "2024-01-01 00:00:00",
            "event": "TestEvent",
            "data": {"key": "value"},
        }
    ]


def test_save_writes_entries_to_disk(tmp_path):
    log_path = tmp_path / "events.json"
    logger = Logger(log_path)
    logger.entries = [
        {"timestamp": "2024-01-01 00:00:00", "event": "E", "data": {"n": 1}}
    ]

    output_path = tmp_path / "out.json"
    output = logger.save(output_path)

    assert output == output_path
    with open(output_path, encoding="utf-8") as saved:
        assert json.load(saved) == logger.entries
