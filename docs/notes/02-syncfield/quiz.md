# 02 · SyncField

Read the concepts in [concept.html](concept.html), run the experiments in `labs/`, and write up what you understood in [my-note.md](my-note.md). Then write your own answer inside each question's **Answer** block to check that understanding. The block folds and unfolds in a Markdown preview (GitHub, PyCharm); write in it with the editor.
The SyncField source quoted in concept.html is installed at [`.venv/lib/python3.12/site-packages/syncfield/`](../../../.venv/lib/python3.12/site-packages/syncfield/) (version 0.8.14). Links into it open locally only, since `.venv` isn't committed.

```bash
# replace <path to X> with the path to that file or directory from where you run the command
uv sync --group notes
uv run --group notes <path to 1_fake_sensor.py>             # default 200Hz, 5 s, no hardware
uv run --group notes <path to 2_webcam_mic.py>              # default 5 s, audible chirp
uv run --group notes <path to 3_analyze_episode.py>         # analyzes the latest episode from lab 1 or 2
uv run --group notes <path to 3_analyze_episode.py> <path to labs/output/1_fake_sensor/ep_...>
uv run --group notes <path to 3_analyze_episode.py> <path to labs/output/2_webcam_mic/ep_...>
```

## Questions

### 1. Two timestamps
Why does SyncField keep the host-arrival `capture_ns` as the main timestamp, and put the device clock in a separate `device_timestamp_ns` field instead of replacing it? Connect this to [01-time quiz](../01-time/quiz.md) question 6, "Where to timestamp".

<details>
<summary>Answer</summary>

</details>

### 2. The polling loop
Run [`1_fake_sensor.py`](labs/1_fake_sensor.py) at its default 200Hz and analyze it with [`3_analyze_episode.py`](labs/3_analyze_episode.py). How far is the measured rate from the target? Find the lines in [`polling_sensor.py`](../../../.venv/lib/python3.12/site-packages/syncfield/adapters/polling_sensor.py) that explain it, and say which loop from [01-time lab 2](../01-time/labs/2_sleep_jitter.py) they correspond to. What would you change?

<details>
<summary>Answer</summary>

</details>

### 3. Device clock vs host clock
In the [`3_analyze_episode.py`](labs/3_analyze_episode.py) output for [lab 1](labs/1_fake_sensor.py), what do the `start` and `end` values of `device - capture` tell you about the two clocks? What do `fitted drift` and the residual tell you? The fake device drifts at 40ppm; why is the fitted drift not exactly 40? Compare with [01-time lab 3](../01-time/labs/3_clock_offset.py).

<details>
<summary>Answer</summary>

</details>

### 4. The start sequence
Why is `connect()` separate from `start_recording()`? Why does the orchestrator open the writers before calling `start_recording()`, and play the start chirp only after every stream has started? See [concept.html](concept.html) section 3, "The Stream interface and the session lifecycle", and [`orchestrator.py`](../../../.venv/lib/python3.12/site-packages/syncfield/orchestrator.py).

<details>
<summary>Answer</summary>

</details>

### 5. Crash safety
If the process is killed in the middle of a recording, which files survive and in what state? Is `flush()` after every line enough to guarantee nothing is lost? See [concept.html](concept.html) section 5, "Writers and crash safety".

<details>
<summary>Answer</summary>

</details>

### 6. The chirp
In the [`2_webcam_mic.py`](labs/2_webcam_mic.py) episode, which source does `chirp_start_source` show, and how precise is each source? Why is a frequency sweep used instead of a plain beep or a clap? See [concept.html](concept.html) section 6, "The chirp anchor".

<details>
<summary>Answer</summary>

</details>
