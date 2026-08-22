# Selected-v0 archive

This directory contains the historical 14-case selected-v0 component regression slice and its proposed language renderings.

It is deliberately archived. It is **not** the product-level holistic golden semantic suite and must not be used for training, holistic generation, product evaluation, or a new teacher bake-off.

Permitted uses are limited to:

- reproducing the historical selected-v0 experiment;
- checking selected-v0 component behavior for regressions.

The canonical lifecycle and eligibility restrictions are recorded in `archive_manifest.json` and enforced by `edge_imci.corpus_policy` tests. The future product suite must use the distinct `HOLISTIC_PRODUCT_GOLDEN` corpus role and the major-sick-child rule/policy substrate.
