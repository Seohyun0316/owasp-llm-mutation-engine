# src/pipelines/inspect_registry.py
from __future__ import annotations

from src.config.enabled_buckets import ENABLED_BUCKETS
from src.core.registry import OperatorRegistry


def main() -> None:
    registry = OperatorRegistry()
    loaded = registry.load_from_package("src.operators", strict=False)

    print("=" * 80)
    print(f"[registry] loaded operators: {loaded}")
    print(f"[registry] load_errors: {len(registry.load_errors)}")
    print("=" * 80)

    if registry.load_errors:
        print("\n[load errors]")
        for modname, reason in registry.load_errors:
            print(f"- {modname}: {reason}")

    print("\n[all operators]")
    for h in registry.list_ops():
        meta = h.meta
        print("-" * 80)
        print(f"op_id          : {h.op_id}")
        print(f"module         : {h.module}")
        print(f"bucket_tags    : {meta.get('bucket_tags', [])}")
        print(f"surface_compat : {meta.get('surface_compat', [])}")
        print(f"risk_level     : {meta.get('risk_level', None)}")
        print(f"strength_range : {meta.get('strength_range', None)}")

    print("\n" + "=" * 80)
    print(f"[enabled buckets] {ENABLED_BUCKETS}")
    print("=" * 80)

    for bucket_id in ENABLED_BUCKETS:
        matched = registry.filter(bucket_id=bucket_id)
        print(f"\n[bucket] {bucket_id} -> {len(matched)} operators")
        for h in matched:
            print(f"  - {h.op_id}")


if __name__ == "__main__":
    main()
