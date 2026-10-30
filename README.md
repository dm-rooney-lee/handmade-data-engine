# handmade-data-engine

A handmade data engine for hand data.

Rebuilding, at home, the end-to-end process of **capturing → synchronizing → labeling → packaging into datasets** human hand manipulation demonstrations (egocentric visuo-tactile human demonstrations), using a DIY tactile glove and cameras.
A cottage-industry-scale take on the data engine of [OpenGraph Labs](https://opengraphlabs.com/).

## Approach

1. Build the e2e pipeline first on the OpenGraph Labs stack as inferred from their public SDKs.
2. Scale up data volume and size, and find bottlenecks through monitoring.
3. Swap in a better stack only where a bottleneck is measured, compare before/after on the same input, and decide whether to adopt it.

Stages and the improvement process are in [docs/PLAN.md](docs/PLAN.md); measurement and comparison results go in `docs/reports/`.

## Setup

Requires [uv](https://docs.astral.sh/uv/). It installs Python 3.12 and the dependencies into `.venv`.

```bash
uv sync
uv run docs/notes/01-time/labs/1_clocks.py
```

## References

- [OpenGraph Labs](https://opengraphlabs.com/)
- [syncfield-python](https://github.com/OpenGraphLabs/syncfield-python) — multi-stream capture and timestamping SDK
- [oglo-python](https://github.com/OpenGraphLabs/oglo-python) — OGLO tactile glove SDK
- [LeRobot](https://github.com/huggingface/lerobot)
- [DexCap](https://dex-cap.github.io/)
- [UMI](https://umi-gripper.github.io/)
