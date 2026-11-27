"""Lab 02-3: Analyze a recorded episode — 01-time's metrics on real SyncField output.

Goals:
- Sample intervals: compute rate, p50/p99/max interval, and late samples from capture_ns, the
  same metrics as 01-time lab 2, but on what SyncField actually wrote.
- Two clocks per sample: where device_timestamp_ns exists, look at device - capture over the
  session. Its trend is offset + drift (01-time lab 3); its wobble is the arrival latency jitter.
- Anchors: see where the chirps and the recording anchor sit relative to each stream's samples.

usage: uv run --group notes 3_analyze_episode.py [episode_dir]
       default: the latest episode from lab 1 or 2 (output/1_fake_sensor/, output/2_webcam_mic/)
"""
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path(__file__).parent / "output"

JsonLine = dict[str, Any]  # one parsed JSONL line


def load_jsonl(path: Path) -> list[JsonLine]:
    with open(path) as file:
        return [json.loads(line) for line in file if line.strip()]


def percentile(sorted_values: Sequence[float], quantile: float) -> float:
    """quantile is 0..1, e.g. 0.99 for p99. sorted_values must already be sorted."""
    return sorted_values[int(quantile * (len(sorted_values) - 1))]


def fit_line(x_values: Sequence[float], y_values: Sequence[float]) -> tuple[float, float]:
    """Least-squares line through (x_values, y_values). Returns (slope, intercept)."""
    count = len(x_values)
    mean_x = sum(x_values) / count
    mean_y = sum(y_values) / count
    x_spread = sum((x - mean_x) ** 2 for x in x_values)  # how far x spreads around its mean
    xy_co_spread = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))  # how y moves with x
    slope = xy_co_spread / x_spread
    return slope, mean_y - slope * mean_x


def report_intervals(json_lines: list[JsonLine], target_hz: float | None) -> None:
    capture_ns_list = [json_line["capture_ns"] for json_line in json_lines]
    # time between consecutive samples, sorted so percentile() can index into it
    intervals_ns = sorted(
        current_ns - previous_ns for previous_ns, current_ns in zip(capture_ns_list, capture_ns_list[1:])
    )
    duration_s = (capture_ns_list[-1] - capture_ns_list[0]) / 1e9
    expected_interval_ns = 1e9 / target_hz if target_hz else percentile(intervals_ns, 0.5)
    late_count = sum(1 for interval_ns in intervals_ns if interval_ns > 2 * expected_interval_ns)
    rate_hz = (len(capture_ns_list) - 1) / duration_s
    print(
        f"    rate={rate_hz:8.2f}Hz (target {target_hz or '?'})  "
        f"p50={percentile(intervals_ns, 0.5) / 1e3:8.1f}us  p99={percentile(intervals_ns, 0.99) / 1e3:8.1f}us  "
        f"max={intervals_ns[-1] / 1e3:8.1f}us  late(>2x)={late_count}"
    )
    if target_hz:
        mean_interval_ns = duration_s * 1e9 / (len(capture_ns_list) - 1)
        print(
            f"    vs target: rate {(rate_hz - target_hz) / target_hz * 100:+.1f}%  "
            f"mean interval {mean_interval_ns / 1e3:.1f}us = target {expected_interval_ns / 1e3:.1f}us "
            f"{(mean_interval_ns - expected_interval_ns) / 1e3:+.1f}us per sample"
        )


def report_two_clocks(json_lines: list[JsonLine]) -> None:
    capture_and_device_ns = [
        (json_line["capture_ns"], json_line["device_timestamp_ns"])
        for json_line in json_lines
        if json_line.get("device_timestamp_ns") is not None
    ]
    if len(capture_and_device_ns) < 2:
        print("    device_timestamp_ns: none (host arrival time only)")
        return

    # device - capture = (device clock - host clock) - arrival latency
    first_capture_ns = capture_and_device_ns[0][0]
    elapsed_s = [(capture_ns - first_capture_ns) / 1e9 for capture_ns, _ in capture_and_device_ns]
    device_minus_capture_us = [(device_ns - capture_ns) / 1e3 for capture_ns, device_ns in capture_and_device_ns]
    # the slope is in us per second, and 1us per 1s is exactly 1ppm
    drift_ppm, offset_at_first_sample_us = fit_line(elapsed_s, device_minus_capture_us)
    residuals_us = sorted(
        difference_us - (offset_at_first_sample_us + drift_ppm * seconds)
        for seconds, difference_us in zip(elapsed_s, device_minus_capture_us)
    )
    print(
        f"    device - capture: start={device_minus_capture_us[0]:12.1f}us  "
        f"end={device_minus_capture_us[-1]:12.1f}us  fitted drift={drift_ppm:.2f}ppm"
    )
    print(
        f"    residual around the line: p1={percentile(residuals_us, 0.01):+8.1f}us  "
        f"p50={percentile(residuals_us, 0.5):+8.1f}us  p99={percentile(residuals_us, 0.99):+8.1f}us"
    )


def main() -> None:
    if len(sys.argv) > 1:
        episode_dir = Path(sys.argv[1])
    else:
        # every ep_* under output/<lab>/, then the one modified most recently (not by name)
        episode_dir = max(OUTPUT_DIR.glob("*/ep_*"), key=lambda episode: episode.stat().st_mtime)
    sync_point = json.loads((episode_dir / "sync_point.json").read_text())
    manifest = json.loads((episode_dir / "manifest.json").read_text())
    session_start_ns = sync_point["monotonic_ns"]

    def since_start_ms(host_ns: int) -> float:
        return (host_ns - session_start_ns) / 1e6

    print(f"[{episode_dir.name}]  host={sync_point['host_id']}  started {sync_point['iso_datetime']}")
    for chirp_name in ("chirp_start", "chirp_stop"):
        if f"{chirp_name}_ns" in sync_point:
            print(
                f"  {chirp_name:11} at {since_start_ms(sync_point[f'{chirp_name}_ns']):9.1f}ms  "
                f"source={sync_point.get(f'{chirp_name}_source')}"
            )

    for stream_id, stream_info in manifest["streams"].items():
        print(
            f"\n  stream={stream_id}  kind={stream_info['kind']}  status={stream_info['status']}  "
            f"frames={stream_info['frame_count']}"
        )
        recording_anchor = stream_info.get("recording_anchor")
        if recording_anchor:
            print(
                f"    first sample at {since_start_ms(recording_anchor['first_frame_host_ns']):9.1f}ms  "
                f"(armed -> first sample {recording_anchor['first_frame_latency_ns'] / 1e6:.2f}ms)"
            )

        # sensors write {stream}.jsonl; video and audio write {stream}.timestamps.jsonl next to the media file
        samples_path = episode_dir / f"{stream_id}.jsonl"
        if not samples_path.exists():
            samples_path = episode_dir / f"{stream_id}.timestamps.jsonl"
        json_lines = load_jsonl(samples_path)
        if len(json_lines) < 2:
            print("    too few samples")
            continue
        report_intervals(json_lines, stream_info["capabilities"].get("target_hz"))
        report_two_clocks(json_lines)


if __name__ == "__main__":
    main()
