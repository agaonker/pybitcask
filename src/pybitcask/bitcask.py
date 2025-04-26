"""Implementation of the Bitcask key-value store."""

# -*- coding: utf-8 -*-
import logging
import mmap
import struct
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .formats import BinaryFormat, DataFormat, JsonFormat, get_format_by_identifier

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Bitcask:
    """
    A log-structured hash table for fast key/value data storage.

    The Bitcask design provides high-performance operations by using a log-structured
    storage engine with an in-memory hash table of keys. This implementation follows
    the original Bitcask design while providing a Pythonic interface.
    """

    # Size of format identifier in bytes
    FORMAT_ID_SIZE = 1

    def __init__(self, directory: str, debug_mode: bool = False):
        """
        Initialize a new Bitcask instance.

        Args:
        ----
            directory: The directory where data files will be stored.
            debug_mode: If True, writes data in human-readable format.

        """
        self.data_dir = Path(directory)
        self.data_dir.mkdir(exist_ok=True)
        self.debug_mode = debug_mode
        self.format: DataFormat = JsonFormat() if debug_mode else BinaryFormat()
        logger.debug("Initialized with format: %s", self.format.__class__.__name__)

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
            logger.debug("Found existing data file: %s", self.active_file_path)
            self._open_active_file()
            self._build_index()
        else:
            logger.debug("No existing data files found, creating new one")
            self._create_new_data_file()

    def _create_new_data_file(self):
        """Create a new data file for writing."""
        self.active_file_id += 1
        self.active_file_path = self.data_dir / f"{self.active_file_id}.data"
        self.active_file_path.touch()
        self._open_active_file()
        # Write format identifier at the start of the file
        identifier = self.format.get_format_identifier()
        logger.debug("Writing format identifier %r to new file", identifier)
        self.active_file.write(identifier)
        self.active_file.flush()

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

    def _build_index(self):
        """Build the in-memory index from existing data files."""
        self.index.clear()
        for data_file in sorted(self.data_dir.glob("*.data")):
            format = self._detect_format(data_file)
            logger.debug(
                "Building index for file %s with format %s",
                data_file,
                format.__class__.__name__,
            )
            with open(data_file, "rb") as f:
                # Skip format identifier
                f.seek(self.FORMAT_ID_SIZE)
                while True:
                    try:
                        if isinstance(format, JsonFormat):
                            # Read line by line for JSON format
                            line = f.readline()
                            if not line:
                                break
                            try:
                                key, _, timestamp = format.decode_record(line)
                                value_pos = f.tell() - len(line)
                                value_size = len(line)
                                self.index[key] = (
                                    int(data_file.stem),
                                    value_size,
                                    value_pos,
                                    timestamp,
                                )
                                logger.debug(
                                    "Indexed JSON record: key=%s, pos=%d, size=%d",
                                    key,
                                    value_pos,
                                    value_size,
                                )
                            except Exception as e:
                                logger.warning("Failed to decode JSON record: %s", e)
                                continue
                        else:
                            # Read binary format
                            record_pos = (
                                f.tell()
                            )  # Get position before reading anything
                            header = f.read(16)
                            if not header or len(header) < 16:
                                break
                            try:
                                key_size, value_size, timestamp = struct.unpack(
                                    ">IIQ", header
                                )
                                key = f.read(key_size).decode("utf-8")
                                # Skip value
                                f.seek(value_size, 1)
                                # Total record size is header + key + value
                                total_size = 16 + key_size + value_size
                                self.index[key] = (
                                    int(data_file.stem),
                                    total_size,
                                    record_pos,
                                    timestamp,
                                )
                                logger.debug(
                                    "Indexed binary record: key=%s, pos=%d, size=%d",
                                    key,
                                    record_pos,
                                    total_size,
                                )
                            except Exception as e:
                                logger.warning("Failed to decode binary record: %s", e)
                                continue
                    except Exception as e:
                        logger.error("Error processing file %s: %s", data_file, e)
                        break

    def put(self, key: str, value: Any) -> None:
        """Store a key-value pair."""
        with self._lock:
            timestamp = int(time.time() * 1000)  # Current time in milliseconds
            record = self.format.encode_record(key, value, timestamp)

            # Write to active file
            self.active_file.write(record)
            self.active_file.flush()
            record_pos = self.active_file.tell() - len(record)

            # Update index
            self.index[key] = (
                self.active_file_id,
                len(record),
                record_pos,
                timestamp,
            )
            logger.debug(
                "Wrote record: key=%s, pos=%d, size=%d",
                key,
                record_pos,
                len(record),
            )

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        if key not in self.index:
            logger.debug("Key not found in index: %s", key)
            return None

        file_id, value_size, value_pos, _ = self.index[key]
        file_path = self.data_dir / f"{file_id}.data"
        format = self._detect_format(file_path)
        logger.debug(
            "Reading key=%s from file=%s, pos=%d, size=%d",
            key,
            file_path,
            value_pos,
            value_size,
        )

        with open(file_path, "rb") as f:
            f.seek(value_pos)  # Position already includes format identifier offset
            if isinstance(format, JsonFormat):
                # For JSON format, read the entire line
                data = f.readline()
                logger.debug("Read JSON data: %r", data)
            else:
                # For binary format, read the header first
                header = f.read(16)
                if not header or len(header) < 16:
                    logger.warning("Failed to read binary header")
                    return None
                key_size, value_size, _ = struct.unpack(">IIQ", header)
                # Read the rest of the record
                data = header + f.read(key_size + value_size)
                logger.debug("Read binary data: %r", data)

            try:
                _, value, _ = format.decode_record(data)
                return value
            except Exception as e:
                logger.error("Failed to decode record: %s", e)
                return None

    def list_keys(self) -> list[str]:
        """
        List all keys in the database.

        Returns
        -------
            A list of all keys in the database.

        """
        return list(self.index.keys())

    def delete(self, key: str) -> None:
        """Delete a key-value pair."""
        with self._lock:
            if key in self.index:
                timestamp = int(time.time() * 1000)
                tombstone = self.format.encode_tombstone(key, timestamp)

                self.active_file.write(tombstone)
                self.active_file.flush()
                del self.index[key]
                logger.debug("Deleted key: %s", key)

    def batch_write(self, data: Dict[str, Any]) -> None:
        """
        Write multiple key-value pairs in a single operation.

        Args:
        ----
            data: Dictionary of key-value pairs to write.

        """
        with self._lock:
            timestamp = int(time.time() * 1000)  # Current time in milliseconds
            for key, value in data.items():
                record = self.format.encode_record(key, value, timestamp)

                # Write to active file
                self.active_file.write(record)
                record_pos = self.active_file.tell() - len(record)

                # Update index
                self.index[key] = (
                    self.active_file_id,
                    len(record),
                    record_pos,
                    timestamp,
                )
                logger.debug(
                    "Batch wrote record: key=%s, pos=%d, size=%d",
                    key,
                    record_pos,
                    len(record),
                )

            # Flush all writes at once
            self.active_file.flush()

    def close(self):
        """Close the database."""
        if self.active_file:
            self.active_file.close()
            self.active_file = None
            logger.debug("Closed database")

    def clear(self) -> None:
        """
        Delete all data and start fresh.

        This will:
        1. Close any open files
        2. Delete all data files
        3. Clear the in-memory index
        4. Create a new empty database
        """
        # Close any open files
        self.close()

        # Delete all data files
        for data_file in self.data_dir.glob("*.data"):
            data_file.unlink()

        # Clear the index
        self.index.clear()

        # Reset file counter
        self.active_file_id = 0

        # Create new empty database
        self._create_new_data_file()
        logger.debug("Database cleared and reset")
