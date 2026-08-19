"""Configuration for the neuromorphic event-camera game.

Keep gameplay and event-processing tuning values here so they can be adjusted
at the outreach stand without changing the processing code.
"""

# Acquisition and event processing
EVENT_SLICE_US = 5_000
SENSOR_WIDTH = 320
SENSOR_HEIGHT = 320

# Activity is expressed in events per second.
EMA_ALPHA = 0.2

# Terminal-only Milestone 1 feedback.
TERMINAL_REPORT_INTERVAL_SECONDS = 0.5
