# Travelicious Restaurant — Wayanad Travel Itinerary

Single-page site. No build step, no dependencies. Open `index.html` or upload the whole
folder to any host (Netlify drop, Vercel, Hostinger, cPanel `public_html`).

```
index.html             the site
fetch-photos.py        one-time photo downloader (see below)
assets/
  tr-logo.png          supplied logo, white artwork on transparent
  images/              destination photos land here
```

## Photographs

Each card is a **slideshow** and resolves its pictures in this order:

1. **Local files** in `assets/images/` — fastest, free, nothing to configure.
2. **Photos on the Google Maps listing** — needs an API key.
3. **The brass contour panel** — so a card with no photo still looks finished.

A card with a single photo shows it plain. A card with two or more gets a fading
slideshow with prev/next arrows, dot indicators and auto-advance (which pauses on
hover and honours *reduce motion*).

**Adding more slides to a card:** the base file (e.g. `edakkal-caves.jpg`) is slide
one; drop numbered siblings next to it — `edakkal-caves-2.jpg`, `edakkal-caves-3.jpg`,
… — and they become the following slides automatically, no code change. (Numbering
must be contiguous; the site stops at the first gap.) With a Google key set instead,
each card pulls several listing photos, each with its own credit. Tune `maxPhotos`
and the `slideMs` auto-advance interval in the `CONFIG` block near the top of the
script in `index.html`.

### Option A — download them once, then host them yourself *(recommended)*

`fetch-photos.py` pulls one picture per destination into `assets/images/` and writes
`assets/images/credits.json` with the photographer and licence. Run it once; after
that the site serves local files, needs no key, loads faster and costs nothing per
visitor.

```bash
# free, no key, no billing — Wikimedia Commons only
python3 fetch-photos.py --source commons

# Commons where it exists, Google Maps for the gaps
python3 fetch-photos.py --source auto --key AIza...

# Google Maps for all 21
python3 fetch-photos.py --source google --key AIza...
```

**Wikimedia Commons** is free and licensed for commercial reuse. The script keeps
only files under CC0 / public domain / CC BY / CC BY-SA and rejects anything marked
non-commercial or no-derivatives, so what lands in `assets/images/` is safe to
publish. Expect good coverage for Edakkal, Chembra, Banasura, Pookode, Soochipara,
Kuruva and the Jain temple, and gaps on the small local spots — Manjapara,
Nellarachal, Cheengeri, 900 Kandi. Those are worth shooting yourself anyway.

**Google Maps** covers all 21 but the pictures are visitor snapshots of uneven
quality. Getting a key: Google Cloud console → enable **Places API (New)** → create
a key → restrict it to your domain. Billing must be on; 21 lookups sits deep inside
the free monthly allowance.

Flags: `--width 1600` (largest edge), `--force` (re-download files you already have).

Anything already in `assets/images/` is left alone, so your own photography always
wins.

### Option B — live from Google on every page load

Paste the key into the `CONFIG` block near the bottom of `index.html`:

```js
const CONFIG = {
  googleApiKey : "AIza…",
  photoWidth   : 1280,
  cacheDays    : 30
};
```

Photos are fetched only when a card scrolls into view, and each lookup is cached in
the visitor's browser for 30 days. Restrict the key by HTTP referrer before going
live, since a browser key is public. Option A is cheaper and faster — use this one
only if you want the pictures to track the listings automatically.

### Option C — your own photography

Drop a JPG with the matching name into `assets/images/`. It takes priority over
everything else. **1600 × 1000 px**, landscape, under 300 KB each.

### About attribution

Neither source is a free-for-all — both require the photographer to be named, which
is exactly why grabbing pictures off a web image search is a bad idea for a business
site. The credit sits in the bottom-right corner of each photo and is generated
automatically from `credits.json`:

| Source | Credit shown |
|---|---|
| Wikimedia Commons | `Photo · Rameshng · CC BY-SA 3.0` (both parts linked) |
| Google Maps | `Photo · <contributor> / Google Maps` |
| Your own photography | nothing — no credit line is drawn |

Leave those credits in place. Removing them breaks the licence you're relying on.

| File name | Destination |
|---|---|
| `edakkal-caves.jpg` | Edakkal Caves |
| `heritage-museum.jpg` | Ambalavayal Heritage Museum |
| `phantom-rock.jpg` | Phantom Rock |
| `manjapara-viewpoint.jpg` | Manjapara View Point |
| `cheengeri-hill.jpg` | Cheengeri Hill |
| `karapuzha-dam.jpg` | Karapuzha Dam & Adventure Park |
| `nellarachal-viewpoint.jpg` | Nellarachal Viewpoint |
| `jain-temple.jpg` | Jain Temple, Sulthan Bathery |
| `sulthan-bathery.jpg` | Sulthan Bathery Town |
| `muthanga-sanctuary.jpg` | Wayanad / Muthanga Wildlife Sanctuary |
| `kanthanpara-falls.jpg` | Kanthanpara Waterfalls |
| `chembra-peak.jpg` | Chembra Peak |
| `soochipara-falls.jpg` | Soochipara Waterfalls |
| `900-kandi-glass-bridge.jpg` | 900 Kandi Glass Bridge |
| `karlad-lake.jpg` | Karlad Lake Adventure Camp |
| `pookode-lake.jpg` | Pookode Lake |
| `lakkidi-viewpoint.jpg` | Lakkidi Viewpoint |
| `kuruva-island.jpg` | Kuruva Island |
| `banasura-sagar-dam.jpg` | Banasura Sagar Dam |
| `banasura-meenmutty-falls.jpg` | Banasura Meenmutty Falls |
| `banasura-trekking-point.jpg` | Banasura Trekking Point |

Use licensed or own-shot photography. Kerala Tourism releases press images on request,
and Wikimedia Commons has usable frames for Edakkal, Chembra, Banasura and Pookode.

## Editing content

Everything lives in the `PLACES` array near the bottom of `index.html`:

```js
{ name:"Edakkal Caves", km:1.8, kind:"Rock art · Trek",
  img:"assets/images/edakkal-caves.jpg",
  note:"…one or two sentences…",
  lat:11.6268407, lng:76.2342690, pid:"ChIJ43AF…" }
```

`km` drives the distance plaque, the three distance bands and the radius filter.
`lat`/`lng` drive the embedded map. `pid` is the Google Place ID — it makes the
"Google Maps" link open the real business listing rather than a text search.

Restaurant address, hours, phone and Instagram are plain HTML in the `#house`
section and the footer. The phone number appears three times (masthead button,
plaque, footer) and `@traveliciousrestaurant` five times (masthead icon, plaque row,
"Follow on Instagram" button, footer contact list, footer handle). Search and replace
if either ever changes.

## Notes

- The embedded map uses the keyless `output=embed` endpoint — no API key needed for
  the map itself. A key is only involved if you want photographs from Google.
- "Directions" links are pre-set to start from the restaurant, so a guest gets a route
  from their table.
- Distances are the ones supplied on the printed itinerary. Coordinates and place IDs
  were pulled from Google Places; restaurant hours were current as of July 2026.
- Responsive to 360 px, keyboard focus visible, `prefers-reduced-motion` respected.
