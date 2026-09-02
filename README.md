# Lab-Grown Import Monitor

Monthly official statistics on United States imports of cut laboratory-grown diamonds
(HTS 7104.91.10.00), with a UN Comtrade cross-check, published as a fixed-format release with
open data. Maintained by Stienhardt, New York. Method and caveats: [METHODOLOGY.md](METHODOLOGY.md).

## Contents

- `data/us-imports-hs710491-monthly.csv`: UN Comtrade, US imports of HS 710491 by partner, monthly
  from January 2024 (value in US dollars, quantity where reported, net weight where reported).
- `scripts/census_pull.py`: pulls the primary Census series (needs a free API key in
  `CENSUS_API_KEY`).
- `releases/`: one folder per edition with the release text, tables, and chart.

## Reproduce

```
python scripts/census_pull.py --from 2024-01 --to 2026-07 --out data/census-hts7104911000-monthly.csv
```

## License

Data compilations, text, and charts: CC BY 4.0. Cite "Stienhardt, Lab-Grown Import Monitor,
[edition date]". Census and UN Comtrade remain the sources of record and are cited in every table.
