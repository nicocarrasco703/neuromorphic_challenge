"""Vectorized event-activity measurements used by the game."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import EMA_ALPHA, EVENT_SLICE_US, SENSOR_WIDTH


@dataclass(frozen=True)
class ActivityState:
    """Activity statistics for one event slice, all in events per second."""

    total_rate: float
    smoothed_rate: float
    region_rates: np.ndarray
    target_rate: float = 0.0
    outside_rate: float = 0.0


class ActivityAnalyzer:
    """Measure event rate without reconstructing conventional image frames."""

    def __init__(
        self,
        *,
        ema_alpha: float = EMA_ALPHA,
        slice_us: int = EVENT_SLICE_US,
        width: int = SENSOR_WIDTH,
    ) -> None:
        if not 0.0 < ema_alpha <= 1.0:
            raise ValueError("ema_alpha must be in (0, 1]")
        if slice_us <= 0:
            raise ValueError("slice_us must be positive")
        self.ema_alpha = ema_alpha
        self.slice_seconds = slice_us / 1_000_000.0
        self.width = width
        self._smoothed_rate = 0.0

    def process(self, events: np.ndarray) -> ActivityState:
        """Return total and left/right activity for one structured event batch.

        For normal multi-event slices, duration comes from the event timestamps.
        Empty and one-event slices use the configured slice duration, preserving
        a meaningful zero/low activity measurement.
        """
        count = len(events)
        duration = self._duration_seconds(events)
        total_rate = count / duration

        if count:
            left_count = np.count_nonzero(events["x"] < self.width // 2)
            right_count = count - left_count
            region_rates = np.array((left_count / duration, right_count / duration), dtype=float)
        else:
            region_rates = np.zeros(2, dtype=float)

        self._smoothed_rate = (
            self.ema_alpha * total_rate + (1.0 - self.ema_alpha) * self._smoothed_rate
        )
        return ActivityState(total_rate=total_rate, smoothed_rate=self._smoothed_rate, region_rates=region_rates)

    def _duration_seconds(self, events: np.ndarray) -> float:
        if len(events) < 2:
            return self.slice_seconds
        timestamps = events["t"]
        elapsed_us = int(timestamps[-1]) - int(timestamps[0])
        return max(elapsed_us / 1_000_000.0, self.slice_seconds)
