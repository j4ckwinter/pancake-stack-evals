# Historical migration assessor regression

`source.tar.gz` is the complete tree at introducing commit `c2b044ea3eb460519942f58af4926d6fda04bfe2`. `provenance.json` pins its parent, archive digest, and every extracted file. The private scenario module pins the provenance file's digest and checks each auxiliary artifact before extraction.

`introducing.diff` is the actual Git diff from the parent, restricted to `tests/behavioral/support.py` and the contract scenario directory. This extraction focuses the review on the affected assessor and task contract. The full contemporaneous repository remains available to the candidate.

`base-support.py.txt` comes from the introducing commit's parent. `repaired-support.py.txt` comes from fixing commit `e3a04e80210c87315c1d30cec324b352f3a4f11a`. The clean control replaces only that production file in the introducing tree and recomputes its displayed diff against the same parent. It is a counterfactual control, not a historical revision. No fixing-commit tests, documentation, or answer-bearing evidence enter the candidate tree.

The private regression test executes the historical `support.assess` against a valid migration using a shared source module and compatible billing/documentation updates. The faulty assessor rejects it before checking behavior. The repaired assessor accepts it and still rejects modified notes, modified stored archives, and unrelated JSON additions. These fixture checks establish discrimination for this mechanism, not model performance.
