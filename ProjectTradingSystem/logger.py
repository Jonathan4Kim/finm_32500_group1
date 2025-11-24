# logger.py
import json
import time
from pathlib import Path
from threading import Lock


class Logger:
    _instance = None
    _lock = Lock()


    def __new__(cls, filename="events.json"):
        """
        Ensure a single instance (Singleton).
        Thread-safe for multi-threaded OMS / Risk systems.
        """
        with cls._lock:
            # ensure instance hasn't been created yet
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance


    def __init__(self, filename="events.json"):
        if getattr(self, "_initialized", False):
            return

        self.filename = Path(filename)
        self.filename.touch(exist_ok=True)
        self._initialized = True
        self.entries = []


    def log(self, event_type: str, data: dict):
        print(f"{event_type} -> {data}")
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            "data": data
        }
        self.entries.append(entry)


    def save(self, output_path: str):
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(self.entries, out, indent=4)

        return output_path
