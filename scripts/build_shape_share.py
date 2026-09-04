"""Ring-shape search share: turn the Semrush keyword pull into a share table, a twelve-month trend
note, and a Datawrapper bar chart. Reads data/semrush-shape-keywords-<date>.csv (semicolon separated,
Semrush phrase_these export). Writes releases/<edition>/shape-search-share.{md,csv} and publishes or
updates a Datawrapper bar chart when DATAWRAPPER_TOKEN is available.

Usage: python scripts/build_shape_share.py --edition 2026-09-04 --pull 2026-09-03 [--chart-id ID]
"""
import argparse, csv, io, json, os, urllib.request, urllib.error

# Query families: engagement-ring intent terms grouped by outline family. Volumes are US monthly
# averages from Semrush; the trend field is Semrush's twelve-month index (1.00 = the peak month).
FAMILIES = {
    "Marquise": ["marquise engagement ring"],
    "Princess": ["princess cut engagement ring"],
    "Oval": ["oval engagement ring"],
    "Emerald": ["emerald cut engagement ring"],
    "Hexagon family (Dutch marquise, elongated hexagon, hexagon)": ["dutch marquise engagement ring", "elongated hexagon engagement ring", "hexagon engagement ring"],
    "Round": ["round engagement ring"],
    "Radiant": ["radiant engagement ring"],
    "Pear": ["pear engagement ring"],
    "Moval": ["moval engagement ring"],
    "Cushion": ["cushion engagement ring"],
    "Baguette": ["baguette engagement ring"],
    "Elongated cushion": ["elongated cushion engagement ring"],
    "Old mine": ["old mine cut engagement ring"],
    "Heart": ["heart engagement ring"],
    "Asscher": ["asscher engagement ring"],
    "Kite": ["kite engagement ring"],
    "Trillion": ["trillion engagement ring"],
    "Old European": ["old european cut engagement ring"],
    "Elongated radiant": ["elongated radiant engagement ring"],
}
TERM_FAMILY_DM = ["dutch marquise diamond", "dutch marquise", "dutch marquise engagement ring"]

def load(path):
    rows = {}
    for r in csv.DictReader(io.open(path, encoding="utf-8"), delimiter=";"):
        k = r["keyword"].strip().lower()
        rows[k] = {"volume": int(r["volume"] or 0), "trend": [float(x) for x in (r.get("trend") or "").split(",") if x.strip()]}
    return rows

def trend_growth(trend):
    """Ratio of the mean of the last three index points to the mean of the first three."""
    if len(trend) < 6:
        return None
    a = sum(trend[:3]) / 3.0
    b = sum(trend[-3:]) / 3.0
    return (b / a) if a else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", required=True)
    ap.add_argument("--pull", required=True, help="pull date YYYY-MM-DD")
    ap.add_argument("--chart-id")
    a = ap.parse_args()
    kw = load("data/semrush-shape-keywords-%s.csv" % a.pull)
    fam = []
    for name, terms in FAMILIES.items():
        vol = sum(kw.get(t, {}).get("volume", 0) for t in terms)
        fam.append((name, vol, terms))
    fam.sort(key=lambda x: -x[1])
    total = sum(v for _, v, _ in fam)
    out_dir = os.path.join("releases", a.edition)
    os.makedirs(out_dir, exist_ok=True)
    with io.open(os.path.join(out_dir, "shape-search-share.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["shape_family", "us_monthly_searches", "share_pct", "terms"])
        for name, vol, terms in fam:
            w.writerow([name, vol, round(100.0 * vol / total, 1), " + ".join(terms)])
    dm_terms = {t: kw.get(t, {}) for t in TERM_FAMILY_DM}
    dm_total = sum(v.get("volume", 0) for v in dm_terms.values())
    growth = {t: trend_growth(v.get("trend", [])) for t, v in dm_terms.items()}
    lines = ["# Ring-shape search share, United States (edition %s)" % a.edition, "",
             "Source: Semrush keyword database, United States, monthly average search volume and twelve-month trend index, retrieved %s. Query families are engagement-ring intent terms; the hexagon family sums three terms because the outline is sold under several names. Shares are of the %s total below and describe what people type, not what they buy. No Stienhardt data is used." % (a.pull, "{:,}".format(total)),
             "", "| Shape family | US searches per month | Share |", "|---|---:|---:|"]
    for name, vol, terms in fam:
        lines.append("| %s | %s | %.1f%% |" % (name, "{:,}".format(vol), 100.0 * vol / total))
    lines += ["", "## The Dutch Marquise term",
              "The comparison table counts 4,380 monthly searches across three engagement-ring phrases: \"dutch marquise engagement ring\", \"elongated hexagon engagement ring\", and \"hexagon engagement ring\". A separate broader term check, which is not part of the table's 55,320-search denominator, totals about %s monthly searches across \"dutch marquise diamond\", \"dutch marquise\", and \"dutch marquise engagement ring\". Semrush's twelve-month trend index for each broader phrasing rose over the year (mean of the last three months divided by the mean of the first three: %s). \"Dutch marquise\" is a trade name used for elongated hexagonal-cut diamonds; grading reports may use other shape descriptions." % (
                  "{:,}".format(dm_total),
                  ", ".join("%s %.1fx" % (t, g) for t, g in growth.items() if g)),
              "", "For comparison, US monthly searches for \"asscher engagement ring\" are %s, \"kite engagement ring\" %s, \"trillion engagement ring\" %s, \"elongated cushion engagement ring\" %s, and \"moval engagement ring\" %s." % tuple(
                  "{:,}".format(kw.get(t, {}).get("volume", 0)) for t in ("asscher engagement ring", "kite engagement ring", "trillion engagement ring", "elongated cushion engagement ring", "moval engagement ring")),
              "", "Caveats: search volume is a demand proxy with rounding at the low end; a name that is new to the market can grow fast from a small base; Semrush volumes are twelve-month averages, so the index is the better read of direction. The table counts one fixed phrasing per family, so it under-counts shapes people search by other words: round buyers type \"solitaire\" or \"round diamond\" far more often than \"round engagement ring\", and cushion buyers type \"cushion cut diamond\" (22,200 a month) more than \"cushion engagement ring\". Read it as a comparison of like phrasings, not as market share. Raw pull: ../../data/semrush-shape-keywords-%s.csv." % a.pull]
    text = "\n".join(lines) + "\n"
    if "—" in text:
        raise SystemExit("em dash")
    io.open(os.path.join(out_dir, "shape-search-share.md"), "w", encoding="utf-8", newline="\n").write(text)
    print(text)

    # Datawrapper bar chart
    tok = os.environ.get("DATAWRAPPER_TOKEN")
    if not tok:
        env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env):
            for line in io.open(env, encoding="utf-8"):
                if line.startswith("DATAWRAPPER_TOKEN="):
                    tok = line.split("=", 1)[1].strip()
    if not tok:
        print("no DATAWRAPPER_TOKEN; chart skipped")
        return
    API = "https://api.datawrapper.de/v3"
    def req(method, path, body=None, ctype="application/json", raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        r = urllib.request.Request(API + path, data=data, method=method, headers={"Authorization": "Bearer " + tok, "Content-Type": ctype})
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                t = resp.read().decode()
                return resp.status, (json.loads(t) if t.strip().startswith(("{", "[")) else t)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()[:300]
    meta = {"title": "What people search for by ring shape, United States",
            "type": "d3-bars",
            "metadata": {"describe": {"intro": "Monthly US searches for engagement-ring terms by outline family. The hexagon family sums \"dutch marquise\", \"elongated hexagon\", and \"hexagon\" engagement ring queries.",
                                      "source-name": "Semrush, US database, retrieved %s" % a.pull,
                                      "source-url": "https://github.com/JacobiusMakes/lgd-import-monitor",
                                      "byline": "Stienhardt, Lab-Grown Import Monitor, edition %s" % a.edition},
                         "axes": {"labels": "Shape family", "bars": "US searches per month"},
                         "visualize": {"base-color": "#2F57B0", "thick": False, "sort-bars": True, "value-label-alignment": "right", "show-value-labels": True},
                         "data": {"transpose": False, "horizontal-header": True},
                         "publish": {"embed-width": 700, "embed-height": 560}}}
    if a.chart_id:
        cid = a.chart_id
        req("PATCH", "/charts/" + cid, meta)
    else:
        st, r = req("POST", "/charts", meta)
        if st not in (200, 201):
            raise SystemExit("create failed %s %s" % (st, r))
        cid = r["id"]
    data = "Shape family,US searches per month\n" + "\n".join("%s,%d" % (n.replace(",", " and"), v) for n, v, _ in fam)
    st, r = req("PUT", "/charts/%s/data" % cid, ctype="text/csv", raw=data.encode())
    if st not in (200, 201, 204):
        raise SystemExit("data failed %s %s" % (st, r))
    st, r = req("POST", "/charts/%s/publish" % cid, {})
    if st not in (200, 201):
        raise SystemExit("publish failed %s %s" % (st, r))
    st, info = req("GET", "/charts/" + cid)
    print("chart id:", cid, "| public:", info.get("publicUrl") if isinstance(info, dict) else None)

if __name__ == "__main__":
    main()
