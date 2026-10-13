# Validation-test controls, 13 October 2026

All four trials produced tests that passed the correct reader and detected separate boolean and float validation regressions. Current Verify guidance and the proposed addition each passed twice. Keep the current guidance. This pilot did not demonstrate a correctness benefit from the additional wording.

## What changed

The evaluator now checks whether generated rejection tests fail when the relevant validation is absent. The fixture includes an existing boolean test whose wrong invoice field can mask a missing version-type check. Candidates receive a normal request to add boolean and float version coverage and change only the test file.

Hidden assessment runs the generated tests against the correct reader and two isolated mutants. One admits boolean version tags; the other admits floating-point tags. Both retain all other validation. Passing requires nonempty control coverage, matching test identities, no errors or skipped coverage, and assertion failures against both mutants. A syntax failure or a passing test that rejects the wrong field cannot earn success.

Independent review found that one combined mutant could reward boolean-only coverage. Separate mutants and focused evaluator regressions corrected that issue before live trials.

## Method and results

Source was clean library revision `59332a2`; the clean evaluator harness was `0d49850`. Both arms loaded TDD and its Verify reference. The revised arm added two sentences about otherwise-valid input and varying one dimension. The source checkout stayed unchanged. Exact input hashes, treatment hashes, prompts, invocations, artifacts, and outcomes are retained in the [evidence record](evidence/validation-controls-2026-10-13.json).

Two repetitions ran in current/revised then revised/current order. All four candidates reported `gpt-6.1-sol` with medium effort on Codex CLI 0.160.0. Each had an isolated profile, no delegation, and a 300-second limit. Every run finished, preserved production files, retained valid-version assertions, and removed its temporary profile and copied credentials.

| Guidance | Completed | Correct control | Boolean mutant detected | Float mutant detected | Median seconds | Median total tokens |
| --- | --- | --- | --- | --- | --- | --- |
| Current | 2/2 | 2/2 | 2/2 | 2/2 | 60.9 | 92,548 |
| Proposed | 2/2 | 2/2 | 2/2 | 2/2 | 57.0 | 82,571.5 |

Token totals include cached input and are usage, not monetary cost. Timing ranges were 41.4 to 80.5 seconds for current guidance and 55.3 to 58.6 seconds for the proposal. Two observations per arm cannot establish a speed or cost improvement.

The lead inspected every generated test and final answer, and checked the recorded before/after unittest commands. All candidates read Verify. All retained the assertions for integer versions 1 and 2. No production correction was needed because the supplied reader already behaved correctly.

A separate assessor requested as `gpt-5.6-sol` reviewed neutral-labeled tests and reports without treatment identities. It passed all four after receiving the exact contract and a missing baseline command excerpt. Initial concerns about redundant `False` and `1.5` checks did not violate the observable rejection contract. The evidence preserves that adjudication. Package validation and all 97 evaluator checks passed before the live run.

## Limits and reproduction

This is one synthetic validation task on one model and CLI host. It does not establish general test quality, installed-plugin behavior, or Claude support. The automatic oracle recognizes unittest exception assertions. Other valid assertion styles require manual adjudication rather than silent changes to scoring.

Use the [validation procedure](behavioral-evaluation.md#validation-test-pilot) with a checkout of the recorded baseline and the published evaluator. Raw sessions remain private outside Git. The committed evidence retains generated tests and command results without authentication material.
