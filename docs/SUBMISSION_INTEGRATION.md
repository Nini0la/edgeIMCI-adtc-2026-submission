# Submission Integration Review

## Branch Disposition

| Branch | Disposition | Reason |
|---|---|---|
| `main` | Final submission branch | Receives the reviewed integration work and corrective changes |
| `chore/sync-upstream-provenance` | Retained integration history | Contains the template update, selected 4B model and dataset disclosures, metadata fix, preliminary CPU evidence, and measured before/after examples |
| `upload/edge-history` | Preserved as a historical archive, not merged | Separate research history with no common Git ancestor to the template; its clinical fixes already occur in the imported application subset |

The reviewed integration commits are `c79afd6`, `b67a14a`, `f4ed297`, `9bfe553`,
`a9e56b3`, and `ca4d8b6`. The historical research branch ends at `9c4b6e6` and
predates the application subset imported by `35b378c` from the later research
source described in [`FIDELITY_SUBSET.md`](FIDELITY_SUBSET.md).

No branch was deleted and no historical result was rewritten. Merging the research
archive wholesale would introduce unrelated corpora, research tooling, and older
root documentation/license choices without supplying a missing 4B submission fix.
Additional historical clinical tests or audit artifacts can be ported separately
if needed; they are not prerequisites for this integration.

## Corrections

- The reconstruction builder now refuses existing output paths and source-tree
  overlaps instead of recursively deleting directories. Missing inputs and
  Parquet dependencies are checked before output creation. No dataset was rebuilt.
- The future comparison runner checks merged-model bytes against the retained
  original inventory before inference. The retained comparison outputs are
  unchanged and are not represented as having run this newer guard.
- Regression tests cover those safeguards and adapter-download failure behavior.
- Legacy frontend test tooling moves to Vitest 4.1.11 or a compatible patch
  release to address the mocker path-traversal advisory, without changing Vite
  or the application runtime. Its tests and build are checked after the update.
- Current model licensing, historical candidate records, and legacy 0.6B GUI
  documents are distinguished from the selected 4B artifact.
- The profiling runbook targets `main`. An active profile must finish on its
  original checkout; do not change its commit or relabel its resulting report.
- `download_model.sh` remains the official template with only its two permitted
  model assignments changed. No custom download logic was introduced.

## Published Snapshot Errata

The pinned public dataset card at revision
`da8daa8efbd583d92000920366085f6dd00c3fb2` says its builder is included under
`provenance/`, but that snapshot's file listing does not contain the builder.
The submission retains the [builder source](../provenance/dataset/build_dataset_package.py).
Its current safety fixes do not change the published dataset files or establish
equivalence to the unavailable original final TRAIN serialization.

The pinned model card at revision `1aeace1a2eb6e46e5e93d6536cbd1c19db982e53`
predates the public dataset publication and paired before/after demonstration.
Its statements that those items were unavailable describe that older snapshot;
the current [report](../REPORT.md) and [provenance index](../provenance/README.md)
document subsequent work. The immutable model download pin is unchanged.

## Remaining Boundaries

The adapter is publicly hosted with a retrieval helper, not vendored as a large
Git blob. Organizer acceptance of that arrangement remains a question; this
review does not imply that a fetch helper is an original training script.

Full ADTC profiling, dataset/source-license review, and clinical authorization
are not established by this integration. Preliminary laptop measurements and
public before/after examples retain their stated limitations. The retained GUI
is a historical 0.6B integration; the selected 4B GGUF is evaluated independently.
