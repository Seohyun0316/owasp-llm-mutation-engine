# Day 1 Checklist (2/10) — Contract / Policy / Seed / Backlog Verification

본 문서는 Day 1 산출물이 **main에 정확히 반영되었고**, 팀이 동일한 계약(contract)과 정책(policy)을 기반으로 개발을 시작할 수 있는 상태인지 확인한 결과를 기록한다.  
검증은 (A) Git 기준, (B) 문서/데이터 내용, (C) 재현성/정책 스모크 테스트의 3축으로 수행하였다.

---

## 0. Scope (Day 1 Deliverables)

- `docs/operator_contract.md` (v0.1)
- `docs/operator_backlog.md` (v0.1) *(파일명은 레포 기준으로 조정 가능)*
- `examples/seed_samples.json` (v1)

---

## A) Git 기준 검증 (Merge / Location / Evidence)

### A-1. main merge 확인
- [ ] `main` 브랜치에 Day 1 관련 PR이 모두 merge 되었음을 확인했다.
- [ ] 로컬에서 `git checkout main && git pull` 후, Day 1 변경사항이 최신 상태로 반영됨을 확인했다.

### A-2. 파일 경로/배치 확인
- [ ] `docs/operator_contract.md`가 `docs/` 하위에 존재함을 확인했다.
- [ ] operator backlog 문서가 `docs/` 하위에 존재함을 확인했다.
- [ ] `examples/seed_samples.json`가 `examples/` 하위에 존재함을 확인했다.

### A-3. 증빙 링크(선택)
- PR/커밋 링크:
  - operator contract: _______________________________
  - operator backlog: _______________________________
  - seed samples: _______________________________

---

## B) 문서/데이터 내용 검증 (Contract Completeness / Backlog Quality / Seed Corpus)

### B-1. Operator Contract(v0.1) 필수 항목 충족 확인
`docs/operator_contract.md`에서 아래 항목이 명확히 정의되어 있음을 확인했다.

- [ ] Operator metadata 필수 필드:
  - [ ] `op_id`
  - [ ] `bucket_tags[]`
  - [ ] `surface_compat[]`
  - [ ] `risk_level`
  - [ ] `strength_range`
- [ ] `apply()` 시그니처 정의(입력: `seed_text`, `ctx`, `rng` 등)
- [ ] 반환 규격 정의:
  - [ ] `status` ∈ {`OK`, `SKIPPED`, `INVALID`}
  - [ ] `mutation_trace` 최소 필드 및 형식
- [ ] 문자열 처리 정책 정의:
  - [ ] UTF-8 처리 원칙
  - [ ] 최대 길이 제한(또는 truncate 규칙)
  - [ ] 줄바꿈/공백 정규화 규칙
- [ ] RNG 정책 정의:
  - [ ] seed 입력 받는 방식
  - [ ] per-testcase RNG 스코프(동일 조건 재현성 규칙)

### B-2. Operator Backlog 최소 기준 충족 확인
- [ ] 연산자 백로그 항목 수가 **최소 15개 이상**임을 확인했다.
- [ ] 각 연산자 항목에 최소 정보가 포함됨을 확인했다.
  - [ ] 목표/목적
  - [ ] 대상 bucket(들)
  - [ ] 파라미터(있다면)
  - [ ] strength(1~5 등)
  - [ ] risk/주의점(있다면)

### B-3. Seed Corpus 최소 기준 충족 확인
- [ ] `examples/seed_samples.json`의 seed 개수가 **10~20개 범위(또는 합의된 범위)**임을 확인했다.
- [ ] 각 seed가 bucket 태깅(단일 또는 멀티라벨)을 포함함을 확인했다.
- [ ] JSON이 UTF-8로 정상 로드되며(한글/이모지 포함 시) 깨지지 않음을 확인했다.

---

## C) 재현성/정책 스모크 검증 (Reproducibility / Trace / Text Safety)

### C-1. 재현성(Reproducibility) 검증
동일 입력 조건에서 동일 출력이 재현되는지 확인했다.

- [ ] 동일 `seed_base` 및 동일 testcase 파생 규칙에서 결과가 일치한다.
- 실행 방법(예시):
  - [ ] `python -m examples.run_one_case > out1.txt`
  - [ ] `python -m examples.run_one_case > out2.txt`
  - [ ] `fc out1.txt out2.txt` 결과 차이 없음

### C-2. Trace 필드(계약 준수) 검증
- [ ] 모든 mutation step의 trace에 최소 필드가 존재함을 확인했다.
  - [ ] `op_id`
  - [ ] `status`
  - [ ] `params`
  - [ ] `len_before`
  - [ ] `len_after`

### C-3. 문자열 정책/경계조건 스모크 검증
다음 케이스에서 crash/exception 없이 동작함을 확인했다.

- [ ] 빈 문자열 seed
- [ ] 매우 긴 문자열 seed (합의된 길이 또는 임의로 큰 입력)
- [ ] 한글/이모지 포함 seed

---

## Day 1 Final Verdict

- [ ] Day 1 산출물은 main에 반영되었고, 계약/정책/seed/backlog의 최소 기준을 충족한다.
- [ ] Day 1 기준으로 Day 2(Framework skeleton + first ops) 작업을 진행해도 된다.

---

## Sign-off

- Verified by (A): Damin Oh  Date: 2026.02.12
- Verified by (B): ____________  Date: ____________
- Verified by (C): ____________  Date: ____________
