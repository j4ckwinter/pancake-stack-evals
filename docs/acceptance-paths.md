# Unrelated acceptance paths and clean controls

Across both guidance variants, all four defect presentations were detected and all four clean-control reviews reported no findings. These cases extend Check coverage beyond the historical fixture. They show no advantage from the existing acceptance-path paragraph on these small tasks, so the guidance remains unchanged.

The [fixtures](../tests/behavioral/acceptance_cases.py) cover simultaneous booking moves and voucher-funded checkout. Each has a faulty early gate and a correct control. Booking swaps and cycles must be judged against final occupancy. Checkout affordability must use the price after the voucher. Existing visible tests pass in both faulty and clean fixtures. Separate evaluator tests exercise the public APIs with valid triggers, invalid inputs, and preservation checks.

| Case | Current guidance | Paragraph removed |
| --- | --- | --- |
| Simultaneous-move defect | Detected | Detected |
| Simultaneous-move control | No findings | No findings |
| Net-affordability defect | Detected | Detected |
| Net-affordability control | No findings | No findings |

The [runner](../tests/behavioral/acceptance_compare.py) requires frozen sources differing only by removal of the acceptance paragraph in Check. Every subject receives the same ordinary review request and explicit Check entrypoint. Hidden criteria and treatment identities remain outside the subject workspace. Trials use private profiles, inherit model settings, disable delegation, and preserve input identities. Execution validity, scope, defect detection, false positives, and reporting accuracy are separate judgments.

Run from the evaluator checkout with a Codex file authentication cache available:

```sh
PANCAKE_STACK_SOURCE=/path/to/pancake-stack python3 -B tests/behavioral/acceptance_compare.py --current /path/to/frozen-current --without /path/to/frozen-without --output /private/new-acceptance-records
```

All eight runs completed within the 240-second bounds and preserved their fixtures and bundles. Subjects reported gpt-6.1-sol with null effort; no override was requested. Two domain groups ran concurrently, with order counterbalanced inside each group. Timing is descriptive only.

A fresh same-model assessor judged neutral packets. Initial packets used incomplete CLI command events and wrongly marked two reproduction claims unsupported. Raw session calls and matched outputs show three passing tests followed by the expected API exception in both cases. Reassessment cleared those failures without rerunning subjects. A duplicate flattened output briefly exposed guidance before masking was repaired, so blinding is partial. The [normalized evidence](evidence/acceptance-paths-2026-10-22.json) preserves exact input identities, corrected judgments, and output and raw-session hashes. Raw records remain private.

The 145 package and evaluator checks passed with unchanged inputs before these trials. Subsequent extractor regression tests cover nested calls, failed outputs, and cross-turn records. These are one observation per treatment and case on synthetic projects. They establish neither repeatability nor general review superiority, and do not exercise installation, native discovery, or Claude workflows.
