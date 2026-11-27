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

`capture_ns` is the main timestamp because it's guaranteed all devices have this value.  
And `device_timestamp_ns` cannot be used to directly compare time between different devices.

`capture_ns` includes latency, and it is composed of average latency and jitter.  
To remove jitter, simple linear regression is used and this requires both `capture_ns` and `device_timestamp_ns`.  
SyncField keeps both values and converts them later.

</details>

### 2. The polling loop
Run [`1_fake_sensor.py`](labs/1_fake_sensor.py) at its default 200Hz and analyze it with [`3_analyze_episode.py`](labs/3_analyze_episode.py). How far is the measured rate from the target? Find the lines in [`polling_sensor.py`](../../../.venv/lib/python3.12/site-packages/syncfield/adapters/polling_sensor.py) that explain it, and say which loop from [01-time lab 2](../01-time/labs/2_sleep_jitter.py) they correspond to. What would you change?

<details>
<summary>Answer</summary>

When run at a target rate of 200Hz, it got 165.13Hz which is about 35Hz off from the target.  
`vs target: rate -17.4%  mean interval 6055.7us = target 5000.0us +1055.7us per sample` shows each loop took about 1ms longer.  
This is due to the code below:
```python
time.sleep(max(0.0, self._period - elapsed))
```
It sleeps for `period - elapsed`.  
So it's an improved version of "sampling with relative sleep" in [`2_sleep_jitter.py`](../01-time/labs/2_sleep_jitter.py).  
But it does not consider oversleeping. So the oversleep accumulates every loop.   
It would be improved if it sleeps for time left until the deadline.  
Then, next sleep will be shorter even though oversleep occurred in previous loop. 

</details>

### 3. Device clock vs host clock
In the [`3_analyze_episode.py`](labs/3_analyze_episode.py) output for [lab 1](labs/1_fake_sensor.py), what do the `start` and `end` values of `device - capture` tell you about the two clocks? What do `fitted drift` and the residual tell you? The fake device drifts at 40ppm; why is the fitted drift not exactly 40? Compare with [01-time lab 3](../01-time/labs/3_clock_offset.py).

<details>
<summary>Answer</summary>

Start and end values of `device - capture` tell:
- device clock is about 123ms ahead of host clock
- start and end have different values due to drift
 
Fitted drift tells how much time difference grows per second (ppm).  
Residual tells how much the latency jittered, with offset and drift removed.  

Fitted drift is not 40ppm because of latency jitter.  
latency = mean latency + jitter, so y = offset - mean latency - jitter, and fit_line measures the slope of y.  
- offset grows at the true drift, 40ppm.
- The mean latency is the same for every sample, so its slope is 0. It only shifts the line.
- The jitter is random, but in a short recording it can happen to lean one way over time.

So fitted drift = true drift - slope of the jitter.  
In this 5 s recording the jitter happened to grow by about 8.81us per second (later samples arrived a bit later), so fitted drift = 40 - 8.81 = 31.19ppm.  
The jitter is random, so this error can be positive or negative.  
A longer recording makes it smaller, because the same jitter is spread over more time: a 30 s recording gave 40.47ppm.

01-time lab 3 runs for 600 s, so drift changes the offset by 24,000us, far more than the jitter, and its estimate is close to 40ppm (39.8).  
Run for only 5 s, it misses too: 19ppm with mean, 0.6ppm with min_rtt.  
Its round trips cancel the mean latency, which makes the offset more accurate, not the drift.

</details>

### 4. The start sequence
Why is `connect()` separate from `start_recording()`? Why does the orchestrator open the writers before calling `start_recording()`, and play the start chirp only after every stream has started? See [concept.html](concept.html) section 3, "The Stream interface and the session lifecycle", and [`orchestrator.py`](../../../.venv/lib/python3.12/site-packages/syncfield/orchestrator.py).

<details>
<summary>Answer</summary>

Opening a device is slow and unpredictable.  
So before recording starts, let `connect()` open all devices.  
Then, all devices are ready to record at the same instant.  

The orchestrator opens the writers before `start_recording()` so the first samples can be written to the files immediately.

The chirp is played after every stream has started so its sound can be actually recorded.  
There is no point in playing the chirp if the streams aren't recording yet.

</details>

### 5. Crash safety
If the process is killed in the middle of a recording, which files survive and in what state? Is `flush()` after every line enough to guarantee nothing is lost? See [concept.html](concept.html) section 5, "Writers and crash safety".

<details>
<summary>Answer</summary>

When the process is killed in the middle of a recording, the files survive in the states below:
- `{stream}.jsonl`, `{stream}.timestamps.jsonl`: The file survives, and every flushed line is complete JSON. The last line may be cut off, but the lines before it can be read.
- `session_log.jsonl`: The file survives, and every event is flushed, so the log survives up to right before the crash.
- `sync_point.json`: The file survives, since it is written at the start of the recording.
- `manifest.json`: The file doesn't exist, since it is written only at `stop()`. So an episode without a manifest means the recording didn't finish.

`flush()` is not enough to guarantee nothing is lost in the cases below:
- When a writer uses a queue (e.g. the OGLO glove): it writes in batches, so all rows still in the queue or not yet flushed are lost.
- OS crash or power off: even flushed data can be lost. Any data not yet written to disk is lost.

</details>

### 6. The chirp
In the [`2_webcam_mic.py`](labs/2_webcam_mic.py) episode, which source does `chirp_start_source` show, and how precise is each source? Why is a frequency sweep used instead of a plain beep or a clap? See [concept.html](concept.html) section 6, "The chirp anchor".

<details>
<summary>Answer</summary>

In the lab 2 episode, `chirp_start_source` is `hardware`.  
There are three sources for `chirp_start_source`, hardware, software_fallback and silent.  
- hardware: The most precise source since expected DAC time is given  
- software_fallback: Host time stamped right before playing. This option is used when DAC time is either 0 or not provided or when callback is not returned in 0.1 s. It is too early by the unknown buffer wait. 
- silent: Sound wasn't played. This could be due to no device or not played on purpose. This host cannot be the anchor.  

Frequency sweep is used over a plain beep or a clap because:  
- beep: The same cycle repeats every 1ms, so its waveform looks the same even after shifting 1ms. The score has a peak every 1ms, which makes it difficult to identify the true position.
- clap: Sounds differ every time, so no known sound exists. Also, a person claps, not the computer, so the host clock never records when it happened.
- sweep: The pitch keeps changing, so the intervals between crests keep changing too. The crests line up only at one position, so the known sound matches the recording at only one position.  

</details>
