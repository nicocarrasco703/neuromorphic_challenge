# AGENTS.md

## Project: Neuromorphic Event Camera Challenge

### Goal

Build a simple, robust, interactive game for a public Computer Science outreach event using:

- Raspberry Pi 5
- Prophesee GenX320 event camera
- OpenEB / open-source Metavision SDK modules
- Python
- NumPy
- OpenCV

OpenEB and the camera stack are already installed and working on the target Raspberry Pi.

The game should demonstrate, in a visually intuitive way, the main idea behind event cameras:

> Event cameras report brightness changes asynchronously instead of producing conventional image frames.

The game must be suitable for a stand where many people will use it repeatedly throughout the day. Reliability, simplicity, and clear visual feedback are more important than architectural sophistication.

---

# 1. Core gameplay

The player stands in front of the event camera and completes a sequence of short challenges.

The main states are:

1. `WAITING`
2. `COUNTDOWN`
3. `MOVE`
4. `FREEZE`
5. `TARGET`
6. `RESULTS`

The first MVP only needs:

- `WAITING`
- `COUNTDOWN`
- `MOVE`
- `FREEZE`
- `RESULTS`

Later versions may add spatial challenges such as:

- move only on the left side
- move only on the right side
- generate activity inside a highlighted random region
- avoid generating events outside the target region
- combos
- reaction-time scoring
- leaderboard

The game should last roughly 20–30 seconds by default.

---

# 2. Design philosophy

Keep the implementation intentionally simple.

Do NOT introduce unnecessary abstractions, frameworks, concurrency, or machine learning.

The main loop should remain easy to understand.

The intended architecture is approximately:

```text
GenX320
   |
   v
OpenEB / Metavision
   |
   v
EventSource
   |
   v
ActivityAnalyzer
   |
   v
GameEngine
   |
   v
Renderer
```

All components may initially run in a single Python process and a single main loop.

---

# 3. Hard constraints

These constraints should be treated as project requirements.

- Python-first implementation.
- Target platform is Raspberry Pi 5.
- Sensor is Prophesee GenX320.
- Use OpenEB / open Metavision SDK modules only.
- OpenEB is already installed; do not add installation scripts unless explicitly requested.
- Do not use proprietary Metavision SDK-only components.
- No machine learning.
- No pose estimation.
- No hand detection.
- No person tracking.
- No neural networks.
- No ROS.
- No Qt.
- No PyGame unless explicitly requested later.
- No multiprocessing initially.
- No custom threading initially.
- No asyncio initially.
- No database initially.
- Use JSON for leaderboard persistence if needed.
- Use OpenCV for the fullscreen UI.
- Use NumPy vectorized operations for event processing.
- Never loop over individual events in Python.
- Game logic must operate directly on event statistics.
- Rendering must not control game timing.
- Game timing must not depend on rendered frame count.
- Prefer sensor timestamps or `time.monotonic()` for timing.
- All meaningful thresholds and durations must live in configuration.
- The game should support both live camera input and recorded event files if practical with the installed API.

Most importantly:

> DO NOT convert this project into a conventional computer-vision pipeline.

The point of the demo is to exploit event activity directly.

---

# 4. Recommended repository structure

Keep the repository small.

```text
neuromorphic-game/
|
├── AGENTS.md
├── main.py
├── config.py
├── camera.py
├── activity.py
├── game.py
├── renderer.py
├── leaderboard.py
|
├── assets/
|
└── tests/
    ├── test_activity.py
    └── test_game.py
```

Do not create additional packages or directories unless they solve a real problem.

---

# 5. Camera acquisition

The camera layer should be the only part of the project that knows about OpenEB / Metavision.

Preferred interface:

```python
class EventSource:
    def __iter__(self):
        ...
```

Each iteration should yield one batch/slice of events.

Expected event fields:

```text
x
y
p
t
```

Prefer using the installed equivalent of:

```python
from metavision_sdk_stream import Camera, CameraStreamSlicer
```

with a live camera.

If the installed OpenEB version exposes a slightly different API, adapt only `camera.py`.

Do not spread Metavision-specific API calls throughout the project.

The rest of the application should receive NumPy event arrays and remain independent of the camera API.

---

# 6. Event batching

Do not process every event individually.

Use event slices.

A reasonable starting point is:

```text
event slice duration: ~5 ms
```

This gives approximately:

```text
event processing: ~200 Hz
```

The exact value must be configurable.

Possible initial configuration:

```python
EVENT_SLICE_US = 5000
```

Do not assume rendering must run at the same rate.

---

# 7. ActivityAnalyzer

This module contains almost all of the event-processing logic.

Expected interface:

```python
class ActivityAnalyzer:
    def process(self, events) -> ActivityState:
        ...
```

Suggested output:

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class ActivityState:
    total_rate: float
    region_rates: np.ndarray
    target_rate: float
    outside_rate: float
```

The exact fields may evolve, but keep this object simple.

---

# 8. Event rate

For an event batch with `N` events over interval `dt`:

```text
rate = N / dt
```

Represent rates preferably as events per second.

Example:

```python
instant_rate = len(events) / dt_seconds
```

Do not use raw counts as the only measure if batch duration may vary.

---

# 9. Activity smoothing

Use a simple exponential moving average.

For instantaneous activity `r_k`:

```text
A_k = alpha * r_k + (1 - alpha) * A_(k-1)
```

Example:

```python
activity = alpha * instant_rate + (1.0 - alpha) * activity
```

`alpha` must be configurable.

Do not build a complicated temporal filter unless testing demonstrates a need.

---

# 10. Spatial regions

The GenX320 has a 320x320 sensor.

Spatial challenges should be implemented using boolean NumPy masks.

For example:

```python
x = events["x"]
y = events["y"]

left = x < width // 2
right = ~left

top = y < height // 2
bottom = ~top

top_left = np.count_nonzero(left & top)
top_right = np.count_nonzero(right & top)
bottom_left = np.count_nonzero(left & bottom)
bottom_right = np.count_nonzero(right & bottom)
```

For an arbitrary ROI:

```python
inside = (
    (x >= roi.x0) &
    (x < roi.x1) &
    (y >= roi.y0) &
    (y < roi.y1)
)

n_inside = np.count_nonzero(inside)
n_total = len(events)
n_outside = n_total - n_inside
```

Never write:

```python
for event in events:
    ...
```

for event-level processing.

---

# 11. GameEngine

The game engine must not know anything about OpenEB.

Expected interface:

```python
class GameEngine:
    def update(self, activity: ActivityState, now: float):
        ...
```

Use an enum for states.

Example:

```python
from enum import Enum, auto

class GameState(Enum):
    WAITING = auto()
    COUNTDOWN = auto()
    MOVE = auto()
    FREEZE = auto()
    TARGET = auto()
    RESULTS = auto()
```

Do not create one class per state.

Do not create a generic state-machine framework.

A few explicit `if` / `match` branches are preferable.

---

# 12. Basic state transitions

Initial version:

```text
WAITING
   |
   | SPACE / ENTER
   v
COUNTDOWN
   |
   | 3 s
   v
MOVE
   |
   | random duration
   v
FREEZE
   |
   | random duration
   v
MOVE / FREEZE
   |
   | until game duration ends
   v
RESULTS
```

Challenge durations should vary slightly so the player cannot simply predict every transition.

Suggested starting range:

```text
MOVE:   1.0–2.5 s
FREEZE: 1.0–2.5 s
```

Keep these values configurable.

---

# 13. MOVE scoring

During `MOVE`, high event activity should produce a high score.

Use a normalized score:

```text
move_score = clip(
    (activity - minimum_activity)
    /
    (maximum_activity - minimum_activity),
    0,
    1
)
```

Avoid relying on one fixed event-rate threshold across all environments.

---

# 14. FREEZE scoring

During `FREEZE`, lower event activity should produce a higher score.

Example:

```text
freeze_score = 1 - normalized_activity
```

The UI should clearly communicate that the player is trying to make the event stream nearly disappear.

---

# 15. TARGET scoring

Later versions can highlight a region on screen and ask the player to create movement only there.

Do not score only:

```text
target_events / total_events
```

because this makes extremely small movements artificially optimal.

Instead combine:

1. sufficient activity inside the target
2. spatial precision

Recommended form:

```text
activity_term =
    min(1, target_events / required_target_events)

precision_term =
    target_events / (total_events + epsilon)

target_score =
    activity_term * precision_term
```

Equivalent rate-based versions are acceptable.

The player should need to:

- generate enough events
- generate them mostly inside the correct region

---

# 16. Calibration

The game must include a short automatic calibration stage.

Do not hard-code absolute event-rate thresholds as the primary logic.

Suggested calibration sequence:

```text
1. Ask player to remain still for ~2–3 seconds.
2. Measure background / idle activity.
3. Ask player to move for ~2–3 seconds.
4. Measure typical active event rate.
5. Normalize MOVE/FREEZE thresholds between those values.
```

Store values such as:

```python
background_rate
active_rate
freeze_threshold
move_threshold
```

If calibration produces invalid values, fall back to conservative defaults and allow the game to continue.

A stand demo should not crash because calibration was imperfect.

---

# 17. Reaction time

Optional later feature.

When switching from `MOVE` to `FREEZE`, measure the time until activity crosses the freeze threshold.

Conceptually:

```text
reaction_time =
    threshold_crossing_time - command_change_time
```

Likewise for `FREEZE -> MOVE`.

Do not advertise this as sensor latency.

It is a gameplay reaction-time metric involving:

- human response
- scene motion
- sensor output
- event filtering
- threshold logic

Keep terminology scientifically accurate.

---

# 18. Renderer

Use OpenCV.

Expected interface:

```python
class Renderer:
    def render(
        self,
        game_state,
        activity_state,
        event_frame,
    ):
        ...
```

The UI should support fullscreen display.

The UI should be readable from a few meters away.

Use:

- large text
- high contrast
- very few simultaneous numbers
- obvious instructions
- visible score
- visible activity meter
- visual feedback for correct/incorrect actions

Avoid clutter.

---

# 19. Suggested UI layout

For a landscape monitor:

```text
┌──────────────────────────────┬─────────────────────┐
│                              │                     │
│                              │      FREEZE!        │
│                              │                     │
│      EVENT CAMERA VIEW       │     ACTIVITY        │
│                              │   ███░░░░░░ 27%     │
│                              │                     │
│                              │     SCORE 1450      │
│                              │     COMBO x4        │
│                              │                     │
└──────────────────────────────┴─────────────────────┘
```

The event-camera visualization should occupy most of the screen.

---

# 20. Event visualization

Prefer using an existing OpenEB / Metavision frame-generation utility if available.

For example, if supported by the installed OpenEB version:

```python
from metavision_sdk_core import BaseFrameGenerationAlgorithm
```

Use it only for visualization.

Game logic must not depend on generated image frames.

If the installed version does not expose a convenient renderer, implement a minimal NumPy/OpenCV visualization from event coordinates.

Do not introduce a complex event-to-frame reconstruction algorithm.

---

# 21. Different processing and rendering rates

Event processing and game logic should run at the slice rate.

Rendering should run approximately at monitor refresh rate.

For example:

```text
event processing: ~200 Hz
rendering:         ~60 Hz
```

Conceptually:

```python
for event_slice in event_source:

    activity = analyzer.process(event_slice)
    game.update(activity, now)

    if should_render(now):
        renderer.render(...)
```

Do not call expensive UI operations for every event slice if unnecessary.

---

# 22. Timing

Use:

```python
time.monotonic()
```

for wall-clock gameplay timing unless sensor timestamps are specifically needed.

Never use:

```text
number_of_rendered_frames / fps
```

to estimate elapsed game time.

Rendering may drop frames and should not alter game behavior.

---

# 23. Configuration

All important parameters should live in `config.py`.

Examples:

```python
EVENT_SLICE_US = 5000
RENDER_FPS = 60

CALIBRATION_STILL_SECONDS = 2.5
CALIBRATION_MOVE_SECONDS = 2.5

COUNTDOWN_SECONDS = 3.0
GAME_DURATION_SECONDS = 25.0

MOVE_MIN_SECONDS = 1.0
MOVE_MAX_SECONDS = 2.5

FREEZE_MIN_SECONDS = 1.0
FREEZE_MAX_SECONDS = 2.5

EMA_ALPHA = 0.2

LEADERBOARD_SIZE = 10
```

Do not scatter magic numbers through the code.

---

# 24. Leaderboard

Implement only after the game works reliably.

Use a simple JSON file.

Example:

```json
[
  {
    "name": "NIC",
    "score": 1820
  }
]
```

Requirements:

- keep only top N scores
- sort descending
- recover gracefully if JSON is missing or corrupted
- never crash the game because leaderboard persistence failed

Do not introduce SQLite or a server.

---

# 25. Controls

Keep keyboard controls minimal.

Suggested defaults:

```text
SPACE / ENTER -> start game
ESC           -> exit
R             -> restart
C             -> recalibrate
F             -> toggle fullscreen, optional
```

Avoid requiring mouse interaction during normal gameplay.

---

# 26. Debug mode

Provide an optional debug overlay.

For example:

```text
--debug
```

The debug UI may display:

- total event rate
- EMA activity
- background rate
- active calibration rate
- current thresholds
- state elapsed time
- events per ROI
- current target ROI

Debug information should not appear in normal stand mode.

---

# 27. Offline development

If supported by the installed OpenEB API, allow:

```bash
python main.py --input recording.raw
```

as well as:

```bash
python main.py
```

for live camera.

The same `ActivityAnalyzer`, `GameEngine`, and `Renderer` should work for both.

This is valuable because most game logic should be developable without physically using the sensor.

---

# 28. Error handling

This is a public stand application.

Prefer graceful degradation over crashes.

Handle at least:

- no camera found
- empty event slice
- temporary absence of events
- failed calibration
- malformed leaderboard file
- failed leaderboard write
- invalid input file
- renderer/window closure

When the camera is unavailable, display a clear error instead of a Python traceback in fullscreen mode.

Logging to the terminal is fine.

---

# 29. Performance rules

The following are mandatory:

### Never loop over individual events in Python

Bad:

```python
for event in events:
    ...
```

Good:

```python
x = events["x"]
mask = x < width // 2
count = np.count_nonzero(mask)
```

### Prefer NumPy boolean masks

Use vectorized masks for all ROI calculations.

### Avoid unnecessary copies

Do not repeatedly clone full event arrays unless required.

### Keep visualization independent

If rendering becomes expensive, lower rendering FPS before modifying event processing.

### Avoid premature C++

Do not rewrite components in C++ unless profiling demonstrates that Python/NumPy is the bottleneck.

---

# 30. Testing

Focus tests on logic that does not require the real camera.

## `test_activity.py`

Create synthetic structured NumPy event arrays.

Test:

- total event counting
- left/right region counting
- target ROI counting
- outside-target counting
- rate calculation
- EMA smoothing
- empty batches

## `test_game.py`

Test:

- state transitions
- countdown completion
- MOVE scoring
- FREEZE scoring
- TARGET scoring
- game timeout
- score accumulation
- calibration-derived thresholds

Tests should not need OpenCV windows or a connected camera.

---

# 31. Development milestones

Implement in this order.

## Milestone 1 — Camera + event rate

Goal:

```text
GenX320
  ->
event batches
  ->
total event rate
```

Acceptance criteria:

- live events arrive continuously
- total event rate is displayed in terminal
- no Python per-event loops

---

## Milestone 2 — Event visualization

Goal:

```text
camera
  ->
event visualization
  ->
OpenCV fullscreen window
```

Acceptance criteria:

- person movement is clearly visible
- image updates smoothly enough for a stand
- ESC exits cleanly

---

## Milestone 3 — MOVE / FREEZE MVP

Goal:

```text
WAITING
  ->
COUNTDOWN
  ->
MOVE
  ->
FREEZE
  ->
RESULTS
```

Acceptance criteria:

- player can complete a full game
- MOVE rewards activity
- FREEZE rewards low activity
- timing does not depend on rendering FPS
- final score appears

This is the first real playable version.

---

## Milestone 4 — Calibration

Acceptance criteria:

- background activity measured automatically
- active movement measured automatically
- thresholds adapt to current environment
- game remains playable if calibration is imperfect

---

## Milestone 5 — Spatial challenges

Add:

- LEFT
- RIGHT
- random TARGET ROI

Acceptance criteria:

- ROI decisions use only event coordinates
- no hand/person detection
- events outside target reduce score

---

## Milestone 6 — Polish

Add only after gameplay is stable:

- combos
- reaction time
- sound effects if desired
- leaderboard
- improved visuals
- attract-mode screen
- instructions for first-time players

---

# 32. Non-goals

Do NOT implement any of these unless explicitly requested later:

- semantic segmentation
- skeleton tracking
- gesture classification
- face recognition
- optical flow
- event reconstruction networks
- deep learning
- hand landmarks
- remote backend
- online accounts
- web frontend
- cloud storage
- distributed processing
- ROS
- custom C++ extensions
- elaborate plugin systems
- generic ECS architecture
- generic state-machine framework

These features are not necessary for the educational goal.

---

# 33. Code quality expectations

Prefer:

- clear functions
- short modules
- explicit control flow
- dataclasses where useful
- type hints for public interfaces
- docstrings for non-obvious logic
- comments explaining event-camera-specific assumptions

Avoid:

- excessive inheritance
- generic factories
- dependency injection frameworks
- clever abstractions
- metaprogramming
- hidden global state

This is a small scientific demo, not a production SaaS platform.

---

# 34. Scientific communication

The UI and comments should use terminology accurately.

Good phrases:

- event rate
- temporal resolution
- asynchronous events
- brightness changes
- event activity
- reaction time

Avoid claiming:

- the game measures exact sensor latency
- every event corresponds to physical motion
- event cameras have zero latency
- the generated event visualization is a conventional camera frame

The demo should help visitors understand that an event is approximately:

```text
e_i = (x_i, y_i, t_i, p_i)
```

and represents a brightness change at a pixel.

---

# 35. Desired first implementation

When starting from this repository, implement only the MVP unless explicitly asked for more.

The first working version should provide:

```text
GenX320 live input
+
event visualization
+
automatic idle/activity calibration
+
MOVE / FREEZE gameplay
+
score
+
fullscreen OpenCV UI
```

Everything else is secondary.

The core application should ideally remain small enough that a researcher can understand the entire gameplay pipeline by reading:

```text
main.py
activity.py
game.py
```

in one sitting.

---

# 36. Guiding principle

If there are two possible implementations, prefer the one that:

1. has fewer dependencies,
2. has fewer moving parts,
3. uses direct event statistics,
4. is easier to debug on a Raspberry Pi,
5. is more robust for an all-day public demo.

The purpose of the project is not to showcase software architecture.

The purpose is to showcase event-based vision.
