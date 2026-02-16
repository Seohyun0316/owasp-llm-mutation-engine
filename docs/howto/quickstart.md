# Quickstart (v0.1) — Mutation Framework

이 문서는 “처음 보는 사람이 5분 안에 로컬에서 재현성 테스트까지 돌리는 것”이 목표다.

---

## 0) Prerequisites

- Python 3.12+ 권장 (Windows에서도 동작)
- Git

---

## 1) Setup

### 1.1 가상환경 생성/활성화(권장)

Windows PowerShell:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -U pip

PowerShell 실행 정책 때문에 Activate가 막히면:

- 현재 세션만 허용:

      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

- 또는 가상환경 활성화 대신 venv python을 직접 사용해도 된다:

      .\.venv\Scripts\python.exe -m pip install -U pip

### 1.2 의존성 설치

레포에 `requirements.txt`가 있다면:

    pip install -r requirements.txt

없다면 최소로:

    pip install pytest

---

## 2) Run Tests

### 2.1 전체 유닛 테스트

    python -m pytest -q

---

## 3) Snapshot Harness

스냅샷은 “같은 입력/seed/strength이면 결과가 동일”함을 검증한다.

### 3.1 스냅샷 생성/갱신

PowerShell:

    $env:UPDATE_SNAPSHOTS="1"
    python -m pytest -q -m snapshot
    Remove-Item Env:\UPDATE_SNAPSHOTS

- `tests/snapshot/snapshots.json`의 `expect`가 채워진다.

### 3.2 스냅샷 비교(기본 모드)

    python -m pytest -q -m snapshot

---

## 4) Minimal Example Run (Mutator)

본 프로젝트는 CLI가 아직 확정되지 않았으므로, “Python 스크립트 실행” 예시를 제공한다.

### 4.1 `scripts/quickstart_run.py`로 실행(권장)

1) 파일 생성: `scripts/quickstart_run.py`

    from src.core.registry import OperatorRegistry
    from src.core.mutator import Mutator

    def main() -> None:
        reg = OperatorRegistry()
        reg.load_from_package("src.operators")

        m = Mutator(reg)
        outs = m.generate_children(
            seed_text="Hello",
            bucket_id="LLM01_PROMPT_INJECTION",
            surface="PROMPT_TEXT",
            n=3,
            k=1,
            seed_base=1337,
            strength=2,
            constraints={"max_chars": 128},
            metadata={"seed_id": "quickstart"},
        )

        for i, o in enumerate(outs):
            print("=" * 40)
            print(f"child {i} status={o.last_status}")
            print(o.child_text)

    if __name__ == "__main__":
        main()

2) 실행:

    python scripts\quickstart_run.py

---

## 5) Common Issues

### 5.1 `No module named pytest`

    pip install pytest

### 5.2 `python -m pytest`가 안 잡히는 경우(가상환경 미활성화)

- 가상환경 활성화:

      .\.venv\Scripts\Activate.ps1

- 또는 가상환경 파이썬으로 직접 실행:

      .\.venv\Scripts\python.exe -m pytest -q

### 5.3 스냅샷이 계속 불일치

- 선택 정책/연산자 구현/Guard 정책이 바뀌면 스냅샷이 깨질 수 있다.
- 의도된 변경이면 스냅샷을 갱신한다:

      $env:UPDATE_SNAPSHOTS="1"
      python -m pytest -q -m snapshot
      Remove-Item Env:\UPDATE_SNAPSHOTS

- 자세한 내용은 `docs/howto/snapshots.md`를 참고한다.

### 5.4 `Remove-Item Env:\UPDATE_SNAPSHOTS` 실패

이미 환경 변수가 없으면 실패할 수 있다:

    Remove-Item Env:\UPDATE_SNAPSHOTS -ErrorAction SilentlyContinue
