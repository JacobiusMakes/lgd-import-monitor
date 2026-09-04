"""Validate a Lab-Grown Import Monitor edition before publication or press outreach.

Usage:
  python scripts/validate_release.py --edition 2026-09-04
  python scripts/validate_release.py --edition 2026-09-04 --press-note ../../outreach/import-monitor/PRESS-NOTE-2026-09-04.md
"""
import argparse
import csv
import io
import os
import re


def read(path):
    return io.open(path, encoding="utf-8").read()


def money_millions(value):
    return "$%.1f million" % (value / 1e6)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--edition", required=True)
    parser.add_argument("--press-note")
    args = parser.parse_args()

    release_dir = os.path.join("releases", args.edition)
    release_path = os.path.join(release_dir, "RELEASE.md")
    shape_path = os.path.join(release_dir, "shape-search-share.md")
    chart_data_path = os.path.join(release_dir, "monthly-world.csv")
    census_path = os.path.join("data", "census-hts7104911000-monthly.csv")

    release = read(release_path)
    shape = read(shape_path)
    public_texts = [(release_path, release), (shape_path, shape)]
    if args.press_note:
        public_texts.append((args.press_note, read(args.press_note)))

    failures = []
    for path, text in public_texts:
        if "—" in text:
            failures.append("em dash in %s" % path)
        for banned in (
            "nobody publishes",
            "never been public",
            "dominated by small goods",
            "reclassification within hs 7104 is ruled out",
        ):
            if banned in text.lower():
                failures.append("unsupported phrase %r in %s" % (banned, path))

    if "DRAFT" in release or "pending an API key" in release:
        failures.append("release is still marked draft or pending")

    census_rows = list(csv.DictReader(io.open(census_path, encoding="utf-8")))
    totals = {}
    for row in census_rows:
        if (row.get("cty_code") or "").strip() in ("-", "0000", "TOTAL FOR ALL COUNTRIES"):
            totals[row["month"]] = {
                "value": int(float(row["gen_val_usd"])),
                "qty": int(float(row["gen_qty"])),
            }
    latest = max(totals)
    latest_row = totals[latest]
    previous_year = "%04d-%s" % (int(latest[:4]) - 1, latest[5:])
    previous_month_year, previous_month_number = int(latest[:4]), int(latest[5:]) - 1
    if previous_month_number == 0:
        previous_month_year, previous_month_number = previous_month_year - 1, 12
    previous_month = "%04d-%02d" % (previous_month_year, previous_month_number)
    yoy = round(abs(100 * (latest_row["value"] / totals[previous_year]["value"] - 1)))
    mom = round(100 * (latest_row["value"] / totals[previous_month]["value"] - 1))

    required_release = (
        money_millions(latest_row["value"]),
        "{:,}".format(latest_row["qty"]),
        "%d percent below" % yoy,
        "up %d percent" % mom,
    )
    for value in required_release:
        if value not in release:
            failures.append("latest Census value missing from release: %s" % value)

    chart_rows = list(csv.DictReader(io.open(chart_data_path, encoding="utf-8")))
    if chart_rows[-1]["month"] != latest:
        failures.append("chart data does not end at latest Census month")
    if int(chart_rows[-1]["customs_value_usd"]) != latest_row["value"]:
        failures.append("chart latest value does not match Census")

    shape_csv = list(csv.DictReader(io.open(os.path.join(release_dir, "shape-search-share.csv"), encoding="utf-8")))
    hexagon = next(row for row in shape_csv if row["shape_family"].startswith("Hexagon family"))
    if int(hexagon["us_monthly_searches"]) != 4380:
        failures.append("hexagon engagement-ring comparison total changed")
    if not re.search(r"4,380 monthly searches.*not part of.*55,320-search denominator.*12,100", shape, re.S):
        failures.append("shape release does not distinguish the 4,380 comparison from the 12,100 broader check")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        raise SystemExit(1)

    print("PASS: edition", args.edition)
    print("latest Census month:", latest)
    print("latest value:", latest_row["value"])
    print("latest quantity:", latest_row["qty"])
    print("year over year:", "%d percent below" % yoy)
    print("month over month:", "up %d percent" % mom)
    print("shape totals: 4,380 comparison; 12,100 broader check")


if __name__ == "__main__":
    main()
