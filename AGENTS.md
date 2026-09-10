# Project reference

Japanese SPA summarizing HEROINES/imaginate crowdfunding projects from CAMPFIRE.
Scraping runs manually outside the app. The browser displays a bundled JSON snapshot
with filters, sorting, pagination, funding totals, supporter counts, and reward breakdowns.
There is no backend, database, runtime data API, or LLM integration.

## Stack

- Svelte 5 runes, SvelteKit 2, Vite 7, JavaScript ES modules with JSDoc.
- `@vincjo/datatables` manages table rows, filters, sorting, and pagination.
- Component CSS and shared CSS variables; no CSS framework.
- Bun for dependencies and data scripts; `bun.lock` is the committed lockfile.
- Python/Jupyter with `requests`, BeautifulSoup, and `pyperclip` for scraping.
- Static adapter and GitHub Actions deploy to GitHub Pages.
- `svelte-check`, TypeScript tooling, and Prettier. Several core files use `@ts-nocheck`.
- `@svar-ui/svelte-grid` is installed but unused by the current app.

## File map

| Path                                          | Responsibility                                                                  |
| --------------------------------------------- | ------------------------------------------------------------------------------- |
| `src/routes/+page.svelte`                     | Main page, table instance, columns, responsive layout, metadata, footer.        |
| `src/routes/+page.js`                         | `prerender = true`, `ssr = false`: static shell with client rendering.          |
| `src/routes/+layout.svelte`                   | Favicon, shared CSS variables, layout wrapper.                                  |
| `src/lib/procData.js`                         | Imports snapshot, derives rows and filter indexes, formats money and dates.     |
| `src/lib/data/heroinesCF.json`                | Dataset bundled into the app. Filename is not a freshness guarantee.            |
| `src/lib/ProjectSelector.svelte`              | Group, member, event-year, and funding-range filters; apply/reset actions.      |
| `src/lib/GroupFilter.svelte`                  | Group checkboxes and project counts.                                            |
| `src/lib/*Cell.svelte`, `ThSortCustom.svelte` | Cell rendering and sortable headers.                                            |
| `src/lib/ProjectOverview.svelte`              | Unused view-switch placeholder.                                                 |
| `src/lib/assets/`, `static/`                  | Imported images/icons and static-file directory.                                |
| `scrape_data/`                                | Python scraper/tests, checkpoint state, notebook, cleanup scripts, raw exports. |
| `.github/workflows/build.yml`                 | Build and Pages deployment.                                                     |
| `.github/workflows/update-data.yml`           | Manual scrape, staged merge, backup, push, and rebuild orchestration.           |

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
5. The older manual workflow remains available for historical data work. `scraper.ipynb`
   takes explicit project IDs, combines rewards with identical prices, and copies
   comma-separated JSON objects to the clipboard.
6. Clean and merge historical exports manually. `01_regroup_and_merge.js` joins overview/detail exports by
   URL, normalizes reward prices/dates, and extracts subject fields into `processed.json`.
   `02_regroup2.js` patches dates and supporter counts into `processed3.json`.
   These are separate utilities with hardcoded filenames, not an automated pipeline.
   Run them from `scrape_data/` after checking their inputs and outputs.
7. Review records and update `src/lib/data/heroinesCF.json` manually. Changing files in
   `scrape_data/` alone does not update the app.
8. At module initialization, `procData.js` keeps records with `per === '終了'`, flattens
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

## Commands and deployment

- Install: `bun install`; develop: `bun run dev`.
- Validate app changes: `bun run check`; build: `bun run build`; preview: `bun run preview`.
- Scraper tests: `python -m unittest discover -s scrape_data -p 'test_*.py' -v`.
- Local dry run: `python scrape_data/scraper.py --output-dir <temporary-directory>`.
- Full scan: add `--full-scan`; the GitHub Action exposes the same option as an input.
- Formatting: `bun run lint` (Prettier only), `bun run format`.
- No automated test suite is configured.
- Static output goes to `build/`. Production `BASE_PATH` controls the deployment subpath;
  CI sets it to `/<repository-name>`. Development uses an empty base path.
- Automatic deployment watches `src/**`, `static/**`, and `svelte.config.js` on `main`.
  Other changes require a manual workflow run or a watched-file change.
- `vite.config.js` injects `__BUILD_DATE__`; the footer shows build date, not scrape date.
- Scraper requests are sequential, spaced by one second, limited to 30 seconds, and retried
  three times. Listing failures stop publication; individual project failures are retained
  in progress and do not prevent successful projects from being published.
- Restore a database by copying the desired `src/lib/data/old/backup_at_*.json` over
`src/lib/data/heroinesCF.json`, then run the Pages build workflow manually.

Keep Japanese UI text and existing Svelte/CSS patterns. Treat `.svelte-kit/`, `build/`,
and `node_modules/` as generated. Update this reference when architecture or data flow changes.
