"""Lab 01-1: Comparing clocks — properties, measured resolution, reference points.

Goals:
- Properties: see which clocks are adjustable or monotonic, and why timestamps should use monotonic.
- Measured resolution: confirm the smallest step Python can observe on this machine is far finer
  than other error sources (loop jitter, USB latency), so resolution is not the bottleneck.
- Reference points: see that time_ns counts from the Unix epoch while monotonic_ns counts from an
  arbitrary point, so a monotonic value means nothing on its own, only differences do.
"""
import time
from typing import Literal

ClockName = Literal["time", "monotonic", "perf_counter", "process_time"]
CLOCKS: list[ClockName] = ["time", "monotonic", "perf_counter", "process_time"]


def measure_resolution(time_fn, samples=10_000):
    """Measure the smallest interval at which the value changes."""
    deltas = []
    for _ in range(samples):
        a = time_fn()
        b = time_fn()
        while b == a:
            b = time_fn()
        deltas.append(b - a)
    deltas.sort()
    return deltas[0], deltas[len(deltas) // 2]


def main():
    print("[clock properties]")
    for clock_name in CLOCKS:
        info = time.get_clock_info(clock_name)
        print(
            f"  {clock_name:13} adjustable={info.adjustable!s:5} monotonic={info.monotonic!s:5} "
            f"resolution={info.resolution:.1e}s  impl={info.implementation}"
        )

    print("\n[measured resolution]")
    for time_fn in (time.time_ns, time.monotonic_ns, time.perf_counter_ns):
        lo, median = measure_resolution(time_fn)
        print(f"  {time_fn.__name__:18} min={lo}ns  median={median}ns")

    print("\n[reference points]")
    print(f"  time_ns      = {time.time_ns()}")
    print(f"  monotonic_ns = {time.monotonic_ns()}")


if __name__ == "__main__":
    main()
