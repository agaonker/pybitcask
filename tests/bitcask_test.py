"""Unit tests for the Bitcask key-value store implementation."""

# -*- coding: utf-8 -*-
import logging
import shutil
import tempfile
import unittest
from pathlib import Path

from pybitcask import Bitcask, EntryCountRotation, SizeBasedRotation

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


class TestRotation(unittest.TestCase):
    """Test suite for file rotation functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="bitcask-rotation-test-"))

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.test_dir)

    def test_entry_count_rotation(self):
        """Test rotation based on entry count."""
        # Rotate after 5 entries
        rotation = EntryCountRotation(max_entries=5)
        db = Bitcask(str(self.test_dir), rotation_strategy=rotation)

        # Write 5 entries - should trigger rotation after 5th
        for i in range(5):
            db.put(f"key{i}", f"value{i}")

        # Write one more entry to trigger rotation check
        db.put("key5", "value5")

        # File should have rotated (file_id > 1 means we rotated from initial file)
        self.assertGreater(db.active_file_id, 1)

        # Verify all data is still accessible
        for i in range(6):
            self.assertEqual(db.get(f"key{i}"), f"value{i}")

        db.close()

    def test_size_based_rotation(self):
        """Test rotation based on file size."""
        # Rotate after 100 bytes (small for testing)
        rotation = SizeBasedRotation(max_size_bytes=100)
        db = Bitcask(str(self.test_dir), rotation_strategy=rotation)

        initial_file_id = db.active_file_id

        # Write enough data to exceed 100 bytes
        db.put("key1", "a" * 50)
        db.put("key2", "b" * 50)

        # Should have rotated by now
        self.assertGreater(db.active_file_id, initial_file_id)

        # Verify data is still accessible
        self.assertEqual(db.get("key1"), "a" * 50)
        self.assertEqual(db.get("key2"), "b" * 50)

        db.close()

    def test_no_rotation_without_strategy(self):
        """Test that rotation doesn't happen without a strategy."""
        db = Bitcask(str(self.test_dir))

        initial_file_id = db.active_file_id

        # Write many entries
        for i in range(100):
            db.put(f"key{i}", f"value{i}" * 100)

        # Should still be on the same file (no rotation strategy)
        self.assertEqual(db.active_file_id, initial_file_id)

        db.close()

    def test_rotation_with_batch_write(self):
        """Test that rotation works with batch writes."""
        rotation = EntryCountRotation(max_entries=3)
        db = Bitcask(str(self.test_dir), rotation_strategy=rotation)

        # Batch write 5 entries - should trigger rotation
        data = {f"key{i}": f"value{i}" for i in range(5)}
        db.batch_write(data)

        # Should have rotated
        self.assertGreater(db.active_file_id, 1)

        # Verify all data is accessible
        for i in range(5):
            self.assertEqual(db.get(f"key{i}"), f"value{i}")

        db.close()

    def test_rotation_persistence(self):
        """Test that data persists correctly after rotation."""
        rotation = EntryCountRotation(max_entries=3)
        db = Bitcask(str(self.test_dir), rotation_strategy=rotation)

        # Write enough to cause multiple rotations
        for i in range(10):
            db.put(f"key{i}", f"value{i}")

        db.close()

        # Reopen without rotation strategy
        db2 = Bitcask(str(self.test_dir))

        # All data should still be accessible
        for i in range(10):
            self.assertEqual(db2.get(f"key{i}"), f"value{i}")

        db2.close()


class TestAutoCompaction(unittest.TestCase):
    """Test suite for automatic compaction scheduling."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="bitcask-autocompact-test-"))

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        shutil.rmtree(self.test_dir)

    def test_start_stop_auto_compaction(self):
        """Test starting and stopping auto-compaction."""
        db = Bitcask(str(self.test_dir))

        # Initially not running
        self.assertFalse(db.auto_compaction_running)

        # Start auto-compaction
        scheduler = db.start_auto_compaction(interval_seconds=1.0)
        self.assertTrue(db.auto_compaction_running)
        self.assertIsNotNone(scheduler)

        # Stop auto-compaction
        result = db.stop_auto_compaction()
        self.assertTrue(result)
        self.assertFalse(db.auto_compaction_running)

        db.close()

    def test_auto_compaction_on_close(self):
        """Test that auto-compaction stops when database is closed."""
        db = Bitcask(str(self.test_dir))

        db.start_auto_compaction(interval_seconds=1.0)
        self.assertTrue(db.auto_compaction_running)

        # Close should stop the scheduler
        db.close()
        self.assertFalse(db.auto_compaction_running)

    def test_auto_compaction_callback(self):
        """Test that compaction callback is invoked."""
        db = Bitcask(str(self.test_dir))

        # Write data and create dead entries
        for i in range(100):
            db.put(f"key{i}", f"value{i}" * 100)

        # Overwrite to create dead data
        for i in range(100):
            db.put(f"key{i}", f"newvalue{i}")

        callback_results = []

        def on_complete(result):
            callback_results.append(result)

        scheduler = db.start_auto_compaction(
            interval_seconds=0.1,
            threshold_ratio=0.1,
            on_compaction_complete=on_complete,
        )

        # Manually trigger compaction
        result = scheduler.trigger_compaction(force=True)

        # Should have gotten a result
        self.assertIsNotNone(result)
        self.assertTrue(result.get("performed", False))

        # Callback should have been called
        self.assertEqual(len(callback_results), 1)

        db.close()

    def test_double_start_auto_compaction(self):
        """Test that starting auto-compaction twice returns same scheduler."""
        db = Bitcask(str(self.test_dir))

        scheduler1 = db.start_auto_compaction(interval_seconds=1.0)
        scheduler2 = db.start_auto_compaction(interval_seconds=1.0)

        # Should return the same scheduler
        self.assertIs(scheduler1, scheduler2)

        db.close()

    def test_scheduler_properties(self):
        """Test scheduler property getters and setters."""
        db = Bitcask(str(self.test_dir))

        scheduler = db.start_auto_compaction(
            interval_seconds=10.0,
            threshold_ratio=0.5,
        )

        self.assertEqual(scheduler.interval_seconds, 10.0)
        self.assertEqual(scheduler.threshold_ratio, 0.5)

        # Update properties
        scheduler.interval_seconds = 20.0
        scheduler.threshold_ratio = 0.7

        self.assertEqual(scheduler.interval_seconds, 20.0)
        self.assertEqual(scheduler.threshold_ratio, 0.7)

        db.close()


if __name__ == "__main__":
    unittest.main()
