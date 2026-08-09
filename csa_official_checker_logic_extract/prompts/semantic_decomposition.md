# CSA checker semantic decomposition

You receive a statically extracted implementation class, its callbacks,
checker-local helper call slices, frontend registrations, state traits, and
numbered source lines. Split the implementation into ordered semantic logic
units.

Your response is machine-consumed. Return exactly one JSON object and no
Markdown fences, commentary, or additional keys outside the object. The top
level object MUST have exactly these keys: `summary`, `analysis_mode`, and
`logic_units`. `analysis_mode` MUST be exactly one of `path_sensitive`,
`path_insensitive`, or `hybrid` (use `path_sensitive` for normal CSA checker
callbacks). Every logic unit MUST contain every key shown below, including
empty arrays. `kind` MUST be copied exactly from the allowed list below; do not
invent variants such as `path-sensitive`, `state-model`, or translated names.

Return JSON only. For each unit provide:

```json
{
  "slug": "stable-human-readable-slug",
  "kind": "entry_filter",
  "meta_op": "A precise, searchable description of the checker behavior.",
  "callback_context": ["ClassName::callback"],
  "applies_to_frontends": ["frontend ID"],
  "depends_on": ["earlier unit slug"],
  "api_names": ["clang::ento::CheckerContext::getState"],
  "behavior": {
    "preconditions": [],
    "state_reads": [],
    "state_writes": [],
    "transitions": [],
    "reports": []
  },
  "source_selectors": [
    {
      "role": "callback_segment",
      "symbol": "ClassName::callback",
      "start_line": 1,
      "end_line": 2
    }
  ]
}
```

Allowed `kind` values are exactly `entry_filter`, `value_modeling`, `state_modeling`,
`constraint_reasoning`, `detection`, `state_transition`, `reporting`,
`lifecycle_cleanup`, `escape_handling`, and `utility`.

The `behavior` object MUST have exactly these five keys, each containing an
array of strings: `preconditions`, `state_reads`, `state_writes`,
`transitions`, and `reports`. `source_selectors` line numbers are one-based and
inclusive. `callback_context` contains only callback method names from the
static context. `applies_to_frontends` contains frontend display names from the
static context, not generated IDs. `depends_on` contains only earlier unit
slugs from this response.

Do not return source code or API IDs. `api_names` may contain only qualified
Stage 1 API names visibly called by the selected source; use an empty array for
checker-local helpers or unresolved calls. Do not treat registration functions,
`shouldRegister` functions, or frontend enable conditions as logic units. A
callback may be split into several units, and a unit may select callback and
helper ranges. Keep ranges minimal but complete and list them in execution or
call order. Dependencies must refer to unit slugs in the same checker and must
be acyclic. Describe only behavior supported by the supplied source.

The collector will reject unknown symbols, invalid line ranges, modified source
text, unknown frontend/callback references, unresolved dependency slugs, and
cycles. It reconstructs all `meta_impl`, `source_spans`, and `api_refs` fields
from static source data after this response.
