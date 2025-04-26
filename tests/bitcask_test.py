"""Unit tests for the Bitcask key-value store implementation."""

# -*- coding: utf-8 -*-
import logging
import shutil
import tempfile
import unittest
from pathlib import Path

from pybitcask import Bitcask

# Disable all logging before importing Bitcask
logging.disable(logging.CRITICAL)

logger = logging.getLogger(__name__)


class TestBitcask(unittest.TestCase):
    """Test suite for the Bitcask key-value store implementation."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="bitcask-test-"))
        self.db = Bitcask(str(self.test_dir))

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        self.db.close()
        shutil.rmtree(self.test_dir)

    def test_basic_operations(self):
        """Test basic Bitcask operations: put, get, delete."""
        # Test data
        test_data = {
            "key1": "value1",
            "key2": {"nested": "value2"},
            "key3": 123,
            "key4": [1, 2, 3],
        }

        # Test put and get
        for key, value in test_data.items():
            self.db.put(key, value)
            retrieved = self.db.get(key)
            self.assertEqual(
                retrieved, value, f"Retrieved value for {key} does not match original"
            )
            logger.debug("Successfully stored and retrieved %s: %s", key, value)

        # Test delete
        key_to_delete = "key2"
        self.db.delete(key_to_delete)
        deleted_value = self.db.get(key_to_delete)
        self.assertIsNone(deleted_value, f"Deleted key {key_to_delete} still exists")
        logger.debug("Successfully deleted %s", key_to_delete)

        # Test non-existent key
        non_existent = self.db.get("non_existent_key")
        self.assertIsNone(non_existent, "Non-existent key should return None")
        logger.debug("Successfully handled non-existent key")

        # Test overwrite
        new_value = "new_value1"
        self.db.put("key1", new_value)
        retrieved = self.db.get("key1")
        self.assertEqual(
            retrieved, new_value, "Overwritten value does not match new value"
        )
        logger.debug("Successfully overwrote key1 with new value")

    def test_delete(self):
        """Test delete operation."""
        self.db.put("key1", "value1")
        self.assertEqual(self.db.get("key1"), "value1")

        self.db.delete("key1")
        self.assertIsNone(self.db.get("key1"))

    def test_persistence(self):
        """Test data persistence."""
        # Write some data
        self.db.put("key1", "value1")
        self.db.put("key2", "value2")
        self.db.close()

        # Reopen the database
        new_db = Bitcask(str(self.test_dir))

        # Verify data persistence
        self.assertEqual(new_db.get("key1"), "value1")
        self.assertEqual(new_db.get("key2"), "value2")
        new_db.close()

    def test_batch_write(self):
        """Test batch write operation."""
        data = {"key3": "value3", "key4": "value4"}
        self.db.batch_write(data)
        self.assertEqual(self.db.get("key3"), "value3")
        self.assertEqual(self.db.get("key4"), "value4")


if __name__ == "__main__":
    unittest.main()
