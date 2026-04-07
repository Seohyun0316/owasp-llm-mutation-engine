# OWASP LLM Mutation Engine

A mutation-based prompt transformation framework for benchmarking LLM security scanners, with an initial focus on **LLM01: Prompt Injection**.

## Overview

This repository contains the **code-side implementation** of the Mutation Engine and its supporting workflow for building, validating, mutating, and exporting prompt mutation inputs.

The current repository focuses on:

- Mutation Engine core logic
- Operator implementations
- LLM01-oriented seed processing scripts
- Schema documentation
- Batch/reporting pipelines
- Small sample artifacts for inspection

Large datasets, raw resources, and generated outputs are managed separately from the code repository.

---

## Project Goal

The goal of this project is to support a reproducible workflow like the following:

1. Prepare prompt seed data from multiple datasets
2. Normalize and validate the seed data
3. Convert them into mutation-ready seed records
4. Run the Mutation Engine with selected operators
5. Export execution input JSONL for downstream evaluation
6. Analyze batch-level mutation and diversity results

The initial pilot scope is centered on **LLM01 Prompt Injection**.

---

## Repository Structure

```text
.
├─ schema/               # schema documentation for normalized records and mutation seeds
├─ src/
│  ├─ config/            # bucket definitions and enabled bucket configuration
│  ├─ core/              # mutation engine core modules
│  ├─ operators/         # mutation operators
│  └─ pipelines/         # batch/report/export/smoke-test pipelines
├─ scripts/              # preprocessing, validation, and schema inspection scripts
├─ sample/               # small example summary artifacts
├─ docs/                 # design notes, operator docs, policy docs, how-to docs
└─ README.md
```

---

## Quick Start

This repository currently focuses on the **LLM01 Prompt Injection** pilot workflow.

A typical workflow is:

```text
sampled raw prompt data
→ normalization
→ prompt seed validation / merge
→ mutation seed construction
→ mutation seed validation
→ batch mutation run
→ reporting / diversity analysis
→ execution input export
```

### 1. Review the schema documents

Start by reading the schema layer to understand the expected record structures.

- [`schema/README.md`](schema/README.md)
- [`schema/normalized_v1.md`](schema/normalized_v1.md)
- [`schema/mutation_seed_v1.md`](schema/mutation_seed_v1.md)

### 2. Review the preprocessing scripts

Then inspect the LLM01 preprocessing and validation scripts.

- [`scripts/README.md`](scripts/README.md)

### 3. Review the pipeline layer

Then inspect the runnable pipeline scripts.

- [`src/pipelines/README.md`](src/pipelines/README.md)

### 4. Inspect small example artifacts

For lightweight examples of summary artifacts, see:

- [`sample/README.md`](sample/README.md)

### 5. Understand data handling

This repository does not serve as the long-term storage location for full datasets and large generated outputs.

- [`data/README.md`](data/README.md)

---

## Running the Mutation Engine

This repository currently focuses on the **LLM01 Prompt Injection** pilot workflow.

> **Note**
>
> Some scripts assume project-specific local input/output paths.  
> Full datasets and large generated artifacts are managed separately from this code repository, so make sure the expected local data files are available before running the commands below.
>
> The commands below show the typical entry points for each stage of the workflow.  
> Depending on your local setup, you may need to adjust input/output paths inside the scripts or prepare the expected local data files in advance.

### 1. Inspect the current seed schema

Use this script to inspect the structure of LLM01 seed records.

```bash
python scripts/inspect_llm01_seed_schema.py
```

### 2. Normalize sampled raw prompt data

Normalize sampled raw prompt records into the shared intermediate structure.

```bash
python scripts/normalization/normalize_sampled_raw.py
```

### 3. Validate and merge prompt seed data

Validate prompt seed records and merge them into a dataset-level structure.

```bash
python scripts/normalization/validate_and_merge_prompt_seeds.py
```

### 4. Build mutation-ready LLM01 seeds

Construct mutation-ready seed records for the Mutation Engine.

```bash
python scripts/normalization/build_mutation_seeds_llm01.py
```

### 5. Validate mutation seed records

Validate the generated mutation seed dataset before running mutation pipelines.

```bash
python scripts/normalization/validate_mutation_seeds_llm01.py
```

You can also validate the prompt seed dataset directly:

```bash
python scripts/normalization/validate_prompt_seed_dataset_llm01.py
```

### 6. Inspect the operator registry

Inspect which operators are currently registered and available.

```bash
python src/pipelines/inspect_registry.py
```

### 7. Run a smoke test

Run a lightweight smoke test for the current operator setup.

```bash
python src/pipelines/run_operator_smoke_test.py
```

### 8. Run the LLM01 batch pipeline

Run the main LLM01 mutation batch workflow.

```bash
python src/pipelines/run_llm01_batch.py
```

### 9. Generate reports

Generate batch-level and diversity-related reports.

```bash
python src/pipelines/report_llm01_batch.py
python src/pipelines/report_llm01_diversity.py
```

### 10. Export execution input JSONL

Export execution-ready JSONL records for downstream evaluation.

```bash
python src/pipelines/export_execution_input_jsonl.py
```

---

## Recommended End-to-End Order

A practical execution order is:

```text
inspect schema
→ normalize sampled raw data
→ validate and merge prompt seeds
→ build mutation seeds
→ validate mutation seeds
→ inspect registry
→ run operator smoke test
→ run LLM01 batch
→ generate reports
→ export execution input JSONL
```

---

## Documentation Map

- [Schema documentation](schema/README.md)
- [Pipeline scripts](src/pipelines/README.md)
- [Preprocessing scripts](scripts/README.md)
- [Sample artifacts](sample/README.md)
- [Data guidance](data/README.md)

---

## Data Repository

Large datasets, raw resources, and large generated artifacts are managed separately from this code repository.

- **Data Repository Link:** [LLM01 PRompt Injection Dataset](https://github.com/ODamDam/LLM01_PromptInjection_Dataset)

You can replace the placeholders above with your external data repository link and a short explanation.

---

## Current Scope

This repository currently emphasizes:

- **LLM01 Prompt Injection**
- prompt seed normalization
- mutation seed construction
- execution input export
- operator-based mutation workflows
- small-scale batch/report tooling

Additional OWASP LLM categories may be expanded later, but the current pilot is intentionally focused.

---

## Main Components

### Core Engine
The core engine includes registry, selection, mutation support types, and related components used by operators and pipelines.

### Operators
Operators are organized under `src/operators/` and represent concrete mutation strategies such as:

- formatting-based wrapping
- lexical perturbation
- syntactic framing
- obfuscation
- authority/pretext framing
- HTML embedding
- related LLM01-oriented transformations

### Pipelines
The pipeline layer contains batch/report/export scripts that support the end-to-end workflow around mutation generation and execution input preparation.

---

## Notes

- Full datasets and large generated artifacts are intentionally not tracked in this repository.
- Small sample artifacts are included only for structure illustration and documentation support.
- Some folders may evolve as the project expands beyond the initial LLM01 pilot.

---

## Status

This repository reflects an actively reorganized project structure for:

- core mutation engine development
- LLM01 seed preprocessing
- schema documentation
- pipeline-based execution preparation
- scanner benchmarking support

---
