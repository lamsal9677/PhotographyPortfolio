# Usability audit — 2026-11-01

Audited the actual GitHub Pages deployment, then exercised the updated local build. This is a practical usability and regression review, not a claim of exhaustive accessibility certification or load testing.

## Findings and changes

| Finding | Impact | Resolution |
| --- | --- | --- |
| Stories navigation disappeared when there were no published stories | Owner and visitors could not discover the feature | Permanent Stories destination with an honest empty state |
| No complete photo index | Visitors could not confidently browse the whole portfolio | All work page with 54 unique photographs, filters and search |
| Fixed navigation omitted Stories on phones | Phone users missed a whole content type | Consistent four-link navigation that wraps into two rows |
| Almost-black page surfaces felt heavy | Photos and controls lacked a lighter visual hierarchy | Medium sage/stone surfaces; darker photo-viewing mats |
| Static opening did not show the range of work | First impression depended on only two photographs | Curated slideshow mixing events and nature, with pause/previous/next |
| Browser Back left modal views without a useful navigation model | Users could accidentally leave the site | URL/history-backed collection and photo layers |
| Repeated generic descriptions | Search and screen-reader users could not distinguish subjects | More specific descriptions based on visible subjects |
| Story cover could appear again in its own gallery | Unnecessary repetition | Deduplicate the cover at render time |
| Every text edit re-encoded every photograph | Slow publishing and unnecessary compute | Content-addressed image-processing cache in local and Actions builds |
| Hardcoded photographer name in dynamic captions | Site settings edits were inconsistent | Use the content-driven identity throughout |

## Verification log

- Live baseline confirmed: 54 photographs, seven collections, no published stories.
- Updated archive: category filter and text search returned the expected pigeon photograph.
- Opening a filtered result retained the filtered viewer sequence.
- Browser Back closed the viewer and restored search/filter state.
- Permanent Stories page clearly reported that no stories have been published.
- Additional viewport, keyboard and deployment checks are recorded below as completed.

## Remaining editorial issues

Stories need real owner-written content; the existing blank draft should not be published as-is. About needs the owner's personal history and perspective. Those are tracked in TODO.md rather than filled with invented copy.

## Completed verification

- Phone widths 320px and 390px: no horizontal page overflow; all four navigation destinations remain visible.
- Tablet width 768px and desktop: native-ratio photo rows and nested collection/photo navigation checked.
- All work contains exactly 54 unique photo buttons, with no failed loaded image URLs in the tested view.
- Nature filter returns 42 photographs; Birds returns 12; text search and zero-result/reset handling work.
- Back closes a photograph without losing the archive filter/search. Escape closes a nested viewer and leaves its parent collection open. Closing the collection restores page scrolling.
- Opening slideshow Next changes image, label, and position; manual use pauses autoplay. Reduced motion disables autoplay/entrance effects by implementation; no OS preference was changed during testing.
- Twelve automated build checks pass, including draft exclusion, safe story text, unique slides, story cover deduplication, asset versioning, cached images, and output validity.
- Source story count is still zero published stories. No fictional story or personal background was added.

## Deployment

GitHub Actions build and Pages deployment succeeded for code commit `a0dcb71`: https://github.com/lamsal9677/PhotographyPortfolio/actions/runs/41369066596. The current site is https://lamsal9677.github.io/PhotographyPortfolio/ (not the older ChatGPT prototype).

## Editorial follow-up — 2026-11-01

Owner feedback: diagonal arrow decoration was excessive, the boxed slideshow felt dated, and controls needed a more contemporary style.

- Reviewed Jimmy Chin, Nadav Kander, and Rinko Kawauchi as image-led portfolio references.
- Replaced the framed player with an automatically advancing photo strip, starting with the mountain photograph. Adjacent frames remain visible; the active photograph retains its proportions.
- Removed visible opening playback controls and all decorative diagonal arrows from generated pages and frontend copy.
- Used SVG Instagram, Facebook, and mail icons with accessible names. Contact and filter controls now use consistent rounded styling.
- Removed repeated “View photograph” captions and hardcoded photographer-name labels.
- Verified automatic progression, 320px/390px page widths, keyboard selection, collection opening, photo navigation, and SVG viewer controls.
- Thirteen automated checks pass, including a regression check against arrow decoration and old player controls.

Editorial deployment verified: https://github.com/lamsal9677/PhotographyPortfolio/actions/runs/41370674101 (code `0c9f67d`). Automatic progression was observed through multiple frames without interaction, with correct centering at 1800px.
