# CSA checker logic extraction (Stage 2)

This directory owns the checker-logic dataset. It does not modify or append to
`csa_official_api_extract/csa_api.json`.

Generate the reviewed acceptance corpus:

```bash
.venv/bin/python csa_official_checker_logic_extract/collect_checker_metaop.py
```

Validate an existing corpus against the current LLVM source and Stage 1 API
IDs:

```bash
.venv/bin/python csa_official_checker_logic_extract/collect_checker_metaop.py \
  --validate csa_official_checker_logic_extract/csa_meat_op.json
```

The canonical file is grouped by implementation class. `rag_records.py`
creates transient records with one record per `logic_units[].id`; it never
writes a second flattened knowledge file. The reviewed initial corpus covers
`DivZeroChecker`, `SimpleStreamChecker`, and `MallocChecker`. Additional
checkers should be added through a reviewed semantic plan produced from the
static callback/helper slice using `prompts/semantic_decomposition.md`.

Generate a temporary Tree-sitter inventory for semantic decomposition with
`--inventory-output /tmp/csa-inventory.json`. Repeat `--checker ClassName` to
limit the scan. The inventory identifies classes, callbacks, checker-local call
slices, ProgramState macros, directly included checker-local headers, and
registration relationships. It is intermediate data, not another canonical
dataset.

Run LLM decomposition through an OpenAI-compatible endpoint, then hydrate the
validated plan into canonical JSON:

```bash
.venv/bin/python csa_official_checker_logic_extract/decompose_with_llm.py \
  --checker DivZeroChecker --model deepseek-chat \
  --output /tmp/divzero-semantic-plan.json
.venv/bin/python csa_official_checker_logic_extract/collect_checker_metaop.py \
  --semantic-plan /tmp/divzero-semantic-plan.json \
  --output /tmp/divzero-metaop.json
```

The default config is
`csa_official_api_extract/llm_config_csa_meta_op.json` and contains `base_url`
and `key`. CLI arguments or `CSA_LLM_BASE_URL`/`CSA_LLM_API_KEY` override it.
The generated meta-op is always a separate Stage 2 artifact,
`csa_meat_op.json`; `csa_api.json` is
never opened for writing.
