import numpy as np
import pytest

from activity import ActivityAnalyzer


EVENT_DTYPE = np.dtype([("x", "u2"), ("y", "u2"), ("p", "i1"), ("t", "u8")])


def events(rows: list[tuple[int, int, int, int]]) -> np.ndarray:
    return np.array(rows, dtype=EVENT_DTYPE)


def test_rate_and_left_right_regions() -> None:
    analyzer = ActivityAnalyzer(ema_alpha=1.0, slice_us=5_000, width=320)
    state = analyzer.process(events([(10, 1, 1, 0), (200, 1, 0, 1_000_000), (30, 2, 1, 1_000_000)]))

    assert state.total_rate == pytest.approx(3.0)
    assert state.region_rates.tolist() == pytest.approx([2.0, 1.0])
    assert state.smoothed_rate == pytest.approx(3.0)


def test_ema_smoothing() -> None:
    analyzer = ActivityAnalyzer(ema_alpha=0.25, slice_us=1_000_000)
    active = analyzer.process(events([(0, 0, 1, 0), (0, 0, 1, 1_000_000)]))
    idle = analyzer.process(np.empty(0, dtype=EVENT_DTYPE))

    assert active.smoothed_rate == pytest.approx(0.5)
    assert idle.total_rate == 0.0
    assert idle.smoothed_rate == pytest.approx(0.375)


def test_empty_batch_has_zero_rates() -> None:
    state = ActivityAnalyzer().process(np.empty(0, dtype=EVENT_DTYPE))

    assert state.total_rate == 0.0
    assert state.region_rates.tolist() == [0.0, 0.0]
