"""Implementation of the Bitcask key-value store."""

# -*- coding: utf-8 -*-
import logging
import mmap
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .config import config
from .formats import (
    DataFormat,
    JsonFormat,
    ProtoFormat,
    get_format_by_identifier,
)

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Bitcask:
    """A log-structured hash table for fast key/value data storage.

    The Bitcask design provides high-performance operations by using a log-structured
    storage engine with an in-memory hash table of keys. This implementation follows
    the original Bitcask design while providing a Pythonic interface.
    """

    # Size of format identifier in bytes
    FORMAT_ID_SIZE = 1

    def __init__(
        self,
        directory: Optional[str] = None,
        debug_mode: Optional[bool] = None,
    ):
        """Initialize a new Bitcask instance.

        Args:
        ----
            directory: The directory where data files will be stored.
                      If None, uses the configured default directory.
            debug_mode: If True, writes data in human-readable format.
                       If None, uses the configured debug mode.

        """
        self.data_dir = config.get_data_dir(directory)
        self.debug_mode = (
            debug_mode if debug_mode is not None else config.get_debug_mode()
        )
        self.format: DataFormat = JsonFormat() if self.debug_mode else ProtoFormat()
        logger.debug("Initialized with format: %s", self.format.__class__.__name__)

        # In-memory index: key -> (file_id, value_size, value_pos, timestamp)
        self.index: Dict[str, dict] = {}

        # Current active file for writing
        self.active_file: Optional[mmap.mmap] = None
        self.active_file_id: int = 0
        self.active_file_path: Optional[Path] = None
        self.active_file_entry_count: int = 0
        self.active_file_last_write: Optional[datetime] = None

        # Lock for thread safety
        self._lock = threading.Lock()

        # Create data directory if it doesn't exist
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.error("Permission denied creating data directory: %s", e)
            raise
        except Exception as e:
            logger.error("Error creating data directory: %s", e)
            raise

        # Initialize or recover from existing data
        self._initialize()

    def _initialize(self):
        """Initialize or recover the database state."""
        # Find the latest data file
        data_files = sorted(self.data_dir.glob("data_*.db"))
        if data_files:
            self.active_file_id = int(data_files[-1].stem.split("_")[1])
            self.active_file_path = data_files[-1]
            logger.debug("Found existing data file: %s", self.active_file_path)
            self._open_active_file()
            self._build_index()
        else:
            logger.debug("No existing data files found, creating new one")
            self.active_file_id = 0  # Start from 0
            self._create_new_data_file()

    def _create_new_data_file(self):
        """Create a new data file for writing."""
        if self.active_file is not None:
            self.active_file.close()

        self.active_file_id += 1
        self.active_file_path = self.data_dir / f"data_{self.active_file_id}.db"
        self.active_file_path.touch()
        self._open_active_file()

        # Write format identifier at the start of the file
        identifier = self.format.get_format_identifier()
        logger.debug("Writing format identifier %r to new file", identifier)
        self.active_file.write(identifier)
        self.active_file.flush()
        self.active_file_entry_count = 0
        self.active_file_last_write = datetime.now()

    def _open_active_file(self):
        """Open the active file for writing."""
        if self.active_file:
            self.active_file.close()
        self.active_file = open(self.active_file_path, "a+b")
        self.active_file.seek(0, 2)  # Seek to end
        logger.debug(
            "Opened active file: %s, size: %d",
            self.active_file_path,
            self.active_file.tell(),
        )

    def _detect_format(self, data_file: Path) -> DataFormat:
        """Detect the format of a data file."""
        try:
            with open(data_file, "rb") as f:
                # Read format identifier (first byte)
                identifier = f.read(self.FORMAT_ID_SIZE)
                if not identifier:
                    # Empty file, use current format
                    logger.debug(
                        "Empty file %s, using current format: %s",
                        data_file,
                        self.format.__class__.__name__,
                    )
                    return self.format

                # Try to detect format from identifier
                try:
                    format = get_format_by_identifier(identifier)
                    logger.debug(
                        "Detected format %s for file %s",
                        format.__class__.__name__,
                        data_file,
                    )
                    return format
                except ValueError:
                    # If format detection fails, use current format
                    logger.warning(
                        "Could not detect format for file %s, using current format: %s",
                        data_file,
                        self.format.__class__.__name__,
                    )
                    return self.format
        except Exception as e:
            logger.error("Error detecting format for file %s: %s", data_file, e)
            return self.format

    def _build_index(self) -> None:
        """Build the in-memory index from data files."""
        self.index.clear()
        self.active_file = None
        self.active_file_id = 0

        # Get all data files
        data_files = sorted(
            [
                f
                for f in os.listdir(self.data_dir)
                if f.startswith("data_") and f.endswith(".db")
            ]
        )

        if not data_files:
            # No data files exist, create a new one
            self._create_new_data_file()
            return

        # Process each data file
        for filename in data_files:
            file_path = os.path.join(self.data_dir, filename)
            file_id = int(filename.split("_")[1].split(".")[0])
            with open(file_path, "rb") as f:
                # Read format identifier
                format_byte = f.read(1)
                if not format_byte:
                    continue

                format = get_format_by_identifier(format_byte)
                if not format:
                    logger.warning(f"Unknown format in {filename}, skipping")
                    continue

                # Read records
                while True:
                    try:
                        key, value, timestamp, record_size, is_tombstone = (
                            format.read_record(f)
                        )
                        if key is None:  # End of file
                            break

                        if is_tombstone:
                            # Remove from index if it exists
                            if key in self.index:
                                del self.index[key]
                            continue

                        # Update index only if this is the latest record for the key
                        current_entry = self.index.get(key)
                        if (
                            current_entry is None
                            or current_entry["timestamp"] < timestamp
                        ):
                            self.index[key] = {
                                "file_id": file_id,
                                "value_size": len(str(value).encode()),
                                "value_pos": f.tell() - record_size,
                                "timestamp": timestamp,
                            }
                    except Exception as e:
                        logger.error(f"Error reading record from {filename}: {e}")
                        break

        # Set active file to the latest one
        if data_files:
            self.active_file_id = int(data_files[-1].split("_")[1].split(".")[0])
            self.active_file_path = self.data_dir / data_files[-1]
            self._open_active_file()
        else:
            self._create_new_data_file()

    def put(self, key: str, value: Any) -> None:
        """Store a key-value pair."""
        with self._lock:
            if self.active_file is None:
                self._create_new_data_file()

            timestamp = int(time.time() * 1000)  # Current time in milliseconds
            record = self.format.encode_record(key, value, timestamp)

            # Write to active file
            record_pos = self.active_file.tell()
            self.active_file.write(record)
            self.active_file.flush()  # Ensure data is written to disk

            # Update entry count and last write time
            self.active_file_entry_count += 1
            self.active_file_last_write = datetime.now()

            # Update index with current file info
            self.index[key] = {
                "file_id": self.active_file_id,
                "value_size": len(str(value).encode()),
                "value_pos": record_pos,
                "timestamp": timestamp,
            }
            logger.debug(
                "Wrote record: key=%s, pos=%d, size=%d",
                key,
                record_pos,
                len(record),
            )

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        with self._lock:
            if key not in self.index:
                return None

            entry = self.index[key]
            file_path = self.data_dir / f"data_{entry['file_id']}.db"

            if not file_path.exists():
                logger.error(f"Data file not found: {file_path}")
                return None

            try:
                with open(file_path, "rb") as f:
                    # Read format identifier
                    format_byte = f.read(1)
                    if not format_byte:
                        return None

                    format = get_format_by_identifier(format_byte)
                    if not format:
                        logger.warning(f"Unknown format in {file_path}")
                        return None

                    # Seek to value position
                    f.seek(entry["value_pos"])
                    key, value, _, _, is_tombstone = format.read_record(f)
                    if is_tombstone:
                        # Remove from index if it's a tombstone
                        del self.index[key]
                        return None
                    return value

            except Exception as e:
                logger.error(f"Error reading value for key {key}: {e}")
                return None

    def list_keys(self) -> list[str]:
        """List all keys in the database."""
        return list(self.index.keys())

    def delete(self, key: str) -> bool:
        """Delete a key-value pair.

        Returns
        -------
            bool: True if the key was deleted, False if the key was not found

        """
        with self._lock:
            if key not in self.index:
                return False

            # Ensure we have an active file
            if self.active_file is None:
                self._create_new_data_file()

            timestamp = int(time.time() * 1000)
            tombstone = self.format.encode_tombstone(key, timestamp)

            # Write tombstone and ensure it's flushed to disk
            self.active_file.write(tombstone)
            self.active_file.flush()
            os.fsync(self.active_file.fileno())

            # Remove from index
            del self.index[key]
            logger.debug("Deleted key: %s", key)
            return True

    def batch_write(self, data: Dict[str, Any]) -> None:
        """Write multiple key-value pairs in a single operation."""
        with self._lock:
            timestamp = int(time.time() * 1000)  # Current time in milliseconds
            for key, value in data.items():
                record = self.format.encode_record(key, value, timestamp)

                # Write to active file
                record_pos = self.active_file.tell()
                self.active_file.write(record)

                # Update index
                self.index[key] = {
                    "file_id": self.active_file_id,
                    "value_size": len(str(value).encode()),
                    "value_pos": record_pos,
                    "timestamp": timestamp,
                }
                logger.debug(
                    "Batch wrote record: key=%s, pos=%d, size=%d",
                    key,
                    record_pos,
                    len(record),
                )

            # Flush all writes at once
            self.active_file.flush()
            self.active_file_entry_count += len(data)
            self.active_file_last_write = datetime.now()

    def close(self):
        """Close the database."""
        if self.active_file:
            self.active_file.close()
            self.active_file = None
            logger.debug("Closed database")

    def clear(self) -> None:
        """Delete all data and start fresh."""
        with self._lock:
            # Close any open files
            if self.active_file:
                self.active_file.close()
                self.active_file = None

            # Delete all data files
            for data_file in self.data_dir.glob("data_*.db"):
                data_file.unlink()

            # Clear the index
            self.index.clear()

            # Reset file counter and create new empty database
            self.active_file_id = 0
            self._create_new_data_file()
            logger.debug("Database cleared and reset")
