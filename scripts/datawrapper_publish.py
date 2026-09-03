"""Create and publish the monthly-value chart on Datawrapper from an edition's CSV, then print the
public URL and the embed code. Reads DATAWRAPPER_TOKEN from the environment or ../.env.

Usage: python scripts/datawrapper_publish.py --edition 2026-09-04 [--chart-id <id to update>]
"""
import argparse, csv, io, json, os, sys, urllib.request, urllib.error

API = "https://api.datawrapper.de/v3"

def token():
    t = os.environ.get("DATAWRAPPER_TOKEN")
    if not t:
        env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env):
            for line in io.open(env, encoding="utf-8"):
                if line.startswith("DATAWRAPPER_TOKEN="):
                    t = line.split("=", 1)[1].strip().strip('"')
    if not t:
        raise SystemExit("DATAWRAPPER_TOKEN missing (put it in the .env next to this folder)")
    return t

def req(method, path, body=None, tok=None, ctype="application/json", raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    r = urllib.request.Request(API + path, data=data, method=method,
                               headers={"Authorization": "Bearer " + tok, "Content-Type": ctype})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            txt = resp.read().decode()
            return resp.status, (json.loads(txt) if txt.strip().startswith(("{", "[")) else txt)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", required=True)
    ap.add_argument("--chart-id")
    a = ap.parse_args()
    tok = token()
    csv_path = os.path.join("releases", a.edition, "monthly-world.csv")
    rows = list(csv.DictReader(io.open(csv_path, encoding="utf-8")))
    data = "Month,Customs value (USD millions)\n" + "\n".join(
        "%s,%.1f" % (r["month"], int(r["customs_value_usd"]) / 1e6) for r in rows)
    meta = {
        "title": "US imports of cut lab-grown diamonds, by month",
        "type": "column-chart",
        "metadata": {
            "describe": {
                "intro": "Customs value of US imports under HS 710491 (synthetic diamonds, worked), in millions of US dollars. The step down in September 2025 coincides with the US tariff on Indian goods rising to 50 percent; causation is not asserted.",
                "source-name": "UN Comtrade Database; US Census Bureau (HTS 7104.91.10.00)",
                "source-url": "https://github.com/JacobiusMakes/lgd-import-monitor",
                "byline": "Stienhardt, Lab-Grown Import Monitor, edition %s" % a.edition,
                "number-prepend": "$", "number-append": "M",
            },
            "visualize": {"base-color": "#2F57B0", "thick": False, "value-label-format": "0.0",
                          "grid": "y", "rotate-labels": False, "number-prepend": "$", "number-append": "M"},
            "publish": {"embed-width": 700, "embed-height": 420},
        },
    }
    if a.chart_id:
        cid = a.chart_id
        st, r = req("PATCH", "/charts/" + cid, meta, tok)
    else:
        st, r = req("POST", "/charts", meta, tok)
        if st not in (200, 201):
            raise SystemExit("create failed %s %s" % (st, r))
        cid = r["id"]
    st, r = req("PUT", "/charts/%s/data" % cid, tok=tok, ctype="text/csv", raw=data.encode())
    if st not in (200, 201, 204):
        raise SystemExit("data upload failed %s %s" % (st, r))
    st, r = req("POST", "/charts/%s/publish" % cid, {}, tok)
    if st not in (200, 201):
        raise SystemExit("publish failed %s %s" % (st, r))
    url = (r.get("data") or r).get("publicUrl") if isinstance(r, dict) else None
    st, info = req("GET", "/charts/" + cid, tok=tok)
    pub = (info.get("publicUrl") if isinstance(info, dict) else None) or url
    print("chart id:", cid)
    print("public url:", pub)
    print("embed:", '<iframe title="US imports of cut lab-grown diamonds" src="%s" width="700" height="420" style="border:0" loading="lazy"></iframe>' % pub)
    print("River: open the chart in app.datawrapper.de, Publish, then 'Publish to River' (attribution link freezes to the edition page).")

if __name__ == "__main__":
    main()
