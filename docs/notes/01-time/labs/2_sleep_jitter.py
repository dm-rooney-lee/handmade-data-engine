"""Lab 01-2: Jitter and lag in a fixed-rate loop — relative sleep vs absolute deadline.

Goals:
- Relative sleep vs absolute deadline: see how a late wake-up carries over into later samples,
  and how that shows up in the long-run rate and lag (how far behind schedule the loop ends up).
- Tail jitter: look at p99 and max, not just the median, since a single late sample can blur
  when a contact happened.
- Rate: vary the target rate to see how well a general-purpose OS holds a fixed-rate loop, and
  why fast sensors are sampled on a microcontroller instead of a Python loop on the PC.

usage: python3 2_sleep_jitter.py [rate_hz] [duration_s]
"""
import sys
import time


def sample_with_relative_sleep(n, period_ns):
    """Sleep for one period every iteration."""
    ts = []
    for _ in range(n):
        ts.append(time.monotonic_ns())
        time.sleep(period_ns / 1e9)
    return ts


def sample_with_absolute_deadline(n, period_ns):
    """Sleep until the i-th deadline measured from the start time."""
    ts = []
    start = time.monotonic_ns()
    for i in range(n):
        # The i-th sample is due at a fixed time computed from the start: start, start + 1 period,
        # start + 2 periods, ... It doesn't depend on when the previous sample actually happened.
        deadline = start + i * period_ns

        # How long until that deadline, measured from now.
        remaining = deadline - time.monotonic_ns()

        # Ahead of schedule: sleep until the deadline (the OS may still wake us up a bit late).
        # Already past the deadline: don't sleep, take the sample right away to catch up.
        if remaining > 0:
            time.sleep(remaining / 1e9)
        ts.append(time.monotonic_ns())
    return ts


def report(name, ts, period_ns):
    intervals = sorted(b - a for a, b in zip(ts, ts[1:]))

    def pct(q: float):
        return intervals[int(q * (len(intervals) - 1))] / 1e3

    total = ts[-1] - ts[0]
    expected = (len(ts) - 1) * period_ns
    late = sum(1 for iv in intervals if iv > 2 * period_ns)
    print(
        f"  {name:17} rate={(len(ts) - 1) / (total / 1e9):8.1f}Hz  "
        f"p50={pct(0.5):7.1f}us  p99={pct(0.99):8.1f}us  max={pct(1.0):8.1f}us  "
        f"late(>2x)={late:5}  lag={(total - expected) / 1e6:+9.2f}ms"
    )


def main():
    rate_hz = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    duration_s = float(sys.argv[2]) if len(sys.argv) > 2 else 3
    period_ns = 1_000_000_000 // rate_hz
    n = int(rate_hz * duration_s)

    print(f"[target {rate_hz}Hz, period {period_ns / 1e3:.1f}us, {n} samples]")
    report("relative_sleep", sample_with_relative_sleep(n, period_ns), period_ns)
    report("absolute_deadline", sample_with_absolute_deadline(n, period_ns), period_ns)


if __name__ == "__main__":
    main()
