"""Unit tests for the Bitcask key-value store implementation."""

# -*- coding: utf-8 -*-
import shutil
import unittest
from pathlib import Path

from pybitcask import Bitcask


class TestBitcask(unittest.TestCase):
    """Test suite for the Bitcask key-value store implementation."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = Path("/Users/ashish/bitcask-test-dir")
        self.test_dir.mkdir(exist_ok=True)
        self.db = Bitcask(str(self.test_dir))

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        self.db.close()
        shutil.rmtree(self.test_dir)

    def test_basic_operations(self):
        """Test basic put and get operations."""
        # Test put and get
        self.db.put("key1", "value1")
        self.assertEqual(self.db.get("key1"), "value1")

        # Test updating a value
        self.db.put("key1", "new_value1")
        self.assertEqual(self.db.get("key1"), "new_value1")

        # Test non-existent key
        self.assertIsNone(self.db.get("nonexistent"))

        # Test complex data types
        complex_data = {"name": "test", "values": [1, 2, 3]}
        self.db.put("complex", complex_data)
        self.assertEqual(self.db.get("complex"), complex_data)

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
