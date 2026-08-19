"""OpenEB-specific event acquisition.

All other modules receive structured NumPy event arrays with ``x``, ``y``,
``p`` and ``t`` fields and deliberately remain independent of Metavision.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import numpy as np

from config import EVENT_SLICE_US, SENSOR_HEIGHT, SENSOR_WIDTH


class CameraError(RuntimeError):
    """Raised when OpenEB cannot open a recording or live camera."""


class EventSource:
    """Yield fixed-duration CD-event slices from a RAW recording or camera.

    ``input_path=None`` selects the first connected OpenEB camera.  Passing a
    RAW path uses the same OpenEB iterator, making offline and live processing
    follow the same path.
    """

    def __init__(self, input_path: str | Path | None = None, slice_us: int = EVENT_SLICE_US) -> None:
        if slice_us <= 0:
            raise ValueError("slice_us must be positive")
        self.input_path = None if input_path is None else Path(input_path)
        self.slice_us = slice_us
        self.width = SENSOR_WIDTH
        self.height = SENSOR_HEIGHT

    def __iter__(self) -> Iterator[np.ndarray]:
        if self.input_path is not None and not self.input_path.is_file():
            raise CameraError(f"Recording not found: {self.input_path}")

        try:
            # OpenEB's public Python iterator supports RAW files and devices.
            from metavision_core.event_io import EventsIterator
        except ImportError as exc:
            raise CameraError(
                "OpenEB Python bindings are unavailable. Run with the Python "
                "environment that has metavision_core installed."
            ) from exc

        source = "" if self.input_path is None else str(self.input_path)
        try:
            iterator = EventsIterator(source, mode="delta_t", delta_t=self.slice_us)
            height, width = iterator.get_size()
            if width is not None and height is not None:
                self.width, self.height = int(width), int(height)
            yield from iterator
        except Exception as exc:
            description = "live camera" if self.input_path is None else str(self.input_path)
            raise CameraError(f"Could not open {description}: {exc}") from exc
