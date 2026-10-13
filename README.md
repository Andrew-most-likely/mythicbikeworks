# Mythic Bike Works website

Static site: plain HTML, CSS and JS. No build step.

```
index.html            main page
thanks.html           shown after form submit when JavaScript is off
404.html
assets/css/styles.css
assets/js/main.js     header, open/closed status, form logic
assets/img/           optimized photos and logos
```

## Preview locally

```
python3 -m http.server 8000
```

Then open http://localhost:8000.

## Contact form setup (required)

The form sends email through [Web3Forms](https://web3forms.com) (free, 250 submissions/month, no backend).

1. Go to web3forms.com, enter the shop email address, and get an access key.
2. In `index.html`, replace `YOUR_WEB3FORMS_ACCESS_KEY` with that key.

Each email has a subject like "Part inquiry from Jane" and includes the inquiry type, bike, part, and message.
Reply-to is set to the customer's email, so hitting Reply answers them directly.

## Hours

Hours appear in three places. Change all three:

- `index.html`: the hours table
- `index.html`: `openingHoursSpecification` in the JSON-LD block (Google)
- `assets/js/main.js`: the `HOURS` object (drives the "Open now" badge)

## Deploy

Any static host works. Cloudflare Pages, Netlify or GitHub Pages are all free:
upload this folder and point the mythicbikeworks.com domain at it.
