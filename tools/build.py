"""Builds the Mythic Bike Works site from src/ into plain HTML files.

    python3 tools/build.py

No dependencies beyond the Python standard library. Pages live in src/pages/*.html,
each starting with a <!--meta {json} --> block. Shared pieces live in src/partials/.
Output files (index.html, service/index.html, ...) are committed and served as-is.
"""
import html
import json
import os
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT_DIR, "src")
SITE = "https://mythicbikeworks.com"
VERSION = "14"  # bump when assets/css/styles.css or assets/js/main.js change

SOUTH_COUNTY = ["Peace Dale", "Wakefield", "Kingston", "South Kingstown", "Narragansett", "North Kingstown",
                "Charlestown", "Exeter", "Richmond", "Westerly", "Jamestown", "Newport"]
MAIL_STATES = ["Rhode Island", "Massachusetts", "Connecticut", "New York", "New Jersey", "Pennsylvania",
               "New Hampshire", "Vermont", "Maine"]

# Everything the pages may load. Only this site, the form service, and (later) Cloudflare analytics.
CSP = ("default-src 'self'; "
       "script-src 'self' 'inline-speculation-rules' https://static.cloudflareinsights.com; "
       "style-src 'self'; img-src 'self' data:; font-src 'self'; "
       "connect-src 'self' https://api.web3forms.com https://cloudflareinsights.com; "
       "form-action https://api.web3forms.com; base-uri 'self'; object-src 'none'")

# Fetch every linked page of this site as soon as a page loads (they are small), and fully
# render the next page when a link is hovered or pressed. Chrome and Edge only; other
# browsers get a <link rel=prefetch> fallback from main.js.
SPECULATION = {
    "prefetch": [{"where": {"and": [
        {"href_matches": "/*"},
        {"not": {"selector_matches": "[target=_blank], [href*='/board/'], [href*='/hub/']"}}]},
        "eagerness": "eager"}],
    "prerender": [{"where": {"and": [
        {"href_matches": "/*"},
        {"not": {"selector_matches": "[target=_blank], [href*='/board/'], [href*='/hub/']"}}]},
        "eagerness": "moderate"}],
}

def req(inquiry, name):
    """Inline "Request" link that opens the form preset to one service."""
    q = name.replace(" ", "%20").replace("&amp;", "%26").replace(",", "%2C")
    return (f'<a class="row-link" href="{{{{R}}}}contact/?inquiry={inquiry}&amp;service={q}" '
            f'data-inquiry="{inquiry}" data-service="{name}">Request<span class="sr"> {name}</span></a>')


def row(name, price, text, inquiry):
    return (f'            <li class="menu-row">\n'
            f'              <div class="menu-name"><h3>{name}</h3><p class="price">{price}</p></div>\n'
            f'              <p>{text} {req(inquiry, re.sub(r"<[^>]+>.*", "", name).strip())}</p>\n'
            f'            </li>')


SUSP_PRICES = "\n".join([
    '          <ul class="menu menu-tight">',
    row('Basic service <span class="interval">every 50 hr</span>', '$50 <small>per fork or shock</small>',
        "Fork lower seals and oil, or rear shock air can seals and oil.", "suspension"),
    row('Full overhaul <span class="interval">every 200 hr</span>', '$140 <small>each</small>',
        "Lower, damper and air spring seals, damper fluid, shock eye bushings. Knobs and dials as needed.", "suspension"),
    row("Linkage bearings", '<span class="price-q">Quoted</span>',
        "Pivot bearings inspected and replaced, hardware torqued to spec.", "suspension"),
    "          </ul>",
    '          <p class="fine">Labor only, parts extra. Same rates for drop-off and mail-in. We confirm the quote before work starts.</p>'])

STEPS = """          <ol class="steps steps-tight">
            <li><h3>Message us</h3><p>Model and what it's doing. Choose <strong>Shipping it in</strong>.</p></li>
            <li><h3>Get a quote</h3><p>We reply with the price and packing instructions.</p></li>
            <li><h3>Ship it</h3><p>Just the fork or shock, to Peace Dale, RI.</p></li>
            <li><h3>Ride it</h3><p>Serviced in-house and shipped home.</p></li>
          </ol>"""


def read(*parts):
    with open(os.path.join(SRC, *parts), encoding="utf-8") as f:
        return f.read()


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def jsonld(meta, url):
    if meta.get("jsonld") == "business":
        return json.loads(read("data", "business.json"))
    graph = [{"@type": "BikeStore", "@id": SITE + "/#shop", "name": "Mythic Bike Works", "url": SITE + "/",
              "telephone": "+1-401-218-0029",
              "address": {"@type": "PostalAddress", "streetAddress": "1207 Kingstown Rd", "addressLocality": "Peace Dale",
                          "addressRegion": "RI", "postalCode": "02879", "addressCountry": "US"}}]
    svc = meta.get("service")
    if svc:
        area = ([{"@type": "State", "name": s} for s in MAIL_STATES] + [{"@type": "Country", "name": "United States"}]
                if meta.get("area") == "mail" else [{"@type": "City", "name": c} for c in SOUTH_COUNTY])
        node = {"@type": "Service", "name": svc["name"], "serviceType": svc["serviceType"],
                "provider": {"@id": SITE + "/#shop"}, "url": url, "areaServed": area,
                "offers": [{"@type": "Offer", "name": n, "price": p, "priceCurrency": "USD"} for n, p in svc.get("offers", [])]}
        if svc.get("brand"):
            node["brand"] = {"@type": "Brand", "name": svc["brand"]}
        graph.append(node)
    if meta.get("crumb"):
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": meta["crumb"], "item": url}]})
    return {"@context": "https://schema.org", "@graph": graph}


def head(meta, url, r):
    t = html.escape(meta["title"], quote=True)
    d = html.escape(meta["description"], quote=True)
    ogt = html.escape(meta.get("og_title", meta["title"]), quote=True)
    preload = ""
    if meta.get("hero_preload"):
        preload = f"""
  <link rel="preload" as="image" imagesrcset="{r}assets/img/hero-portrait-700.webp 700w, {r}assets/img/hero-portrait-1100.webp 1100w" imagesizes="100vw" media="(max-width: 640px)" fetchpriority="high">
  <link rel="preload" as="image" imagesrcset="{r}assets/img/hero-1200.webp 1200w, {r}assets/img/hero-1600.webp 1600w, {r}assets/img/hero-2400.webp 2400w" imagesizes="(max-width: 900px) 100vw, 60vw" media="(min-width: 641px)" fetchpriority="high">"""
    if meta.get("hero"):
        h = meta["hero"]["img"]
        preload = f"""
  <link rel="preload" as="image" imagesrcset="{r}assets/img/{h}-hero-800.webp 800w, {r}assets/img/{h}-hero-1600.webp 1600w" imagesizes="(max-width: 900px) 100vw, 520px" fetchpriority="high">"""
    ld = json.dumps(jsonld(meta, url), indent=2, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta http-equiv="Content-Security-Policy" content="{CSP}">
  <title>{t}</title>
  <meta name="description" content="{d}">
  <meta name="theme-color" content="#ffffff">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{ogt}">
  <meta property="og:description" content="{d}">
  <meta property="og:image" content="{SITE}/assets/img/og.jpg">
  <meta property="og:url" content="{url}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{r}favicon.ico" sizes="any">
  <link rel="apple-touch-icon" href="{r}apple-touch-icon.png">
  <link rel="preload" href="{r}assets/fonts/archivo-latin.woff2" as="font" type="font/woff2" crossorigin>{preload}
  <link rel="stylesheet" href="{r}assets/css/styles.css?v={VERSION}">
  <script type="speculationrules">{json.dumps(SPECULATION)}</script>
  <script type="application/ld+json">
{ld}
  </script>
</head>
<body>
"""


def build_page(filename):
    raw = read("pages", filename)
    m = re.match(r"<!--meta\s*(\{.*?\})\s*-->\s*", raw, re.S)
    meta = json.loads(m.group(1))
    body = raw[m.end():]
    out = meta["out"]
    if meta.get("hero"):
        h, alt = meta["hero"]["img"], html.escape(meta["hero"]["alt"], quote=True)
        body = body.replace("{{HERO_IMG}}", (
            f'<img class="panel-img" src="{{{{R}}}}assets/img/{h}-hero-800.webp" '
            f'srcset="{{{{R}}}}assets/img/{h}-hero-800.webp 800w, {{{{R}}}}assets/img/{h}-hero-1600.webp 1600w" '
            f'sizes="(max-width: 900px) 100vw, 520px" alt="{alt}" width="1600" height="992" fetchpriority="high">'))
    depth = out.count("/")
    r = "../" * depth
    url = SITE + "/" + (out[:-len("index.html")] if out.endswith("index.html") else out)

    form = read("partials", "form.html")
    parts = [head(meta, url, r), read("partials", "header.html"), '  <main id="main">\n', body]
    parts.append("  </main>\n\n")
    parts.append(read("partials", "footer.html"))
    if not meta.get("inline_form"):
        parts.append("\n" + read("partials", "drawer.html"))
    parts.append(f'\n  <script src="{r}assets/js/main.js?v={VERSION}" defer></script>\n</body>\n</html>\n')
    page = "".join(parts)

    page = (page.replace("{{FORM}}", form).replace("{{HOURS}}", read("partials", "hours.html"))
                .replace("{{SUSP_PRICES}}", SUSP_PRICES).replace("{{STEPS}}", STEPS))
    for key in ("service", "suspension", "canecreek", "wheels"):
        page = page.replace("{{CUR_%s}}" % key, ' aria-current="page"' if meta.get("nav") == key else "")
    page = page.replace("{{HEADER_CLASS}}", "").replace("{{R}}", r)
    leftover = re.findall(r"\{\{[A-Z_a-z]+\}\}", page)
    if leftover:
        raise SystemExit(f"{filename}: unfilled placeholders {sorted(set(leftover))}")

    path = os.path.join(ROOT_DIR, out)
    os.makedirs(os.path.dirname(path) or ROOT_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)
    return out


def bump_static_pages():
    for name in ("thanks.html", "404.html"):
        p = os.path.join(ROOT_DIR, name)
        s = open(p, encoding="utf-8").read()
        s = re.sub(r"styles\.css\?v=\d+", f"styles.css?v={VERSION}", s)
        open(p, "w", encoding="utf-8").write(s)


def sitemap(outs):
    urls = "\n".join(
        f"  <url><loc>{SITE}/{o[:-len('index.html')] if o.endswith('index.html') else o}</loc></url>" for o in outs)
    with open(os.path.join(ROOT_DIR, "sitemap.xml"), "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n')


if __name__ == "__main__":
    order = ["home.html", "service.html", "suspension.html", "cane-creek.html", "wheels.html", "contact.html"]
    outs = [build_page(p) for p in order]
    bump_static_pages()
    sitemap(outs)
    for o in outs:
        print("built", o)
