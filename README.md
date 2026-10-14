# Mythic Bike Works website

Static site, no dependencies: plain HTML, CSS and JavaScript, self-hosted font, no outside
scripts or trackers. Pages are generated from `src/` by a standard-library Python script.

```
src/pages/*.html      page content; each starts with a <!--meta {json} --> block
src/partials/         header, footer, contact form, slide-in panel, hours table
src/data/business.json  business details for Google (home page)
tools/build.py        builds every page:  python3 tools/build.py
index.html, service/, suspension-service/, cane-creek-service-center/,
wheels-and-builds/, contact/   generated output (commit it)
thanks.html, 404.html   hand-written
assets/css, assets/js, assets/img, assets/fonts
board/  hub/          design board and project hub (hidden from search)
```

Edit files in `src/`, run `python3 tools/build.py`, then commit and push.
## Contact form setup (required)

The form sends email through [Web3Forms](https://web3forms.com) (free, 250 submissions/month, no backend).

1. Go to web3forms.com, enter the shop email address, and get an access key.
2. In `src/partials/form.html`, replace `YOUR_WEB3FORMS_ACCESS_KEY` with that key, then rebuild.

Each email has a subject like "Part inquiry from Jane" and includes the inquiry type, the service picked,
how the customer wants a reply (email, call or text), their bike, the part, and the message.
Reply-to is set to the customer's email, so hitting Reply answers them directly.

## Hours

Hours appear in three places. Change all three:

- `src/partials/hours.html`: the hours table
- `src/data/business.json`: `openingHoursSpecification` (Google)
- `src/pages/contact.html` and `src/pages/cane-creek.html`: hours written in the text
- `assets/js/main.js`: the `HOURS` object (drives the "Open now" badge)

## Caching

CSS and JS links end in `?v=N`. After changing `styles.css` or `main.js`, bump `VERSION` in
`tools/build.py` and rebuild. `_headers` sets long caching on Cloudflare Pages.

## Security policy and preloading

Every generated page has a Content-Security-Policy that only allows this site, the Web3Forms
form endpoint, and Cloudflare Web Analytics. Pages preload each other with speculation rules
(Chrome, Edge) and a prefetch fallback in `main.js` (other browsers).

## Deploy

Any static host works. Cloudflare Pages, Netlify or GitHub Pages are all free:
upload this folder and point the mythicbikeworks.com domain at it.
