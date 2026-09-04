# Lab-Grown Import Monitor

Monthly official statistics on United States imports of cut laboratory-grown diamonds
(HTS 7104.91.10.00), with a UN Comtrade cross-check, published as a fixed-format release with
open data. Maintained by [Stienhardt & Stones](https://stienhardt.com/?utm_source=github&utm_medium=data_repository&utm_campaign=lgd_import_monitor),
New York. Method and caveats: [METHODOLOGY.md](METHODOLOGY.md).

The dated releases are designed for citation and reuse. GitHub displays the repository's
machine-readable citation from [CITATION.cff](CITATION.cff), including the edition date and
dataset version.

## Use the data

- [Browse and query all four dataset configurations on Hugging Face](https://huggingface.co/datasets/JacobiusMakes/lab-grown-diamond-import-monitor).
- [Download the fixed September 2026 edition](https://github.com/JacobiusMakes/lgd-import-monitor/releases/tag/v2026.09.04).
- [Open the interactive monthly-value chart](https://datawrapper.dwcdn.net/rLZxK/5/).

## Contents

- `data/us-imports-hs710491-monthly.csv`: UN Comtrade, US imports of HS 710491 by partner, monthly
  from January 2024 (value in US dollars, quantity where reported, net weight where reported).
- `scripts/census_pull.py`: pulls the primary Census series (needs a free API key in
  `CENSUS_API_KEY`).
- `releases/`: one folder per edition with the release text, tables, and chart, plus
  `shape-search-share.md`, a like-for-like comparison of US search demand by ring outline
  (Semrush; raw pull in `data/semrush-shape-keywords-<date>.csv`; built by
  `scripts/build_shape_share.py`).

## Reproduce

```
python scripts/census_pull.py --from 2024-01 --to 2026-07 --out data/census-hts7104911000-monthly.csv
```

Before publishing or sending an edition to reporters:

```
python scripts/validate_release.py --edition 2026-09-04
```

## License

Data compilations, text, and charts: CC BY 4.0. Cite "Stienhardt, Lab-Grown Import Monitor,
[edition date]". Census and UN Comtrade remain the sources of record and are cited in every table.

## Related open data from Stienhardt

* [agent-shoppable-census](https://github.com/JacobiusMakes/agent-shoppable-census): which US ring
  sellers an AI agent can actually shop, split into merchant-built and platform-inherited.
* [diamondbench](https://github.com/JacobiusMakes/diamondbench): an open benchmark of AI answer
  accuracy on diamond questions.
* [dutch-marquise-spec](https://github.com/JacobiusMakes/dutch-marquise-spec): the open geometry
  specification for the Dutch Marquise cut (DOI 10.5281/zenodo.21938899).
