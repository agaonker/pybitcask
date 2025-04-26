"""Data format implementations for Bitcask."""

import json
import struct
from abc import ABC, abstractmethod
from typing import Any, Tuple


class DataFormat(ABC):
    """Abstract base class for data formats."""

    # Format identifiers (1 byte)
    FORMAT_BINARY = b"\x01"
    FORMAT_JSON = b"\x02"

    @abstractmethod
    def get_format_identifier(self) -> bytes:
        """Get the format identifier byte."""
        pass

    @abstractmethod
    def encode_record(self, key: str, value: Any, timestamp: int) -> bytes:
        """Encode a record into bytes."""
        pass

    @abstractmethod
    def decode_record(self, data: bytes) -> Tuple[str, Any, int]:
        """Decode bytes into a record."""
        pass

    @abstractmethod
    def encode_tombstone(self, key: str, timestamp: int) -> bytes:
        """Encode a tombstone record into bytes."""
        pass

    @abstractmethod
    def read_record(self, file) -> Tuple[str, Any, int, int]:
        """Read a record from a file.

        Args:
        ----
            file: The file object to read from

        Returns:
        -------
            Tuple of (key, value, timestamp, record_size)

        """
        pass


class BinaryFormat(DataFormat):
    """Binary format implementation."""

    def get_format_identifier(self) -> bytes:
        """Get the format identifier byte."""
        return self.FORMAT_BINARY

    def encode_record(self, key: str, value: Any, timestamp: int) -> bytes:
        """Encode a record into binary format."""
        value_bytes = json.dumps(value).encode("utf-8")
        key_bytes = key.encode("utf-8")
        header = struct.pack(">IIQ", len(key_bytes), len(value_bytes), timestamp)
        return header + key_bytes + value_bytes

    def decode_record(self, data: bytes) -> Tuple[str, Any, int]:
        """Decode binary format into a record."""
        try:
            # First 16 bytes are the header
            key_size, value_size, timestamp = struct.unpack(">IIQ", data[:16])

            # Next key_size bytes are the key
            key = data[16 : 16 + key_size].decode("utf-8")

            # Next value_size bytes are the value
            value_bytes = data[16 + key_size : 16 + key_size + value_size]
            value = json.loads(value_bytes.decode("utf-8"))

            return key, value, timestamp
        except (struct.error, json.JSONDecodeError, UnicodeDecodeError) as err:
            raise ValueError(f"Failed to decode binary record: {str(err)}") from err

    def encode_tombstone(self, key: str, timestamp: int) -> bytes:
        """Encode a tombstone in binary format."""
        key_bytes = key.encode("utf-8")
        header = struct.pack(">IIQ", len(key_bytes), 0, timestamp)
        return header + key_bytes

    def read_record(self, file) -> Tuple[str, Any, int, int]:
        """Read a record from a file in binary format."""
        header = file.read(16)
        if not header or len(header) < 16:
            return None, None, None, None

        try:
            key_size, value_size, timestamp = struct.unpack(">IIQ", header)
            key = file.read(key_size).decode("utf-8")
            value_bytes = file.read(value_size)
            value = json.loads(value_bytes.decode("utf-8"))
            total_size = 16 + key_size + value_size
            return key, value, timestamp, total_size
        except Exception as e:
            raise ValueError(f"Failed to read binary record: {str(e)}") from e


class JsonFormat(DataFormat):
    """JSON format implementation for human-readable storage."""

    def get_format_identifier(self) -> bytes:
        """Get the format identifier byte."""
        return self.FORMAT_JSON

    def encode_record(self, key: str, value: Any, timestamp: int) -> bytes:
        """Encode a record into JSON format."""
        record = {"key": key, "value": value, "timestamp": timestamp}
        return (json.dumps(record) + "\n").encode("utf-8")

    def decode_record(self, data: bytes) -> Tuple[str, Any, int]:
        """Decode JSON format into a record."""
        try:
            record = json.loads(data.decode("utf-8").strip())
            return record["key"], record["value"], record["timestamp"]
        except (json.JSONDecodeError, KeyError) as err:
            raise ValueError(f"Failed to decode JSON record: {str(err)}") from err

    def encode_tombstone(self, key: str, timestamp: int) -> bytes:
        """Encode a tombstone in JSON format."""
        record = {"key": key, "value": None, "timestamp": timestamp, "deleted": True}
        return (json.dumps(record) + "\n").encode("utf-8")

    def read_record(self, file) -> Tuple[str, Any, int, int]:
        """Read a record from a file in JSON format."""
        line = file.readline()
        if not line:
            return None, None, None, None

        try:
            record = json.loads(line.decode("utf-8").strip())
            key = record["key"]
            value = record["value"]
            timestamp = record["timestamp"]
            record_size = len(line)
            return key, value, timestamp, record_size
        except Exception as e:
            raise ValueError(f"Failed to read JSON record: {str(e)}") from e


def get_format_by_identifier(identifier: bytes) -> DataFormat:
    """Get the appropriate format class based on the identifier byte."""
    format_map = {
        DataFormat.FORMAT_BINARY: BinaryFormat,
        DataFormat.FORMAT_JSON: JsonFormat,
    }
    format_class = format_map.get(identifier)
    if format_class is None:
        raise ValueError(f"Unknown format identifier: {identifier!r}")
    return format_class()
