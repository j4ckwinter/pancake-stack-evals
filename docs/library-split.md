# Declarative library migration, 7 October 2026

This is the historical migration record. The evaluator has since been hosted on GitHub and the library has gained pinned CI. See the [current evaluator overview](../README.md); the original observations below retain their date.

The library and evaluator now have separate working trees. The evaluator retains the original history through `795dc890ee0b0acf24e743d82362c4a92e4202e1`. It has no remote. All historical fixture inputs and evidence were preserved; preference and catalog helpers moved to `fixtures/legacy-0.19.3` for historical tests only.

## Verified result

The [retained record](evidence/library-split-2026-10-07.json) identifies the exact library and evaluator revisions and hashes. All 70 checks passed against a clean clone of the committed library. Both checkouts remained unchanged. The library has 19 skills and no bundled Python files, tests, script directories, hooks, or evaluation evidence. The new package regression rejects those additions while accepting a Markdown reference.

Two fresh source-skill trials checked behavior. Setup declined to promise saved defaults and returned task wording for two inherited reviewers. Challenge completed two independent reviewer verdicts against the keyword-compatibility fixture. Both found the billing caller regression while existing tests passed. A fresh parent snapshot comparison confirmed the fixture unchanged. Inherited model and effort were requested; exact applied IDs were not reported by the host.

Independent review found incomplete provenance hashing and stale persistent-Setup guidance. Both were corrected. The reviewer confirmed the corrections and no remaining actionable findings.

## Limits and next checks

These are source-skill observations on the current collaboration host. Version 0.20.0 installation and authenticated Claude workflows remain unverified. The generic skill-creator validator could not run because PyYAML was absent; the repository-specific validator passed. Historical helper tests must not be interpreted as current runtime capabilities.

The user requested a local-only evaluation repository. GitHub CI cannot access it, so automatic pull-request validation remains pending. A future workflow should check out a pinned evaluator revision alongside the target library revision and retain both identities. No repository was published and no plugin was installed during this migration.
