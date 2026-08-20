# Clinical source

The source from which `imci-selected-v0` is derived is **WHO — Integrated Management of Childhood Illness, Chart Booklet, March 2014** (ISBN 978 92 4 150682 3). The EdgeIMCI machine-readable encoding is not WHO-authored.

The WHO PDF is not redistributed with EdgeIMCI. Obtain it separately from WHO and place the unmodified file at:

```text
data/sources/IMCI chartbooklet 2014.pdf
```

Every encoded `imci-selected-v0` rule records the source section, `source_pdf_page` from the PDF viewer, and `source_printed_page` shown by the publisher. The 15-rule subset is not complete IMCI and does not represent the full respiratory or diarrhoea algorithms.
