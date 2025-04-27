"""Tests for file rotation strategies."""

from datetime import datetime, timedelta

from pybitcask.rotation import (
    CompositeRotation,
    EntryCountRotation,
    SizeBasedRotation,
    TimeBasedRotation,
)


class TestSizeBasedRotation:
    """Test size-based rotation strategy."""

    def test_should_rotate_when_size_exceeds_max(self):
        """Test rotation when file size exceeds maximum."""
        rotation = SizeBasedRotation(max_size_bytes=1000)
        assert rotation.should_rotate(1001, 0, datetime.now()) is True

    def test_should_not_rotate_when_size_below_max(self):
        """Test no rotation when file size is below maximum."""
        rotation = SizeBasedRotation(max_size_bytes=1000)
        assert rotation.should_rotate(999, 0, datetime.now()) is False

    def test_should_rotate_at_exact_max_size(self):
        """Test rotation at exact maximum size."""
        rotation = SizeBasedRotation(max_size_bytes=1000)
        assert rotation.should_rotate(1000, 0, datetime.now()) is True


class TestEntryCountRotation:
    """Test entry count-based rotation strategy."""

    def test_should_rotate_when_entries_exceed_max(self):
        """Test rotation when entry count exceeds maximum."""
        rotation = EntryCountRotation(max_entries=100)
        assert rotation.should_rotate(0, 101, datetime.now()) is True

    def test_should_not_rotate_when_entries_below_max(self):
        """Test no rotation when entry count is below maximum."""
        rotation = EntryCountRotation(max_entries=100)
        assert rotation.should_rotate(0, 99, datetime.now()) is False

    def test_should_rotate_at_exact_max_entries(self):
        """Test rotation at exact maximum entries."""
        rotation = EntryCountRotation(max_entries=100)
        assert rotation.should_rotate(0, 100, datetime.now()) is True


class TestTimeBasedRotation:
    """Test time-based rotation strategy."""

    def test_should_not_rotate_on_first_write(self):
        """Test no rotation on first write."""
        rotation = TimeBasedRotation(interval_seconds=3600)
        now = datetime.now()
        assert rotation.should_rotate(0, 0, now) is False
        assert rotation.last_rotation_time == now

    def test_should_rotate_after_interval(self):
        """Test rotation after interval has passed."""
        rotation = TimeBasedRotation(interval_seconds=3600)
        start_time = datetime.now()
        rotation.last_rotation_time = start_time
        later_time = start_time + timedelta(seconds=3601)
        assert rotation.should_rotate(0, 0, later_time) is True

    def test_should_not_rotate_before_interval(self):
        """Test no rotation before interval has passed."""
        rotation = TimeBasedRotation(interval_seconds=3600)
        start_time = datetime.now()
        rotation.last_rotation_time = start_time
        later_time = start_time + timedelta(seconds=3599)
        assert rotation.should_rotate(0, 0, later_time) is False


class TestCompositeRotation:
    """Test composite rotation strategy."""

    def test_should_rotate_when_any_strategy_requires(self):
        """Test rotation when any strategy requires it."""
        strategies = [
            SizeBasedRotation(max_size_bytes=1000),
            EntryCountRotation(max_entries=100),
        ]
        rotation = CompositeRotation(strategies)
        # Size exceeds but entries don't
        assert rotation.should_rotate(1001, 50, datetime.now()) is True
        # Entries exceed but size doesn't
        assert rotation.should_rotate(500, 101, datetime.now()) is True

    def test_should_not_rotate_when_no_strategy_requires(self):
        """Test no rotation when no strategy requires it."""
        strategies = [
            SizeBasedRotation(max_size_bytes=1000),
            EntryCountRotation(max_entries=100),
        ]
        rotation = CompositeRotation(strategies)
        assert rotation.should_rotate(500, 50, datetime.now()) is False
