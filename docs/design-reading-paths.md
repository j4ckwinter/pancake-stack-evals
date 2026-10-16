# Design reading paths, 16 October 2026

A bounded source-guidance pilot found no substantive design regression after
splitting the Design entrypoint into conditional references. An independent,
partially blinded assessor marked **30 criteria passed, none failed, and two
unavailable** across ten proposals. The unavailable criteria concern neutral
worker briefs: fresh launches and completed workers were observed, but their
briefs could not be independently audited. This supports retaining the extraction
for these cases; it does not establish general effectiveness or improved efficiency.

[Normalized evidence](evidence/design-reading-paths-2026-10-16.json) contains exact
source and evaluator hashes, original manifests, requests, invocations, outputs,
read-operation evidence, worker records, costs and both assessor judgments.
The [runner protocol](design-comparison.md) describes preparation and assessment.
Raw sessions remain private outside both repositories.

## Comparison and observed behavior

The baseline was `ec4ad1b1193123434f0400b0d0e8bc7304152663`. The candidate was a
frozen dirty snapshot on that revision; every Design file matches the later
`9c84761` commit. The main entrypoint fell from **1,392 to 852 words**. That is an
entrypoint reduction, not a reduction in total guidance, consumed context or model
cost. Successful commands requesting the new boundary, lifecycle and migration
references were observed where relevant. A successful command does not establish
exact text consumed or understood; output truncation can limit returned context.

Five natural requests covered an optional interface, validation, stored-record
migration, concurrent ownership/retry, and explicitly independent competing
designs. Each arm ran once per case in a fresh project and temporary profile.
Ordinary work remained direct. Both independent-design trials recorded two
completed proposals and a subsequent separate judge, all launched with
`fork_turns="none"`. Both judges contributed concrete reasoning. These observations
do not prove hidden context isolation or neutral brief contents.

| Case | Baseline seconds | Candidate seconds | Baseline total tokens | Candidate total tokens |
| --- | ---: | ---: | ---: | ---: |
| Optional interface | 27.109 | 24.549 | 65,666 | 63,789 |
| Validation boundary | 23.906 | 25.904 | 48,410 | 47,461 |
| Stored-record migration | 32.565 | 37.330 | 84,249 | 64,962 |
| Shared ownership and retry | 44.737 | 52.162 | 83,992 | 65,362 |
| Independent designs | 177.905 | 169.496 | 498,544 | 678,606 |

Tokens include all observed sessions, with complete usage records for these runs.
They are usage proxies, not invoices. Cost varies by case; the independent
candidate used more tokens despite finishing sooner. One observation per arm and
case cannot support a causal speed or efficiency claim.

All ten runs completed, produced nonempty final responses, preserved project
files, and left checked preferences unchanged. Source and evaluator identities
remained stable during each batch. Codex CLI `0.160.0` received no model or effort
overrides. Sessions reported `gpt-6.1-sol`; lead effort was null and workers
reported `low`. These are isolated CLI observations, not inheritance proof for the
parent conversation or evidence of model diversity.

## Scope and isolation limits

Artifact preservation did **not** establish full scope adherence. A later audit
found parent-directory filename discovery listing sibling isolated-profile plugin
paths in the baseline judge and in the candidate's first proposer and judge.
The original assessor packet included launch/completion/verdict records but omitted
those worker command bodies. Its separate supplemental assessment preserves the
original 30/0/2 substantive verdict and records the broader discovery. Filename
listing is not profile-content reading; no such content read was found in the
inspected operations. Exact worker-instruction compliance remains unavailable
because worker briefs are withheld. No clean-scope certification is inferred for
other runs from the absence of a supplemental finding.

The initial live runner recorded a 300-second cap for every case. An external
supervisor enforced a 180-second ordinary-case cap and checked preservation,
timeout, input stability and root completion; all ordinary cases finished below
53 seconds. The committed runner now enforces those gates directly, stops on a
missing or empty final response, and checks drift before launch. Tests exercise
invalid first results and input drift. Original trial records retain their
original evaluator hashes and are not retroactively relabeled with these gates.

## Separate final-source routing check

One additional trial started at `parallel-work.md` on the frozen clean skill
revision `e43a5ec`, after the routing and prerequisite-planning changes. It
successfully read `competing-designs.md`, launched two fresh-context proposers and
a fresh separate judge, and completed in **179.667 seconds**. Its records and
identity are separate from the paired Design comparison. No implementation or
runtime tests were requested.

All three workers listed sibling profile plugin filenames during discovery. The
lead disclosed two workers, so its final response underreported the observed
count. The retained call evidence corrects that account. Profile-content reading
was not evidenced. This run demonstrates the explicit routing path and completed
comparison, not full scope compliance or general validation of planning behavior.

## Decisions and remaining work

Retain the smaller Design entrypoint and conditional references, the explicit
independent-design routing, and shared prerequisite and resource-isolation rules.
Do not claim performance gains from shorter instructions or this pilot. Keep
semantic quality, artifact preservation, actual reads, worker completion and
scope adherence as separate evidence. Stronger discovery confinement and auditable
neutral briefs remain open evaluation limitations; adding more prose alone is not
a demonstrated remedy.

The existing [historical review evidence](historical-review.md) and six rerun
regression tests cover legitimate shared modules and compatible facade/documentation
changes rejected by an overrestrictive assessor. They also protect persisted
artifacts and reject independent contract regressions. This is reused historical
and test coverage, with no new live historical-review trial. The previously missed
target remains **0/2 detections in each arm**; clean-control specificity remains
unavailable. These structural instruction changes do not resolve that detection gap.

The pilot uses small synthetic projects, one host and model, partial assessor
blinding and no installed-plugin check. Proposed designs and verification plans
are not evidence of runtime correctness, production savings or cross-host parity.
