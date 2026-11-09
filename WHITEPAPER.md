# 백서 — intellectism news collector

## 초록

`intellectism-news`는 **공개 뉴스 수집기**입니다. 하나의 수집 엔진으로 노동·소유·정치경제 분야의 뉴스를 모으고, 점수화·중복 제거·검증을 거쳐 분야별 10개의 후보를 JSON과 Markdown으로 남깁니다. 2026년 11월 10일 기준으로 3개 분야가 실제로 돌아갑니다.

이 저장소의 경계는 **수집기**입니다. 편집·검토·방송·발행·정정은 [`../intellectism/`](../intellectism/)가 맡습니다. 수집기는 공개 데이터만 만지고, LLM 키·private 데이터·영상 렌더링은 로컬 채널 호스트에만 둡니다. 이 경계 덕분에 GitHub 쪽이 뚫려도 LLM 키와 private 데이터는 안전하고, 로컬 호스트가 뚫려도 공개 데이터만 영향을 받습니다. 파이프라인은 전부 무료 티어와 무료 도구로 구성됩니다.

## 1. 문제

- **정보 과잉**: 노동·소유·정치경제 분야의 뉴스는 RSS, 정부 API, arXiv, 학술 검색에 흩어져 있습니다. 매일 같은 기준으로 고르기 어렵습니다.
- **재현성**: 어떤 기준으로 후보를 골랐는지, 어떤 소스가 실패했는지 기록하지 않으면 다음 날 같은 실수를 반복합니다.
- **보안**: LLM API 키와 private 데이터를 CI에 넣으면 로그·아티팩트·포크 PR을 통해 유출될 수 있습니다.
- **비용**: 유료 API와 클라우드 스토리지를 쓰면 개인 채널 운영 비용이 빠르게 늘어납니다.
- **편집 병목**: 수집·큐레이션·블로그·영상·쇼츠가 한 흐름으로 이어지지 않으면 매일 수동 작업이 필요합니다.

## 2. 접근

1. **공개 ETL과 private compute를 분리**합니다. 공개 수집은 시크릿 없이 GitHub Actions에서 돌고, LLM·음성·렌더링은 `intellectism/`의 Mac mini에서 돌립니다.
2. **PR을 결정 단위로 씁니다.** PR은 공개 데이터의 변경 제안이고, private 결과물은 PR에 넣지 않습니다. PR에는 메타데이터와 링크만 남깁니다.
3. **TDD로 검증 계층을 만듭니다.** Python 수집기와 Rust 검증기를 함께 두고, `make check`가 모든 JSON을 검사합니다.
4. **무료 티어를 기본값으로 둡니다.** GitHub Actions와 무료 소스만 사용합니다.
5. **E2E를 실제 소스로 돌립니다.** `make e2e`는 임시 루트에서 실제 RSS/API/arXiv를 호출하고 결과를 검증합니다.

## 3. 아키텍처

```text
[GitHub Actions]  공개 수집, 테스트, lint, PR 생성
        │  raw JSON / digest / PR
        ▼
[Git + PR]  데이터·다이제스트·메타데이터
        │  handoff
        ▼
[intellectism/]  채널 편집·검토·방송·발행·정정
        │
        ▼
[YouTube / 블로그]  공개 배포
```

자세한 구성과 결정 기록은 [ARCHITECTURE.md](ARCHITECTURE.md)에 있습니다.

## 4. 구현

- **Python 3.14** 수집기: `src/intellectism_news/`
- **Rust 1.98** 검증기: `crates/inews-core/` (`normalize`, `validate`)
- **설정**: `config/fields.yaml` — 분야별 키워드, 소스, 가중치, 제한
- **수집 소스**: RSS, Federal Register, arXiv, OpenAlex
- **큐레이션**: 키워드 가중치, 소스 가중치, 중복 병합, 부정 키워드, 분야별 상한
- **재시도**: 429/5xx에 대해 2/5/10초 백오프, `retries` 기록
- **출력**: `data/<field>/<YYYY>/<YYYY-MM-DD>.json`, `digests/<field>/<YYYY>/<YYYY-MM-DD>.md`
- **상태**: `state/<field>/seen.json` — 같은 항목 반복 방지

## 5. 무료 파이프라인

| 워크플로 | 트리거 | 역할 |
|---|---|---|
| `ci.yml` | PR, push | `make check` — 테스트, lint, Rust 검증 |
| `e2e.yml` | 스케줄, 수동 | `make e2e` — 실제 수집을 임시 루트에서 실행 |
| `daily.yml` | 스케줄, 수동 | `make daily` — 운영 수집 및 커밋 |

로컬 진입점:

- `make setup` — Python 3.14 + Rust 1.98 환경
- `make test` — Python + Rust 테스트
- `make lint` — ruff, cargo fmt, clippy
- `make check` — 테스트 + lint + Rust normalize/validate
- `make daily` — 운영 수집
- `make e2e` — 실제 E2E
- `make candidates` — 후보 Markdown/JSON

비용은 GitHub Actions 무료 티어로 끝납니다. 유료 API는 없습니다.

## 6. 평가

2026년 11월 9일 기준 실제 E2E 결과:

| 분야 | 후보 | 오류 | 재시도 |
|---|---:|---:|---:|
| labor | 10 | 0 | 0 |
| ownership | 10 | 0 | 0 |
| policy | 10 | 0 | 0 |

- 3개 분야 수집 시간: 약 38초 (labor 12.3s, ownership 10.7s, policy 14.6s)
- 테스트: Python 68개 + Rust 26개
- `make check`: 전체 통과
- `make e2e`: 10/10/10, 0 errors

## 7. 한계

- **OpenAlex 무료 일일 예산**: 현재 IP의 무료 예산이 소진되어 OpenAlex 소스는 `enabled: false`로 꺼져 있습니다. 예산이 회복되면 `enabled: true`로 다시 켤 수 있습니다.
- **수집기 경계**: 이 저장소는 수집·검증까지 담당합니다. 편집·영상·업로드는 `intellectism/`에서 합니다.
- **콘텐츠 품질**: 후보 수는 10개를 맞췄지만, 일부 학술 항목은 채널 주제와 거리가 있을 수 있습니다. 부정 키워드와 분야별 쿼리로 계속 조정해야 합니다.
- **API 키**: BLS·EIA·Congress.gov·Companies House는 무료 키가 필요합니다. GitHub Secrets에 넣습니다.

## 8. 로드맵

| 단계 | 내용 | 상태 |
|---|---|---|
| M0–M6 | 환경, 스키마, 3개 분야, 후보 통합, Actions, Rust, 안정화 | 완료 |
| M7 | E2E 파이프라인 + 무료 CI | 완료 |
| M8 | 채널 핸드오프 문서화 | 완료 |
| M9 | 채널 E2E (in `intellectism/`) — A/B 2D/3D 앵커 파일럿 | 미완료 (구조만) |

## 9. 참고

- [README.md](README.md) — 빠른 시작
- [ARCHITECTURE.md](ARCHITECTURE.md) — 구성 요소, 보안, 저장소, 결정 기록
- [MILESTONES.md](MILESTONES.md) — 마일스톤과 테스트
- [`../intellectism/WHITEPAPER.md`](../intellectism/WHITEPAPER.md) — 채널 백서
