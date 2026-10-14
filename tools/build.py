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
VERSION = "12"  # bump when assets/css/styles.css or assets/js/main.js change

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

SUSP_PRICES = """          <ul class="menu">
            <li class="menu-row">
              <div class="menu-name"><h3>Basic service <span class="interval">50 hr</span></h3><p class="price">$50 <small>per fork or shock</small></p></div>
              <ul class="items"><li>Fork lower seals and oil replaced</li><li>Rear shock air can seals and oil replaced</li></ul>
              <a class="row-link" href="{{R}}contact/?inquiry=suspension&amp;service=Basic%20service" data-inquiry="suspension" data-service="Basic service">Request<span class="sr"> basic service</span></a>
            </li>
            <li class="menu-row">
              <div class="menu-name"><h3>Full overhaul <span class="interval">200 hr</span></h3><p class="price">$140 <small>each</small></p></div>
              <ul class="items"><li>Lower, damper and air spring seals replaced</li><li>Damper fluid replaced</li><li>Shock eye bushings replaced</li><li>Knobs, levers and dials replaced as needed</li></ul>
              <a class="row-link" href="{{R}}contact/?inquiry=suspension&amp;service=Full%20overhaul" data-inquiry="suspension" data-service="Full overhaul">Request<span class="sr"> full overhaul</span></a>
            </li>
            <li class="menu-row">
              <div class="menu-name"><h3>Linkage bearings</h3><p class="price price-q">Quoted</p></div>
              <ul class="items"><li>Pivot bearings inspected and replaced</li><li>Pivot hardware torqued to spec</li></ul>
              <a class="row-link" href="{{R}}contact/?inquiry=suspension&amp;service=Linkage%20bearings" data-inquiry="suspension" data-service="Linkage bearings">Request<span class="sr"> linkage bearings</span></a>
            </li>
          </ul>
          <p class="fine">Prices are labor. Parts extra. We confirm the quote before any work starts.</p>"""

STEPS = """          <ol class="steps">
            <li><h3>Send us a message</h3><p>Tell us the fork or shock model and what it's doing. Choose <strong>Shipping it in</strong> on the form.</p></li>
            <li><h3>Get a quote and instructions</h3><p>We reply with the price and how to pack and ship it.</p></li>
            <li><h3>Ship it to Peace Dale, RI</h3><p>Send just the fork or shock unless we ask for more.</p></li>
            <li><h3>Serviced and shipped back</h3><p>We do the work in-house and send it home, ready to bolt on.</p></li>
          </ol>"""

CTA = """    <section class="cta-band">
      <div class="wrap cta-inner">
        <div>
          <h2>Ready when you are.</h2>
          <p>Send a message or call <a href="tel:+14012180029">401-218-0029</a>. Open Mon, Thu–Sat at 1207 Kingstown Rd, Peace Dale, RI.</p>
        </div>
        <a class="btn btn-dark btn-lg" href="{{R}}contact/" data-open-contact>Send a message</a>
      </div>
    </section>"""


def read(*parts):
    with open(os.path.join(SRC, *parts), encoding="utf-8") as f:
        return f.read()


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def faq_html(faqs):
    items = "\n".join(
        f'          <details class="faq-item">\n            <summary>{html.escape(q)}</summary>\n            <p>{a}</p>\n          </details>'
        for q, a in faqs)
    return f"""    <section class="section" aria-labelledby="faq-title">
      <div class="wrap two-col">
        <div class="col-intro">
          <p class="kicker">Questions</p>
          <h2 id="faq-title">Common questions</h2>
        </div>
        <div class="faq">
{items}
        </div>
      </div>
    </section>"""


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
    if meta.get("faqs"):
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a).replace("{{R}}", "")}}
            for q, a in meta["faqs"]]})
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
  <link rel="preload" as="image" imagesrcset="{r}assets/img/{h}-hero-800.webp 800w, {r}assets/img/{h}-hero-1600.webp 1600w" imagesizes="(max-width: 1200px) 100vw, 1200px" fetchpriority="high">"""
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
        img = (f'      <div class="wrap hero-media"><img class="page-hero-img" src="{{{{R}}}}assets/img/{h}-hero-1600.webp" '
               f'srcset="{{{{R}}}}assets/img/{h}-hero-800.webp 800w, {{{{R}}}}assets/img/{h}-hero-1600.webp 1600w" '
               f'sizes="(max-width: 1200px) 100vw, 1200px" alt="{alt}" width="1600" height="992" fetchpriority="high"></div>\n')
        # Photo sits under the headline, inside the hero section.
        start = body.index('<section class="page-hero')
        end = body.index("    </section>", start)
        body = body[:start] + body[start:end].replace('<section class="page-hero', '<section class="page-hero has-img', 1) + img + body[end:]
    depth = out.count("/")
    r = "../" * depth
    url = SITE + "/" + (out[:-len("index.html")] if out.endswith("index.html") else out)

    form = read("partials", "form.html")
    parts = [head(meta, url, r), read("partials", "header.html"), '  <main id="main">\n', body]
    if meta.get("faqs"):
        parts.append(faq_html(meta["faqs"]) + "\n\n")
    if meta.get("crumb") and not meta.get("inline_form"):
        parts.append(CTA + "\n")
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
