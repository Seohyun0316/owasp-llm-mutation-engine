# Schema

This directory documents the record formats used in the preprocessing and mutation pipeline.

## Files

### `normalized_v1.md`
Defines the normalized intermediate record format used to convert heterogeneous source datasets into a shared structure.

This schema is intended to support:

- cross-dataset normalization
- seed tagging and inspection
- later conversion into mutation-ready records

### `mutation_seed_v1.md`
Defines the mutation-ready seed record format used by the Mutation Engine workflow.

This schema is intended to support:

- mutation target selection
- bucket-aware processing
- attack surface annotation
- downstream execution input generation

---

## Relationship Between the Schemas

The general data flow is:

```text
raw dataset record
→ normalized_v1
→ mutation_seed_v1
→ mutation / batch pipeline
→ execution input jsonl
```

### `normalized_v1`
Use this schema when the goal is to preserve source data in a common format.

### `mutation_seed_v1`
Use this schema when the goal is to produce records that can actually enter the Mutation Engine workflow.

---

## Why This Directory Exists

The project uses multiple prompt-oriented datasets with different structures.  
Without an explicit schema layer, preprocessing and downstream mutation logic become difficult to maintain and reproduce.

This directory exists to make the record contracts explicit.

---

## Scope

These documents currently emphasize the LLM01 pilot workflow, but the overall schema layer is intended to remain extensible.

---

## Recommended Reading Order

1. `normalized_v1.md`
2. `mutation_seed_v1.md`

---

## Related Documentation

- [`normalized_v1.md`](normalized_v1.md)
- [`mutation_seed_v1.md`](mutation_seed_v1.md)
- [`../scripts/README.md`](../scripts/README.md)
- [`../src/pipelines/README.md`](../src/pipelines/README.md)

---
