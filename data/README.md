# Data

This directory is reserved for data-related guidance and local/generated data paths, but the full tracked dataset contents are intentionally not maintained in this repository.

## Purpose

This repository focuses on the **code-side implementation** of the Mutation Engine workflow.

Large data resources such as:

- raw datasets
- normalized datasets
- mutation seed datasets
- notebooks
- large generated outputs

are handled separately from the main code repository.

---

## Why Data Is Not Fully Tracked Here

The project includes multiple prompt-oriented datasets and generated artifacts that can become large, frequently updated, or better suited for separate storage/versioning.

Keeping them out of the main code repository improves:

- repository size management
- reviewability of code changes
- separation of code and data responsibilities

---

## Typical Data Categories

Examples of data that may exist in the broader project workflow include:

- raw source datasets
- normalized prompt records
- mutation seed datasets
- execution input JSONL files
- run outputs and summary artifacts

---

## Local / Generated Paths

Depending on the active workflow, local paths may include items such as:

- `data/inputs/`
- `data/outputs/`

These are typically treated as local/generated artifacts rather than version-controlled source code assets.

---

## Relationship to Other Directories

- Schema definitions live in [`../schema/README.md`](../schema/README.md)
- Preprocessing scripts live in [`../scripts/README.md`](../scripts/README.md)
- Execution/report pipelines live in [`../src/pipelines/README.md`](../src/pipelines/README.md)
- Lightweight example summaries live in [`../sample/README.md`](../sample/README.md)

---

## Recommended Interpretation

- Use `schema/` to understand the expected record formats
- Use `scripts/` to prepare and validate data
- Use `src/pipelines/` to run batch/report/export workflows
- Use `sample/` to inspect small example artifacts
- Use the separate data storage location for full datasets and large outputs

---

## Note

If this project uses a separate data repository, document its location and usage policy here when that repository is finalized.

---

## Related Documentation

- [`../schema/README.md`](../schema/README.md)
- [`../scripts/README.md`](../scripts/README.md)
- [`../src/pipelines/README.md`](../src/pipelines/README.md)
- [`../sample/README.md`](../sample/README.md)

---
