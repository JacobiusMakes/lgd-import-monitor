# Methodology: the Lab-Grown Import Monitor

A monthly, fixed-format release of official statistics on United States imports of cut
laboratory-grown diamonds. Published by Stienhardt, a New York retailer of laboratory-grown
diamonds. Everything here is reproducible from public sources; the scripts in this repository pull
the numbers, and every figure carries its source and retrieval date. No em dashes.

## What is measured

**Primary series (United States Census Bureau).** US general imports under HTS 7104.91.10.00,
described in the Harmonized Tariff Schedule as "Cut but not set, and suitable for use in the
manufacture of jewelry" under heading 7104.91 (synthetic or reconstructed precious or
semiprecious stones: diamonds). Unit of quantity: number of stones ("No."). General rate of duty:
Free (column 2: 10 percent). Source: hts.usitc.gov, retrieved 2026-09-02. Pulled by
`scripts/census_pull.py` from the Census International Trade API (requires a free API key).

Reported fields per month: general imports value (US dollars, customs value), quantity (number of
stones), and imports by country of origin.

**Derived figure: average declared customs value per imported stone.** Value divided by quantity.
This is the number nobody publishes. It is a declared customs value at the border, not a retail
price, not a per-carat price, and not a quality-adjusted index. It moves with the mix of sizes
and qualities imported as much as with price. It is published because it is the only official
per-stone measure of what enters the country.

**Cross-check series (UN Comtrade).** US imports under HS 710491 (the six-digit international
parent of the US ten-digit line), by partner country, monthly. Pulled from the public Comtrade
preview endpoint (one period per call; no key) by the backfill script and stored in
`data/us-imports-hs710491-monthly.csv`. Comtrade's US figures are the Census figures resubmitted
to the UN; small differences arise from revisions and timing. When the two disagree, the Census
figure is primary and the difference is stated.

## Release timing

Census publishes the FT-900 (U.S. International Trade in Goods and Services) about five weeks after
the reference month; the July 2026 release is scheduled for 3 September 2026. Detailed
commodity-by-country data in the API typically follows the same day or the next business day. Each
Monitor edition is dated the day after the FT-900 and covers the same reference month.

## What the numbers do not say

- Melee dominates the count. On the first pull (2026-09-02) the Census series showed 0.4 to 2.9
  million stones a month at an average declared value of $8 to $27 per stone. Large center stones
  are a small share of the count and an unknown share of the value. Read the value series for
  supply; read the count and per-stone value as a mix indicator only.
- Pieces, not carats. The HTS unit is number of stones. Carat weight is not reported at this
  line, so a shift toward larger stones raises average value per piece without any price change.
- Customs value, not retail. Declared value at the border excludes duty, US wholesale margins,
  setting, and retail margins.
- Origin, not manufacture. Country of origin follows customs rules; a stone grown in one country
  and cut in another is generally recorded under the country of substantial transformation.
- Re-routing shows up as origin shifts. Changes in the India, Hong Kong, United Arab Emirates, and
  Thailand shares are reported without inference about why.
- The Harmonized Tariff Schedule uses the word "synthetic" for this heading. The Monitor quotes it
  only as the tariff-schedule term. Stienhardt's own descriptive term is laboratory-grown, in line
  with the US FTC Jewelry Guides (16 CFR 23.12).

## Standing checks run before each edition

- Reclassification within HS 7104: pull 7104 (heading total), 7104.99, 7104.21, and 7104.29 for
  the same months (`data/us-imports-hs7104-family-world-monthly.csv`). Result on 2026-09-02: the
  heading total fell with 7104.91 (August 2025 $54.4 million to September 2025 $8.7 million) and the
  other lines stayed under $5.1 million a month with no offsetting rise.
- Revisions: restate the prior twelve months from a fresh pull; flag any month revised by more than
  five percent.
- Census versus Comtrade: state the difference for the latest month when both exist.

## Standing tariff table (dated; verified before each edition)

| Effective | Measure | Rate on cut lab-grown diamonds | Source, date |
|---|---|---|---|
| 2025-08-07 | US tariff on Indian imports, first stage | 25 percent | National Jeweler, Lenore Fedow, 2025-08-06 |
| 2025-08-27 | Additional 25 percent on Indian imports, citing Russian oil purchases | 50 percent total | National Jeweler, Lenore Fedow, 2025-08-06 |
| As of 2026-02-07 | US reciprocal tariff on India (recently reduced from 50 percent) | 25 percent, plus the Free MFN rate | JCK, Rob Bates, 2026-02-09 |
| After the US-India interim agreement (planned for March 2026) | Reciprocal tariff reduced; natural cut diamonds and gems to 0 percent; lab-grown excluded from the duty elimination (not in Annex III) | 18 percent | Rapaport 2026-02-07 quoting GJEPC; JCK 2026-02-09 |
| Until 2026-07-24 | Section 122 surcharge (time-limited) | 10 percent | GJEPC via JewelBuzz, 2026-07-25 |
| From 2026-07-24, 00:01 EDT | Section 301 regime (no statutory expiry) | India 10 percent; China, Hong Kong, Thailand, Türkiye, UAE, Israel, Vietnam 12.5 percent | GJEPC via JewelBuzz, 2026-07-25 |

Gap stated plainly: the transition from the reciprocal tariff regime to the Section 122 surcharge
is not documented in this table yet. It is verified against primary sources before edition one
ships; until then, no edition draws a conclusion from a rate change across that boundary.

## Attribution and reuse

- Census: "This product uses the Census Bureau Data API but is not endorsed or certified by the
  Census Bureau."
- UN Comtrade: figures cite "UN Comtrade Database, retrieved [date]".
- The Monitor's tables, charts, and CSVs are CC BY 4.0; cite "Stienhardt, Lab-Grown Import
  Monitor, [edition date]". Charts published through Datawrapper River carry a frozen attribution
  link to the edition page.
- Revisions: Census revises prior months; each edition restates the prior twelve months from the
  current API pull and flags revisions larger than five percent.

## What Stienhardt does not do with this

No forecast, no price recommendation, no claim about any competitor, and no statement about
Stienhardt's own volumes or prices. The Monitor exists so that a monthly official series that no
one was publishing is published, with its caveats attached.
