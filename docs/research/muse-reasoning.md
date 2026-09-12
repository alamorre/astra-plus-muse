# Muse reasoning configuration research

Checked 2026-09-12. Scope: choose Muse's strongest supported reasoning configuration for delegated coding work when capability matters more than cost.

## Recommendation

Target **Muse Spark 1.3 with `max` reasoning**, with explicit validation that the selected model and account actually serve that effort. This is the strongest configuration supported by the primary evidence below. It is an evidence-based default recommendation, not proof that max wins on every task or in this repository's particular workflow.

Do not choose `ultra` simply because its name sounds stronger or the CLI accepts it. No primary source found establishes a distinct Muse Spark 1.3 ultra mode, its superiority to max, or whether it aliases or falls back to another effort. Do not assume contributor and standard variants expose identical effort levels without checking the current model catalog and runtime behavior.

## Primary evidence

1. Meta's September 2 release article currently states that Muse Spark 1.3 with max reasoning is available in Muse Code and Meta Model API. This establishes a named, released configuration. [Meta: Introducing Muse Spark 1.3](https://research.meta.ai/blog/introducing-muse-spark-1-3)

2. Meta's linked evaluation methodology says its Muse Spark 1.3 results use **max** reasoning, while Muse Spark 1.2 uses **xhigh**. Its software-engineering evaluations include DeepSWE with a mini-swe agent, and Terminal-Bench using native coding harnesses. This supports matching the configuration Meta evaluates, but is not a controlled comparison of 1.3 medium against 1.3 max. [Meta: Muse Spark 1.3 Evaluation Methodology](https://research.meta.ai/static/muse-spark-1-3-multimodal-evaluation-methodology)

3. Cursor's own current model documentation lists minimal, low, medium, high (default), extra high, and max. It reports higher effort producing higher CursorBench scores. This is primary evidence for Cursor's harness and evaluation, rather than an assertion about Muse Code flag mapping. [Cursor: Muse Spark 1.3](https://prod.cursor.com/docs/models/muse-spark-1-3)

4. CursorBench 4.0, updated September 10, reports the following Muse Spark 1.3 scores on coding-agent tasks. The benchmark owner cautions that results vary and small differences may not be statistically meaningful. [CursorBench 4.0](https://cursor.com/cursorbench)

   | Effort | Score |
   | --- | ---: |
   | Minimal | 24.3% |
   | Low | 29.3% |
   | Medium | 32.6% |
   | High | 33.4% |
   | Extra high | 37.5% |
   | Max | 41.6% |

   Max exceeds medium by 9.0 percentage points in this evaluation. This is a meaningful reason to prefer max when cost is secondary, while retaining uncertainty about transfer to a different harness and task distribution.

## Local inspection reported by the coordinating agent

- The installed/repository skill launcher defaults to `medium`; the direct invocation example also passes medium, and guidance says to start medium and raise effort when justified. This is a deliberate skill setting, not a random choice or Muse's built-in default.
- Installed Muse Code 1.1.1 advertises `none|minimal|low|medium|high|xhigh|max|ultra`, with default `high`.
- CLI argument acceptance alone does not establish that the backend serves that effort. A bounded compatibility request was performed using Contributor at max, a one-step cap, a harmless “Reply with only OK” prompt, and shell/write/web tools disabled. It failed with exit code 1 and API 400: `reasoning_effort max requires an active Muse Code subscription for model muse-spark-1.3-contributor.` This verifies a current entitlement blocker on this credential route, not model competency. Command and event/error logs were retained locally. A second bounded check, explicitly requested by the user after implementation, returned the same API 400 and exit code 1; max access remains unresolved. No effective max run or competency gain was demonstrated locally.

## Limits and implementation requirements

- Public Meta developer documentation could not be fully inspected: `dev.meta.ai` required login and `developer.meta.com` requests failed. The release article and methodology were accessible.
- No inspected Meta primary source proves contributor/standard checkpoint parity or contributor support for max. Third-party descriptions were not treated as decisive evidence.
- No inspected primary source ranks `ultra` above `max`, or documents an equivalence between them.
- A change should request max explicitly in both launch paths, update the medium-first guidance, and preserve explicit user overrides. Before treating a run as max, inspect current model support and surface unsupported settings or fallback warnings rather than silently claiming max.
- Keep the original scope and acceptance scenarios when comparing results. A representative repeated evaluation can assess local benefit; one trivial prompt cannot establish competency or prove which reasoning mode the backend served.
