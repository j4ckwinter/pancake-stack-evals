# Keep the focused TypeScript and boundary references

The 20 October 2026 review considered moving repeated generic boundary advice out of TypeScript guidance. The candidate was rejected before behavioral trials. Neither library reference changed.

The current TypeScript reference has 343 whitespace-separated words. The proposed conditional extraction had 320 words and linked to the existing 154-word boundary reference for external input or transport boundaries. That saves 23 words in the TypeScript file while introducing another navigation step. A reader loading both files would receive 474 words. These are static file counts, not measured agent context consumption; Design may already load both references when relevant.

The candidate retained discriminated unions, exhaustive handling, branded identifiers when justified, unknown values, predicate invariants, narrow assertions, inference, utility types, satisfies, caller-oriented signatures, and compiler limits. It moved runtime parser/schema reuse and transport ownership behind a conditional link. Static inspection found no conflicting policy or demonstrated behavioral defect in the existing overlap.

The small reduction did not justify another dependency solely to shorten the file. Keep the generic boundary reference focused and the TypeScript reference useful on its own. Revisit ownership if the rules diverge or an observed task demonstrates a maintenance or behavior problem. This is a maintainer judgment, not evidence that either layout performs better.

Minimize Reader Load determined the rejection. Subtract Before You Add ruled out adding a new skill or splitting either already short reference. No live agent or installation trial was run for this rejected candidate.

The [rejected candidate evidence](evidence/boundary-extraction-2026-10-20.json) retains hashes and counts. The rejected candidate text remains private.
