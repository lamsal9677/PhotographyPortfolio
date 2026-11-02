# Working on this portfolio

Read `docs/PROJECT_CONTEXT.md` and `TODO.md` before making changes. They record the owner's intent, current architecture, hosting, and pending content decisions.

- Pull the repository before editing so CMS changes are preserved.
- Keep the portfolio compatible with GitHub Pages project paths and the eventual custom domain.
- Preserve photo aspect ratios. Test phone and desktop views for frontend changes.
- Do not invent stories, locations, client details, or biography. Pending owner content belongs in TODO.md.
- Do not change repository visibility, DNS, or account access without an explicit user request.
- Run `python -m unittest discover -s tests -v` and `python scripts/build.py` for build/content changes. Generated `_site/` and `.cache/` must not be committed.
- Record completed work and remaining decisions in TODO.md and update the project context when architecture changes.
