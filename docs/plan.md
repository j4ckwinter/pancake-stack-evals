# Project plan

## Current state

Version 0.19.3 packages the same 19 workflows for Codex and Claude Code. Both hosts share the skill tree and keep separate preferences. Delegates inherit host effort unless the task explicitly requests an effort. Existing saved effort remains stored but inactive.

Version 0.19.3 adds commit requests to the shipping workflow and requires repository commit-message conventions, with Conventional Commits as the fallback when none is documented. See [shipping guidance](https://github.com/j4ckwinter/pancake-stack/blob/795dc890ee0b0acf24e743d82362c4a92e4202e1/skills/pancake/references/shipping.md). Installed-host verification for this version remains pending.

Native Claude validation, isolated local installation, skill inventory, and model metadata discovery passed for 0.19.0 on 6 October 2026. Authenticated Claude behavior remains pending. See [Claude Code support](claude.md).

Installed Codex CLI trials on 5 October 2026 verified isolated Setup persistence, saved Challenge and implementation panels, proportionate review for a small edit, and competing Design proposals with a separate judge. The [installation record](installation-verification.md) and [trial results](behavioral-results.md) retain the evidence and unsuccessful earlier trials.

The [7 October baseline comparison](baseline-comparison.md) observed more consistent defect reproduction and independent migration review with Pancake. Both treatments passed all nine artifact checks. Pancake used more time and tokens, and one migration introduced a compatibility risk its reviewer missed. These results establish a process benefit on the tested fixtures, not improved correctness.

Version 0.19.2 strengthens the migration fixture to protect keyword callers and adds reviewer evaluation checks. The [reviewer comparison](behavioral-results.md#reviewer-detection-and-narrow-consolidation-7-october-2026) found all seeded defects with both instruction variants and no false actionable findings. The small trial did not demonstrate lower overhead, so the production Check instructions remain unchanged. Broader repository tasks and authenticated Claude workflows remain verification gaps.

The completed list records delivered guidance and repository work. The dated sections below record verification at their original versions. Their pending statements describe those earlier trials, not the current backlog.

## Completed

- Benchmark validity guidance for completed timed work, failure counts, representative tuning, runtime limits, and end-to-end impact.
- Skill evaluation guidance that separates natural candidate tasks from private assessment criteria and variant identities.
- Reusable fixtures and artifact checks for the seven recorded workflow trial families, with an isolated [evaluation procedure](behavioral-evaluation.md).
- Concrete [prompt recipes](recipes.md) for the existing skills, with host and evidence limitations.
- Explicit completion requirement for obtainable independent review of consequential changes. Later collaboration and installed CLI trials obtained completed reviewer verdicts. Earlier failures remain in the [trial results](behavioral-results.md).

- Conditional personalization guidance for requested working-style profiles, separate from shared defaults.

- Conditional TypeScript guidance for domain variants, type reuse, and runtime validation.

- Conditional verification-recipe maintenance with scoped corrections and explicit execution gaps.

- Teach skill for evidence-based explanations at the learner's requested depth.

- Recap skill for scoped context recovery and reconciliation with current artifacts.

- Plugin manifest and local marketplace.
- Setup skill with model discovery and preference storage.
- Read-only how skill for explaining existing code with evidence.
- Wtf skill for restating the previous answer in plain language.
- Balls skill for short standup updates covering blockers, aims, and lessons learned.
- Design skill for grounded proposals, proportionate alternatives, and verification plans.
- Why skill for evidence-based investigation of historical rationale.
- Verify skill for observable behavior checks, evidence, and scoped cleanup.
- Handoff skill for continuation notes grounded in conversation and repository state.
- Pr skill for titles and descriptions grounded in the ticket and branch diff.
- Scope skill for grounded implementation briefs and explicit requirement gaps.
- Pancake implementation sequence with proportional review, failure handling, and continuation notes.
- Sift prose skill applied throughout pancake drafting and replies.
- Challenge skill for evidence-based adversarial review and conditional pancake integration.
- Reflect skill for evidence-based lessons and structural improvement proposals.
- Conditional measured-experiment guidance for performance, prototypes, and skill evaluations.
- Check guidance for hidden consumers and evidence behind compatibility assumptions.
- Optional project verification recipes with execution evidence and scoped cleanup.
- Conditional cookoff and parallel-work guidance with isolated candidates and explicit coverage.
- Conditional substantial-work guidance with measurable completion criteria and phase checkpoints.
- Conditional decision trails for consequential choices, evidence, corrections, and continuation.
- Design guidance for caller usage, valid data shapes, state ownership, and recurring workaround diagnosis.
- Conditional Sift guidance for tutorials, task guides, reference material, and explanations.
- Check guidance for constraint comments, enforcement gaps, and justified or defective suppressions.
- Setup and Pancake reporting that separates saved preferences, resolved inheritance, and actual host application.
- Conditional runtime and trace diagnosis with source attribution and explicit evidence limits.
- Conditional visual-parity guidance for comparable captures, image differences, inspection, and state coverage.
- Conditional PR maintenance with evidence-based feedback triage, bounded retries, and revision-specific CI reporting.
- Conditional shipping guidance for current verification, dependency order, authorized delivery, and result confirmation.
- Substantial-work continuation guidance for ownership, recoverable unit state, dependent revisions, and bounded sustained runs.
- Conditional handoff guidance for evidence-based pickup and explicit pauses without automatic workspace cleanup.
- Conditional worktree cleanup with ownership checks, data preservation, normal Git removal, and result confirmation.
- Implementation guidance for scoped subtraction, observed usage, and reducing unnecessary indirection.
- Design guidance for changed constraints, useful foundations, and migrations with verifiable target states.
- Fix guidance for failed hypotheses, shared premises, distinguishing observations, and scoped root-cause correction.
- Design exploration guidance for concrete alternatives and consumer-focused tradeoffs.
- Design boundary guidance for runtime validation, authoritative schemas, and meaningful domain types.
- Design lifecycle guidance for retries, partial failures, caller migration, and structurally coordinated shared state.
- Verification guidance for discriminating observations, contract-based expectations, and integration evidence.
- Implementation execution guidance for useful automation, bounded context, and continued authorized work.
- Reflection guidance for owning safeguards, checking failure and valid cases, and verified structural learning.
- Shared core values and check, fix, and pancake skill definitions.
- Isolated tests for discovery, validation, inheritance, and persistence.
- Local installation, backend discovery, and user-confirmed setup invocation in VS Code.

## Next

- Run authenticated Claude How, Fix, Check, Setup interaction, reviewer panels, and competing Design. Verify requested versus applied model and effort separately. This environment reports no Claude authentication.
- Verify Git-backed Claude installation after the host metadata is available on the remote source.
- Verify visible VS Code labels, picker filtering, and namespaced invocation in a fresh chat. Backend discovery does not establish the visible result.
- Exercise a host with genuinely absent collaboration tools. Rejected selections, partial Design exploration, a rejected judge, and delegation outside task permissions now have observed fallback results.
- Exercise installed workflows on real repository tasks. The synthetic trials establish individual outcomes, not broad reliability.

License selection and public distribution remain deferred. They require a separate owner decision and publication authorization.

Git-backed CLI installation passed on 6 October 2026 in a new temporary profile. The installed 0.18.2 manifest and skill resources matched source. See the [installation record](installation-verification.md).

An installed Setup invocation also saved supplied inherited choices at the default path under temporary `CODEX_HOME`. A fresh helper process confirmed persistence. Backend discovery returned all 19 enabled skills without errors. Visible selection remains separate.

Five installed fallback tasks on 6 October covered rejected implementation and Challenge reviewers, partial Design exploration, a rejected judge, and a task prohibiting delegation. Their artifacts and reporting passed the scoped checks. See the [trial results](behavioral-results.md).

## Claude Code in 0.19.0

Both native manifests reference one shared workflow tree. Explicit `--host claude` selects Claude-owned preferences while unqualified helper calls retain Codex defaults. Schema versions, field inheritance, panels, and review requirements remain unchanged. The Claude catalog adapter reads CLI initialization metadata without a user or model turn and preserves missing effort metadata as undiscovered.

Isolated native validation and local installation passed on Claude Code 2.1.291. SDK initialization listed all 19 unique namespaced workflows. Codex 0.160.0 also installed the package, and an installed How task passed source and preservation assessment. Authenticated Claude workflow and per-worker settings remain unverified. The [host evidence](evidence/claude-support-2026-10-06.json) retains observed results and limits.

## Behavioral evaluation

The [3 October 2026 reusable-fixture trials](behavioral-results.md) exercised all seven recorded trial families and a measurement-validity task. All task artifacts passed their respective acceptance checks. The migration candidate and a fresh follow-up still reported direct review despite available independent review. The empty-input candidate's final reply omitted failing-before evidence. These remain reporting and process gaps, not passing workflow verdicts. No installed-host behavior or causal improvement is claimed.

An isolated independent explanation trial at e1cc602 selected How through Pancake, returned a correct code-cited answer, reported static inspection honestly, and preserved every fixture file. This is one repository-source scenario, not a VS Code installation or general behavioral verdict. Broader workflow trials remain pending.

An isolated independent defect-fix trial at 77c833f reproduced an empty-input crash, demonstrated the regression test failing before correction, reran the original case, and preserved unrelated files. Parent inspection and a fresh test run confirmed the resulting artifact. The final reply omitted the cause and before/after evidence, despite collecting them; broader evaluation should track this reporting gap. This remains a repository-source trial, not installed VS Code verification.

An isolated independent verification-gap trial at 97c5027 confirmed local shipping rates while reporting both a missing sandbox token and an absent carrier client. Parent reruns confirmed the reported outcomes, unchanged fixture files, and absent preference writes. The reply did not claim integration readiness. This is one repository-source scenario; actual carrier connectivity and installed VS Code invocation remain unverified.

An isolated independent preference-fallback trial at 73d5bb5 accurately explained source behavior and reported that an unsupported saved research model and effort could not be applied. Parent resolution confirmed the requested fields and inspection confirmed unchanged project and preference files. This covers direct research fallback only; partial selections, rejected delegated invocations, and installed VS Code behavior remain unverified.

An isolated independent change-review trial at d7bb8b2 found a renamed export field breaking an existing consumer, despite passing exporter checks. It reported unavailable external billing compatibility as a gap and preserved read-only scope. Parent reruns reproduced the consumer failure and confirmed unchanged fixture files and Git state. This covers one review scenario, not independent review during consequential implementation or installed VS Code behavior.

An isolated independent prose trial at 68a74c4 removed unsupported praise while preserving reported check attribution, an exact command and count, a verification gap, an uncertain diagnosis, and a proposed action awaiting approval. Parent inspection confirmed the revised text and unchanged fixture files. This covers a supplied-passage rewrite, not installed VS Code invocation or evidence preservation across substantial implementation.

An isolated independent implementation trial at fb6779c migrated a shared live payload and consumer while preserving old archived records. Parent contract checks passed and unrelated files were unchanged. The implementing agent disclosed direct review only, despite available independent review for this shared-interface migration. This records a proportional-review gap in one small synthetic fixture; installed VS Code behavior remains unverified.

Version 0.14.27 clarifies that implementation review depth follows affected contracts and failure consequences rather than diff size. Small shared-API changes retain the independent-review guidance. This addresses the observed migration-trial interpretation; behavioral confirmation of the clarification and installed VS Code verification remain pending.

A fresh isolated migration trial at e1e77d7 followed the revised review guidance and obtained an independent read-only review. Host agent status confirmed the reviewer completed; parent contract reruns passed and unrelated files were preserved. This is one successful follow-up on the same synthetic fixture, not proof of causal improvement, larger-migration reliability, or installed VS Code behavior.


## Follow-up safeguards in 0.16.5

Ordinary unittest discovery now validates the repository's package relationships and restricted skill/header/link conventions using isolated malformed copies. [Accepted safeguards](safeguards.md) record ownership, enforcement, regression checks, and limits. The [focused follow-up](behavioral-results.md#focused-tool-record-follow-up) retains actual CLI tool evidence for summary and migration trials. It establishes source reads and summary reproduction ordering while preserving the final-report and independent-review gaps. No additional product skill, command, or hook was introduced.


## Completion workflow in 0.16.6

Implementation now carries defect observations and consequential review needs into its completion step. Review is a separate phase, and standalone fix explicitly reports the original failure and corrected result. [Fresh workflow trials](behavioral-results.md#completion-workflow-correction-in-0166) passed summary reporting and recorded independent migration review on a collaboration-capable host. These are scoped observed successes, not proof of universal adherence or a controlled causal comparison.


## Test-first development in 0.17.0

The requested `tdd` skill adds an explicit failing-test-before-implementation cycle. It reuses existing test infrastructure, preserves unrelated assertions, and distinguishes behavioral failures from environment failures. Requests only to add tests do not authorize production changes. Pancake routes explicit test-first requests to the skill, and the README and prompt recipes document its use.

[Three focused trials](behavioral-results.md#tdd-skill-in-0170) exercised a full failing-before/passing-after cycle, a test-only defect regression, and passing coverage of existing behavior. Independent review clarified the test-only branch. The record preserves source hashes, evidence, and limits.
