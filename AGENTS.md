# Project reference

Japanese SPA summarizing HEROINES/imaginate crowdfunding projects from CAMPFIRE.
The catalogue groups idol crowdfunding projects by agency. HEROINES is the public-known
name and imaginate the company name for the same agency; they are not separate agencies.
Use the exact proper-name label `heroines/imaginate` in the planned agency selector,
without a katakana translation. Only this agency is implemented currently.
Scraping runs manually outside the app. The browser displays a bundled JSON snapshot
with filters, sorting, pagination, funding totals, supporter counts, and reward breakdowns.
Here, an agency "database" means a committed JSON snapshot. There is no backend server,
database service, runtime data API, or LLM integration.

## Design spec convention

- Store feature designs in `docs/specs/` as `YYYY-MM-DD-<status>-<feature>.md`.
  Use the design's creation date in Japan time and a snake_case feature name.
- Status is `design` while being developed, `spec` once the design is finalized,
  and `implemented` only after implementation and its required validation are complete.
  Rename the same document when its status changes, retaining its creation date and
  feature name; update links and its internal status instead of keeping duplicate copies.
- A finalized spec records the design, not permission to implement. Respect any separate
  user confirmation requirement, and keep proposed behavior distinct from current behavior.
- The finalized `multiple_agency` design is
  [2026-09-10-spec-multiple_agency.md](docs/specs/2026-09-10-spec-multiple_agency.md).
  It is documentation only. Frontend, scraper, data, and workflow changes await explicit
  implementation confirmation. Update `update-data.yml` only after the frontend is implemented.

## Stack

- Svelte 5 runes, SvelteKit 2, Vite 7, JavaScript ES modules with JSDoc.
- `@vincjo/datatables` manages table rows, filters, sorting, and pagination.
- Component CSS and shared CSS variables; no CSS framework.
- Bun for dependencies and data scripts; `bun.lock` is the committed lockfile.
- Python CLI with `requests` and BeautifulSoup for automated scraping; the notebook
  remains available with `pyperclip` as a manual reference.
- Static adapter and GitHub Actions deploy to GitHub Pages.
- `svelte-check`, TypeScript tooling, and Prettier. Several core files use `@ts-nocheck`.
- `@svar-ui/svelte-grid` is installed but unused by the current app.

## File map

| Path                                          | Responsibility                                                               |
| --------------------------------------------- | ---------------------------------------------------------------------------- |
| `src/routes/+page.svelte`                     | Main page, table instance, columns, responsive layout, metadata, footer.     |
| `src/routes/+page.js`                         | `prerender = true`, `ssr = false`: static shell with client rendering.       |
| `src/routes/+layout.svelte`                   | Favicon, shared CSS variables, layout wrapper.                               |
| `src/lib/procData.js`                         | Imports snapshot, derives rows and filter indexes, formats money and dates.  |
| `src/lib/data/heroinesCF.json`                | Dataset bundled into the app. Filename is not a freshness guarantee.         |
| `src/lib/ProjectSelector.svelte`              | Group, member, event-year, and funding-range filters; apply/reset actions.   |
| `src/lib/GroupFilter.svelte`                  | Group checkboxes and project counts.                                         |
| `src/lib/*Cell.svelte`, `ThSortCustom.svelte` | Cell rendering and sortable headers.                                         |
| `src/lib/ProjectOverview.svelte`              | Unused view-switch placeholder.                                              |
| `src/lib/assets/`, `static/`                  | Imported images/icons and static-file directory.                             |
| `scrape_data/scraper.py`                      | Automated listing discovery, project parsing, validation, and staged output. |
| `scrape_data/apply_update.py`                 | Applies staged files, creates backups, commits, and pushes database updates. |
| `scrape_data/scrape_progress.json`            | Committed checkpoint and pending-project state.                              |
| `scrape_data/test_*.py`                       | Scraper and update-application tests run by the GitHub Action.               |
| `scrape_data/scraper.ipynb`                   | Optional manual scraping reference; not used by the automated workflow.      |
| `scrape_data/old/`                            | Archived manual scripts and historical exports; not used by the pipeline.    |
| `.github/workflows/build.yml`                 | Build and Pages deployment.                                                  |
| `.github/workflows/update-data.yml`           | Manual scrape, staged merge, backup, push, and rebuild orchestration.        |

## Data flow

1. The manual `Update scraped crowdfunding data` GitHub Action runs
   `scrape_data/scraper.py`. It follows the heroines listing pagination until the
   checkpoint in `scrape_data/scrape_progress.json`, or all pages with `full_scan=true`.
   The initial checkpoint is project `956928`.
2. The scraper records newly finished projects, keeps unfinished and failed projects in
   the progress file, and writes only temporary candidate files and a run report.
   It does not modify the database or frontend source directly.
3. The action runs `scrape_data/apply_update.py` only after staging succeeds. It creates
   `src/lib/data/old/backup_at_<UTC>_run<id>_attempt<attempt>.json` before replacing the
   database, commits the database/progress together, and pushes to `main`.
4. A database commit explicitly calls `.github/workflows/build.yml` at that commit SHA.
   A progress-only update does not rebuild the site. A dry run uploads the report without
   committing, backing up, or deploying.
5. The notebook is retained only as a manual reference. The historical cleanup scripts
   and raw exports are archived under `scrape_data/old/` and are not part of the
   automated pipeline.
6. Review records and update `src/lib/data/heroinesCF.json` manually when needed. Changing files in
   `scrape_data/` alone does not update the app.
7. At module initialization, `procData.js` keeps records with `per === '終了'`, flattens
   `subject`, and derives `totalpatrons`, `averageFund`, `period`, and `ppTotal`.
   It builds `gpMap`, `mbSet`, and `yrSelection` for the filter UI.

Raw records contain `url`, `title`, numeric `total` (yen), numeric `rest` (supporters),
`per`, `start`/`end` (`YYYY-MM-DD`), `eventYear`, `subject: { group, member, type }`,
and `pricePatrons: [{ price, patrons }]`. Some historical exports also contain `sub`.
Groups split on `/` or `／`; the member index splits on commas.
`ppTotal` sums reward price × supporters and is distinct from reported `total`.

Before updating data, check duplicate URLs, subject parsing, numeric fields, and event year.
The notebook uses the start year and hardcodes completed status; the older merge script
extracts event year from `sub`. Review these values against the project details.

Current scraping scope is CAMPFIRE only. Its page scraper and normalized record format
are intended for reuse by future agencies, but compatibility is not guaranteed: page
markup, title/member conventions, and event-year extraction may differ. Check representative
pages before onboarding an agency. If the existing parser does not fit, add a suitable
page-scraper script/adapter and review orchestration, dependencies, validation, and GitHub
Actions for required changes; do not assume selecting a different database is sufficient.
The current automated discovery visits only `https://camp-fire.jp/profile/heroines/projects`;
the footer's imaginate attribution link is not an additional automated discovery source.

## Commands and deployment

- Install: `bun install`; develop: `bun run dev`.
- Validate app changes: `bun run check`; build: `bun run build`; preview: `bun run preview`.
- Scraper tests: `python -m unittest discover -s scrape_data -p 'test_*.py' -v`.
- Local dry run: `python scrape_data/scraper.py --output-dir <temporary-directory>`.
- Full scan: add `--full-scan`; the GitHub Action exposes the same option as an input.
- Formatting: `bun run lint` (Prettier only), `bun run format`.
- The scraper and update scripts have a Python unittest suite. The GitHub Action runs
  it before every scrape; frontend validation uses `bun run check` and `bun run build`.
- Static output goes to `build/`. Production `BASE_PATH` controls the deployment subpath;
  CI sets it to `/<repository-name>`. Development uses an empty base path.
- Automatic deployment watches `src/**`, `static/**`, and `svelte.config.js` on `main`.
  Other changes require a manual workflow run or a watched-file change.
- `vite.config.js` injects `__BUILD_DATE__`; the footer shows build date, not scrape date.
- Scraper requests are sequential, spaced by one second, limited to 30 seconds, and retried
  three times. Listing failures stop publication; individual project failures are retained
  in progress and do not prevent successful projects from being published.
- Run the `Update scraped crowdfunding data` workflow manually from GitHub. `dry_run=true`
  uploads staged results without committing, while `full_scan=true` ignores the checkpoint.
- The production workflow uses Node 24-compatible action versions (`checkout@v6`,
  `setup-python@v6`, `upload-artifact@v6`, `upload-pages-artifact@v5`, and
  `deploy-pages@v5`). The scrape and Pages deployment have been verified successfully.
- Restore a database by copying the desired `src/lib/data/old/backup_at_*.json` over
  `src/lib/data/heroinesCF.json`, then run the Pages build workflow manually.

Keep Japanese UI text and existing Svelte/CSS patterns. Treat `.svelte-kit/`, `build/`,
and `node_modules/` as generated. Update this reference when architecture or data flow changes.
