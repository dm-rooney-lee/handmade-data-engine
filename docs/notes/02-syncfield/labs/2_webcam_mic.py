"""Lab 02-2: Record the Mac's webcam and microphone with start/stop chirps.

Goals:
- Real devices: record a video stream and the host microphone in one session, the minimal
  version of what SyncField does in the field.
- Chirps: hear the start and stop chirps, and find them later in sync_point.json. Since the
  chirps are recorded by the microphone, the audio track carries a shared physical anchor.
- Host-arrival timestamps: webcam frames have no device clock, so capture_ns is the only
  timestamp. Lab 3 shows what that looks like next to the fake sensor from lab 1.

The first run asks for camera and microphone permission for your terminal (or PyCharm).

usage: uv run --group notes 2_webcam_mic.py [duration_s] [chirp_mode]
       chirp_mode: audible (default, 400-2500Hz) | ultrasound (17-19kHz, SyncField's default) | off
"""
import sys
import time
from pathlib import Path

import syncfield as sf
from syncfield.adapters import UVCWebcamStream

OUTPUT_DIR = Path(__file__).parent / "output"


def main():
    duration_s = float(sys.argv[1]) if len(sys.argv) > 1 else 5
    chirp_mode = sys.argv[2] if len(sys.argv) > 2 else "audible"

    # enable_host_audio=True (the default) adds a HostAudioStream for the microphone
    # automatically when no other stream records audio.
    session = sf.SessionOrchestrator(host_id="lab_host", output_dir=OUTPUT_DIR)
    session.set_chirp_mode(chirp_mode)
    session.add(UVCWebcamStream("mac_webcam", device_index=0, output_dir=session.output_dir))

    session.connect()
    session.start(countdown_s=3, on_countdown_tick=lambda n: print(f"  {n} ..."))
    print(f"recording {duration_s:.0f}s ...")
    time.sleep(duration_s)
    report = session.stop()
    session.disconnect()

    episode_dir = session.last_episode_dir
    print(f"\nepisode: {episode_dir}")
    for path in sorted(episode_dir.iterdir()):
        print(f"  {path.name:28} {path.stat().st_size:>11,} bytes")
    for f in report.finalizations:
        print(f"\n  stream={f.stream_id} status={f.status} frames={f.frame_count}")


if __name__ == "__main__":
    main()
