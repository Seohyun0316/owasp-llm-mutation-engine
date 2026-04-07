# Scripts

This directory contains utility scripts for preprocessing, validation, and inspection around the LLM01 seed-building workflow.

## Purpose

The scripts here are primarily used before or around the mutation stage.

They support tasks such as:

- raw prompt seed normalization
- prompt seed validation
- mutation seed construction
- mutation seed validation
- schema inspection

---

## Structure

```text
scripts/
├─ inspect_llm01_seed_schema.py
└─ normalization/
   ├─ normalize_sampled_raw.py
   ├─ validate_and_merge_prompt_seeds.py
   ├─ build_mutation_seeds_llm01.py
   ├─ validate_mutation_seeds_llm01.py
   └─ validate_prompt_seed_dataset_llm01.py
```

---

## Files

### `inspect_llm01_seed_schema.py`
Inspects the structure of LLM01 seed records and helps verify whether the expected schema layout is being followed.

---

## `normalization/`

### `normalize_sampled_raw.py`
Normalizes raw sampled prompt data into the shared intermediate structure.

### `validate_and_merge_prompt_seeds.py`
Validates prompt seed inputs and merges them into a unified dataset-level structure.

### `build_mutation_seeds_llm01.py`
Builds mutation-ready LLM01 seed records from validated prompt seed data.

### `validate_mutation_seeds_llm01.py`
Validates the resulting mutation seed records.

### `validate_prompt_seed_dataset_llm01.py`
Validates the prompt seed dataset before mutation-seed construction.

---

## Expected Workflow Position

These scripts generally belong to the following stage:

```text
sampled raw prompt data
→ normalization
→ prompt seed validation / merge
→ mutation seed construction
→ mutation seed validation
```

After that, the resulting records may be consumed by the pipeline layer in `src/pipelines/`.

---

## Relationship to Other Directories

- Schema definitions: [`../schema/README.md`](../schema/README.md)
- Pipeline scripts: [`../src/pipelines/README.md`](../src/pipelines/README.md)

---

## Scope

These scripts are currently specialized for the LLM01 pilot workflow and related seed-processing tasks.

---

## Related Documentation

- [`../schema/README.md`](../schema/README.md)
- [`../src/pipelines/README.md`](../src/pipelines/README.md)
- [`../sample/README.md`](../sample/README.md)

---
