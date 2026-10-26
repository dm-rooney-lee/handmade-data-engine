# handmade-data-engine

손으로 만드는 손(hand) 데이터 엔진.

집에서 직접 만든 촉각 장갑과 카메라로 사람의 손 조작 시연(egocentric visuo-tactile human demonstration)을 **수집 → 동기화 → 라벨링 → 데이터셋화**하는 e2e 과정을 재현하며 공부한다.
[OpenGraph Labs](https://opengraphlabs.com/)의 data engine을 가내수공업 규모로 따라가 보는 프로젝트.

## 접근

1. 공개 SDK로 추정한 OpenGraph Labs 스택으로 e2e를 먼저 완성한다.
2. 데이터 양·크기를 키워가며 모니터링으로 병목을 찾는다.
3. 측정된 병목에 한해 더 나은 스택으로 갈아끼우고, 같은 입력으로 전후를 비교해 채택 여부를 결정한다.

자세한 단계와 개선 절차는 [docs/PLAN.md](docs/PLAN.md), 측정·비교 결과는 `docs/reports/`에 기록한다.

## 참고 자료

- [OpenGraph Labs](https://opengraphlabs.com/)
- [syncfield-python](https://github.com/OpenGraphLabs/syncfield-python) — 멀티 스트림 캡처·타임스탬프 SDK
- [oglo-python](https://github.com/OpenGraphLabs/oglo-python) — OGLO 촉각 장갑 SDK
- [LeRobot](https://github.com/huggingface/lerobot)
- [DexCap](https://dex-cap.github.io/)
- [UMI](https://umi-gripper.github.io/)
