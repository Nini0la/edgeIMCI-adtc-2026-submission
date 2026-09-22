# Dataset Source and Rights Disclosure

Status: source disclosure recorded; rights clearance remains pending with the
project owner. This is a provenance disclosure, not legal advice, a legal
clearance, or a new dataset license.

## Release and Credits

The public release associated with selected model `4B-alpha-second` contains
2,258 reconstructed TRAIN rows and 139 validation rows. As recorded in
[publication.json](publication.json), TRAIN combines a hash-verified 1,831-row
baseline and 427 enrichment records; the original final internal TRAIN file is
unavailable, so byte identity to that file is not claimed. Validation is recorded
as byte-identical to the frozen release. The public dataset remains pinned at
`da8daa8efbd583d92000920366085f6dd00c3fb2`; this disclosure changes neither the
dataset nor its publication metadata.

Credit for dataset construction and curation belongs to the edgeIMCI project
owner and contributors, with AI assistance as described below. This is not a
claim that every row was exclusively human-authored or that all underlying
rights belong to the project. The clinical reference is World Health
Organization, *Integrated Management of Childhood Illness: Chart Booklet*,
March 2014, ISBN 9789241506823. The dataset is project-constructed, not authored
or endorsed by WHO.

## Reviewer Status

Construction details below reflect retained project construction records;
publication facts are supported by the linked local record. Neither is an
independent row-by-row rights audit.

| Component | Documented facts / source | License basis / unknowns |
| --- | --- | --- |
| Baseline and validation | Project-constructed synthetic/curated material; 1,831 baseline TRAIN rows. Project documentation identifies Azure GPT-4.1 assistance for baseline work. | Exact row-level model attribution is not fully verified. Contributor rights and applicable provider terms need owner confirmation; no complete clinical or privacy clearance is claimed. |
| Enrichment: 427 TRAIN rows | Expansion records: Azure GPT-5.4 phrased inputs only for 338 Alpha3 rows; deterministic local targets were computed beforehand. The 45 Delta1 rows inherit targets; 44 Delta2 rows have newly written scope/safety targets. | AI input phrasing is distinct from target computation. Project construction alone does not establish provider, contributor, or source rights. |
| WHO clinical reference | March 2014 booklet cited above. No WHO PDF is redistributed in the dataset package. | Non-redistribution of the PDF does not prove that no protected text was copied or adapted. A source-specific permission or applicable legal exception has not been established here. |
| Lundin external benchmark | Not identified as a training component in the supplied inventory. | Absence from training has not been independently proven; this is not a blanket exclusion or rights-clearance claim. |
| Public dataset | Local publication record specifies `license: other` and no general redistribution license asserted. | Public accessibility is not a general reuse grant. Apache licensing for code/base-model components and GPL licensing for the submission do not license the dataset. |

## Official Policy Context

**WHO.** The [open-access policy][who-open] explicitly says publications before
2017 will not be reissued under CC BY-NC-SA 3.0 IGO. It therefore does not
retroactively license this 2014 reference. The [copyright policy][who-copyright]
directs users to the publication's notice and permissions process for material
outside that license. Where permission is needed, the [permission terms][who-terms]
require actual WHO approval; citation, a submitted request, or public availability
is not approval. Applicable legal exceptions are not ruled out by this
disclosure, and no determination of their applicability is made here.

**Microsoft/Azure.** The current [MCA general online-services terms][ms-general]
classify Output Content as Customer Data and state that Microsoft does not own
it. They also restrict synthetic training-data generation for models or systems
with substantially similar functionality, subject to service-specific exceptions
in the [Azure terms][ms-azure]. Non-ownership is not an unrestricted reuse grant
or third-party rights clearance. The project's applicable agreement, service
coverage, and terms version have not been verified. These links identify the
owner's contract check, not evidence of either compliance or breach.

## Completion Boundary

On 2026-09-22 the project owner answered **"No separate permissions"** when asked
about written permissions or a documented licensing/legal basis for the WHO-derived
material and AI-generated examples. No permission records were supplied. This
does not establish whether a statutory exception or the applicable provider
contract permits a particular use; neither question has been determined here.

**Completed:** source inventory, AI-role distinctions, clinical citation,
publication/license boundaries, and official policy references are documented.

**Outstanding owner confirmation:** establish the applicable source permission
or legal exception for the actual material used, and confirm provider-agreement
coverage and contributor rights for the intended training and redistribution.
No approval is invented, and the existing pending rights/clinical statuses are
not changed. Clinical review and privacy clearance are not represented as
complete.

These disclosure uncertainties do not themselves block tooling/profile work,
create a new Gate 2 legal-approval requirement, or demonstrate that the model's
outputs are wrong. They also do not authorize clinical use or general reuse.

[who-open]: https://www.who.int/about/policies/publishing/open-access
[who-copyright]: https://www.who.int/about/policies/publishing/copyright
[who-terms]: https://www.who.int/about/policies/publishing/copyright/terms-and-conditions
[ms-general]: https://www.microsoft.com/licensing/terms/product/ForOnlineServices/MCA
[ms-azure]: https://www.microsoft.com/licensing/terms/productoffering/MicrosoftAzure/MCA
