# Plan

- **Part 1. Staged implementation plan**: complete the e2e pipeline.
- **Part 2. Data-driven improvement plan**: find bottlenecks that appear as data volume and size grow, using monitoring, and improve based on measurements.

## Principles

1. **Complete v1 end-to-end first.**
2. **Swap a stack component only when a bottleneck is measured.** "I heard it's better" is not a reason to swap.
3. **Keep the swap points (seams) in place from v1, but finalize interface details only when a second implementation is attached.** Abstractions built around a single implementation are usually wrong.
4. **Compare on the same input, changing one thing at a time.** Build a replay source and a synthetic device from v1.
5. **The "current OGL stack" is inferred from their public SDKs (syncfield-python, oglo-python).** Their internal systems (sync service, OG Center) may differ.

## Swap points

Keep the boundaries below while building v1, so that only the affected point needs to be swapped once a bottleneck is confirmed.

| # | Swap point | v1 (inferred OGL) | v2 candidate (ideal) | Boundary interface |
|---|---|---|---|---|
| ① | Device→PC protocol | Text (line-delimited JSON) | Binary (COBS + CRC, protobuf schema) | `FrameDecoder` |
| ② | Glove firmware | C++ (Arduino) | Rust (Embassy, esp-hal) | Protocol from ① |
| ③ | Capture core | Python | Rust + PyO3 | `Stream` / session Python API |
| ④ | Storage format | JSONL + mp4 | MCAP | `EpisodeWriter` / `EpisodeReader` |
| ⑥ | Processing orchestration | Simple queue worker | Ray | `Processor` runner |

⑤ Sync method (PTP) is **excluded** due to hardware constraints at home (needs NICs with hardware timestamping; webcams don't support PTP).

---

# Part 1. Staged implementation plan (v1 e2e)

Stack: Python 3.12, FastAPI, React + Vite, PyAV, sounddevice, pyserial, Postgres, MinIO, ESP32 + Arduino C++

### A0. Concepts (1 week)
Proceed in order. For each topic: explanation → run labs → answer questions → review.
Each topic folder `docs/notes/NN-<topic>/` holds the concept explanation (`concept.html`), questions and answers (`summary.md`), and labs (`labs/`).
1. Time: clock domain, monotonic vs wall clock, sampling rate/jitter
2. Reading the SyncField code
3. Reading the OGLO code
4. Dataset structure: LeRobot format, egocentric datasets (Ego4D, HOT3D)
5. Imitation learning
- **Done when**: every question in each topic's `summary.md` is answered and reviewed

### A1. Single-stream capture + measurement foundation (1–2 weeks)
- Webcam recording with per-frame `{frame_number, capture_ns}` written to jsonl
- Episode folder v1 format: `manifest.json`, `{stream}.mp4`, `{stream}.timestamps.jsonl`, `{stream}.jsonl`
- **Synthetic device**: generates a signal with known ground-truth timing at a given rate
- **Replay source**: re-streams a saved episode at its original timing (or k× speed)
- **Benchmark harness skeleton**: measures latency, jitter, drop rate, CPU, and file size on the same input
- **Done when**: one episode folder is produced, and a drop rate/jitter report is printed for synthetic device input

### A2. DIY tactile glove (2–3 weeks)
- ESP32 + 5 FSRs + IMU, ~1kHz sampling, with device timestamps
- USB serial transfer over a text protocol, PC-side `FrameDecoder` v1
- **Done when**: finger contact shows up on a live graph, and the actual sampling rate and loss rate are measured

### A3. Multi-stream synchronization (2 weeks)
- Webcam + glove + IMU + audio in one session
- RTT-based clock offset estimation, linear drift correction from start/end offsets
- Cross-correlation check against physical event anchors (chirp/clap/tap)
- **Done when**: sync error in the tap test is 10ms or less

### A4. Ingest pipeline + monitoring (2 weeks)
- Episode upload → MinIO, metadata (episode, task, collector, quality score) → Postgres
- Post-processing jobs run by a simple queue worker
- Conversion to LeRobot format (parquet + mp4)
- Prometheus + Grafana + OpenTelemetry wired in (setup in Part 2)
- **Done when**: an uploaded episode is automatically converted into a LeRobot dataset, and per-stage metrics show up on the dashboard

### A5. Post-processing & auto-labeling (2–3 weeks)
- Segment `approach → grasp → hold → release` with a hysteresis threshold on tactile data
- MediaPipe Hands keypoints, SAM 2/3 object masks
- QA checks: frame drops, sync error, sensor gaps, calibration anomalies → quality score
- **Done when**: 20 cup-grasping demonstrations are labeled and QA'd with no human intervention

### A6. Visualization & review (1 week)
- Rerun timeline (video + tactile time series + hand keypoints)
- Web review tool: tactile graph under the video, editable segment labels
- **Done when**: label edits in the review tool are reflected in the dataset

### A7. Using the data (optional)
- Vision-to-touch model (predict contact from video), with glove data as ground truth
- Low-cost robot arm + LeRobot imitation learning

---

# Part 2. Data-driven improvement plan

## Goal

For each axis along which data grows, measure **where things first break down (the knee point)**, find the cause, and improve it.
Improvements range from config and implementation fixes to stack swaps; **try the cheapest option first and decide on adoption by measurement.**

## Growth axes

| Axis | Examples |
|---|---|
| Load within an episode | Number of streams, sampling rate, video resolution/fps |
| Episode length | 30 s → 10 min → 1 hour |
| Accumulated volume | 10 → 1,000 → 10,000 episodes, total size GB → TB |
| Concurrency | Number of concurrent capture sessions/uploads |

## Monitoring setup

- **Prometheus + Grafana** (docker-compose): metrics collection and dashboards for every layer
- **OpenTelemetry tracing**: per-stage duration of the upload → conversion → labeling → QA pipeline
- The capture process exposes metrics via `prometheus_client` (visible live during recording)
- Wired in at A4 to secure a **v1 baseline** first

## Metrics by layer

| Layer | Metrics |
|---|---|
| Device & transport | Actual sampling rate, packet loss/corruption, serial buffer overflow, bytes/s |
| Capture | Per-stream queue depth, write latency, frame drops, CPU/memory, GC pauses, disk write throughput |
| Sync | Estimated offset/drift, residual error against anchors over time |
| Storage | File size per stream per minute, write/read throughput, random seek time |
| Ingest & processing | Upload throughput, queue lag, job duration p50/p95, GPU utilization, failure/retry rate |
| Metadata DB | Query latency, row count, index hits |
| Training reads | Dataloader throughput (samples/s), video decoding cost |

## Load generation

- **Scaled synthetic device**: number of streams N × rate × duration as parameters
- **Replay at k× speed**: replay real recordings faster to increase load with realistic patterns
- **Bulk episode generator**: for accumulated-volume experiments (clone and vary real recordings)

## Procedure

1. **Baseline**: measure the default load on the current setup
2. **Step up**: grow one axis at a time and record metrics
3. **Find the knee point**: where latency, drop rate, etc. degrade sharply
4. **Confirm the cause**: use profiling (py-spy, tracing) to locate which layer/swap point the bottleneck is in
5. **Choose a fix**: cheapest first from the table below; swap the stack only when config/implementation fixes don't solve it
6. **Re-measure on the same input**: switch between v1/v2 via config and compare
7. **Record the decision**: in `docs/reports/NN-<scenario>.md`, record the axis, knee point, cause, fixes tried, before/after numbers, and **adopted/rejected** with reasons

Rejection is a result too. "Swapped it and saw no difference" is grounds for keeping v1.

If no bottleneck appears at home-scale load, **keep increasing load on that axis until a knee point shows up.** Don't swap a stack component for learning purposes alone. Finding where and why a bottleneck appears is itself the result.

## Expected bottlenecks and candidate fixes (hypotheses)

These are pre-measurement hypotheses, to be confirmed or refuted by actual measurements.

| Scenario | Expected bottleneck | Candidate fixes (cheap → expensive) |
|---|---|---|
| More streams / higher rate | JSON serialization, repeated small writes, Python GIL | Write batching → binary protocol (①) → Rust core (③) |
| Unstable device sampling | Firmware loop latency, timer precision | Interrupt/timer-based sampling → Rust firmware (②) |
| Longer episodes | Memory buildup, single huge files, batch processing at stop | Streaming writes / chunking → MCAP (④) |
| Higher resolution / fps | Video encoding CPU | Encoding preset tuning → hardware encoder (macOS VideoToolbox) |
| More episodes | Object storage small-file problem, slow listing, metadata queries | Add indexes → manifests in DB → partitioning / dataset sharding |
| Processing backlog | Single worker, idle GPU | Parallel workers → GPU batch inference → Ray (⑥) |
| Concurrent uploads | Network/MinIO throughput, upload failures | Multipart / resumable uploads → backpressure |
| Training reads | Video decoding, many small file reads | Tune parquet row groups → pre-decoded cache |

## Comparison metrics for stack swaps

Proceed with a swap only when the bottleneck is confirmed to be at that swap point, and compare with the metrics below.

| Swap | Comparison metrics |
|---|---|
| ① Text → binary | Bandwidth, decoding CPU, max stable sampling rate, corrupted packet detection rate |
| ② C++ → Rust firmware | Sampling jitter, device timestamp accuracy, binary size |
| ③ Python → Rust core | Latency/jitter/drop rate as stream count grows, CPU, tail latency (p99) |
| ④ JSONL → MCAP | File size, write throughput, read/random seek speed, corruption recovery |
| ⑥ Simple worker → Ray | Time to process N episodes, GPU utilization, failure retries |
