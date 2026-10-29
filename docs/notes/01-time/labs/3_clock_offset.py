"""Lab 01-3: Aligning two clock domains — RTT-based offset estimation and linear drift correction (simulation).

Fix a known offset and drift between the host clock and a device clock, then see how well
ping round trips alone can recover them.

Goals:
- Offset estimation: see how the offset between two clock domains can be estimated from ping
  round trips alone, as t2 - (t1 + t4) / 2.
- Drift correction: see how far a start-only offset degrades over a session because of drift,
  and how much a linear correction from start and end offsets recovers.
- mean vs min_rtt: compare the two estimators and see how the latency distribution decides
  which one works better.

usage: python3 3_clock_offset.py [drift_ppm] [session_s]
"""
import random
import sys
from random import Random

INITIAL_OFFSET_NS = 123_456_789  # how far the device clock is ahead of the host at session start
HOST_START_NS = 5_000_000_000_000  # the monotonic reference point is arbitrary (here ~83 min after boot)
PINGS = 50

rng: Random = random.Random(42)
# drift of the device clock relative to the host; each cheap crystal is off its nominal
# frequency by tens of ppm, so two of them can differ by up to the sum
drift_ppm = float(sys.argv[1]) if len(sys.argv) > 1 else 40
session_s = float(sys.argv[2]) if len(sys.argv) > 2 else 600


def device_clock(host_ns):
    # offset(x) = offset0 + drift * (x - session start)
    elapsed = host_ns - HOST_START_NS
    return host_ns + INITIAL_OFFSET_NS + int(elapsed * drift_ppm * 1e-6)


def true_offset(host_ns):
    """The offset at this instant: device reading - host reading. It changes over time with drift."""
    return device_clock(host_ns) - host_ns


def sample_one_way_latency_ns():
    """Simulated USB serial one-way latency: the sum of a bounded base delay and a long-tailed extra delay.

    Called separately for each direction of a ping, so the two directions usually differ.
    Median is about 1.1ms; about 10% exceed 2.7ms and about 1% exceed 5ms.
    """
    # Base delay: uniform between 200us and 600us, every value in the range equally likely.
    # Stands for the fixed cost of a transfer (USB polling interval, driver, serial handling).
    base = rng.uniform(200_000, 600_000)

    # Extra delay: exponential with mean 1ms (expovariate takes the rate, 1 / mean).
    # Small values are most likely, but occasionally it is many times the mean.
    # Stands for unpredictable waits such as OS scheduling or other USB traffic.
    extra = rng.expovariate(1 / 1_000_000)

    return int(base + extra)


def ping(t1):
    """Host sends at t1, the device stamps t2 on its own clock and replies, host receives at t4."""
    arrive = t1 + sample_one_way_latency_ns()
    t2 = device_clock(arrive)
    t4 = arrive + sample_one_way_latency_ns()
    return t1, t2, t4


def estimate(host_ns, method):
    """Return (midpoint_ns, estimated offset): the host time the offset was measured at, and the offset there."""
    samples = [ping(host_ns + i * 1_000_000) for i in range(PINGS)]
    # offset estimate: device time - midpoint of the round trip (assumes equal up/down latency)
    # midpoint, offset, rtt
    points = [((t1 + t4) // 2, t2 - (t1 + t4) // 2, t4 - t1) for t1, t2, t4 in samples]
    if method == "mean":
        mean_midpoint_ns = sum(p[0] for p in points) // len(points)
        mean_offset = sum(p[1] for p in points) / len(points)
        return mean_midpoint_ns, mean_offset
    if method == "min_rtt":
        midpoint_ns, offset, _ = min(points, key=lambda p: p[2])
        return midpoint_ns, offset
    raise ValueError(method)


def main():
    start = HOST_START_NS
    end = HOST_START_NS + int(session_s * 1e9)
    checkpoints = [start, (start + end) // 2, end]

    print(f"[true drift {drift_ppm}ppm, session {session_s:.0f}s, {PINGS} pings per estimate]")
    for method in ("mean", "min_rtt"):
        host0, offset0 = estimate(start, method)
        host1, offset1 = estimate(end, method)
        drift = (offset1 - offset0) / (host1 - host0)

        print(f"\n  method={method}  estimated drift={drift * 1e6:.2f}ppm")
        # At each checkpoint, predict the offset in two ways and compare each with the true offset.
        for cp in checkpoints:
            # Baseline: sync once at the start and reuse that offset for the whole session.
            # This assumes there is no drift, so its error grows over time.
            constant_offset = offset0

            # Drift-corrected: follow the line through (host0, offset0) with slope = estimated drift.
            # cp - host0 is the host time elapsed since offset0 was measured.
            # In a real pipeline, this is the offset used to convert device timestamps to host time.
            linear_offset = offset0 + drift * (cp - host0)
            print(
                f"    t={(cp - start) / 1e9:6.0f}s  "
                f"start-offset-only error={(constant_offset - true_offset(cp)) / 1e3:+10.1f}us  "
                f"linear-corrected error={(linear_offset - true_offset(cp)) / 1e3:+8.1f}us"
            )


if __name__ == "__main__":
    main()
