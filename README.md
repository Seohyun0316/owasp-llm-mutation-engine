# Root README Add-on: Quick Start and README Link Structure

This document provides:

1. A `Quick Start` section that can be pasted into the root `README.md`
2. A recommended reading order for new readers
3. A link structure that connects the root README and subdirectory READMEs

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

These scripts support tasks such as:

- normalization of sampled raw prompt data
- prompt seed validation
- mutation seed construction
- mutation seed validation
- schema inspection

### 3. Review the pipeline layer

Then inspect the runnable pipeline scripts.

- [`src/pipelines/README.md`](src/pipelines/README.md)

These scripts support tasks such as:

- batch mutation runs
- execution input export
- registry inspection
- batch/diversity reporting
- operator smoke testing

### 4. Inspect small example artifacts

For lightweight examples of summary artifacts, see:

- [`sample/README.md`](sample/README.md)

### 5. Understand data handling

This repository does not serve as the long-term storage location for full datasets and large generated outputs.

- [`data/README.md`](data/README.md)

---

## Recommended Reading Order

For a new reader, the recommended reading order is:

1. [`README.md`](README.md)
2. [`schema/README.md`](schema/README.md)
3. [`schema/normalized_v1.md`](schema/normalized_v1.md)
4. [`schema/mutation_seed_v1.md`](schema/mutation_seed_v1.md)
5. [`scripts/README.md`](scripts/README.md)
6. [`src/pipelines/README.md`](src/pipelines/README.md)
7. [`sample/README.md`](sample/README.md)
8. [`data/README.md`](data/README.md)

