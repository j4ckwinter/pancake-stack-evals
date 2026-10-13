# Evaluate a workflow on a fresh task

Use the scenarios in [tests/behavioral/cases](../tests/behavioral/cases) to check workflow behavior against small, repeatable projects. They derive from the trial families recorded in [the project plan](plan.md). They are new fixtures, not recovered copies of the historical trials.

The [3 October 2026 trial results](behavioral-results.md) record observed outcomes and unresolved process gaps.

## Repeated baseline comparison

The explicit live runner `tests/behavioral/compare.py` compares `summary`, `records`, and `exporter` with and without source Pancake guidance. It is never invoked by repository tests or CI. It requires an authenticated Codex CLI file cache and consumes live model usage. Use a new private output directory outside this repository:

```sh
python3 -B tests/behavioral/compare.py --output /tmp/pstack-comparison-unique --model gpt-6.1-sol --effort medium --repetitions 3
```

Check the active CLI and model access before using the example. The runner uses identical natural requests and common scope constraints, a fresh project and profile per candidate, and a two-thread limit. The treatment adds only the source skill invocation and its bundle. It alternates baseline-first and Pancake-first pairs across cases and repetitions; this is counterbalanced ordering, not random assignment. Runs are sequential. Each candidate has a five-minute timeout; an execution failure stops the batch for inspection. Failed artifact checks remain in the results.

Before running, define the hypothesis as improved task quality or workflow adherence at measurable additional cost. Use three repetitions per case and treatment (18 runs) as a bounded pilot, not an effectiveness threshold. The criteria are:

- **Task quality:** trusted artifact checks pass, requested regression coverage is meaningful, existing coverage is retained, and the review identifies the local consumer failure and inaccessible external contract without unsupported findings.
- **Scope preservation:** protected files and read-only workspaces remain unchanged; candidates do not create plugin preferences.
- **Workflow adherence:** source reads, failure reproduction before correction, executed verification, and linked completed migration reviewers are observed in tool/session records. Score these separately from correct artifacts. Baseline candidates are not required to follow Pancake, but their observed behavior can be compared.
- **Cost:** report elapsed seconds, input/cached/output tokens, and recorded top-level tool calls including workers. An orchestration call may contain several shell or patch operations; this count does not measure every nested operation. Tokens are a usage proxy, not an invoice or monetary estimate. Distinguish task checks from guidance reads and avoid labeling all additional calls unnecessary.

Inspect final responses and changed tests as well as machine results. A completed worker must actually review the relevant project and final code state; identity alone is insufficient. Record missing usage, unavailable blinding, source-read failures, and any configuration mismatch. Keep outputs under neutral labels when using a separate assessor; final responses can still reveal the treatment. Small synthetic tasks can saturate correctness and cannot establish production benefit or installed-host parity.

Raw output includes prompts, commands, session records, final responses, source hashes, and candidate workspaces. It may contain account metadata: keep it private and publish only inspected, sanitized excerpts. The runner removes copied authentication before assessment and executes generated application/tests through `codex sandbox --permission-profile :read-only`, with isolated Codex and Claude preference paths. Verify that sandbox support works on the active host; the runner must not fall back to unrestricted execution. It removes temporary candidate directories after each run and preserves records in the explicit output directory for assessment. Do not point candidates at the assessor files or copy authentication into committed evidence.

## Three-arm outcome and proportionality pilot

The `comparison` suite reuses the runner for `baseline`, `pancake`, and the local
Codex adaptation of `poteto`. The baseline has no workflow bundle. This is a
source-guidance comparison on one host, not plugin installation validation.
Run only when live model usage is authorized:

```sh
PANCAKE_STACK_SOURCE=/absolute/path/pancake-stack python3 -B tests/behavioral/compare.py --suite comparison --poteto-source /absolute/path/codex/skills --output /tmp/pstack-three-arm-unique --model gpt-6.1-sol --effort medium --repetitions 2 --timeout 300
```

Two repetitions give 12 sequential trials on two new tasks. `label` requires an
exact CLI typo correction with every other byte preserved. `contract` migrates
versioned invoice envelopes across producer, live reader, and archive reader
while preserving keyword APIs, a protected facade, and persisted archives.
Its public README defines malformed-record and version behavior. Trusted
artifact probes stay outside candidate projects and exercise these documented
contracts. Candidate test quality and verification evidence require separate
inspection; passing artifacts do not certify added regression coverage.
The contract case permits Python and Markdown additions, including shared
modules, and behavior-preserving changes to the billing facade and README.
The assessor protects persisted archives and unrelated existing files. Review
added files and documentation for task relevance separately. A file outside
automatic assessment scope needs adjudication, not an automatic claim that
the candidate violated the task. Historical cases keep their original policy.

All arms receive identical requests, model and effort, scope restrictions,
timeouts, and two-thread limits. Scoped implementation delegates and read-only
reviewers are permitted, inherit the lead's model and effort, and cannot
create grandchildren. Saved preference reads and writes are prohibited. Arm
order rotates across cases and repetitions; two repetitions do not completely
balance positions within each individual case. Three repetitions do.

The poteto source must contain `poteto-mode/SKILL.md`. Preparation selects only
sibling skills with the Codex compatibility marker, copies their complete trees
into a random `bundle/skills`, and rejects symlinks. It does not install skills,
auto-discover them through the profile, or copy saved settings. The manifest
records every copied file hash, selected skills, and available origin metadata.
Relative Markdown links are audited against copied resources; unresolved links
are recorded for inspection, including template placeholders and optional
references. Absolute links are not a correctness gate. Optional external
plugins are not copied or installed. Missing optional capabilities must be
reported as limitations of the observed run.

Source, evaluator, and poteto identities are checked before and after every
comparison trial. A changed input stops the batch and invalidates its stable
input assumption. Raw evidence remains private. The 300-second candidate and
45-second assessment limits bound 12 candidate/assessment pairs to roughly
69 minutes plus preparation and evidence collection. Infrastructure failures
stop the batch; artifact failures remain visible outcomes.

Predeclare assessment as artifact success, preservation of protected files,
verification evidence, and cost. Report per-case elapsed time, input/cached/
output/total tokens, missing usage, tool-call and command-event counts,
completed workers, changed/added files, and final-response characters. Workers
are not automatically reviewers. Inspect their scope and completion evidence.
Use the tiny task to assess proportionality; do not collapse quality and cost
into an invented composite score. Keep timeouts visible rather than comparing
only fast successful runs. Token counts are usage proxies, not monetary cost.

Candidates necessarily see their guidance identity. They do not receive arm
comparisons or ground truth. Independent assessment can use neutral labels,
but final prose can reveal treatment. A small synthetic pilot on one model and
host cannot establish general effectiveness, production savings, installed
plugin behavior, or diverse-model review quality.

## Reviewer detection and instruction consolidation

Use `compare.py --suite review` for the focused reviewer experiment. The baseline is the current source Check skill; the consolidated variant replaces only three adjacent contract-tracing paragraphs in a temporary bundle. It adds no compatibility instructions and changes no shipped skill. The hypothesis is that this consolidation preserves defect detection and useful review behavior while reducing overhead. Reject adoption on observed quality or process regressions; overlapping cost ranges in a small pilot leave the overhead claim inconclusive.

```sh
python3 -B tests/behavioral/compare.py --suite review --output /tmp/pstack-review-unique --model gpt-6.1-sol --repetitions 2
```

This command consumes live model usage. Omitting `--effort` uses the isolated CLI's default; record the actual selection from sessions. It does not inherit the parent conversation's effort. The runner uses the same authentication isolation, private output, timeout, counterbalanced sequential ordering, and cleanup as the workflow comparison above. Review candidates have read-only sandboxes and are told not to delegate. This tests reviewer instructions, not implementation-panel orchestration or installed-host behavior.

`tests/behavioral/review.py` prepares three single-defect migrations and a clean migration from the records fixture. All four pass their local tests. Independent fixture tests demonstrate that only the intended contract fails: the established keyword caller, producer-to-consumer integration, or reading the stored archive. The clean migration preserves all three. Two repetitions give 16 reviews, including four clean-control runs. Candidates see ordinary source, README requirements, and a supplied diff, without case labels or ground truth.

Before examining results, use these assessment rules:

- Count detection only when a finding identifies the expected mechanism, concrete trigger, and consequence. Deduplicate repeated descriptions of that mechanism. A passing test claim or generic compatibility warning is insufficient.
- Count missing expected mechanisms as missed defects. Count unsupported actionable findings separately, on faulty changes as well as clean controls. Report both total false findings and the fraction of clean controls with any false finding. Optional test suggestions clearly separated from breakage are not false findings.
- Inspect actual command records for reading the diff and affected callers, running focused checks, respecting scope, and grounding the final verdict. Mark unavailable evidence as unavailable. Do not infer those actions from a candidate's final claims.
- Report execution failures and missing usage separately. Report elapsed seconds, input/cached/output/total tokens, orchestration tool calls, and emitted command-action events with sample counts, medians, and ranges. Only completed executions enter successful-run cost summaries; failed reviews still contribute misses. Tokens are usage, not monetary cost. Command-action events can omit completed commands; inspect paired raw function/custom tool calls and outputs for process evidence, and do not treat event counts as the number of executed shell commands.

After adjudicating each output, `review.summarize(results, assessments)` joins ordered runner results with records containing matching `run_id`, `case`, supported `detected` mechanism IDs, `false_findings`, and a `process` map of observed booleans or nulls. `review.score` holds the private mechanism IDs and rejects unsupported IDs. Keep assessment records outside candidate workspaces. Retain sanitized verdicts and evidence pointers so another reader can inspect the judgments; regex matching against prose is not defect assessment.

Use neutral output labels and withhold treatments from an independent assessor when available. Record any lack of blinding or independence. These small, related fixtures measure specific compatibility failures and can saturate accuracy; they cannot establish general reviewer quality or production cost savings.

## Three-arm review comparison

Use `--suite review-comparison` to compare an unguided baseline, the source
Pancake entrypoint, and the local Codex adaptation of Poteto on review tasks.
The historical `review` suite retains its four invoice cases and its Check
baseline and consolidated arms. Run the new suite only with live usage
authorized and with a new private output directory:

```sh
PANCAKE_STACK_SOURCE=/absolute/path/pancake-stack python3 -B tests/behavioral/compare.py --suite review-comparison --poteto-source /absolute/path/codex/skills --output /tmp/pstack-review-comparison-unique --model gpt-6.1-sol --effort medium --repetitions 1 --timeout 240
```

One repetition produces 12 sequential runs. All arms receive the same organic
review request, model, effort, timeout, and read-only sandbox. The baseline has
no bundle. Pancake starts at `pancake/SKILL.md`; Poteto starts at its own
`poteto-mode/SKILL.md`. Independent read-only delegation is permitted when
useful, with inherited model and effort, two threads, and no grandchildren.
Source identity checks, bundle inventories, preference restrictions, usage
collection, and credential cleanup match the three-arm implementation suite.
The runner stops if an input changes before or during a trial. Arm order rotates
across cases. One repetition does not balance positions within each case.

The private `review_comparison.py` registry owns two bug cases and two matched
clean controls. The configuration pair simplifies an option resolver whose
contract distinguishes zero from an omitted or null limit. The lifecycle pair
changes a file reader to return an iterable consumed after the call returns.
All four projects pass their local tests. Independent evaluator probes check
zero-limit selection and consumption after return, and verify that the clean
reader closes its stream after consumption. Candidates receive ordinary source,
a README contract, and `change.diff`. Case identities, expected mechanisms,
and trusted probes stay outside their workspace.

Predeclare the following rubric before inspecting outputs:

- Apply the preceding reviewer-detection rules for concrete mechanisms,
  triggers, consequences, duplicate findings, misses, and unsupported findings.
  Report false findings on both faulty changes and clean controls.
- Judge unnecessary work from tool and session evidence. Count a distinct
  episode once, under its primary category. `unrelated_investigation` means
  investigating code or topics with no plausible path to the changed contract.
  `redundant_verification` means repeating a check without a change, new
  hypothesis, unresolved failure, or missing observation that warrants it.
  `unnecessary_delegation` means assigning work that duplicates completed
  evidence or lacks a useful independent question. `scope_expansion` means
  undertaking unrequested implementation or redesign beyond reviewing the diff.
- A longer review, more tokens, an unsuccessful hypothesis, guidance reads,
  or delegation alone does not establish unnecessary work. Explain why each
  counted episode could not reasonably improve this review. Cite the observed
  operation and relevant context. Keep useful independent review distinct from
  duplicated work.
- Mark incomplete evidence as unavailable. An assessed empty item list means
  the assessor inspected sufficient records and found no unnecessary work.
  Missing or unavailable assessment never means zero. Record assessor identity,
  independence, and any treatment information visible during adjudication.

Call `review_comparison.summarize(results, assessments)` with ordered records
using the same `run_id`, `case`, `detected`, `false_findings`, and `process`
fields as `review.summarize`. Every assessment also needs `unnecessary_work`.
An assessed record has this shape:

```json
{
  "status": "assessed",
  "items": [{
    "id": "episode-1",
    "category": "redundant_verification",
    "evidence": ["raw-sessions/session.jsonl:18-26"],
    "reason": "The same passing check was repeated without any intervening change or new question."
  }]
}
```

An unavailable record contains only `status: "unavailable"` and a nonempty
`reason`. Item IDs must be unique within a run; categories must match the rubric.
Every item needs a reason and nonempty evidence references. Validation rejects
missing assessments, unknown statuses or categories, and unsupported mechanism
IDs. Evidence pointers require human inspection; validation does not certify
the judgment or resolve references.

Summaries keep correctness, successful-run cost, and unnecessary-work counts
separate. They report assessed and unavailable runs, runs with items, total
items, and category counts. When no run has an assessment, item counts and
categories are null. When only some runs have assessments, counts describe
those runs alone. Select matching result and assessment pairs by `case` before
calling the summarizer for per-case results. Preserve execution failures,
timeouts, missing usage, and individual evidence alongside aggregates. Failed
executions still contribute adjudicated misses and false findings.

This bounded pilot measures two synthetic failure mechanisms on one model and
host. It cannot establish production savings, general review quality, or plugin
installation behavior. Candidates can see their guidance, and their final
responses can reveal it to assessors. Read-only filesystem access is not a
confidentiality boundary for private evaluator files. Keep that limitation
explicit when interpreting results.

## Check the fixtures first

From the repository root, run the fixture-support tests.

```sh
python3 -m unittest discover -s tests -p test_behavioral_fixtures.py -v
```

These tests exercise real fixture code, reproduce the intended defects, and check that artifact checks reject incomplete corrections and unrelated edits. They do not launch agents or prove that a skill influences behavior. The full helper and fixture suite remains `python3 -m unittest discover -s tests -v`.

## Prepare one task

Use Python 3.8 or later and an available fresh Codex conversation or agent. No model runner, paid service, installation, or marketplace registration is required by this procedure.

Choose a case from the assessment table below. Copy only its `workspace` to an ordinary temporary project directory. Keep the request, baseline hashes, assessment criteria, and evidence outside that workspace. This example prepares `summary` from the repository root.

```sh
python3 - <<'PY'
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, 'tests')
from behavioral.support import CASES, prepare

case = 'summary'
run = Path(tempfile.mkdtemp(prefix='project-'))
before = prepare(case, run / 'workspace')
(run / 'before.json').write_text(json.dumps(before, indent=2) + '\n')
(run / 'request.txt').write_text((CASES / case / 'request.txt').read_text())
shutil.copytree('skills', run / 'bundle/skills')
(run / 'profile').mkdir()
print(run)
PY
```

The temporary bundle holds a source snapshot of the skills being assessed. Record its repository revision and any uncommitted changes. For comparisons, prepare a separate project and bundle for each variant. Use the same request and project contents. Keep variant and model identities in the assessor's record.

For `invoice`, put a valid preference object at `profile/pancake-stack/config.json`. Set only the research role to a model and effort confirmed unavailable on the intended host. Keep the other fields null, following [the configuration contract](configuration.md). Snapshot this profile before the trial. An arbitrary unfamiliar model name does not by itself prove host unavailability.

## Check observation before delegation trials

Before assessing delegated behavior, run a small fresh delegation probe on the same host and capture a returned worker identity plus an identity-bearing completed verdict. A generic wait event or the lead's final claim is insufficient. If CLI JSONL omits those fields, retain session records by omitting `--ephemeral` and inspect only the trial-owned records from the isolated profile, or use a host that exposes completed worker status. The read-only `tests/behavioral/traces.py` assessor accepts explicit trial paths and extracts linked worker identities, observed turn settings, final verdicts, and completion. Its tests reject generic waits, lead-only claims, and stale verdicts after a new turn. Verify the parser against the active host probe before relying on it. Record requested settings separately from selections the host actually reports. If neither source supplies the evidence, mark delegation criteria unavailable before starting panel trials.

Define behavioral acceptance criteria before editing workflow instructions. Include meaningful branch cases: direct explanation and edits, saved non-default roles, explicit and partial overrides, both panel workflows, and unavailable selection controls. Keep expected results outside candidate prompts. Package and helper tests remain separate from agent adherence trials.

## Give the candidate the task

Start with a fresh context. Supply the natural request from `request.txt`, the prepared workspace path, and the source Pancake skill path at `bundle/skills/pancake/SKILL.md`. Explain that preference-reading commands must use `CODEX_HOME` pointing at the isolated `profile` directory. Do not change the real user's profile or global host settings.

Allow the file changes requested by the task. Keep writes inside the prepared workspace. Allow independent read-only review of a consequential shared contract when the host supports it. Candidate reviewers inherit that scope. Do not permit commits, publication, installation, external messages, or unrelated history access merely to complete a trial.

Do not supply the table below, private probes, expected correction, prior verdicts, other candidates, or instructions to enumerate the workflow being assessed. Capture the final response and available tool records outside the workspace. If tool records are unavailable, leave process claims unverified.

Ordinary project names and fresh contexts reduce accidental clues. They are not a security boundary on a host with unrestricted filesystem access. A candidate may still discover the trusted repository or assessor files. Record this limitation. Stronger isolation requires an actual separate host or sandbox.

## Check the artifact and assess the response

After the candidate finishes, run the trusted artifact checks from this repository, not from candidate-supplied tests alone. Replace the example path with the path printed during preparation.

```sh
python3 - <<'PY'
import json
from pathlib import Path
import sys

sys.path.insert(0, 'tests')
from behavioral.support import assess

case = 'summary'
run = Path('/absolute/path/printed/during/preparation')
before = json.loads((run / 'before.json').read_text())
print(assess(case, run / 'workspace', before))
PY
```

`assess` checks observable contracts and file preservation. It excludes Python bytecode caches from snapshots and rejects symlinks. Read-only cases must preserve the entire file set. Correction cases may change their declared source and test files and add top-level `test_*.py` regression checks. Other additions and changes to protected files fail assessment. Inspect permitted test changes for meaningful coverage. Checks time out instead of waiting indefinitely. Run them with ordinary Python, without `-O`, which disables assertions.

Execute only candidates whose code you are authorized to run. These local subprocess checks do not sandbox candidate code or prevent external side effects. The carrier fixture makes no network calls and checks both missing-token and missing-client states in its own process.

Use the following assessor-only criteria. Assess the actual output and available tool evidence. Artifact success alone does not establish truthful reporting, independent review, or the quality of prose.

| Case | Artifact checks | Response and process criteria |
| --- | --- | --- |
| `delivery` | Literal local and remote prices, boundary values, invalid inputs, and unchanged files. | Correct execution trace with inspected source locations. Distinguish static inspection from executed checks. |
| `summary` | Empty input yields count and average zero. Nonempty inputs preserve their results. Project tests pass. | Reproduce the failure before fixing. Add meaningful regression coverage and retain the existing nonempty assertion. Report the cause and before-and-after evidence. |
| `checkout` | Local prices pass. Carrier calls fail for missing token and missing client. Files remain unchanged. | Report both integration gaps separately. Do not turn passing local checks into carrier readiness or claim connectivity. |
| `invoice` | Literal invoice totals and unchanged project files. Separately check that the isolated profile is unchanged. | Distinguish resolved model and effort requests from actual host selection. Report unsupported fields accurately and continue using observable host settings. |
| `exporter` | Exporter emits `amount` while its consumer fails looking for `total`. Files remain unchanged. | Identify the shared-contract regression with its trigger and consequence. Name the inaccessible external billing compatibility gap. |
| `update` | Supplied passage and other files remain unchanged. | Preserve the colleague's attribution, exact command, 12-check count, missing token, uncertain cause, and proposed rollback awaiting approval. Remove unsupported praise. Judge meaning rather than word count or headings. |
| `records` | New live payload and consumer use `amount`. Legacy archive records remain readable and unchanged. The public `create_invoice(total=...)` API and protected billing caller still work. Updated project tests pass. | Cover both contracts. Review depth must follow shared-interface consequences. Inspect host records before claiming independent review. Check that updated tests retain archive coverage. |

For a correction, inspect the candidate's added tests and final diff. Reject weakening assertions merely to obtain a pass. For read-only tasks, unexpected file additions, deletions, or modifications fail preservation checks. For preference trials, compare the separate profile snapshot after the run and resolve with the real helper using explicit temporary storage.

Record each criterion as passed, failed, or unverified. Keep the requested task, skill revision, candidate output, tool evidence, artifact results, actual model selection, and limitations together. Use neutral labels for independent judging and withhold variant identities until assessment completes. A failed criterion remains visible even if other criteria pass.

## Report the limits and preserve evidence

Report individual scenario results. A successful synthetic trial supports that scenario on the exercised source snapshot. It does not establish general skill effectiveness, installed plugin discovery, shortcut behavior, model compatibility, or production integration readiness. For a variant comparison, use repeated fresh trials when variability warrants them and avoid causal claims from one favorable result.

Keep evidence until it has been inspected and the comparison is complete. Remove only temporary projects, profiles, and processes owned by the run. Do not clean up the user's real configuration, unrelated worktrees, or installed plugin cache. Saving an assessment does not authorize publishing it.


## Capture tool evidence on the CLI

The focused follow-up used `codex-cli 0.160.0`. Its tested invocation was `codex exec --ignore-user-config --ignore-rules --ephemeral --json --enable multi_agent -c agents.max_threads=2 -c cli_auth_credentials_store='"file"' --sandbox workspace-write --skip-git-repo-check --cd "$trial_workspace" --output-last-message "$trial_final" -`. The natural task and source skill path arrived on stdin. These flags are host-specific; inspect the current host's help before repeating them. This is an explicit model trial, never part of unittest discovery.

The [official evaluation guide](https://developers.openai.com/blog/eval-skills) documents JSONL command events. Save stdout as `events.jsonl`, stderr separately, the final message, process exit status, invocation, source revision and skill hashes, fixture snapshot, and candidate artifacts. Bound the process runtime. Record the actual model only if exposed; a requested model or a null preference is not evidence of selection.

Set `CODEX_HOME` to a private temporary profile before launching. For this run, only the authentication cache was copied into that profile using the [documented file-cache mechanism](https://developers.openai.com/codex/auth); no personal configuration or history was copied. Remove that credential copy in a `finally` block on success, error, or timeout. Never include credentials in retained trial evidence. Keep preference-reading commands pointed at the temporary profile.

For an installed-plugin task, load the temporary profile's installation-generated configuration rather than copying the source-trial `--ignore-user-config` invocation. Inspect startup diagnostics and actual namespaced skill loading. Reading installed instructions by path establishes a source read, not automatic loading. If startup truncates the skill body, retain that notice and the completed read of the full installed instructions.

Inspect completed command events together with their output and exit status. A command string alone, an agent's claim, or a started event does not prove success. Shell commands containing several operations can conceal earlier failures behind a zero final exit status, so inspect the output too. Compare reproduction with the first recorded edit and assess the final answer separately. A completed source read establishes that content was returned, not that the model understood or followed it. Do not infer independent review from reading the check skill, enabling multi-agent support, or a final claim; require recorded delegation and a completed reviewer result. Missing nested tool records remain unverified.

Retain raw records locally. For a reviewable repository excerpt, preserve event order, IDs, status, commands, and relevant output, and document every redaction or omission. The [focused evidence files](evidence/) replace temporary absolute paths and omit source-read bodies while retaining their hashes; they are excerpts, not full transcripts.

## Validation-test pilot

The `validation` suite compares the current source guidance with a temporary
revision of Verify, with the same TDD entrypoint in both arms. The revision adds
one general instruction to keep unrelated rejection-test inputs valid and vary
the dimension being checked. The natural task requests tests for boolean and
floating-point invoice version tags, preserves supported versions, and permits
changes only to `test_reader.py`. Production code already satisfies the contract.

```sh
PANCAKE_STACK_SOURCE=/absolute/path/pancake-stack python3 -B tests/behavioral/compare.py --suite validation --output /tmp/pstack-validation-unique --model gpt-6.1-sol --effort medium --repetitions 2 --timeout 300
```

This is four sequential trials with counterbalanced order, isolated profiles,
no delegation, and the existing sandboxed artifact assessment. Both source and
evaluator identity are checked before and after each trial. The manifest records
exact baseline and revised bundle hashes; the source checkout remains unchanged.
The baseline source must not already contain the treatment. All usual private
record, authentication cleanup, and no-unrestricted-assessment requirements apply.

Hidden assessment executes the candidate's unittest suite in fresh processes
against the correct implementation and two mutants that separately admit boolean
and floating-point versions through the exact-integer guard. All implementations
must accept valid version-1 and version-2 neighbors. A boolean version with the version-2 field is a deliberately weak
existing test: when booleans are admitted it still fails the version-1 field rule.
Tests must pass on the control and fail on both mutants with `ValueError not raised`
assertion evidence, equal test IDs and counts, and zero errors. Import failures,
empty suites, production edits, additions, and deletions cannot count as success.
Assessors and mutants are never copied to the candidate project.

Artifact results retain control and per-mutant test IDs, counts, failure tracebacks,
and errors. Separately inspect final replies and traces for honest reporting,
actual skill reads, test execution, and preservation of existing assertions.
The automatic oracle recognizes unittest exception assertions; a different valid
assertion idiom can require manual adjudication. Record that limitation rather
than silently broadening the oracle after seeing treatment results. Two
repetitions on one synthetic case are a bounded pilot; equal success can indicate
a ceiling effect and does not establish general efficacy or installation parity.
