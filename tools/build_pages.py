# Regenerates the landing pages (cane-creek-service-center/, suspension-service/)
# from the header and footer in index.html. Run: python3 tools/build_pages.py
import re, json, os, html
ROOT = os.path.expanduser("~/github/mythicbikeworks")
home = open(f"{ROOT}/index.html").read()

def grab(start, end):
    a = home.index(start); b = home.index(end, a) + len(end)
    return home[a:b]

sprite = grab('<svg width="0" height="0"', '</svg>')
header = grab('<header class="site-header"', '</header>')
footer = grab('<footer class="site-footer">', '</footer>')
quick = grab('<nav class="quickbar"', '</nav>')

def up(fragment):
    f = fragment
    f = f.replace('href="#top"', 'href="../"')
    f = re.sub(r'href="#([a-z]+)"', r'href="../#\1"', f)
    f = f.replace('href="cane-creek-service-center/"', 'href="../cane-creek-service-center/"')
    f = f.replace('href="suspension-service/"', 'href="../suspension-service/"')
    f = re.sub(r'(?<=[" ,])assets/', '../assets/', f)
    return f

SITE = "https://mythicbikeworks.com"
STATES = ["Rhode Island", "Massachusetts", "Connecticut", "New York", "New Jersey", "Pennsylvania", "New Hampshire", "Vermont", "Maine"]
BUSINESS = {"@type": "BikeStore", "@id": SITE + "/#shop", "name": "Mythic Bike Works", "url": SITE + "/",
            "telephone": "+1-401-218-0029",
            "address": {"@type": "PostalAddress", "streetAddress": "1207 Kingstown Rd", "addressLocality": "Peace Dale",
                        "addressRegion": "RI", "postalCode": "02879", "addressCountry": "US"}}

def page(slug, title, desc, crumb, body, service, faqs):
    url = f"{SITE}/{slug}/"
    t, d = html.escape(title, quote=True), html.escape(desc, quote=True)
    faq_ld = {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in faqs]}
    ld = {"@context": "https://schema.org", "@graph": [
        BUSINESS,
        dict(service, **{"@type": "Service", "provider": {"@id": SITE + "/#shop"}, "url": url,
                         "areaServed": [{"@type": "State", "name": s} for s in STATES] + [{"@type": "Country", "name": "United States"}]}),
        faq_ld,
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": crumb, "item": url}]}]}
    faq_html = "\n".join(
        f'          <details class="faq-item">\n            <summary>{html.escape(q)}</summary>\n            <p>{a}</p>\n          </details>' for q, a in faqs)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{t}</title>
  <meta name="description" content="{d}">
  <meta name="theme-color" content="#111311">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{t}">
  <meta property="og:description" content="{d}">
  <meta property="og:image" content="{SITE}/assets/img/og.jpg">
  <meta property="og:url" content="{url}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="../favicon.ico" sizes="any">
  <link rel="apple-touch-icon" href="../apple-touch-icon.png">
  <link rel="preload" href="../assets/fonts/archivo-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="../assets/css/styles.css?v=7">
  <script type="application/ld+json">
{json.dumps(ld, indent=2, ensure_ascii=False)}
  </script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>

  {sprite}

  {up(header)}

  <main id="main">
{body}

    <section class="section" aria-labelledby="faq-title">
      <div class="wrap two-col">
        <div class="col-intro">
          <p class="kicker">Questions</p>
          <h2 id="faq-title">Common questions</h2>
        </div>
        <div class="faq">
{faq_html}
        </div>
      </div>
    </section>

    <section class="cta-band">
      <div class="wrap cta-inner">
        <div>
          <h2>Ready when you are.</h2>
          <p>Send a message or call <a href="tel:+14012180029">401-218-0029</a>. Open Mon, Thu–Sat at 1207 Kingstown Rd, Peace Dale, RI.</p>
        </div>
        <a class="btn btn-accent btn-lg" href="../?inquiry=suspension&amp;dropoff=Shipping%20it%20in#contact">Start a request</a>
      </div>
    </section>
  </main>

  {up(footer)}

  {up(quick)}

  <script src="../assets/js/main.js?v=7" defer></script>
</body>
</html>
'''

def hero(kicker, h1, lede, primary, secondary=None):
    sec = f'\n          <a class="btn btn-outline-light btn-lg" href="{secondary[1]}">{secondary[0]}</a>' if secondary else ""
    return f'''    <section class="page-hero">
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a> <span>/</span> <span aria-current="page">{kicker}</span></nav>
        <h1>{h1}</h1>
        <p class="lede">{lede}</p>
        <div class="hero-actions">
          <a class="btn btn-accent btn-lg" href="{primary[1]}">{primary[0]}</a>{sec}
        </div>
      </div>
    </section>'''

PRICES = '''          <ul class="menu">
            <li class="menu-row">
              <div class="menu-name"><h3>Basic service <span class="interval">50 hr</span></h3><p class="price">$50 <small>per fork or shock</small></p></div>
              <ul class="items"><li>Fork lower seals and oil replaced</li><li>Rear shock air can seals and oil replaced</li></ul>
            </li>
            <li class="menu-row">
              <div class="menu-name"><h3>Full overhaul <span class="interval">200 hr</span></h3><p class="price">$140 <small>each</small></p></div>
              <ul class="items"><li>Lower, damper and air spring seals replaced</li><li>Damper fluid replaced</li><li>Shock eye bushings replaced</li><li>Knobs, levers and dials replaced as needed</li></ul>
            </li>
            <li class="menu-row">
              <div class="menu-name"><h3>Linkage bearings</h3><p class="price price-q">Quoted</p></div>
              <ul class="items"><li>Pivot bearings inspected and replaced</li><li>Pivot hardware torqued to spec</li></ul>
            </li>
          </ul>
          <p class="fine">Prices are labor. Parts extra. We confirm the quote before any work starts.</p>'''

STEPS = '''          <ol class="steps">
            <li><h3>Send us a message</h3><p>Tell us the fork or shock model and what it's doing. Choose <strong>Shipping it in</strong> on the form.</p></li>
            <li><h3>Get a quote and instructions</h3><p>We reply with the price and how to pack and ship it.</p></li>
            <li><h3>Ship it to Peace Dale, RI</h3><p>Send just the fork or shock unless we ask for more.</p></li>
            <li><h3>Serviced and shipped back</h3><p>We do the work in-house and send it home, ready to bolt on.</p></li>
          </ol>'''

MAILIN_LINK = "../?inquiry=suspension&amp;dropoff=Shipping%20it%20in#contact"
CC_SRC = "https://canecreek.com/suspension-service/"

# ---------------- Cane Creek page ----------------
cc_body = hero(
    "Cane Creek service center",
    "Cane Creek suspension service center",
    "The only Cane Creek suspension service center on the East Coast, and one of 9 Cane Creek VIP dealers in the U.S. Drop off in Peace Dale, RI, or ship your fork or shock to us from anywhere.",
    ("Start a Cane Creek service", MAILIN_LINK), ("Call 401-218-0029", "tel:+14012180029")) + f'''

    <section class="section">
      <div class="wrap two-col">
        <div class="col-intro">
          <p class="kicker">Why us</p>
          <h2>Factory-level Cane Creek service on the East Coast</h2>
        </div>
        <div class="prose">
          <p>Cane Creek has limited service at its own factory to warranty work and sends riders to its certified service centers (<a href="{CC_SRC}" target="_blank" rel="noopener">Cane Creek</a>). On the East Coast, that service center is us.</p>
          <p>We service Cane Creek forks and shocks in-house, including the <strong>Helm</strong> fork and the <strong>Kitsuma</strong>, <strong>DB Air</strong> and <strong>DB Coil</strong> shocks. Not sure what you have? Send us the model name printed on it and we'll tell you.</p>
          <p>As a Cane Creek VIP dealer we can also order Cane Creek parts and upgrades. <a href="../?inquiry=part#contact">Ask about a part</a>.</p>
          <p>Riding another brand? We service <a href="../suspension-service/">forks and shocks from every major brand</a>.</p>
        </div>
      </div>
    </section>

    <section class="section section-dark">
      <div class="wrap two-col">
        <div class="col-intro">
          <p class="kicker">Pricing</p>
          <h2>Cane Creek service pricing</h2>
          <p class="sub">The same rates for drop-off and mail-in.</p>
        </div>
        <div>
{PRICES}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap two-col">
        <div class="col-intro">
          <p class="kicker">Mail-in</p>
          <h2>Ship it from anywhere</h2>
          <p class="sub">Riders send Cane Creek suspension from across the Northeast and beyond.</p>
        </div>
        <div>
{STEPS}
          <a class="btn btn-dark" href="{MAILIN_LINK}">Start a mail-in service</a>
        </div>
      </div>
    </section>'''

cc_faqs = [
    ("Does Cane Creek still service suspension at the factory?",
     f'Cane Creek says factory service is currently limited to warranty work, and it directs riders to certified service centers. Mythic Bike Works is the only one on the East Coast. <a href="{CC_SRC}" target="_blank" rel="noopener">Cane Creek suspension service</a>.'),
    ("Which Cane Creek products do you service?",
     "Cane Creek forks and shocks, including the Helm fork and the Kitsuma, DB Air and DB Coil shocks. Send us the model name if you're unsure."),
    ("Can I mail my Cane Creek shock or fork to you?",
     f'Yes. <a href="{MAILIN_LINK}">Send us a message</a> first and we\'ll reply with a quote and shipping instructions.'),
    ("How long does service take?",
     "It depends on parts and the season. We give you a turnaround estimate when you get in touch."),
    ("Do you only work on Cane Creek?",
     'No. We service forks and shocks from every major brand, including Fox, RockShox and Marzocchi. <a href="../suspension-service/">See suspension service</a>.'),
    ("Where are you?",
     "1207 Kingstown Rd, Peace Dale, RI 02879, on the South County Bike Path near Wakefield. Open Monday, Thursday and Saturday 9am–5pm and Friday 9am–6pm."),
]
cc = page("cane-creek-service-center",
          "Cane Creek Suspension Service Center, East Coast | Mythic Bike Works",
          "The only Cane Creek suspension service center on the East Coast. Helm, Kitsuma and DB shock service. Drop off in Peace Dale, RI or mail it in.",
          "Cane Creek service center", cc_body,
          {"name": "Cane Creek suspension service", "serviceType": "Bicycle suspension service",
           "brand": {"@type": "Brand", "name": "Cane Creek"},
           "offers": [{"@type": "Offer", "name": "Basic service", "price": "50", "priceCurrency": "USD"},
                      {"@type": "Offer", "name": "Full overhaul", "price": "140", "priceCurrency": "USD"}]},
          cc_faqs)

# ---------------- Suspension page ----------------
sus_body = hero(
    "Suspension service",
    "Fork &amp; shock service, drop off or mail in",
    "Mountain bike suspension service for every brand, done in-house in Peace Dale, RI. Local riders drop off. Riders across the Northeast ship their forks and shocks to us.",
    ("Start a mail-in service", MAILIN_LINK), ("Call 401-218-0029", "tel:+14012180029")) + f'''

    <section class="section">
      <div class="wrap two-col">
        <div class="col-intro">
          <p class="kicker">Every brand</p>
          <h2>All brands, one bench</h2>
        </div>
        <div class="prose">
          <p>We service forks and rear shocks from every major brand, including Fox, RockShox, Marzocchi and Cane Creek.</p>
          <p>For Cane Creek, we are the <a href="../cane-creek-service-center/">only certified suspension service center on the East Coast</a>.</p>
          <h3>Signs it's time for service</h3>
          <ul class="items items-light">
            <li>Oil on the stanchions or shock body</li>
            <li>Harsh over small bumps, or sticky at the top of the travel</li>
            <li>Knocking, clunking or a top-out thud</li>
            <li>More than 50 riding hours since the last lower service</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="section section-dark">
      <div class="wrap two-col">
        <div class="col-intro">
          <p class="kicker">Pricing</p>
          <h2>Suspension service pricing</h2>
          <p class="sub">The same rates for drop-off and mail-in.</p>
        </div>
        <div>
{PRICES}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="wrap two-col">
        <div class="col-intro">
          <p class="kicker">Mail-in</p>
          <h2>How mail-in service works</h2>
          <p class="sub">Riders ship to us from Massachusetts, Connecticut, New York, New Jersey, Pennsylvania, New Hampshire, Vermont, Maine and beyond.</p>
        </div>
        <div>
{STEPS}
          <a class="btn btn-dark" href="{MAILIN_LINK}">Start a mail-in service</a>
        </div>
      </div>
    </section>'''

sus_faqs = [
    ("How often should I service my fork and shock?",
     "A basic lower service about every 50 riding hours and a full overhaul about every 200 hours is a good rule. Your manufacturer's manual has the exact interval."),
    ("Do you service Fox and RockShox?",
     "Yes. We service forks and shocks from every major brand, including Fox, RockShox, Marzocchi and Cane Creek."),
    ("Can I mail my fork or shock to you?",
     f'Yes. <a href="{MAILIN_LINK}">Send us a message</a> with the model and what it\'s doing, and we\'ll reply with a quote and shipping instructions.'),
    ("Do I need to send the whole bike?",
     "Usually just the fork or shock. We'll confirm when we reply. Linkage bearing work needs the frame."),
    ("How long does it take?",
     "It depends on parts and the season. We give you a turnaround estimate when you get in touch."),
    ("Where are you?",
     "1207 Kingstown Rd, Peace Dale, RI 02879, on the South County Bike Path near Wakefield, Narragansett and the URI campus."),
]
sus = page("suspension-service",
           "Fork & Shock Service, Drop Off or Mail In | Mythic Bike Works",
           "Mountain bike fork and shock service for every brand. Drop off in Peace Dale, RI or mail it in from anywhere in the Northeast. Basic service $50, overhaul $140.",
           "Suspension service", sus_body,
           {"name": "Mountain bike suspension service", "serviceType": "Bicycle suspension service",
            "offers": [{"@type": "Offer", "name": "Basic service", "price": "50", "priceCurrency": "USD"},
                       {"@type": "Offer", "name": "Full overhaul", "price": "140", "priceCurrency": "USD"}]},
           sus_faqs)

for slug, content in [("cane-creek-service-center", cc), ("suspension-service", sus)]:
    os.makedirs(f"{ROOT}/{slug}", exist_ok=True)
    open(f"{ROOT}/{slug}/index.html", "w").write(content)
    print("wrote", slug)
