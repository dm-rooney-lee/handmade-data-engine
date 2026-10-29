# 01 · Time

Read the concepts in [concept.html](concept.html), run the experiments in `labs/`, then write your own answer under each question's `Answer:`.

```bash
cd labs
python3 1_clocks.py
python3 2_sleep_jitter.py            # default 1000Hz, 3 s
python3 2_sleep_jitter.py 100 3
python3 3_clock_offset.py            # default drift 40ppm, 600 s session
python3 3_clock_offset.py 100 3600
```

## Questions

### 1. Why monotonic
Why should this project's timestamps use `time.monotonic_ns()` rather than `time.time()`? Which values in the `1_clocks.py` output support this?

Answer:  
time.time() is not suitable for measuring time interval because it has possibility of being adjusted by a user or NTP server.  
time.monotonic_ns() on the other hand, is not adjustable. Hence, it is suitable for measuring time interval.  
adjustable=False and monotonic=True support this.

### 2. Relative sleep vs absolute deadline
In `2_sleep_jitter.py`, why do the two approaches produce different rate and lag? Which one has better jitter (p99, max)? Why?

Answer:  
In relative_sleep, 1ms + extra time is taken per iteration.  
Thus, lag accumulates and results to lower rate.  
In absolute_deadline, if time exceeded the deadline, time remaining until the next deadline decreases.   
Therefore, lag is lower and rate is higher than relative_sleep.
absolute_deadline has better jitter because p50, p99 and max are all nearer to target period than relative_sleep.

### 3. Lowering the rate
What changes when you lower the **target rate** from 1000 to 100? Connect this to why 1kHz tactile sampling is done on the ESP32 rather than in a Python loop on the PC.

Answer:  
Lowering target rate did not make the loop more precise.  
relative_sleep shows longer delay per iteration.
absolute_deadline shows worse p99.
Wake-up delay increased to about 2.5ms.
Wake-up delay is determined by multiple factors such as OS scheduler, timer policy, etc.  
At 1kHz where the period is only 1ms, a PC wake-up delay of hundreds of µs to a few ms is too large.  
In ESP32, however, timer triggers sampling without OS scheduler at consistent interval.  
On the ESP32 the timing error is a few µs or less.

### 4. Drift correction
In `3_clock_offset.py`, why does the "start offset only" error grow over time? Where does the error that remains after linear correction come from?

Answer:  
"start offset only" error grow because it does not take drift in the calculation.  
Error grows linearly in the rate of drift.
So the longer time passes, the larger it gets.  

The error remaining after linear correction is due to the error of two points.
Each point's offset estimate is off because the up and down latencies differ, so the midpoint is not the real time t2 was stamped.  
Since linear correction is based on two points with error, there lies errors.

### 5. mean vs min_rtt
In `3_clock_offset.py`, which was more accurate, `mean` or `min_rtt`? Look at `sample_one_way_latency_ns()` and guess why. If the result differed from what you expected, write that down too.

Answer:  
sample_one_way_latency_ns() is called for sending and receiving returning different values for each latency.  
This means that error can occur in both positive and negative direction.
So in mean method, errors cancel each other resulting to more accurate result.

However, if the direction of errors are fixed to one direction, min_rtt can be more accurate for two reasons.  
One, less rtt means less error range.
Two, the errors no longer average out to 0, so the mean keeps a bias.

### 6. Where to timestamp
What problems arise if a tactile sample is timestamped when it arrives at the PC? If it's timestamped on the device instead, what has to be solved?

Answer:  
If it is timestamped on the PC, the actual time of the tactile data is incorrect due to many factors such as USB latency, buffering, OS scheduling, etc.
And the degree of lateness differs every time making multiple samples get the same timestamp or the intervals between them get distorted.
If it is timestamped on the device, it has to convert the device time to PC time.
This requires estimating offset, correcting drift and verification using anchor.
