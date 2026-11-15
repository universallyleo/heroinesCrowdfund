# Project reference

Japanese SPA summarizing idol crowdfunding projects from CAMPFIRE, with separate agency snapshots.
The catalogue groups idol crowdfunding projects by agency. HEROINES is the public-known
name and imaginate the company name for the same agency; they are not separate agencies.
Use the exact proper-name label `heroines/imaginate` in the agency selector,
without a katakana translation. Registered agencies are `heroines` and `madsink` (MAD’S iNK).
Scraping runs manually outside the app. The browser displays a bundled JSON snapshot
with filters, sorting, pagination, funding totals, supporter counts, and reward breakdowns.
Here, an agency "database" means a committed JSON snapshot. There is no backend server,
database service, runtime data API, or LLM integration.

## Design spec convention

- Store feature designs in `docs/specs/` as `YYYY-MM-DD-<status>-<feature>.md`.
  Use the design's creation date in Japan time and a snake_case feature name.
- Status is `design` while being developed, `spec` once the design is finalized with user agreement,
  and `implemented` only after implementation and its required validation are complete.
  Rename the same document when its status changes, retaining its creation date and
  feature name; update links and its internal status instead of keeping duplicate copies.
- A finalized spec records the design, not permission to implement. Respect any separate
  user confirmation requirement, and keep proposed behavior distinct from current behavior.
- The implemented `multiple_agency` design is
  [2026-09-10-implemented-multiple_agency.md](docs/specs/2026-09-10-implemented-multiple_agency.md).
  Implementation was explicitly authorized on 2026-11-15, including MAD’S iNK onboarding.
  The frontend was completed before editing the update workflow. Feature-branch delivery
  does not authorize merging or deploying to production.

## Multi-agency behavior and maintenance

- The Japanese `事務所` selector changes the title, attribution links, content-update date,
  data table, and filters together. Both heroines/imaginate CAMPFIRE links remain visible;
  imaginate is attribution only, not an automated discovery profile.
- Snapshots load lazily and successful imports are cached. The parent page owns per-agency
  session settings; keyed `AgencyProjects` instances recreate tables/filter indexes. Switching
  back restores draft and applied filters independently, sort, page size, and page number.
  Refresh returns to heroines and clears session memory. No localStorage or URL persistence.
- First visit shows all completed projects in snapshot order, 20 rows per page. Funding bounds
  derive from the selected data and round outward to thousands of yen. Apply/reset returns to
  page 1; reset preserves sort and page size. Loading, retry, reload, empty, and no-match UI is Japanese.
- `src/lib/data/agencies.json` is the shared frontend/Python registry. Stable IDs resolve owned
  database, metadata, progress, and backup paths, plus named scrapers and discovery profiles.
  Keep manual workflow choices synchronized with registry IDs. All entries are visible.
- Each agency's `updatedAt` means record-content update, not scrape attempt or build time.
  No-op/progress-only/error runs preserve it. The footer's `サイト更新` is the build date.
  Heroines metadata was bootstrapped from its verified content commit on 2026-11-12.
- MAD’S iNK titles require `campfire_madsink.py`; financial HTML parsing remains shared.
  `madsink_members.json` records reviewed membership and reference links. Per the user,
  use **latest known** groups even for historical events: main group first, then collaboration
  groups, joined by `/` in `subject.group`, matching the existing heroines format.
  `ちちゃめど` and `まっずぷりんす` are collaboration groups. The user confirmed all five
  shortened MADS PRINCE names and retaining MADMED for former members without a newer group.
  Unknown/ambiguous members must be confirmed with the user, never guessed. Update the mapping
  after review; the next valid MAD’S iNK stage reapplies it to stored rows and updates freshness
  if record content changes. Editing mapping files alone does not update bundled records.
- Initial MAD’S iNK scrape: 27 completed projects and one pending open project (`991831`),
  with no parsing failures. Heroines' 340 records were preserved with an identical Git content hash; its checkpoint
  `990003` and 14 pending entries were migrated losslessly into per-source progress.

## Stack

- Svelte 5 runes, SvelteKit 2, Vite 7, JavaScript ES modules with JSDoc.
- `@vincjo/datatables` manages sorting and pagination; pure agency filters select table rows.
- Component CSS and shared CSS variables; no CSS framework.
- Bun for dependencies and data scripts; `bun.lock` is the committed lockfile.
- Python CLI with `requests` and BeautifulSoup for automated scraping; the notebook
  remains available with `pyperclip` as a manual reference.
- Static adapter and GitHub Actions deploy to GitHub Pages.
- `svelte-check`, TypeScript tooling, and Prettier. Several core files use `@ts-nocheck`.
- `@svar-ui/svelte-grid` is installed but unused by the current app.

## File map

| Path                                                      | Responsibility                                                               |
| --------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `src/routes/+page.svelte`                                 | Agency selection/loading, parent session state, header/metadata/footer.      |
| `src/routes/+page.js`                                     | `prerender = true`, `ssr = false`: static shell with client rendering.       |
| `src/routes/+layout.svelte`                               | Favicon, shared CSS variables, layout wrapper.                               |
| `src/lib/procData.js`                                     | Pure per-snapshot rows/indexes; money and UTC calendar-day formatting.       |
| `src/lib/agencies.js`, `agencyCatalog.js`                 | Registry imports, lazy/cached loading, stale-result protection, Japan dates. |
| `src/lib/agencyState.js`                                  | Independent draft/applied filters, defaults/reset, pure row selection.       |
| `src/lib/AgencyProjects.svelte`                           | Keyed table/filter subtree, restored sort/pagination, existing columns.      |
| `src/lib/data/agencies.json`                              | Registry consumed by JS and Python.                                          |
| `src/lib/data/agencies/*/metadata.json`                   | Agency ownership and last record-content update timestamp.                   |
| `src/lib/data/agencies/madsink/projects.json`             | Reviewed MAD’S iNK completed records.                                        |
| `scrape_data/agency_config.py`                            | Registry/path/schema validation and lossless legacy progress migration.      |
| `scrape_data/campfire_madsink.py`, `madsink_members.json` | MAD’S iNK title/year parser and reviewed latest-group mapping.               |
| `scrape_data/summarize_report.py`                         | GitHub coverage warnings and run summary.                                    |
| `scrape_data/progress/madsink.json`                       | MAD’S iNK checkpoints and pending projects.                                  |
| `src/lib/data/heroinesCF.json`                            | Dataset bundled into the app. Filename is not a freshness guarantee.         |
| `src/lib/ProjectSelector.svelte`                          | Group, member, event-year, and funding-range filters; apply/reset actions.   |
| `src/lib/GroupFilter.svelte`                              | Group checkboxes and project counts.                                         |
| `src/lib/*Cell.svelte`, `ThSortCustom.svelte`             | Cell rendering and sortable headers.                                         |
| `src/lib/ProjectOverview.svelte`                          | Unused view-switch placeholder.                                              |
| `src/lib/assets/`, `static/`                              | Imported images/icons and static-file directory.                             |
| `scrape_data/scraper.py`                                  | Automated listing discovery, project parsing, validation, and staged output. |
| `scrape_data/apply_update.py`                             | Applies staged files, creates backups, commits, and pushes database updates. |
| `scrape_data/scrape_progress.json`                        | Committed checkpoint and pending-project state.                              |
| `scrape_data/test_*.py`                                   | Scraper and update-application tests run by the GitHub Action.               |
| `scrape_data/scraper.ipynb`                               | Optional manual scraping reference; not used by the automated workflow.      |
| `scrape_data/old/`                                        | Archived manual scripts and historical exports; not used by the pipeline.    |
| `.github/workflows/build.yml`                             | Build and Pages deployment.                                                  |
| `.github/workflows/update-data.yml`                       | Manual scrape, staged merge, backup, push, and rebuild orchestration.        |

## Data flow

1. The manual `Update scraped crowdfunding data` action selects one agency. `scraper.py
--agency <id>` resolves files/sources from the registry, validates ownership/data, and
   traverses each configured listing sequentially to its own checkpoint (null = complete scan).
   `--full-scan` ignores discovery checkpoints but skips already stored historical pages.
2. Deduplicate canonical project IDs across profiles. Keep failed/unfinished projects pending.
   Retry known pending URLs even if every listing fails. Failed discovery preserves that source's
   checkpoint and discards its incomplete results; successful sources/pending completions may publish.
   Total operational failure stages no applicable update. Partial reports remain applicable.
3. Stage database, metadata, progress, and report in a temporary directory. Reports include agency,
   source outcomes, source/registry fingerprints, and content-change flags. Scraping never directly
   changes committed data. All diagnostics stay in GitHub, not the SPA.
4. `apply_update.py --agency <id>` validates all candidates, identities, fingerprints, and semantic
   change flags before writes. Changed records create an exact database/metadata backup pair under
   `src/lib/data/old/<agency>/backup_at_<UTC>_run<id>_attempt<attempt>{,.metadata}.json`.
   Local application failures roll back owned files. `--publish` additionally requires a clean main
   checkout, stages only owned changed paths/backups, commits, and pushes without force.
   Without `--publish`, application is local and performs no Git operations.
5. Public record/metadata changes explicitly invoke `build.yml` at the pushed SHA. Progress-only
   updates do not rebuild. Dry runs upload reports/candidates without application, backups, or Git.
   Updates share repository-wide serialization. The build refuses an obsolete revision at deployment
   time; after deployment failure, rerun at current main instead of relying on another scrape.
6. On selection, `processAgencyData(records)` keeps `per === '終了'`, flattens `subject`, derives
   `totalpatrons`, `averageFund`, `period`, and `ppTotal`, and returns independent `gpMap`, `mbSet`,
   and `yrSelection`. Raw cached records are not mutated. Zero supporters display `—` for the average.
7. The notebook remains a manual reference; historical scripts under `scrape_data/old/` are not
   part of this pipeline. For manual record corrections, update the matching metadata timestamp,
   validate, and rebuild. Changing scraping code alone does not change the app's snapshot.

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
Current discovery profiles are `https://camp-fire.jp/profile/heroines/projects/post` and
`https://camp-fire.jp/profile/madsink/projects/post`, each scoped to its own agency.
The imaginate attribution link is not an additional automated discovery source.

## Commands and deployment

- Install: `bun install`; develop: `bun run dev`.
- Validate app changes: `bun test`; `bun run check`; build: `bun run build`; preview: `bun run preview`.
- Scraper tests: `python -m unittest discover -s scrape_data -p 'test_*.py' -v`.
- Local dry run: `python scrape_data/scraper.py --agency madsink --output-dir <temporary-directory>`.
- Full scan: add `--full-scan`; the GitHub Action exposes the same option as an input.
- Formatting: `bun run lint` (Prettier only), `bun run format`.
- The scraper and update scripts have a Python unittest suite. The GitHub Action runs
  it before every scrape; frontend validation uses `bun test`, `bun run check`, and `bun run build`.
- Static output goes to `build/`. Production `BASE_PATH` controls the deployment subpath;
  CI sets it to `/<repository-name>`. Development uses an empty base path.
- Automatic deployment watches `src/**`, `static/**`, and `svelte.config.js` on `main`.
  Other changes require a manual workflow run or a watched-file change.
- `vite.config.js` injects `__BUILD_DATE__`; the footer shows build date, not scrape date.
- Scraper requests are sequential, spaced by one second, limited to 30 seconds, and retried
  three times. Failed sources/projects retain retry state while valid partial stages can publish.
- Run the `Update scraped crowdfunding data` workflow manually from GitHub. `dry_run=true`
  uploads staged results without committing, while `full_scan=true` ignores discovery checkpoints.
- The production workflow uses Node 24-compatible action versions (`checkout@v6`,
  `setup-python@v6`, `upload-artifact@v6`, `upload-pages-artifact@v5`, and
  `deploy-pages@v5`). Feature-branch validation does not constitute a production deployment.
- Restore a matching agency database/metadata backup pair together, retaining its original
  `updatedAt`, commit, then run the Pages build. Restore progress from Git too if intentionally
  rewinding discovery; otherwise review/full-scan so checkpoints do not skip removed records.
  Legacy heroines backups remain under `src/lib/data/old/`; recover their verified content date
  from Git, or use `null` when unknown. Never substitute another agency's metadata/progress.
- Build recovery: `build.yml` has a manual `checkout-ref` input. Use current main (or a superseding
  revision containing the data commit); obsolete revisions are rejected before Pages deployment.

Keep Japanese UI text and existing Svelte/CSS patterns. Treat `.svelte-kit/`, `build/`,
and `node_modules/` as generated. Update this reference when architecture or data flow changes.
