"""Lab 02-1: Record a session with a fake sensor — no hardware needed.

Goals:
- Lifecycle: drive a SessionOrchestrator through connect → start → stop without the viewer,
  and see which files one recording produces.
- Two timestamps per sample: the fake device returns its own clock reading (device_ns), and
  SyncField adds capture_ns when the read returns. See how both land in the same JSONL row.
- Sampling loop: the fake sensor runs at a fixed rate on SyncField's polling loop; lab 3 then
  checks how well that loop holds the target rate.

usage: uv run --group notes 1_fake_sensor.py [rate_hz] [duration_s]
"""
import math
import random
import sys
import time
from collections.abc import Callable
from pathlib import Path

import syncfield as sf
from syncfield.adapters import PollingSensorStream
from syncfield.tone import SilentChirpPlayer

OUTPUT_DIR = Path(__file__).parent / "output" / Path(__file__).stem  # output/<this lab>/ep_*

# The fake device's clock, as in 01-time lab 3: offset(x) = offset0 + drift * (x - start)
DEVICE_OFFSET0_NS = 123_456_789
DEVICE_DRIFT_PPM = 40

latency_rng = random.Random(42)  # fixed seed so every run gets the same fake latencies


def make_fake_device(start_ns: int) -> Callable[[], tuple[dict[str, float], int]]:
    def read() -> tuple[dict[str, float], int]:
        # The device samples first and stamps the sample on its own clock...
        host_now = time.monotonic_ns()
        device_ns = host_now + DEVICE_OFFSET0_NS + int((host_now - start_ns) * DEVICE_DRIFT_PPM * 1e-6)
        fake_value = math.sin(2 * math.pi * 1.0 * (host_now - start_ns) / 1e9)  # a 1 Hz sine

        # ...then the sample takes a while to reach the host (USB, buffering), like a real device.
        time.sleep(latency_rng.uniform(0.0002, 0.0008))

        # Returning (channels, device_ns) tells SyncField this sample carries a device timestamp.
        return {"value": fake_value}, device_ns

    return read


def main() -> None:
    rate_hz = float(sys.argv[1]) if len(sys.argv) > 1 else 200
    duration_s = float(sys.argv[2]) if len(sys.argv) > 2 else 5

    # No viewer, no host microphone, no chirp: this lab needs no hardware at all.
    session = sf.SessionOrchestrator(
        host_id="lab_host",
        output_dir=OUTPUT_DIR,
        chirp_player=SilentChirpPlayer(),
        enable_host_audio=False,
    )
    # SyncField's hint for read says "returns a dict", but the loop also accepts (dict, device_ns).
    # The hint is older than the tuple support, so silence this one check.
    read_fake_device = make_fake_device(time.monotonic_ns())
    session.add(PollingSensorStream("fake_glove", read=read_fake_device, hz=rate_hz))  # type: ignore[arg-type]

    session.connect()  # open devices, start the capture loop (preview only, nothing written yet)
    session.start(countdown_s=0)  # write sync_point, open writers, start_recording on every stream
    print(f"recording {duration_s:.0f}s at {rate_hz:.0f}Hz ...")
    time.sleep(duration_s)
    report = session.stop()  # stop_recording on every stream, write manifest.json
    session.disconnect()

    episode_dir = session.last_episode_dir
    assert episode_dir is not None  # set by stop()
    print(f"\nepisode: {episode_dir}")
    for episode_file in sorted(episode_dir.iterdir()):
        print(f"  {episode_file.name:28} {episode_file.stat().st_size:>9,} bytes")
    for finalization in report.finalizations:
        print(f"\n  stream={finalization.stream_id} status={finalization.status} frames={finalization.frame_count}")


if __name__ == "__main__":
    main()
