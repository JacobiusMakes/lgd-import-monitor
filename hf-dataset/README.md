---
license: cc-by-4.0
language:
  - en
pretty_name: US Lab-Grown Diamond Import Monitor
size_categories:
  - 1K<n<10K
tags:
  - laboratory-grown-diamonds
  - lab-grown-diamonds
  - international-trade
  - us-census
  - un-comtrade
  - time-series
  - jewelry
  - tabular
  - timeseries
  - mlcroissant
  - pandas
configs:
  - config_name: census_monthly
    data_files: data/census-hts7104911000-monthly.csv
  - config_name: comtrade_partner_monthly
    data_files: data/us-imports-hs710491-monthly.csv
  - config_name: comtrade_heading_crosscheck
    data_files: data/us-imports-hs7104-family-world-monthly.csv
  - config_name: latest_release
    data_files: data/monthly-world.csv
---

# US Lab-Grown Diamond Import Monitor

A reproducible monthly dataset on United States imports of cut laboratory-grown
diamonds. The primary series uses US Census Bureau HTS 7104.91.10.00 data. UN
Comtrade HS 710491 data provides a partner-country cross-check.

This dataset is published for journalists, researchers, analysts, and developers
who need a dated source instead of an unsourced market estimate. It does not
describe Stienhardt's sales or inventory.

## Latest edition

The September 4, 2026 edition includes US Census data through July 2026 and UN
Comtrade data through June 2026. Census records $27.8 million in July across
1,324,682 stones, up 52 percent from June and down 59 percent from July 2025.

Customs value is not retail price. Average value per stone is not a price index
because size and quality mix can change from month to month.

[Explore the series in the interactive import monitor](https://huggingface.co/spaces/JacobiusMakes/us-lab-grown-diamond-import-monitor).

## Configurations

- `census_monthly`: the primary HTS 7104.91.10.00 monthly series, including
  customs value and quantity in number of stones.
- `comtrade_partner_monthly`: HS 710491 monthly imports by partner country.
- `comtrade_heading_crosscheck`: world totals for the relevant HS 7104 family
  used to test whether the September 2025 break was a simple reclassification.
- `latest_release`: the compact monthly table used in the current published
  edition.

## Load in Python

```python
from datasets import load_dataset

census = load_dataset(
    "JacobiusMakes/lab-grown-diamond-import-monitor",
    "census_monthly",
)
print(census["train"][0])
```

Each configuration is also available through Hugging Face's browser viewer,
Parquet conversion, API, and embed controls.

The repository root also includes a validated
[Data Package v2 descriptor](datapackage.json) for all four CSV resources.

## Sources and method

- US Census Bureau International Trade API, general imports, HTS
  7104.91.10.00.
- UN Comtrade, reporter United States, imports, commodity HS 710491.
- Harmonized Tariff Schedule of the United States for the product definition.

Full methodology and caveats are in [METHODOLOGY.md](METHODOLOGY.md). The source
repository includes the pull, build, validation, and chart scripts:
[JacobiusMakes/lgd-import-monitor](https://github.com/JacobiusMakes/lgd-import-monitor).

## Citation

Galperin, Jacob. *Lab-Grown Import Monitor*. September 4, 2026 edition.
Stienhardt & Stones, New York. CC BY 4.0.

## Maintainer

[Stienhardt & Stones](https://stienhardt.com/?utm_source=huggingface&utm_medium=data_repository&utm_campaign=lgd_import_monitor),
New York. Corrections and reproducibility issues are welcome through the source
repository.
