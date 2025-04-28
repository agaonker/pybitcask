"""Data format implementations for Bitcask."""

import json
import struct
from abc import ABC, abstractmethod
from typing import Any, Tuple

from pybitcask.proto.record_pb2 import Record


class DataFormat(ABC):
    """Abstract base class for data formats."""

    # Format identifiers (1 byte)
    FORMAT_PROTO = b"\x01"  # Default format
    FORMAT_BINARY = b"\x02"  # Binary format
    FORMAT_JSON = b"\x03"  # JSON format
    DEFAULT_FORMAT = FORMAT_PROTO  # Default format identifier

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


class ProtoFormat(DataFormat):
    """Protocol Buffers format implementation."""

    def get_format_identifier(self) -> bytes:
        """Get the format identifier byte."""
        return self.FORMAT_PROTO

    def encode_record(self, key: str, value: Any, timestamp: int) -> bytes:
        """Encode a record into protobuf format."""
        record = Record()
        record.key = key
        record.value = json.dumps(value).encode("utf-8")
        record.timestamp = timestamp
        record.deleted = False

        # Serialize the protobuf message
        proto_data = record.SerializeToString()

        # Add size prefix (4 bytes, big-endian)
        size_prefix = len(proto_data).to_bytes(4, byteorder="big")

        return size_prefix + proto_data

    def decode_record(self, data: bytes) -> Tuple[str, Any, int]:
        """Decode protobuf format into a record."""
        try:
            # Skip size prefix (4 bytes)
            proto_data = data[4:]

            record = Record()
            record.ParseFromString(proto_data)
            if record.deleted:
                raise ValueError("Record is a tombstone")
            value = json.loads(record.value.decode("utf-8"))
            return record.key, value, record.timestamp
        except Exception as err:
            raise ValueError(f"Failed to decode protobuf record: {str(err)}") from err

    def encode_tombstone(self, key: str, timestamp: int) -> bytes:
        """Encode a tombstone in protobuf format."""
        record = Record()
        record.key = key
        record.timestamp = timestamp
        record.deleted = True

        # Serialize the protobuf message
        proto_data = record.SerializeToString()

        # Add size prefix (4 bytes, big-endian)
        size_prefix = len(proto_data).to_bytes(4, byteorder="big")

        return size_prefix + proto_data

    def read_record(self, file) -> Tuple[str, Any, int, int, bool]:
        """Read a record from a file in protobuf format.

        Returns
        -------
            Tuple of (key, value, timestamp, record_size, is_tombstone)

        """
        try:
            # Read the size of the protobuf message (4 bytes)
            size_bytes = file.read(4)
            if not size_bytes or len(size_bytes) < 4:
                return None, None, None, None, False

            size = int.from_bytes(size_bytes, byteorder="big")

            # Read the protobuf message
            data = file.read(size)
            if not data or len(data) < size:
                return None, None, None, None, False

            record = Record()
            record.ParseFromString(data)

            if record.deleted:
                return record.key, None, record.timestamp, size + 4, True

            value = json.loads(record.value.decode("utf-8"))
            return record.key, value, record.timestamp, size + 4, False
        except Exception as e:
            raise ValueError(f"Failed to read protobuf record: {str(e)}") from e


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

    def read_record(self, file) -> Tuple[str, Any, int, int, bool]:
        """Read a record from a file in binary format.

        Returns
        -------
            Tuple of (key, value, timestamp, record_size, is_tombstone)

        """
        header = file.read(16)
        if not header or len(header) < 16:
            return None, None, None, None, False

        try:
            key_size, value_size, timestamp = struct.unpack(">IIQ", header)
            key = file.read(key_size).decode("utf-8")

            # Check if this is a tombstone (value_size = 0)
            is_tombstone = value_size == 0
            if is_tombstone:
                return key, None, timestamp, 16 + key_size, True

            value_bytes = file.read(value_size)
            value = json.loads(value_bytes.decode("utf-8"))
            total_size = 16 + key_size + value_size
            return key, value, timestamp, total_size, False
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

    def read_record(self, file) -> Tuple[str, Any, int, int, bool]:
        """Read a record from a file in JSON format.

        Returns
        -------
            Tuple of (key, value, timestamp, record_size, is_tombstone)

        """
        line = file.readline()
        if not line:
            return None, None, None, None, False

        try:
            record = json.loads(line)
            is_tombstone = record.get("deleted", False)
            if is_tombstone:
                return record["key"], None, record["timestamp"], len(line), True
            return record["key"], record["value"], record["timestamp"], len(line), False
        except Exception as e:
            raise ValueError(f"Failed to read JSON record: {str(e)}") from e


def get_format_by_identifier(identifier: bytes = None) -> DataFormat:
    """Get the appropriate format class based on the identifier byte.

    Args:
    ----
        identifier: The format identifier byte. If None, returns the default format.

    Returns:
    -------
        A DataFormat instance for the specified format.

    """
    if identifier is None:
        return ProtoFormat()

    format_map = {
        DataFormat.FORMAT_PROTO: ProtoFormat,
        DataFormat.FORMAT_BINARY: BinaryFormat,
        DataFormat.FORMAT_JSON: JsonFormat,
    }
    format_class = format_map.get(identifier)
    if format_class is None:
        # If format is unknown, return ProtoFormat as default
        return ProtoFormat()
    return format_class()
