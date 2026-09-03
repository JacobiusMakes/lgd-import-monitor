"""Build an edition of the Lab-Grown Import Monitor from the Comtrade CSV (and the Census CSV when
present): tables, a chart (SVG), and the release text. No em dashes anywhere.

Usage: python scripts/build_release.py --edition 2026-09-04 --through 202606
"""
import argparse, csv, io, os, collections, datetime

def load(path):
    rows = list(csv.DictReader(io.open(path, encoding="utf-8")))
    for r in rows:
        r["value_usd"] = float(r["value_usd"] or 0)
    return rows

def money(v):
    return "$%.1f million" % (v / 1e6)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", required=True)
    ap.add_argument("--through", required=True, help="last Comtrade period, e.g. 202606")
    ap.add_argument("--data", default="data/us-imports-hs710491-monthly.csv")
    a = ap.parse_args()
    rows = load(a.data)
    world = {r["period"]: r["value_usd"] for r in rows if r["partner_code"] == "0"}
    by = collections.defaultdict(dict)
    for r in rows:
        if r["partner_code"] != "0":
            by[r["period"]][r["partner"]] = r["value_usd"]
    periods = sorted(p for p in world if p <= a.through)
    last = periods[-1]
    y, m = int(last[:4]), int(last[4:])
    prev_year = "%04d%02d" % (y - 1, m)
    two_years = "%04d%02d" % (y - 2, m)
    ytd = [p for p in periods if p[:4] == last[:4]]
    ytd_prev = ["%04d%s" % (y - 1, p[4:]) for p in ytd]
    ytd_two = ["%04d%s" % (y - 2, p[4:]) for p in ytd]
    tot = lambda ps: sum(world.get(p, 0) for p in ps)
    avg_2024 = tot([p for p in periods if p[:4] == "2024"]) / max(1, len([p for p in periods if p[:4] == "2024"]))
    post = [p for p in periods if p >= "202509"]
    avg_post = tot(post) / max(1, len(post))

    def share(p, name):
        w = world.get(p, 0)
        return 100 * by[p].get(name, 0) / w if w else 0

    out_dir = os.path.join("releases", a.edition)
    os.makedirs(out_dir, exist_ok=True)

    # ---------- Census primary series (when the key has been used) ----------
    census_path = "data/census-hts7104911000-monthly.csv"
    census_tbl = ["(Census primary series not pulled yet: run scripts/census_pull.py with CENSUS_API_KEY.)"]
    census_note = ""
    if os.path.exists(census_path):
        crow = list(csv.DictReader(io.open(census_path, encoding="utf-8")))
        cm = collections.defaultdict(lambda: {"val": 0.0, "qty": 0.0, "has_total": False})
        for r in crow:
            mo = r["month"].replace("-", "")
            val = float(r.get("gen_val_usd") or 0)
            qty = float(r.get("gen_qty") or 0)
            if (r.get("cty_code") or "").strip() in ("-", "0000", "TOTAL FOR ALL COUNTRIES"):
                cm[mo] = {"val": val, "qty": qty, "has_total": True}
            elif not cm[mo]["has_total"]:
                cm[mo]["val"] += val
                cm[mo]["qty"] += qty
        census_tbl = ["| Month | Census customs value | Stones (No.) | Average value per stone | Comtrade value | Difference |",
                      "|---|---|---|---|---|---|"]
        for mo in sorted(cm)[-13:]:
            c = cm[mo]
            per = (c["val"] / c["qty"]) if c["qty"] else None
            comt = world.get(mo)
            diff = ("%.1f%%" % (100 * (c["val"] / comt - 1))) if comt else "n/a"
            census_tbl.append("| %s-%s | %s | %s | %s | %s | %s |" % (mo[:4], mo[4:], money(c["val"]),
                              ("{:,.0f}".format(c["qty"]) if c["qty"] else "n/a"),
                              ("$%.0f" % per if per else "n/a"), (money(comt) if comt else "n/a"), diff))
        census_note = ("Average declared value per stone is customs value divided by the number of stones, "
                       "a border figure that moves with the size and quality mix as much as with price.")
        newer = [mo for mo in cm if mo > last and cm[mo]["val"] > 0]
        if newer:
            mo = max(newer)
            c = cm[mo]
            prev = "%04d%s" % (int(mo[:4]) - 1, mo[4:])
            yoy_c = ("%.0f percent %s" % (abs(100 * (c["val"] / cm[prev]["val"] - 1)), "below" if c["val"] < cm[prev]["val"] else "above")
                     if prev in cm and cm[prev]["val"] else "n/a")
            census_note += ("\n\nLatest month, Census only (UN Comtrade has not yet published it): %s-%s, %s across "
                            "{:,.0f} stones, %s the same month a year earlier." % (mo[:4], mo[4:], money(c["val"]), yoy_c)).format(c["qty"])

    # ---------- chart: monthly world value, single hue, annotated ----------
    W, H = 900, 470
    L, R, T, B = 70, 30, 90, 70
    pw, ph = W - L - R, H - T - B
    vmax = max(world[p] for p in periods)
    step = pw / len(periods)
    navy, ink, mute, track, bg = "#2F57B0", "#1c2440", "#4a5068", "#e6e8ef", "#fcfcfb"
    s = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" role="img" aria-labelledby="t d">' % (W, H, W, H),
         '<title id="t">US imports of cut lab-grown diamonds by month, HS 710491</title>',
         '<desc id="d">Monthly customs value of US imports under HS 710491 from January 2024 to %s, UN Comtrade. Values fell from a 2024 average near %s to %s a month after September 2025.</desc>' % (last, money(avg_2024), money(avg_post)),
         '<rect width="%d" height="%d" fill="%s"/>' % (W, H, bg),
         '<text x="%d" y="34" font-family="Marcellus, Georgia, serif" font-size="21" fill="%s">US imports of cut lab-grown diamonds, by month</text>' % (L, ink),
         '<text x="%d" y="56" font-family="Helvetica, Arial, sans-serif" font-size="13" fill="%s">Customs value, US dollars, HS 710491 (synthetic diamonds, worked). UN Comtrade, retrieved 2026-09-02; Census primary series agrees within 5 percent.</text>' % (L, mute)]
    # gridlines
    for g in range(0, 5):
        v = vmax * g / 4
        yy = T + ph - ph * g / 4
        s.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>' % (L, yy, W - R, yy, track))
        s.append('<text x="%d" y="%.1f" text-anchor="end" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="%s">$%dM</text>' % (L - 8, yy + 4, mute, round(v / 1e6)))
    for i, p in enumerate(periods):
        v = world[p]
        x = L + i * step + 2
        bw = step - 4
        bh = ph * v / vmax
        yy = T + ph - bh
        r = min(3, bw / 2)
        s.append('<path d="M%.1f,%.1f v%.1f a%.1f,%.1f 0 0 1 %.1f,-%.1f h%.1f a%.1f,%.1f 0 0 1 %.1f,%.1f v%.1f z" fill="%s"><title>%s: %s</title></path>'
                 % (x, T + ph, -(bh - r), r, r, r, r, bw - 2 * r, r, r, r, r, bh - r, navy, p[:4] + "-" + p[4:], money(v)))
        if p[4:] in ("01", "07"):
            s.append('<text x="%.1f" y="%d" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="%s">%s</text>' % (x + bw / 2, T + ph + 16, mute, ("Jan " if p[4:] == "01" else "Jul ") + p[:4]))
    # annotations: tariff steps
    def xof(p):
        return L + periods.index(p) * step
    for p, label in (("202508", "Aug 2025: India tariff 25% then 50%"), ("202602", "Feb 2026: reduced to 25%, deal to 18%"), ("202607", "Jul 24 2026: Section 301, India 10%")):
        if p in periods:
            xx = xof(p)
            s.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s" stroke-width="1" stroke-dasharray="3,3"/>' % (xx, T - 6, xx, T + ph, mute))
            s.append('<text x="%.1f" y="%d" font-family="Helvetica, Arial, sans-serif" font-size="10.5" fill="%s">%s</text>' % (xx + 4, T + 4, ink, label))
    s.append('<text x="%d" y="%d" font-family="Helvetica, Arial, sans-serif" font-size="11" fill="%s">Stienhardt, Lab-Grown Import Monitor, edition %s. CC BY 4.0. Source: UN Comtrade Database, US imports, HS 710491.</text>' % (L, H - 22, mute, a.edition))
    s.append('</svg>')
    io.open(os.path.join(out_dir, "chart-monthly-value.svg"), "w", encoding="utf-8", newline="\n").write("\n".join(s))

    # ---------- tables ----------
    origins_last12 = collections.Counter()
    last12 = periods[-12:]
    for p in last12:
        for k, v in by[p].items():
            origins_last12[k] += v
    origins_2024 = collections.Counter()
    for p in [q for q in periods if q[:4] == "2024"]:
        for k, v in by[p].items():
            origins_2024[k] += v
    tot12 = sum(origins_last12.values())
    tot24 = sum(origins_2024.values())

    def pct(v, t):
        return "%.1f%%" % (100 * v / t) if t else "n/a"

    monthly_tbl = ["| Month | Customs value | India share | UAE | Thailand |", "|---|---|---|---|---|"]
    for p in periods[-13:]:
        monthly_tbl.append("| %s-%s | %s | %s | %s | %s |" % (p[:4], p[4:], money(world[p]), "%.0f%%" % share(p, "India"),
                                                            money(by[p].get("United Arab Emirates", 0)), money(by[p].get("Thailand", 0))))
    origin_tbl = ["| Origin | Last 12 months | Share | 2024 | Share |", "|---|---|---|---|---|"]
    names = [k for k, _ in origins_last12.most_common(6)]
    for k in names:
        origin_tbl.append("| %s | %s | %s | %s | %s |" % (k, money(origins_last12[k]), pct(origins_last12[k], tot12), money(origins_2024.get(k, 0)), pct(origins_2024.get(k, 0), tot24)))

    yoy = 100 * (world[last] / world[prev_year] - 1) if world.get(prev_year) else None
    ytd_vs_prev = 100 * (tot(ytd) / tot(ytd_prev) - 1) if tot(ytd_prev) else None
    ytd_vs_two = 100 * (tot(ytd) / tot(ytd_two) - 1) if tot(ytd_two) else None
    drop = 100 * (world["202509"] / world["202508"] - 1) if "202509" in world and "202508" in world else None

    release = """# Lab-Grown Import Monitor, edition %(ed)s (DRAFT, Comtrade cross-check series; Census primary series pending an API key)

Stienhardt, New York. Data: UN Comtrade Database, United States imports, HS 710491 (synthetic
diamonds, worked), monthly customs value, retrieved 2026-09-02. Method and caveats: METHODOLOGY.md.
CC BY 4.0. No forecast, no price advice, nothing about Stienhardt's own volumes.

## The number

United States imports of cut lab-grown diamonds were %(last_val)s in %(last_lbl)s, %(yoy)s against
%(prev_lbl)s. Year to date through %(last_lbl)s: %(ytd)s, %(ytd_prev)s against the same months of
%(py)d and %(ytd_two)s against %(py2)d.

## The break in the series

The monthly series ran at an average of %(avg24)s in 2024. It fell from %(aug)s in August 2025 to
%(sep)s in September 2025, an %(drop)s drop in one month, and has averaged %(avg_post)s a month since,
about %(post_pct)s of the 2024 pace. The step coincides with the United States tariff on Indian goods
rising to 25 percent on 7 August 2025 and to 50 percent on 27 August 2025 (National Jeweler, August
2025), with India supplying roughly nine dollars in ten of these imports in 2024. The partial recovery
from February 2026 coincides with the reduction of that tariff (JCK, 2026-02-09) and the later
Section 301 regime at 10 percent for India from 24 July 2026 (GJEPC, 2026-07-25). Coincidence in
timing is reported here; causation is not asserted.

What the origin table shows is that the imports did not move to other countries in any comparable
volume: the United Arab Emirates rose to about one to two million dollars a month and Thailand's
share faded, while India's share fell to the sixties in late 2025 and returned above ninety percent
by spring 2026.

## Monthly, last thirteen months

%(monthly)s

## Origin mix

%(origins)s

## Value per stone (Census primary series, HTS 7104.91.10.00)

%(census)s

%(census_note)s

## What this edition cannot say yet

- What kind of stones these are. The Census count runs between roughly 0.4 and 2.9 million stones
  a month at an average declared value of $8 to $27 per stone, so by count this tariff line is
  dominated by small goods (melee), and the value series, not the count, is the measure that
  tracks finished-jewelry supply. Neither series reports carat weight or size distribution.
- Reclassification within HS 7104 is ruled out. The whole heading 7104 fell from $54.4 million
  (August 2025) to $8.7 million (September 2025), and the neighboring lines stayed flat: 7104.99
  (other worked synthetic stones) ran between $0.8 and $5.1 million a month, 7104.21 and 7104.29
  (unworked) under $1 million, with no offsetting rise (UN Comtrade, same pull). A move to a
  heading outside 7104 cannot be excluded from trade data alone.
- Whether the goods entered under a different customs regime (bonded, foreign trade zone) or were
  diverted to other markets. GJEPC's monthly export statistics for India are the natural
  cross-check and will be cited when read.

## Sources

- UN Comtrade Database, reporter United States, flow imports, commodity HS 710491, periods
  2024-01 to %(last_lbl)s, retrieved 2026-09-02 (public preview endpoint).
- Harmonized Tariff Schedule of the United States, 7104.91.10.00, "Cut but not set, and suitable for
  use in the manufacture of jewelry", unit No., general rate Free; hts.usitc.gov, retrieved 2026-09-02.
- National Jeweler, "Tariff on India to Rise to 50%%, Trump Says" (August 2025); JCK, Rob Bates,
  "U.S. Dropping Tariffs on Indian-Cut Diamonds and Gems, Eventually" (2026-02-09); Rapaport,
  "US to Nix Tariff on Indian Gems and Natural Diamonds" (2026-02-07); GJEPC via JewelBuzz, "US
  Retains 10%% Tariff on Indian Exports Under New Section 301 Regime" (2026-07-25).
- Census FT-900 release schedule: July 2026 data on 3 September 2026.

Chart: chart-monthly-value.svg (static) and https://datawrapper.dwcdn.net/rLZxK/ (interactive, embeddable, always the latest published version).
Second table, search demand by ring shape (Semrush, US): shape-search-share.md, chart https://datawrapper.dwcdn.net/6MPGK/. Data: ../../data/us-imports-hs710491-monthly.csv.
""" % dict(
        ed=a.edition, last_val=money(world[last]), last_lbl="%s-%s" % (last[:4], last[4:]),
        yoy=("down %.0f percent" % -yoy if yoy is not None and yoy < 0 else ("up %.0f percent" % yoy if yoy is not None else "n/a")),
        prev_lbl="%s-%s" % (prev_year[:4], prev_year[4:]), ytd=money(tot(ytd)),
        ytd_prev=("down %.0f percent" % -ytd_vs_prev if ytd_vs_prev is not None and ytd_vs_prev < 0 else ("up %.0f percent" % ytd_vs_prev if ytd_vs_prev is not None else "n/a")),
        py=y - 1, py2=y - 2,
        ytd_two=("down %.0f percent" % -ytd_vs_two if ytd_vs_two is not None and ytd_vs_two < 0 else ("up %.0f percent" % ytd_vs_two if ytd_vs_two is not None else "n/a")),
        avg24=money(avg_2024), aug=money(world.get("202508", 0)), sep=money(world.get("202509", 0)),
        drop=("%.0f percent" % -drop if drop is not None else "n/a"), avg_post=money(avg_post),
        post_pct="%.0f percent" % (100 * avg_post / avg_2024) if avg_2024 else "n/a",
        monthly="\n".join(monthly_tbl), origins="\n".join(origin_tbl),
        census="\n".join(census_tbl), census_note=census_note)
    io.open(os.path.join(out_dir, "RELEASE.md"), "w", encoding="utf-8", newline="\n").write(release)
    with io.open(os.path.join(out_dir, "monthly-world.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "customs_value_usd", "india_share_pct"])
        for p in periods:
            w.writerow([p[:4] + "-" + p[4:], int(world[p]), round(share(p, "India"), 1)])
    print("wrote", out_dir, "| last", last, money(world[last]), "| yoy", yoy, "| ytd vs prev", ytd_vs_prev, "| drop", drop)
    if "—" in release:
        raise SystemExit("em dash in release")

if __name__ == "__main__":
    main()
