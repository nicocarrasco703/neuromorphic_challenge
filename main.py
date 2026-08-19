"""Milestone 1 runner: OpenEB event slices to vectorized terminal activity."""

from __future__ import annotations

import argparse
import sys

from activity import ActivityAnalyzer
from camera import CameraError, EventSource
from config import EVENT_SLICE_US, TERMINAL_REPORT_INTERVAL_SECONDS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Neuromorphic event-rate monitor")
    parser.add_argument("--input", help="Path to a recorded OpenEB .raw file; omit for live camera")
    parser.add_argument("--slice-us", type=int, default=EVENT_SLICE_US, help="Event slice duration in microseconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = EventSource(args.input, slice_us=args.slice_us)
    analyzer = ActivityAnalyzer(slice_us=args.slice_us)
    next_report_time = 0.0

    print("Reading", args.input if args.input else "live camera", f"({args.slice_us} us slices).")
    try:
        for events in source:
            activity = analyzer.process(events)
            # Event timestamps, not render frames, set this reporting cadence.
            event_time = float(events["t"][-1]) / 1_000_000.0 if len(events) else next_report_time
            if event_time >= next_report_time:
                print(
                    f"rate={activity.total_rate:9.0f} ev/s  "
                    f"ema={activity.smoothed_rate:9.0f} ev/s  "
                    f"left={activity.region_rates[0]:9.0f}  right={activity.region_rates[1]:9.0f}"
                )
                next_report_time = event_time + TERMINAL_REPORT_INTERVAL_SECONDS
    except CameraError as exc:
        print(f"Camera error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
