# CSA Checker A/B Progress and Next Steps

Date: 2026-08-09

## Current Outcome

The first CSA checker A/B workflow is implemented and has passed a real Clang
Static Analyzer plugin build and execution test. The target is the definite
division-by-zero behavior of the official `DivZeroChecker`. The generated
implementation is named `GeneratedDivZeroChecker` and its analyzer frontend is
`autochecker.GeneratedDivZero`.

This is no longer only a mocked workflow. The generated shared object was
compiled, loaded by the locally built Clang 24 analyzer, and exercised against
one negative and one positive test case.

## Build Environment

- LLVM source: `/home/llvm/llvm-project`
- LLVM revision: `ee779de847774cc935ec089ebb6185c790aedcf7`
- Clang version: `24.0.0git`
- Out-of-tree build: `/home/checker/llvm-build`
- Clang binary: `/home/checker/llvm-build/bin/clang`
- Build generator: Ninja 1.10.1
- CMake: 3.22.1
- Host compiler: GCC/G++ 11.4.0
- Build configuration: Release, X86 target, Clang only, static analyzer and
  plugin support enabled, tests/examples/docs disabled
- Server used for the completed build: 8 CPU cores, approximately 15 GiB RAM

The official LLVM source tree was not modified. Generated checkers are compiled
as loadable analyzer plugins, so neither `Checkers.td` nor the official checker
`CMakeLists.txt` needs to be edited.

Build reproduction command:

```bash
ninja -C /home/checker/llvm-build -j6 clang SampleAnalyzerPlugin
```

## Implemented Components

### CSA entities

`src/entity/concreteProduct_CSA.py` defines:

- `Case_CSA`
- `Checker_CSA`
- `Rule_CSA`

### Platform adapter

`src/plateform/csa.py` implements:

- compilation of generated C++ into `GeneratedDivZeroChecker.so`;
- inclusion of LLVM source and generated build headers;
- loading the plugin through Clang's `-load` mechanism;
- execution with `-analyzer-checker=autochecker.GeneratedDivZero`;
- capture of return code, stdout, and stderr;
- conversion of missing tools and process errors into recorded execution
  failures.

### Generator

`src/csa_generator.py` implements:

- `expected-warning` parsing;
- selection of only the first non-skipped negative case;
- retrieval of DivZero MetaOps from `csa_meat_op.json`;
- resolution of referenced APIs from `csa_api.json`;
- CSA plugin source and header generation;
- bounded compilation retries through `max_compiler_trys`;
- optional LLM repair using current source and compiler output;
- initial negative-case verification;
- unchanged-checker execution over all prepared cases;
- separate classification of false positives, false negatives, and execution
  failures;
- generation of all A-stage artifacts and the B-stage result JSON.

### Command line entry point

`src/main_csa.py` discovers C/C++ cases below a test directory and runs stages
A and B:

```bash
cd /home/checker/code_check
PYTHONPATH=src python src/main_csa.py csa_test_cases/div_zero \
  --result-dir result-generation
```

## Real Verification Result

Prepared tests:

- negative: `csa_test_cases/div_zero/negative.cpp`
- positive: `csa_test_cases/div_zero/positive.cpp`

Observed result:

- checker plugin compilation: passed;
- plugin registration and discovery: passed;
- negative analyzer return code: 0;
- negative diagnostic: `Division by zero [autochecker.GeneratedDivZero]`;
- positive analyzer return code: 0;
- positive unexpected diagnostics: none;
- A initial-case validation: passed;
- B all prepared cases: 2/2 passed;
- augmentation started: false.

The plugin is also visible in checker help:

```text
autochecker.GeneratedDivZero  Reports definite division by zero
```

Result locations:

```text
result-generation/csa/div-zero/
|-- checker_generation_result.json
`-- first_checker/
    |-- selected_case.cpp
    |-- logic.json
    |-- retrieved_metaops.json
    |-- retrieved_api_refs.json
    |-- generation_prompt.md
    |-- generated_checker.cpp
    |-- generated_checker.h
    |-- compile.stdout
    |-- compile.stderr
    |-- verify.output
    `-- workspace/GeneratedDivZeroChecker.so
```

Focused Python tests also pass: negative selection, expected diagnostic parsing,
and A/B result generation (3 tests total).

The knowledge datasets were used read-only. Hashes recorded after verification:

```text
csa_api.json      7e098ca5bfc2d4a89a1b757581d3e5d7d458a2a3c07f4de25ad8ed233d0f4b67
csa_meat_op.json  3ae6e2f3c9af4a8589ac9788f6b350feda3e19e0cdc27ff1a594d7ad1ae9ed48
```

## Remaining Limitations

- The real verification set currently contains only one definite-zero negative
  case and one positive case. It is enough for the first A/B acceptance test,
  but it is not a broad semantic benchmark.
- The successful source was the deterministic offline DivZero fallback. The
  live LLM generation path and compiler-repair path still need a controlled
  integration test.
- Tainted division is intentionally excluded.
- Checker augmentation is intentionally excluded and
  `augmentation_started` remains false.
- `MallocChecker`, `SimpleStreamChecker`, multi-frontend generation, version
  selection, and rollback remain out of scope.
- Diagnostic matching currently uses expected message text. More complex LLVM
  `-verify` annotations and multiple diagnostics per line need broader parser
  coverage before scaling to the official test suite.

## Next-Step Plan

1. Expand the DivZero test set with constant expressions, branches, remainder,
   compound assignment, symbolic non-zero values, and analyzer execution-error
   cases. Keep taint tests separate.
2. Run the unchanged first checker over that expanded set and preserve the
   initial B-stage baseline before making any source changes.
3. Add an integration test with an injected or configured LLM response and
   force one compiler error to verify the bounded repair loop end to end.
4. Harden diagnostic parsing for multiple `expected-warning` annotations,
   line offsets, `expected-no-diagnostics`, and crashes/timeouts.
5. Only after the A/B baseline is stable, design the augmentation stage for
   failed positive and negative cases. Do not mix augmentation into the current
   first-checker artifact.
6. After DivZero augmentation is validated, reuse the plugin workflow for
   `SimpleStreamChecker`, then evaluate the more complex `MallocChecker`.

## Acceptance Boundary

The current milestone can be accepted as: "first CSA checker A/B infrastructure
implemented; Clang 24 environment built; generated DivZero plugin compiled,
registered, and verified on the prepared positive/negative cases."

It should not yet be described as: "general CSA checker generation completed"
or "all DivZero behavior covered."
