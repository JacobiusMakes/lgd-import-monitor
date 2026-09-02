"""One-command monthly refresh: pull any new Comtrade months, re-pull Census, rebuild the edition,
update the Datawrapper chart, and print what changed. Run the morning after the FT-900 release.

Usage: python scripts/refresh.py --edition 2026-09-04 --through 202607
"""
import argparse, csv, io, json, os, subprocess, sys, time, urllib.request, urllib.error

COMTRADE = "https://comtradeapi.un.org/public/v1/preview/C/M/HS?reporterCode=842&cmdCode=710491&flowCode=M&includeDesc=true"
DATA = "data/us-imports-hs710491-monthly.csv"

def existing_periods():
    if not os.path.exists(DATA):
        return set()
    return {r["period"] for r in csv.DictReader(io.open(DATA, encoding="utf-8"))}

def pull_period(p):
    req = urllib.request.Request(COMTRADE + "&period=" + p, headers={"User-Agent": "curl/8"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            rows = []
            for x in d.get("data", []):
                if x.get("partner2Code") == 0 and x.get("customsCode") == "C00" and x.get("motCode") == 0:
                    rows.append({"period": p, "partner_code": x.get("partnerCode"), "partner": x.get("partnerDesc"),
                                 "value_usd": x.get("primaryValue"), "qty": x.get("qty"), "qty_unit": x.get("qtyUnitAbbr"),
                                 "net_wgt_kg": x.get("netWgt"), "cif_usd": x.get("cifvalue"), "fob_usd": x.get("fobvalue")})
            return rows
        except urllib.error.HTTPError as e:
            time.sleep(6 if e.code == 429 else 3)
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", required=True)
    ap.add_argument("--through", required=True)
    ap.add_argument("--chart-id", default="rLZxK")
    a = ap.parse_args()
    have = existing_periods()
    y, m = int(a.through[:4]), int(a.through[4:])
    wanted = []
    yy, mm = 2024, 1
    while (yy, mm) <= (y, m):
        wanted.append("%04d%02d" % (yy, mm))
        mm += 1
        if mm == 13:
            yy, mm = yy + 1, 1
    missing = [p for p in wanted if p not in have]
    added = []
    for p in missing:
        rows = pull_period(p)
        if rows:
            with io.open(DATA, "a", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writerows(rows)
            added.append(p)
        time.sleep(3)
    print("Comtrade months added:", added or "none (latest month not published yet)")
    last = max(have | set(added)) if (have or added) else None
    subprocess.run([sys.executable, "scripts/census_pull.py", "--from", "2024-01", "--to", "%s-%s" % (a.through[:4], a.through[4:]),
                    "--out", "data/census-hts7104911000-monthly.csv"], check=False)
    subprocess.run([sys.executable, "scripts/build_release.py", "--edition", a.edition, "--through", last], check=True)
    subprocess.run([sys.executable, "scripts/datawrapper_publish.py", "--edition", a.edition, "--chart-id", a.chart_id], check=False)
    print("Rebuilt edition", a.edition, "through", last, "| now update the bracketed figures in the press note and push.")

if __name__ == "__main__":
    main()
