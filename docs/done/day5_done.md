# Day 5 Done — v0.1 문서 정리 + 태그(v0.1-mutation-framework)

## Summary

Day5에서는 v0.1 Mutation Framework의 “문서 패키지”를 완성하고, 릴리즈 기준점을 명확히 하기 위해 `v0.1-mutation-framework` 태그를 생성/푸시하는 절차까지 포함해 종결했다.

---

## What’s Included (Docs Added)

다음 문서들을 신규 추가/정리했다.

- `docs/contract/operator_contract_v0.1.md`
- `docs/policies/policy_validity_guard_v0.1.md`
- `docs/policies/policy_rng_repro_v0.1.md`
- `docs/howto/quickstart.md`
- `docs/howto/snapshots.md`
- `docs/howto/add_operator.md`
- (선택) `docs/architecture/mutation_framework_overview.md`

문서 작성 시 Markdown 펜스(`````, `~~~`)에 의한 렌더링 탈출 문제를 피하기 위해, 코드 블록은 4칸 들여쓰기 방식으로 통일했다.

---

## Validation Checklist

- [ ] `python -m pytest -q` 통과
- [ ] `python -m pytest -q -m snapshot` 통과
- [ ] Quickstart 실행 예시가 로컬에서 재현 가능
- [ ] 스냅샷 갱신 모드가 정상 동작

권장 실행:

    python -m pytest -q

스냅샷 비교:

    python -m pytest -q -m snapshot

스냅샷 갱신(필요 시):

    $env:UPDATE_SNAPSHOTS="1"
    python -m pytest -q -m snapshot
    Remove-Item Env:\UPDATE_SNAPSHOTS -ErrorAction SilentlyContinue

---

## Tagging Procedure (v0.1-mutation-framework)

본 태그는 “v0.1 Mutation Framework (contract/policies/howto) 문서 패키지 + 결정성/스냅샷 기반 프레임워크 상태”를 고정하는 릴리즈 기준점이다.

### 1) 작업 브랜치 확인 및 최신화

현재 브랜치/상태 확인:

    git status
    git branch

원격 최신 반영(선택):

    git fetch origin

### 2) 커밋 정리 및 푸시

문서 변경 포함하여 커밋/푸시가 완료되어 있어야 한다.

    git add docs
    git commit -m "docs: v0.1 contract/policies/howto package"
    git push

(이미 커밋/푸시가 끝났다면 생략)

### 3) 태그 생성 (annotated tag 권장)

로컬 태그 생성:

    git tag -a v0.1-mutation-framework -m "v0.1 mutation framework: contract/policies/howto + snapshot determinism"

태그 확인:

    git tag --list | findstr v0.1-mutation-framework

태그가 가리키는 커밋 확인(선택):

    git show v0.1-mutation-framework

### 4) 태그 푸시

태그만 푸시:

    git push origin v0.1-mutation-framework

또는 모든 태그 푸시:

    git push --tags

### 5) GitHub에서 태그 확인

- GitHub repo → Tags 또는 Releases 화면에서 `v0.1-mutation-framework` 존재 여부 확인
- 필요하면 Releases로 승격(선택)

---

## Notes / Decisions

- 문서의 안정 렌더링을 위해 fenced code block을 제거하고 4칸 들여쓰기 코드블록 스타일로 통일했다.
- v0.1의 재현성 기준은 snapshot harness로 게이트한다.
- Validity Guard는 Policy A(엔진 단일 출구) 기준을 문서로 고정했다.

---

## Next (Optional)

- v0.1 기준점에서 릴리즈 노트 작성(Release 페이지)
- operator catalog/백로그 문서 정리 및 Day6 계획 수립
