"""Automatic compaction scheduling for Bitcask."""

import logging
import threading
import time
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .bitcask import Bitcask

logger = logging.getLogger(__name__)


class CompactionScheduler:
    """Background scheduler for automatic database compaction.

    This scheduler runs a background thread that periodically checks if
    compaction is needed and triggers it automatically based on configured
    thresholds.

    Example:
    -------
        db = Bitcask("/data")
        scheduler = CompactionScheduler(
            db,
            interval_seconds=300,  # Check every 5 minutes
            threshold_ratio=0.3,   # Compact when 30% dead data
        )
        scheduler.start()
        # ... use database ...
        scheduler.stop()

    """

    def __init__(
        self,
        bitcask: "Bitcask",
        interval_seconds: float = 300.0,
        threshold_ratio: float = 0.3,
        on_compaction_complete: Optional[Callable[[dict], None]] = None,
    ):
        """Initialize the compaction scheduler.

        Args:
        ----
            bitcask: The Bitcask instance to manage compaction for.
            interval_seconds: How often to check if compaction is needed.
                             Default: 300 seconds (5 minutes).
            threshold_ratio: Minimum ratio of dead data to trigger compaction.
                            Default: 0.3 (30%).
            on_compaction_complete: Optional callback invoked after compaction.
                                   Receives the compaction result dict.

        """
        self._bitcask = bitcask
        self._on_compaction_complete = on_compaction_complete

        # Initialize with defaults, then use setters for validation
        self._interval_seconds = 300.0
        self._threshold_ratio = 0.3
        self.interval_seconds = interval_seconds
        self.threshold_ratio = threshold_ratio

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._running

    @property
    def interval_seconds(self) -> float:
        """Get the current check interval in seconds."""
        return self._interval_seconds

    @interval_seconds.setter
    def interval_seconds(self, value: float) -> None:
        """Set the check interval in seconds."""
        if value <= 0:
            raise ValueError("interval_seconds must be positive")
        self._interval_seconds = value

    @property
    def threshold_ratio(self) -> float:
        """Get the current compaction threshold ratio."""
        return self._threshold_ratio

    @threshold_ratio.setter
    def threshold_ratio(self, value: float) -> None:
        """Set the compaction threshold ratio."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("threshold_ratio must be between 0.0 and 1.0")
        self._threshold_ratio = value

    def start(self) -> None:
        """Start the background compaction scheduler.

        If the scheduler is already running, this method does nothing.
        """
        with self._lock:
            if self._running:
                logger.warning("Compaction scheduler is already running")
                return

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_scheduler,
                name="BitcaskCompactionScheduler",
                daemon=True,
            )
            self._running = True
            self._thread.start()
            logger.info(
                "Compaction scheduler started (interval=%.1fs, threshold=%.1f%%)",
                self._interval_seconds,
                self._threshold_ratio * 100,
            )

    def stop(self, timeout: Optional[float] = None) -> bool:
        """Stop the background compaction scheduler.

        Args:
        ----
            timeout: Maximum time to wait for the scheduler thread to stop.
                    If None, waits indefinitely.

        Returns:
        -------
            True if the scheduler stopped successfully, False if it timed out.

        """
        with self._lock:
            if not self._running:
                return True

            self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning("Compaction scheduler did not stop within timeout")
                return False

        with self._lock:
            self._running = False
            self._thread = None

        logger.info("Compaction scheduler stopped")
        return True

    def trigger_compaction(self, force: bool = False) -> Optional[dict]:
        """Manually trigger a compaction check.

        This can be called to immediately check and potentially run compaction,
        regardless of the scheduled interval.

        Args:
        ----
            force: If True, forces compaction regardless of threshold.

        Returns:
        -------
            The compaction result dict, or None if compaction was not performed.

        """
        return self._check_and_compact(force=force)

    def _run_scheduler(self) -> None:
        """Background thread that periodically checks for compaction."""
        logger.debug("Compaction scheduler thread started")

        while not self._stop_event.is_set():
            # Wait for the interval, but check stop_event periodically
            # to allow for responsive shutdown
            wait_time = 0.0
            while wait_time < self._interval_seconds and not self._stop_event.is_set():
                time.sleep(min(1.0, self._interval_seconds - wait_time))
                wait_time += 1.0

            if self._stop_event.is_set():
                break

            self._check_and_compact()

        logger.debug("Compaction scheduler thread exiting")

    def _check_and_compact(self, force: bool = False) -> Optional[dict]:
        """Check if compaction is needed and perform it if so.

        Args:
        ----
            force: If True, forces compaction regardless of threshold.

        Returns:
        -------
            The compaction result dict, or None if compaction was not performed.

        """
        try:
            if not force and not self._bitcask.should_compact(self._threshold_ratio):
                logger.debug("Compaction not needed (threshold not met)")
                return None

            logger.info("Starting scheduled compaction (force=%s)", force)
            result = self._bitcask.compact(
                threshold_ratio=self._threshold_ratio,
                force=force,
            )

            if result.get("performed"):
                logger.info(
                    "Scheduled compaction completed: %d records, %.2f MB saved",
                    result.get("records_written", 0),
                    result.get("space_saved_bytes", 0) / (1024 * 1024),
                )

                if self._on_compaction_complete:
                    try:
                        self._on_compaction_complete(result)
                    except Exception as callback_error:
                        logger.error("Error in compaction callback: %s", callback_error)
            else:
                logger.debug("Compaction skipped: %s", result.get("reason", "unknown"))

            return result

        except Exception as e:
            logger.error("Error during scheduled compaction: %s", e)
            return None
