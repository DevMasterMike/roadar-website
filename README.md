# Roadar Marketing Site

Static site for App Store Connect. Three pages, one stylesheet, zero build step.

- `index.html`: landing page (hero, features, privacy, pricing, FAQ)
- `terms.html`: Terms of Service (required by Apple)
- `privacy.html`: Privacy Policy (required by Apple)
- `styles.css`: design tokens mirrored from the iOS app's `DesignSystem/Theme.swift`

Fonts are loaded from Google Fonts (Geist + JetBrains Mono). All icons are inline SVG. The radar animation is pure CSS. No JS, no build, no dependencies.

## Local preview

```sh
cd ~/Desktop/roadar-website
python3 -m http.server 8000
# open http://localhost:8000
```

## Deploy options (pick one)

**Netlify drop (fastest, free):**
1. Go to https://app.netlify.com/drop
2. Drag the `roadar-website` folder onto the page
3. Note the generated URL (e.g. `roadar-abc123.netlify.app`)
4. Optional: add a custom domain `roadar.app` in Site settings &gt; Domain

**Cloudflare Pages (custom domain, free):**
1. Push this folder to a GitHub repo
2. Cloudflare dashboard &gt; Pages &gt; Create &gt; Connect to GitHub
3. Framework preset: None. Build command: empty. Output: `/`
4. Add custom domain in Pages &gt; Custom domains

**GitHub Pages:**
1. Push to a repo (e.g. `roadar-website`)
2. Settings &gt; Pages &gt; Source: deploy from branch `main` / root
3. Site lives at `<user>.github.io/roadar-website`

## App Store Connect URLs to fill

In App Store Connect &gt; App Information and the version submission page:

- **Marketing URL** &rarr; `https://yourdomain/` (landing page)
- **Privacy Policy URL** &rarr; `https://yourdomain/privacy.html` (required)
- **Support URL** &rarr; either the landing page or a `mailto:support@roadar.app` page

Apple rejects submissions whose Privacy Policy URL 404s or hides behind a sign-in wall, so verify the URL loads in an incognito window before submitting.

## Editing legal copy

`terms.html` and `privacy.html` are intentionally hand-maintained copies of the in-app legal text. When the in-app `LegalScreen.swift` changes (Section count, defined terms, contact emails), update the matching section here and bump the `Last updated` date at the top.

Rule: no em dashes anywhere on this site. Use commas, periods, or rewrites.
