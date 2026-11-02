# Sanskar Lamsal — Photography Portfolio

The current photography portfolio, with the dark gallery design and photographs from lamsal.photos.

## Run locally

No dependencies or build step are required. From this folder:

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. Stop the server with Ctrl+C.

## Repository contents

- `index.html`: page markup, responsive styles, collection definitions, and gallery interactions.
- `photos/`: 54 photographs, each with a full-size WebP and a smaller responsive version (108 files total).
- `.nojekyll`: allows GitHub Pages to serve the files directly.
- `_headers`: headers for hosts that support this file. GitHub Pages does not apply these rules.

The gallery uses original image dimensions to preserve aspect ratios, aligned rows on desktop, and a single column on mobile. It includes collection highlights, full collections, keyboard navigation, and swipe navigation in the photo viewer.

## Editing

For now, content and collection definitions are inside the script in `index.html`. The `albums` object controls membership, ordering, and featured images; `descriptions` supplies image descriptions; `sizes` stores image dimensions. Keep dimensions and both image variants in sync when adding photographs.

A hosted CMS is not configured yet. The intended next step is to separate content into editable files and add Pages CMS with image processing, without tying the content to this particular design.

## GitHub Pages and the custom domain

This repository is ready for static hosting, but publishing settings and DNS are not configured by this source import. When enabling Pages, serve the repository root from `main`, or use a Pages deployment workflow. Configure `lamsal.photos` in repository settings only when ready to migrate the domain.

Before switching hosts, update the Open Graph image URL in `index.html` to the final production domain. Keep any tokens or CMS authentication secrets outside the public files.

## Rights

Photographs are by Sanskar Lamsal. All rights reserved. Repository access does not grant permission to reuse the photographs.
