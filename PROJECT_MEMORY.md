# AutoChecker Project Memory

This file records persistent project context and decisions for future sessions.

## Goal

Extend AutoChecker from Clang-Tidy and CodeQL to Clang Static Analyzer (CSA).

The planned workflow has three stages:

1. Extract APIs used to implement CSA checkers.
2. Extract and retrieve implementation logic from official CSA checkers.
3. Add a CSA generator that retrieves the extracted knowledge and asks an LLM
   to generate, compile, run, repair, and augment a checker.

## Local Environment

- AutoChecker repository: `/home/checker/code_check`
- Project Python environment: `/home/checker/code_check/.venv`
- Python version: `3.10.12`
- CSA extraction dependencies installed in `.venv`: `tree-sitter==0.21.3`
  and `tree-sitter-cpp==0.23.4`. `libclang==18.1.1` is installed but is not
  used by the source-only CSA API collector.
- LLVM monorepo: `/home/llvm/llvm-project`
- LLVM revision inspected: `ee779de84` on branch `main`
- CSA public headers: `/home/llvm/llvm-project/clang/include/clang/StaticAnalyzer`
- CSA official checker sources:
  `/home/llvm/llvm-project/clang/lib/StaticAnalyzer/Checkers`
- Checker metadata:
  `/home/llvm/llvm-project/clang/include/clang/StaticAnalyzer/Checkers/Checkers.td`

At the inspected revision, the StaticAnalyzer include tree contains 66 relevant
`.h`, `.def`, and `.td` files. The official checker tree contains 140 `.cpp`
files and 20 `.h` files.

## Current Progress

- Read the existing AutoChecker architecture and the CodeQL/Clang-Tidy
  collectors, retrievers, generators, platform adapters, prompts, and product
  factories.
- Confirmed that no native CSA generation pipeline exists yet.
- Confirmed the LLVM source locations and inspected representative files such
  as `Checker.h` and `DivZeroChecker.cpp`.
- Designed the stage-one CSA API extraction format.
- Implemented `csa_official_api_extract/collect_csa_api.py`. It extracts type
  and callable metadata, links declarations to definitions with deterministic
  qualified-name and parameter signatures, and writes one `csa_api.json` file.
- Replaced the initial libclang implementation with a source-only Tree-sitter
  C++ implementation because unconfigured LLVM sources do not contain generated
  headers such as `Checkers.inc`, `llvm-config.h`, and `DeclNodes.inc`.
- Completed a full extraction at LLVM revision `ee779de84`: 219 files, 673
  types, 5,468 APIs, 148 checker types, and 883 APIs with linked declarations
  and definitions. The generated JSON is 13 MB.
- Audited Stage 1 completeness. Callable extraction is usable, but Stage 1 is
  not final until it adds enums and enum values, using/typedef aliases, template
  parameters, ProgramState registration macros, required includes, per-record
  parse quality, and a formal JSON Schema. These are API facts and belong to
  Stage 1, not checker-logic decomposition.

## Decisions

- Generate one `csa_official_api_extract/csa_api.json` artifact containing a
  flat `api` array. Header and implementation symbols share one schema and are
  distinguished by `source_type` and `category`.
- Extract public CSA framework APIs from `.h` files and checker-local APIs from
  both `.h` and `.cpp` files.
- Keep semantic checker logic extraction as a separate stage. API records may contain exact source
  snippets, but semantic logic summaries belong to stage two.
- Stage 1 and Stage 2 have a strict data boundary. Stage 1 produces only
  `csa_official_api_extract/csa_api.json`. Stage 2 will have a separate directory,
  schema, output file, retriever, and embedding cache for official checker `.cpp`
  logic decomposition. Logic records must never be appended to `csa_api.json`.
- Preserve source path, line range, qualified name, signature, documentation,
  ownership, and checker callback role. These fields are required for useful
  retrieval and traceability.
- Use Tree-sitter C++ for stage-one source-only extraction. It parses target
  `.h` and `.cpp` files without preprocessing includes, generated LLVM headers,
  a compilation database, or an LLVM build.

## Next Action

Review retrieval quality over `csa_official_api_extract/csa_api.json`, especially
the framework API, checker callback, checker helper, and registration
categories. Stage one does not build LLVM or invoke a checker compilation
workflow.
