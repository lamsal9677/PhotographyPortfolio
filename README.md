# Sanskar Lamsal — Photography Portfolio

A static, GitHub-backed portfolio for events, portraits, nature photographs, and field notes. The design and content are separate so either can change independently.

**Start here:** [Connect the editor and publish](docs/SETUP.md).

## Content editing

- **Pages CMS:** `.pages.yml` defines Collections, Stories / Field notes, and Site settings.
- **Folders:** edit the same JSON files in `content/` and upload JPG, PNG, or WebP images into `media/`. Commit your changes to trigger a build.
- No custom login, database, API token in the website, or application server is required. Hosted Pages CMS connects to GitHub separately.

The editor configuration is prepared. Connecting your account and enabling GitHub Pages are still required; see the setup guide. Deployments are gated by the repository variable `PAGES_ENABLED=true`.

## Local development

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/build.py
python -m http.server 8000 --directory _site
```

Open http://localhost:8000. Run the build again after changing content, templates, or assets. Generated output lives in `_site/` and is not committed. The repository root is source, not the publish directory.

## Structure

| Path | Purpose |
| --- | --- |
| `content/site.json` | Identity, contact details, opening images, website URL |
| `content/collections/*.json` | Event / nature collections, covers, photo order, highlights, captions |
| `content/stories/*.json` | Stories, dates, broad locations, writing, and photographs |
| `media/` | Source portfolio images; no manually created thumbnails needed |
| `assets/` | Frontend styles and gallery behavior |
| `templates/index.html` | Homepage design |
| `scripts/build.py` | Validation, image processing, static HTML and story generation |
| `.pages.yml` | Editor schema (JSON syntax, which is also valid YAML) |
| `.github/workflows/pages.yml` | Tests, build, artifact upload, optional Pages deployment |

The build auto-rotates images, reads dimensions, preserves aspect ratios, strips metadata from generated images, and produces responsive WebP files. Filenames are content-hashed so updated images receive new URLs. Reusing one source image in several collections or stories avoids duplicating generated assets.

A collection is shown in People & events or in its selected nature category. An optional story becomes a standalone page and appears under Field notes. The image viewer links to a published story when that image is included in the story. Published stories can cover either nature or events. With no published stories, there is no empty Field notes section.

## Publishing behavior

Every push to `main` builds and validates the site. Deployment runs only after `PAGES_ENABLED` is `true`. Pull requests build without publishing. GitHub Pages must use **GitHub Actions**, not a source branch.

Only published content and referenced, processed images are included in `_site/`. This is publication control, not privacy: source files, drafts, and uploads remain readable if the repository is public. Do not upload confidential client galleries, RAW archives, or sensitive location data. Generated images have metadata removed; original uploads in the repository do not.

Do not run `--include-drafts` for public publishing. It is a local preview flag; incomplete drafts may fail validation until completed.

`_headers` is for hosts that support it; GitHub Pages does not apply that file. Custom-domain DNS and GitHub settings are configured separately. There are no email form submissions: inquiry links open the visitor's email app.

## Rights

All photographs are by Sanskar Lamsal. All rights reserved. Access to this repository does not grant permission to reuse the photographs.
