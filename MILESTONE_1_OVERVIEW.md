# Milestone 1 — Camera + Event Rate

This first implementation establishes the event-processing foundation for the
neuromorphic mini-game. It reads asynchronous events directly from OpenEB,
measures their activity as rates, and does not reconstruct conventional camera
frames or process events one at a time in Python.

## Implemented modules

- `config.py` centralizes the initial event-slice duration (`5 ms`), sensor
  geometry, EMA smoothing, and terminal report interval.
- `camera.py` provides `EventSource`, the only module aware of OpenEB. It can
  open an OpenEB `.raw` recording now, or use the first live camera when no
  input path is supplied later.
- `activity.py` provides `ActivityAnalyzer`. It uses NumPy operations to
  calculate total event rate, left/right event rates, and an exponentially
  smoothed total rate.
- `main.py` connects the source and analyzer, displaying activity in events
  per second in the terminal.
- `tests/test_activity.py` uses synthetic structured event arrays to verify
  rate calculation, vectorized left/right regions, EMA smoothing, and empty
  batches.

## Running with a recording

Activate the dedicated OpenEB-compatible environment, then run:

```bash
conda activate neuromorphic-challenge
python main.py --input recordings/rec_1.raw
```

Omit `--input` when the GenX320 is connected to use live input:

```bash
python main.py
```

## Alignment with Milestone 1

Milestone 1 requires the path **GenX320 → event batches → total event rate**.
The implementation meets this with configurable fixed-duration event slices
(`EVENT_SLICE_US = 5000`) produced by OpenEB and converted to events per
second by `ActivityAnalyzer`.

The included `rec_1.raw` smoke test decoded continuously and produced rates in
the terminal. Unit tests pass (`3 passed`). The same source interface supports
offline recordings today and live camera input when the sensor is available.

The implementation follows the project constraints: event logic uses direct
event statistics, NumPy vectorization is used for spatial counting, and no
per-event Python loops, frame-based CV pipeline, threading, or additional
frameworks were introduced.
