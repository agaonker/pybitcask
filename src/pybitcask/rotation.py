"""File rotation strategies for Bitcask."""

from abc import ABC, abstractmethod
from datetime import datetime


class RotationStrategy(ABC):
    """Abstract base class for file rotation strategies."""

    @abstractmethod
    def should_rotate(
        self, file_size: int, entry_count: int, last_write_time: datetime
    ) -> bool:
        """Determine if a file should be rotated.

        Args:
        ----
            file_size: Current size of the file in bytes
            entry_count: Number of entries in the file
            last_write_time: Timestamp of the last write

        Returns:
        -------
            bool: True if the file should be rotated, False otherwise

        """
        pass


class SizeBasedRotation(RotationStrategy):
    """Rotate files based on maximum size."""

    def __init__(self, max_size_bytes: int):
        """Initialize size-based rotation.

        Args:
        ----
            max_size_bytes: Maximum file size in bytes before rotation

        """
        self.max_size_bytes = max_size_bytes

    def should_rotate(
        self, file_size: int, entry_count: int, last_write_time: datetime
    ) -> bool:
        """Check if file size exceeds maximum."""
        return file_size >= self.max_size_bytes


class EntryCountRotation(RotationStrategy):
    """Rotate files based on maximum number of entries."""

    def __init__(self, max_entries: int):
        """Initialize entry count-based rotation.

        Args:
        ----
            max_entries: Maximum number of entries before rotation

        """
        self.max_entries = max_entries

    def should_rotate(
        self, file_size: int, entry_count: int, last_write_time: datetime
    ) -> bool:
        """Check if entry count exceeds maximum."""
        return entry_count >= self.max_entries


class CompositeRotation(RotationStrategy):
    """Combine multiple rotation strategies."""

    def __init__(self, strategies: list[RotationStrategy]):
        """Initialize composite rotation.

        Args:
        ----
            strategies: List of rotation strategies to combine

        """
        self.strategies = strategies

    def should_rotate(
        self, file_size: int, entry_count: int, last_write_time: datetime
    ) -> bool:
        """Check if any strategy indicates rotation is needed."""
        return any(
            strategy.should_rotate(file_size, entry_count, last_write_time)
            for strategy in self.strategies
        )
