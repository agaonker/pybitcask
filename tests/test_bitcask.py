import unittest
import shutil
import os
from pathlib import Path
from pybitcask.bitcask import Bitcask

class TestBitcask(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("/Users/ashish/bitcask-test-dir")
        self.test_dir.mkdir(exist_ok=True)
        self.db = Bitcask(str(self.test_dir))

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.test_dir)

    def test_basic_operations(self):
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
        self.db.put("key1", "value1")
        self.assertEqual(self.db.get("key1"), "value1")
        
        self.db.delete("key1")
        self.assertIsNone(self.db.get("key1"))

    def test_persistence(self):
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

if __name__ == '__main__':
    unittest.main() 