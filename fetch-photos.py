#!/usr/bin/env python3
"""
Fetch one photograph for each destination and save it into assets/images/,
then write assets/images/credits.json so the site can print the attribution
each licence requires.

Two sources, both legal to use on a commercial site:

  --source commons   Wikimedia Commons. Free, no key, no billing. Only files
                     under a licence that permits commercial reuse are kept,
                     and the photographer + licence are recorded for the credit
                     line. Coverage is excellent for the famous spots and thin
                     for the small local ones.

  --source google    The first photo on each Google Maps listing. Needs a key
                     with "Places API (New)" enabled. Covers all 21, but the
                     pictures are visitor snapshots of uneven quality.

  --source auto      Try Commons first, fall back to Google for anything it
                     misses. Needs a key. This is usually what you want.

Examples
    python3 fetch-photos.py --source commons
    python3 fetch-photos.py --source auto --key AIza...
    python3 fetch-photos.py --source google --key AIza... --force

Anything already sitting in assets/images/ is left alone unless you pass --force,
so your own photography always wins.
"""

import argparse, html, json, os, re, sys, time
import urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "index.html")
IMGDIR = os.path.join(HERE, "assets", "images")

GOOGLE = "https://places.googleapis.com/v1"
COMMONS = "https://commons.wikimedia.org/w/api.php"
UA = "TraveliciousSiteBuilder/1.0 (restaurant website; contact: the site owner)"

# Licences that allow commercial reuse. Anything else is skipped.
OK_LICENCE = re.compile(
    r"(^cc0|public domain|^pd|cc[- ]by([- ]sa)?([- ]\d)?|attribution)", re.I
)
NO_LICENCE = re.compile(r"(non[- ]?commercial|nc\b|fair use|no derivat|\bnd\b)", re.I)

# Search terms per destination, keyed by the image filename. Commons responds
# far better to the plain landmark name than to the label used on the site.
COMMONS_TERMS = {
    "edakkal-caves.jpg":            ["Edakkal Caves", "Edakkal"],
    "heritage-museum.jpg":          ["Ambalavayal Heritage Museum", "Wayanad Heritage Museum"],
    "phantom-rock.jpg":             ["Phantom Rock Wayanad", "Cheengeri Phantom rock"],
    "manjapara-viewpoint.jpg":      ["Manjapara Wayanad", "Ambalavayal Wayanad landscape"],
    "cheengeri-hill.jpg":           ["Cheengeri hill", "Cheengeri Mala"],
    "karapuzha-dam.jpg":            ["Karapuzha Dam", "Karapuzha"],
    "nellarachal-viewpoint.jpg":    ["Nellarachal", "Muttil Wayanad"],
    "jain-temple.jpg":              ["Jain temple Sultan Bathery", "Sultan Bathery Jain temple"],
    "sulthan-bathery.jpg":          ["Sultan Bathery", "Sulthan Bathery town"],
    "muthanga-sanctuary.jpg":       ["Muthanga Wildlife Sanctuary", "Wayanad Wildlife Sanctuary"],
    "kanthanpara-falls.jpg":        ["Kanthanpara waterfalls", "Kanthanpara"],
    "chembra-peak.jpg":             ["Chembra Peak", "Chembra"],
    "soochipara-falls.jpg":         ["Soochipara falls", "Sentinel Rock Waterfalls"],
    "900-kandi-glass-bridge.jpg":   ["900 Kandi Wayanad", "Meppadi Wayanad"],
    "karlad-lake.jpg":              ["Karlad lake", "Karlad Wayanad"],
    "pookode-lake.jpg":             ["Pookode Lake", "Pookot lake"],
    "lakkidi-viewpoint.jpg":        ["Lakkidi Wayanad", "Thamarassery churam"],
    "kuruva-island.jpg":            ["Kuruva Island", "Kuruvadweep"],
    "banasura-sagar-dam.jpg":       ["Banasura Sagar Dam", "Banasurasagar"],
    "banasura-meenmutty-falls.jpg": ["Meenmutty Falls Wayanad", "Banasura Meenmutty"],
    "banasura-trekking-point.jpg":  ["Banasura hills", "Banasura peak"],
}


# ------------------------------------------------------------------ helpers
def destinations():
    """Read the PLACES array out of index.html so there's one source of truth."""
    src = open(PAGE, encoding="utf-8").read()
    block = src.split("const PLACES = [", 1)[1].split("\n];", 1)[0]
    out = []
    for chunk in block.split("{ name:")[1:]:
        n = re.search(r'^"([^"]+)"', chunk)
        i = re.search(r'img:"([^"]+)"', chunk)
        p = re.search(r'pid:"([^"]+)"', chunk)
        if n and i and p:
            out.append({"name": n.group(1), "img": i.group(1), "pid": p.group(1)})
    return out


def get(url, headers=None, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(s).strip()


# ------------------------------------------------------------------ commons
def from_commons(filename, width):
    """Return (bytes, credit) for the best freely-licensed Commons match."""
    for term in COMMONS_TERMS.get(filename, []):
        q = urllib.parse.urlencode({
            "action": "query", "format": "json", "formatversion": "2",
            "generator": "search", "gsrsearch": f"filetype:bitmap {term}",
            "gsrnamespace": "6", "gsrlimit": "12",
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": str(width),
        })
        try:
            data = json.loads(get(f"{COMMONS}?{q}"))
        except Exception:
            continue

        pages = (data.get("query") or {}).get("pages") or []
        best = None
        for pg in pages:
            info = (pg.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata") or {}
            lic = strip_html((meta.get("LicenseShortName") or {}).get("value", ""))
            if not lic or NO_LICENCE.search(lic) or not OK_LICENCE.search(lic):
                continue
            if (info.get("width") or 0) < 900:
                continue
            score = min(info.get("width", 0), 4000)
            if not best or score > best["score"]:
                best = {
                    "score": score,
                    "url": info.get("thumburl") or info.get("url"),
                    "by": strip_html((meta.get("Artist") or {}).get("value", "")) or "Unknown",
                    "uri": pg_url(pg.get("title", "")),
                    "license": lic,
                    "licenseUri": strip_html((meta.get("LicenseUrl") or {}).get("value", "")),
                    "source": "Wikimedia Commons",
                }
        if best and best["url"]:
            try:
                blob = get(best["url"], timeout=90)
                best.pop("score")
                return blob, best
            except Exception:
                pass
        time.sleep(0.3)
    return None, None


def pg_url(title):
    return "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))


# ------------------------------------------------------------------ google
def from_google(pid, width, key):
    url = f"{GOOGLE}/places/{pid}?fields=photos"
    data = json.loads(get(url, {"X-Goog-Api-Key": key}))
    photos = data.get("photos") or []
    if not photos:
        return None, None
    ref = photos[0]["name"]
    attr = (photos[0].get("authorAttributions") or [{}])[0]
    blob = get(f"{GOOGLE}/{ref}/media?maxWidthPx={width}", {"X-Goog-Api-Key": key}, timeout=90)
    return blob, {
        "by": attr.get("displayName", "Google Maps contributor"),
        "uri": attr.get("uri", ""),
        "license": "",
        "licenseUri": "",
        "source": "Google Maps",
    }


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["commons", "google", "auto"], default="commons")
    ap.add_argument("--key", default=os.environ.get("GOOGLE_API_KEY", ""),
                    help="Google Maps Platform key (or set GOOGLE_API_KEY)")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if a.source in ("google", "auto") and not a.key:
        sys.exit("A Google key is required for --source google/auto. "
                 "Use --source commons for the key-free run.")

    places = destinations()
    if not places:
        sys.exit("Could not read the PLACES array from index.html.")

    os.makedirs(IMGDIR, exist_ok=True)
    cpath = os.path.join(IMGDIR, "credits.json")
    credits = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}

    got = kept = missed = 0
    print(f"{len(places)} destinations · source: {a.source}\n")

    for p in places:
        dest = os.path.join(HERE, p["img"])
        fname = os.path.basename(p["img"])

        if os.path.exists(dest) and not a.force:
            print(f"  ·  {p['name']:<34} already have it")
            kept += 1
            continue

        blob = credit = None
        try:
            if a.source in ("commons", "auto"):
                blob, credit = from_commons(fname, a.width)
            if blob is None and a.source in ("google", "auto"):
                blob, credit = from_google(p["pid"], a.width, a.key)
        except urllib.error.HTTPError as e:
            print(f"  ✕  {p['name']:<34} HTTP {e.code}")
            missed += 1
            continue
        except Exception as e:
            print(f"  ✕  {p['name']:<34} {e}")
            missed += 1
            continue

        if not blob:
            print(f"  ✕  {p['name']:<34} nothing freely licensed found")
            missed += 1
            continue

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(blob)
        credits[p["pid"]] = {**credit, "place": p["name"]}
        lic = f" · {credit['license']}" if credit["license"] else ""
        print(f"  ✓  {p['name']:<34} {len(blob)//1024:>5} KB  {credit['by'][:26]}{lic}")
        got += 1
        time.sleep(0.25)

    json.dump(credits, open(cpath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"\nDownloaded {got} · already had {kept} · missing {missed}")
    print(f"Attribution written to {os.path.relpath(cpath, HERE)}")
    if missed:
        print("\nFor the gaps: shoot them yourself, or re-run with --source auto --key ...")
    if got:
        print("\nOptimise before publishing, e.g.")
        print("  mogrify -resize 1600x -quality 78 assets/images/*.jpg")


if __name__ == "__main__":
    main()
