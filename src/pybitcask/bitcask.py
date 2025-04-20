"""Implementation of the Bitcask key-value store."""

# -*- coding: utf-8 -*-
import json
import mmap
import struct
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional


class Bitcask:
    """
    A log-structured hash table for fast key/value data storage.

    The Bitcask design provides high-performance operations by using a log-structured
    storage engine with an in-memory hash table of keys. This implementation follows
    the original Bitcask design while providing a Pythonic interface.
    """

    def __init__(self, directory: str):
        """
        Initialize a new Bitcask instance.

        Args:
        ----
            directory: The directory where data files will be stored.

        """
        self.data_dir = Path(directory)
        self.data_dir.mkdir(exist_ok=True)

        # In-memory index: key -> (file_id, value_size, value_pos, timestamp)
        self.index: Dict[str, tuple] = {}

        # Current active file for writing
        self.active_file: Optional[mmap.mmap] = None
        self.active_file_id: int = 0
        self.active_file_path: Optional[Path] = None

        # Lock for thread safety
        self._lock = threading.Lock()

        # Initialize or recover from existing data
        self._initialize()

    def _initialize(self):
        """Initialize or recover the database state."""
        # Find the latest data file
        data_files = sorted(self.data_dir.glob("*.data"))
        if data_files:
            self.active_file_id = int(data_files[-1].stem)
            self.active_file_path = data_files[-1]
            self._open_active_file()
            self._build_index()
        else:
            self._create_new_data_file()

    def _create_new_data_file(self):
        """Create a new data file for writing."""
        self.active_file_id += 1
        self.active_file_path = self.data_dir / f"{self.active_file_id}.data"
        self.active_file_path.touch()
        self._open_active_file()

    def _open_active_file(self):
        """Open the active file for writing."""
        if self.active_file:
            self.active_file.close()
        self.active_file = open(self.active_file_path, "a+b")
        self.active_file.seek(0, 2)  # Seek to end

    def _build_index(self):
        """Build the in-memory index from existing data files."""
        self.index.clear()
        for data_file in sorted(self.data_dir.glob("*.data")):
            with open(data_file, "rb") as f:
                while True:
                    # Read header
                    header = f.read(
                        16
                    )  # 4 bytes for key_size, 4 for value_size, 8 for timestamp
                    if not header:
                        break

                    key_size, value_size, timestamp = struct.unpack(">IIQ", header)
                    key = f.read(key_size).decode("utf-8")
                    value_pos = f.tell()
                    f.seek(value_size, 1)  # Skip value

                    # Update index with latest version
                    self.index[key] = (
                        int(data_file.stem),
                        value_size,
                        value_pos,
                        timestamp,
                    )

    def put(self, key: str, value: Any) -> None:
        """Store a key-value pair."""
        with self._lock:
            # Serialize value to JSON
            value_bytes = json.dumps(value).encode("utf-8")

            # Prepare record
            key_bytes = key.encode("utf-8")
            timestamp = int(time.time() * 1000)  # Current time in milliseconds

            # Write record: header (key_size, value_size, timestamp) + key + value
            record = struct.pack(">IIQ", len(key_bytes), len(value_bytes), timestamp)
            record += key_bytes + value_bytes

            # Write to active file
            self.active_file.write(record)
            self.active_file.flush()

            # Update index
            self.index[key] = (
                self.active_file_id,
                len(value_bytes),
                self.active_file.tell() - len(value_bytes),
                timestamp,
            )

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        if key not in self.index:
            return None

        file_id, value_size, value_pos, _ = self.index[key]
        file_path = self.data_dir / f"{file_id}.data"

        with open(file_path, "rb") as f:
            f.seek(value_pos)
            value_bytes = f.read(value_size)
            return json.loads(value_bytes.decode("utf-8"))

    def delete(self, key: str) -> None:
        """Delete a key-value pair."""
        with self._lock:
            if key in self.index:
                # Write a tombstone record
                tombstone = struct.pack(
                    ">IIQ", len(key.encode("utf-8")), 0, int(time.time() * 1000)
                )
                tombstone += key.encode("utf-8")

                self.active_file.write(tombstone)
                self.active_file.flush()

                del self.index[key]

    def close(self):
        """Close the database."""
        if self.active_file:
            self.active_file.close()
            self.active_file = None
