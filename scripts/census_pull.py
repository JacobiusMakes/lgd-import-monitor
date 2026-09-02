"""Pull monthly US imports of cut lab-grown diamonds (HTS 7104.91.10.00) from the Census
International Trade API and write a tidy CSV.

Requires a free Census API key (api.census.gov/data/key_signup.html) in the environment as
CENSUS_API_KEY, or in a .env file next to this script. Republication is permitted with the Census
non-endorsement notice (see METHODOLOGY.md).

Usage:
  python scripts/census_pull.py --from 2024-01 --to 2026-07 --out data/census-hts7104911000-monthly.csv

Endpoint: https://api.census.gov/data/timeseries/intltrade/imports/hs
Variables: GEN_VAL_MO (general imports value, USD), GEN_QY1_MO (quantity, unit 1), UNIT_QY1,
CON_VAL_MO (imports for consumption), CTY_CODE, CTY_NAME, I_COMMODITY, time.
"""
import argparse, csv, io, json, os, sys, urllib.parse, urllib.request

HTS = "7104911000"
BASE = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
VARS = "CTY_CODE,CTY_NAME,GEN_VAL_MO,GEN_QY1_MO,UNIT_QY1,CON_VAL_MO"

def key():
    k = os.environ.get("CENSUS_API_KEY")
    if not k:
        env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env):
            for line in io.open(env, encoding="utf-8"):
                if line.startswith("CENSUS_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"')
    if not k:
        raise SystemExit("CENSUS_API_KEY missing. Request one at https://api.census.gov/data/key_signup.html")
    return k

def months(a, b):
    y, m = map(int, a.split("-"))
    y2, m2 = map(int, b.split("-"))
    while (y, m) <= (y2, m2):
        yield "%04d-%02d" % (y, m)
        m += 1
        if m == 13:
            y, m = y + 1, 1

def fetch(t, k):
    q = {"get": VARS, "I_COMMODITY": HTS, "time": t, "COMM_LVL": "HS10", "key": k}
    url = BASE + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": "lgd-import-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode()
    if not body.lstrip().startswith("["):
        # 204 empty (month not yet published) or an HTML error page
        print(t, "no JSON:", " ".join(body.strip()[:80].split()) or "(empty body)", file=sys.stderr)
        return []
    data = json.loads(body)
    hdr, rows = data[0], data[1:]
    return [dict(zip(hdr, row)) for row in rows]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="a", required=True)
    ap.add_argument("--to", dest="b", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    k = key()
    out = []
    for t in months(args.a, args.b):
        try:
            rows = fetch(t, k)
        except urllib.error.HTTPError as e:
            print(t, "HTTP", e.code, file=sys.stderr)
            continue
        for r in rows:
            out.append({"month": t, "cty_code": r.get("CTY_CODE"), "country": r.get("CTY_NAME"),
                        "gen_val_usd": r.get("GEN_VAL_MO"), "gen_qty": r.get("GEN_QY1_MO"), "qty_unit": r.get("UNIT_QY1"),
                        "con_val_usd": r.get("CON_VAL_MO"), "hts": r.get("I_COMMODITY")})
        print(t, len(rows), "rows")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with io.open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["month"])
        w.writeheader()
        w.writerows(out)
    print("wrote", len(out), "rows to", args.out)

if __name__ == "__main__":
    main()
