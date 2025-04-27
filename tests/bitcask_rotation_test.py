"""Tests for Bitcask file rotation functionality."""

import logging
import os
import tempfile

import pytest

from pybitcask.bitcask import Bitcask
from pybitcask.rotation import (
    EntryCountRotation,
    SizeBasedRotation,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


class TestBitcaskRotation:
    """Test file rotation functionality in Bitcask."""

    def test_size_based_rotation(self, temp_dir):
        """Test rotation based on file size."""
        # Create a Bitcask instance with size-based rotation
        # Each record is: 1 byte format + 16 bytes header +
        # 4 bytes key + 50 bytes value = 71 bytes
        # Set max size to 75 bytes so we get one record per file
        rotation = SizeBasedRotation(max_size_bytes=75)
        db = Bitcask(temp_dir, rotation_strategy=rotation)

        # Write data until rotation should occur
        value = "x" * 50  # 50 bytes per value
        for i in range(3):  # Should create 3 files, one record each
            db.put(f"key{i}", value)
            # Check file size after each write
            file_size = os.path.getsize(db.active_file_path)
            print(
                f"After write {i + 1}: file_size={file_size}, "
                f"entry_count={db.active_file_entry_count}"
            )

        # Verify that three files were created (one record per file)
        data_files = sorted(os.listdir(temp_dir))
        assert len(data_files) == 3, "Expected 3 data files, one record per file"

        db.close()

    def test_entry_count_rotation(self, temp_dir):
        """Test rotation based on entry count."""
        # Create a Bitcask instance with entry count-based rotation (1 entry per file)
        rotation = EntryCountRotation(max_entries=1)
        db = Bitcask(temp_dir, rotation_strategy=rotation)

        # Write data until rotation should occur
        for i in range(3):  # Should create 3 files, one record each
            db.put(f"key{i}", f"value{i}")
            # Check file state after each write
            print(
                f"After write {i + 1}: entry_count={db.active_file_entry_count}, "
                f"file_id={db.active_file_id}"
            )

        # Verify that three files were created (one record per file)
        data_files = sorted(os.listdir(temp_dir))
        assert len(data_files) == 3, "Expected 3 data files, one record per file"

        db.close()

    def test_no_rotation_when_disabled(self, temp_dir):
        """Test that no rotation occurs when rotation is disabled."""
        db = Bitcask(temp_dir)  # No rotation strategy

        # Write multiple entries
        for i in range(10):
            db.put(f"key{i}", f"value{i}")

        # Verify that only one file exists
        data_files = sorted(os.listdir(temp_dir))
        assert (
            len(data_files) == 1
        ), "Expected only 1 data file when rotation is disabled"

        db.close()

    def test_rotation_preserves_data(self, temp_dir):
        """Test that data is preserved after rotation."""
        # Create a Bitcask instance with entry count-based rotation
        rotation = EntryCountRotation(max_entries=2)
        db = Bitcask(temp_dir, rotation_strategy=rotation)

        # Write initial data
        db.put("key1", "value1")
        db.put("key2", "value2")
        db.put("key3", "value3")  # This should trigger rotation

        # Verify all data is accessible
        assert db.get("key1") == "value1"
        assert db.get("key2") == "value2"
        assert db.get("key3") == "value3"

        db.close()
