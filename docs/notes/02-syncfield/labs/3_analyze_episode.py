"""Lab 02-3: Analyze a recorded episode — 01-time's metrics on real SyncField output.

Goals:
- Sample intervals: compute rate, p50/p99/max interval, and late samples from capture_ns, the
  same metrics as 01-time lab 2, but on what SyncField actually wrote.
- Two clocks per sample: where device_timestamp_ns exists, look at device - capture over the
  session. Its trend is offset + drift (01-time lab 3); its wobble is the arrival latency jitter.
- Anchors: see where the chirps and the recording anchor sit relative to each stream's samples.

usage: uv run --group notes 3_analyze_episode.py [episode_dir]   (default: latest in ./output)
"""
import json
import sys
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def percentile(sorted_values, q):
    return sorted_values[int(q * (len(sorted_values) - 1))]


def fit_line(xs, ys):
    """Least-squares line through (xs, ys). Returns (slope, intercept)."""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    return slope, mean_y - slope * mean_x


def report_intervals(rows, target_hz):
    capture = [r["capture_ns"] for r in rows]
    intervals = sorted(b - a for a, b in zip(capture, capture[1:]))
    total_s = (capture[-1] - capture[0]) / 1e9
    period_ns = 1e9 / target_hz if target_hz else percentile(intervals, 0.5)
    late = sum(1 for iv in intervals if iv > 2 * period_ns)
    print(
        f"    rate={(len(capture) - 1) / total_s:8.2f}Hz (target {target_hz or '?'})  "
        f"p50={percentile(intervals, 0.5) / 1e3:8.1f}us  p99={percentile(intervals, 0.99) / 1e3:8.1f}us  "
        f"max={intervals[-1] / 1e3:8.1f}us  late(>2x)={late}"
    )


def report_two_clocks(rows):
    pairs = [(r["capture_ns"], r["device_timestamp_ns"]) for r in rows if r.get("device_timestamp_ns") is not None]
    if len(pairs) < 2:
        print("    device_timestamp_ns: none (host arrival time only)")
        return

    # device - capture = (device clock - host clock) - arrival latency
    xs = [(c - pairs[0][0]) / 1e9 for c, _ in pairs]  # seconds since the first sample
    diffs = [(d - c) / 1e3 for c, d in pairs]  # us
    slope, intercept = fit_line(xs, diffs)
    residuals = sorted(y - (intercept + slope * x) for x, y in zip(xs, diffs))
    print(
        f"    device - capture: start={diffs[0]:12.1f}us  end={diffs[-1]:12.1f}us  "
        f"fitted drift={slope:.2f}ppm"
    )
    print(
        f"    residual around the line: p1={percentile(residuals, 0.01):+8.1f}us  "
        f"p50={percentile(residuals, 0.5):+8.1f}us  p99={percentile(residuals, 0.99):+8.1f}us"
    )


def main():
    if len(sys.argv) > 1:
        episode_dir = Path(sys.argv[1])
    else:
        episode_dir = max(OUTPUT_DIR.glob("ep_*"), key=lambda p: p.stat().st_mtime)
    sync_point = json.loads((episode_dir / "sync_point.json").read_text())
    manifest = json.loads((episode_dir / "manifest.json").read_text())
    session_start = sync_point["monotonic_ns"]

    def since_start_ms(ns):
        return (ns - session_start) / 1e6

    print(f"[{episode_dir.name}]  host={sync_point['host_id']}  started {sync_point['iso_datetime']}")
    for name in ("chirp_start", "chirp_stop"):
        if f"{name}_ns" in sync_point:
            print(
                f"  {name:11} at {since_start_ms(sync_point[f'{name}_ns']):9.1f}ms  "
                f"source={sync_point.get(f'{name}_source')}"
            )

    for stream_id, info in manifest["streams"].items():
        print(f"\n  stream={stream_id}  kind={info['kind']}  status={info['status']}  frames={info['frame_count']}")
        anchor = info.get("recording_anchor")
        if anchor:
            print(
                f"    first sample at {since_start_ms(anchor['first_frame_host_ns']):9.1f}ms  "
                f"(armed -> first sample {anchor['first_frame_latency_ns'] / 1e6:.2f}ms)"
            )

        path = episode_dir / f"{stream_id}.jsonl"
        if not path.exists():
            path = episode_dir / f"{stream_id}.timestamps.jsonl"
        rows = load_jsonl(path)
        if len(rows) < 2:
            print("    too few samples")
            continue
        report_intervals(rows, info["capabilities"].get("target_hz"))
        report_two_clocks(rows)


if __name__ == "__main__":
    main()
