# 02 · SyncField

Read the concepts in [concept.html](concept.html), run the experiments in `labs/`, then write your own answer under each question's `Answer:`.
The SyncField source quoted in concept.html is installed at `.venv/lib/python3.12/site-packages/syncfield/` (version 0.8.14).

```bash
# from the repo root
uv sync --group notes
cd docs/notes/02-syncfield/labs
uv run --group notes 1_fake_sensor.py             # default 200Hz, 5 s, no hardware
uv run --group notes 1_fake_sensor.py 1000 5
uv run --group notes 2_webcam_mic.py              # default 5 s, audible chirp
uv run --group notes 3_analyze_episode.py         # analyzes the latest episode in ./output
uv run --group notes 3_analyze_episode.py output/<episode_dir>
```

## Questions

### 1. Two timestamps
Why does SyncField keep the host-arrival `capture_ns` as the main timestamp, and put the device clock in a separate `device_timestamp_ns` field instead of replacing it? Connect this to 01-time question 6.

Answer:

### 2. The polling loop
Run `1_fake_sensor.py` at 200Hz and 1000Hz and analyze both with `3_analyze_episode.py`. How far is the measured rate from the target? Find the lines in `polling_sensor.py` that explain it, and say which loop from 01-time lab 2 they correspond to. What would you change?

Answer:

### 3. Device clock vs host clock
In the `3_analyze_episode.py` output for lab 1, what do `device - capture` (start, end), `fitted drift`, and the residual each tell you? The fake device drifts at 40ppm; why is the fitted drift not exactly 40?

Answer:

### 4. The start sequence
Why is `connect()` separate from `start_recording()`? Why does the orchestrator open the writers before calling `start_recording()`, and play the start chirp only after every stream has started?

Answer:

### 5. Crash safety
If the process is killed in the middle of a recording, which files survive and in what state? Is `flush()` after every line enough to guarantee nothing is lost?

Answer:

### 6. The chirp
In the `2_webcam_mic.py` episode, what is `chirp_start_source`, and what does it mean for how precise that anchor is? Why is a frequency sweep used instead of a plain beep or a clap?

Answer:

### 7. Our design
From concept.html section 7, pick one thing you would keep as-is for our v1 and one thing you would change. Why?

Answer:
