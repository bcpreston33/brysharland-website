# Bry Sharland — artwork portfolio

This is the approved Version 7 visual design, adapted to publish artwork using Pages CMS.

## First-time setup
1. Upload **all repository files**, including the hidden `.pages.yml` file, to the GitHub repository `bcpreston33/brysharland-website`. Preserve folder structure.
2. In [Pages CMS](https://pagescms.org/), select this repository. The **Artwork** collection will appear. Add entries there and upload artwork images.
3. In Cloudflare Pages, connect the GitHub repository, choose **Build command:** `pip install -r requirements.txt && python scripts/build.py` and **Build output directory:** `dist`.
4. Test a new artwork entry in Pages CMS, confirm it appears in the correct category after deployment, and test the lightbox. The homepage category image uses the first entry marked **Feature on homepage**, or the first entry for that category.
5. Only after the new website is tested, update the domain connection. Existing Google Sites remains untouched until then.

## Notes
- The current homepage category tiles deliberately repeat the supplied artwork until category-specific artwork is published.
- Store and contact pages remain placeholders; no shop URL or contact details have been invented.
- Image paths are saved to `assets/uploads` in the repository.
- Changes published through Pages CMS commit to GitHub, triggering Cloudflare Pages deployment when connected.
- For local preview of a built site, run `pip install -r requirements.txt && python scripts/build.py` then `python -m http.server 8000 --directory dist`. Open http://localhost:8000.
- The Pages CMS configuration is `.pages.yml` at repository root. On macOS it may be hidden in Finder.
