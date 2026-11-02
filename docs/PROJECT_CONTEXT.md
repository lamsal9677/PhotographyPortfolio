# Photography portfolio — durable project context

## Owner and goal

Sanskar Lamsal photographs events, portraits, landscapes, birds, wildlife, and insects. The portfolio must make event coverage immediately discoverable while encouraging event visitors to explore nature work. Strong highlights should lead to complete collections. Nature photographs may have associated stories about encounters, place, and the experience of making the photograph.

## Source of truth

- Repository: https://github.com/lamsal9677/PhotographyPortfolio
- Local checkout: `/Users/lamsal9677/Documents/Codex/2026-10-31/i-d/work/PhotographyPortfolio`
- Hosting: GitHub Pages, currently https://lamsal9677.github.io/PhotographyPortfolio/
- Intended custom domain: lamsal.photos. Do not change DNS without an explicit request.
- Editor: hosted Pages CMS, connected by the owner. Configuration is `.pages.yml`.
- Publishing: pushes to main build the site; deployment requires repository variable `PAGES_ENABLED=true`. Owner reports publishing works.
- The earlier `field-and-frame-portfolio-k7m2.almondluck68.chatgpt.site` is an older prototype. It does not automatically update from this GitHub repository. Prefer the GitHub Pages URL for current work.

## Architecture

- Python/Pillow build: `scripts/build.py`.
- Editable content: `content/site.json`, `content/collections/*.json`, `content/stories/*.json`.
- Image originals: `media/`. Generated responsive WebP files: `_site/photos/`.
- Layout: `templates/index.html`, `templates/dialogs.html` and build-generated work/story pages.
- Frontend: `assets/site.css`, `assets/gallery.js`.
- Generated output: `_site/`, ignored by Git. Serve with `python3 -m http.server 8000 --directory _site` after building.
- Image transformations are content-addressed and cached in `.cache/images/`. Content edits must rebuild pages, not re-encode unchanged photographs.
- Build/CI checks: `python -m unittest discover -s tests -v` and `python scripts/build.py`.
- Local task runtime has Pillow in `../python-libs`; for ordinary local development use the documented virtual environment and requirements.txt. JavaScript checks can run with a standard Node installation.

## Content and publication rules

There are currently 54 unique photographs in seven collections: three people/event collections, landscapes, birds, wildlife, and small worlds. The sole story entry is an unfinished draft. Never invent a first-person story, location, client, testimonial, or biographical fact to fill empty sections. Stories are plain-text paragraphs, not rich text, in this version. Unpublished entries are excluded from the built website but are readable in a public source repository. Never put confidential client galleries or precise sensitive wildlife locations in public repository files.

## Design requirements and history

The owner rejected stock photographs, a fictional studio brand, excessive white space, overly dark presentation, forced photo crops, and awkward mobile layouts. Preserve original photograph proportions. Current direction is a medium sage/stone surface, readable dark type, with an unboxed, automatic photographic strip at the top. Keep only the full-screen viewer dark. Keep the work central, copy restrained, and navigation visible on phones.

The current iteration uses an automatically advancing native-ratio photo strip with no visible playback controls, an all-photo archive with filters/search, an always-visible Stories destination, subtle reduced-motion-aware animation, URL-backed galleries, and image-build caching. Do not silently reintroduce dark-all-over styling or fixed object-fit:cover crops for the photography.

## Working agreement

Read this file and `TODO.md` at the start of future portfolio work. Pull main before editing so Pages CMS updates are preserved. Track completed work and remaining decisions in TODO.md. Keep frontend changes compatible with GitHub Pages project subpaths and future custom-domain hosting. Preserve the owner's biography edits. Expanded About content can wait for their input.

## Latest verified release

Code commit `a0dcb71` passed 12 automated checks and a successful GitHub Pages deployment on 2026-11-01. See `docs/AUDIT.md` for the browser verification log and TODO.md for pending owner content.

## Editorial refresh direction

The owner dislikes diagonal arrow/emoji decoration, boxy controls, and the old framed slideshow. Remove decorative arrows from public copy and photo cards. Use native SVG Instagram/Facebook/mail icons with accessible labels. Buttons and filters use restrained rounded shapes. The opening is an automatically advancing horizontal strip: complete active photos at their original ratios, neighboring frames offering visual continuity, and a quiet progress indicator. Hover/focus/touch and reduced-motion preferences stop or suspend movement without a visible Play/Pause interface. Strong nature imagery leads, with events still immediately discoverable through navigation and the hero CTA.

References reviewed: Jimmy Chin, Nadav Kander, Rinko Kawauchi. They inform image-led hierarchy and quiet navigation; do not copy their artwork or branding.
