#!/usr/bin/env python3
"""Test script to demonstrate PyBitcask compaction functionality."""

import time
from tempfile import TemporaryDirectory

from pybitcask import Bitcask


def format_bytes(bytes_val):
    """Format bytes in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def print_stats(db, title):
    """Print database statistics."""
    stats = db.get_compaction_stats()
    print(f"\n📊 {title}")
    print(f"  Files: {stats['total_files']}")
    print(f"  Total size: {format_bytes(stats['total_size'])}")
    print(f"  Live keys: {stats['live_keys']:,}")
    print(f"  Estimated live size: {format_bytes(stats['estimated_live_size'])}")
    print(f"  Dead data ratio: {stats['estimated_dead_ratio']:.1%}")
    print(f"  Should compact: {'Yes' if db.should_compact() else 'No'}")


def main():
    """Demonstrate compaction functionality."""
    print("🧪 PyBitcask Compaction Demo")
    print("=" * 50)

    # Use TemporaryDirectory for automatic cleanup, even on abrupt exits
    with TemporaryDirectory(prefix="pbc_compaction_") as temp_dir:
        # Initialize database in debug mode for easier inspection
        db = Bitcask(temp_dir, debug_mode=True)

        print("\n1️⃣ Creating initial dataset...")
        # Add initial data
        for i in range(100):
            key = f"user:{i:03d}"
            value = {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50),
                "created": time.time(),
                "data": "x" * 100,  # Add some bulk to make files larger
            }
            db.put(key, value)

        print_stats(db, "After Initial Data")

        print("\n2️⃣ Updating half the records (creates dead data)...")
        # Update half the records (creates dead data)
        for i in range(0, 50):
            key = f"user:{i:03d}"
            value = {
                "name": f"Updated User {i}",
                "email": f"updated.user{i}@example.com",
                "age": 25 + (i % 50),
                "updated": time.time(),
                "data": "y" * 150,  # Larger data
            }
            db.put(key, value)

        print_stats(db, "After Updates")

        print("\n3️⃣ Deleting some records (creates tombstones)...")
        # Delete some records
        for i in range(80, 100):
            key = f"user:{i:03d}"
            db.delete(key)

        print_stats(db, "After Deletions")

        print("\n4️⃣ Adding more data to create multiple files...")
        # Add more data to create multiple files
        for i in range(200, 300):
            key = f"product:{i}"
            value = {
                "name": f"Product {i}",
                "price": 10.99 + (i % 100),
                "category": f"Category {i % 10}",
                "description": "A" * 200,  # Bulk data
            }
            db.put(key, value)

        print_stats(db, "After More Data")

        # Check if compaction is recommended
        if db.should_compact():
            print("\n5️⃣ Running compaction...")
            start_time = time.time()
            result = db.compact()
            duration = time.time() - start_time

            if result["performed"]:
                print("✅ Compaction completed!")
                print(f"  Duration: {duration:.2f} seconds")
                print(f"  Records written: {result['records_written']:,}")
                print(f"  Files removed: {result['files_removed']}")
                print(f"  Space saved: {format_bytes(result['space_saved_bytes'])}")
                print(f"  Space reduction: {result['space_saved_ratio']:.1%}")

                print_stats(db, "After Compaction")
            else:
                print(f"❌ Compaction not performed: {result['reason']}")
        else:
            print("\n5️⃣ Compaction not needed (threshold not met)")
            print("   Forcing compaction for demonstration...")
            result = db.compact(force=True)
            if result["performed"]:
                print("✅ Forced compaction completed!")
                print_stats(db, "After Forced Compaction")

        print("\n6️⃣ Verifying data integrity...")
        # Verify some data is still accessible
        test_keys = ["user:001", "user:025", "product:250"]
        for key in test_keys:
            value = db.get(key)
            if value:
                print(f"  ✓ {key}: {value.get('name', 'N/A')}")
            else:
                print(f"  ✗ {key}: Not found")

        # Test deleted keys
        deleted_key = "user:085"
        value = db.get(deleted_key)
        if value is None:
            print(f"  ✓ {deleted_key}: Correctly deleted")
        else:
            print(f"  ✗ {deleted_key}: Should be deleted but found: {value}")

        db.close()

        print(f"\n🧹 Cleaned up test directory: {temp_dir}")

    print("\n✅ Compaction demo completed successfully!")


if __name__ == "__main__":
    main()
