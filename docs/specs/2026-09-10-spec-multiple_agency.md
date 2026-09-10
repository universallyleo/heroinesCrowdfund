# Multiple agency design specification

Date: 2026-09-10 (Asia/Tokyo)  
Feature: `multiple_agency`  
Status: `spec`  
Delivery: design documentation only; implementation requires separate user confirmation.

## 1. Purpose and scope

Allow the existing Japanese SPA to display idol crowdfunding projects belonging to different
agencies, one agency at a time. Each agency owns an independent JSON database, scraper progress,
update timestamp, and backup history. Keep the static SvelteKit/GitHub Pages architecture.

HEROINES and imaginate identify the same agency: the public-known name and company name,
respectively. Its selector label is exactly `heroines/imaginate`. Initially it remains the only
production entry. A second agency will be added when its identity, source pages, and reviewed
data are available; test fixtures can demonstrate switching without inventing a real agency.

This specification covers the selector, data/filter lifecycle, source attribution, database
freshness, scraper configuration, manual GitHub Action input, onboarding, and acceptance criteria.
It authorizes no changes to application code, JSON data, Python scripts, or workflow YAML now.
In a later implementation, finish the frontend before modifying `update-data.yml`.

Excluded: combined cross-agency tables or totals, a backend/admin website, scheduled scraping,
new crowdfunding platforms, automatic agency discovery, and persistent selection in URLs or
browser storage. Existing project columns and financial calculations remain in scope only where
they must consume the selected agency's data safely.

## 2. Current behavior and constraints

The following findings come from the repository as inspected on the design date:

- `src/lib/procData.js` imports `src/lib/data/heroinesCF.json` and creates `processedData`,
  `gpMap`, `mbSet`, and `yrSelection` once at module initialization.
- `ProjectSelector.svelte` and `GroupFilter.svelte` import those global indexes directly.
  `+page.svelte` owns a single `TableHandler`, table markup, header, and footer. Replacing
  the row array alone would leave agency-specific filter options and state behind.
- The footer's `更新` is `__BUILD_DATE__`, not a database update date. It links to both
  CAMPFIRE profiles, but automated discovery uses only the heroines projects listing.
- `scraper.py` already separates listing discovery, project parsing, merging, and staging
  into functions. Its CLI accepts database/progress paths, but the pipeline still uses a
  fixed listing and a heroines checkpoint fallback. New agencies must not inherit that fallback.
- The CAMPFIRE parser assumes supported member brackets, a title ending in `応援プロジェクト`,
  and exactly one event year in the chosen description. Shared HTML does not guarantee
  shared title or year conventions.
- The scraper stages candidates and a report; `apply_update.py` backs up, replaces, commits,
  and pushes selected files. The action explicitly rebuilds at the resulting database commit.
  Progress-only changes currently do not rebuild.
- A full scan traverses the complete listing but skips already stored projects. It is not
  a refresh of all historical records. Retain this behavior and describe it accurately.

## 3. Approach and alternatives

| Approach                                              | Benefit                                                                  | Cost                                                                             | Decision                                                  |
| ----------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | --------------------------------------------------------- |
| Registry plus separate snapshots loaded on demand     | Agency ownership is explicit; initial load avoids every agency's records | Requires a small loading/error lifecycle                                         | Use this                                                  |
| Registry plus eagerly imported separate snapshots     | Switching is synchronous and simple                                      | Every visitor downloads all agency records                                       | Acceptable for a small prototype, not the selected design |
| One merged snapshot with an agency field on every row | One import and one record collection                                     | Changes historical records and increases the chance of mixed filters and updates | Do not use                                                |

Use one JSON registry readable by both JavaScript and Python. Preserve existing heroines
database and progress paths through explicit configuration. Give new agencies conventional
directories. This avoids a data migration solely to add agency selection.

## 4. Agency registry and storage contract

### Registry

Create `src/lib/data/agencies.json`. Its initial contents will describe this single agency:

```json
{
	"schemaVersion": 1,
	"defaultAgencyId": "heroines",
	"agencies": [
		{
			"id": "heroines",
			"label": "heroines/imaginate",
			"sources": [
				{
					"label": "heroines",
					"url": "https://camp-fire.jp/profile/heroines"
				},
				{
					"label": "imaginate",
					"url": "https://camp-fire.jp/profile/imaginate"
				}
			],
			"databasePath": "src/lib/data/heroinesCF.json",
			"metadataPath": "src/lib/data/agencies/heroines/metadata.json",
			"progressPath": "scrape_data/scrape_progress.json",
			"backupRoot": "src/lib/data/old/heroines",
			"scraper": {
				"adapter": "campfire",
				"listingUrl": "https://camp-fire.jp/profile/heroines/projects"
			}
		}
	]
}
```

`id` is a permanent machine identifier, unique and matching `[a-z][a-z0-9_]*`; display names
may change independently. Array order determines selector order. `defaultAgencyId` must
resolve to an entry. All registered entries appear in the UI and are eligible for the action;
there is no separate hidden/enabled state in this feature.

`sources` are public attribution links, not an instruction to crawl those pages. `listingUrl`
is the single discovery entry point for that agency. Keep both existing attribution links
and the existing single listing. Multiple listings within one agency would require a separate
design for discovery/checkpoints; do not silently infer them from attribution links.

Paths use forward slashes and are relative to the repository root. Both runtimes must resolve
the same entry. Validate unique IDs and target paths, known adapter IDs, nonempty labels/source
lists, HTTPS URLs, and the supported schema version. Resolve filesystem paths and reject paths
outside their allowed data/progress/backup directories or paths shared by different agencies.
The registry contains public configuration only, with no credentials or executable commands.

### File ownership

| File        | Existing agency                                | New agency with ID `<id>`                  |
| ----------- | ---------------------------------------------- | ------------------------------------------ |
| Records     | `src/lib/data/heroinesCF.json`                 | `src/lib/data/agencies/<id>/projects.json` |
| Metadata    | `src/lib/data/agencies/heroines/metadata.json` | `src/lib/data/agencies/<id>/metadata.json` |
| Progress    | `scrape_data/scrape_progress.json`             | `scrape_data/progress/<id>.json`           |
| New backups | `src/lib/data/old/heroines/`                   | `src/lib/data/old/<id>/`                   |

Retain historical files under `src/lib/data/old/` where they are. Record that those legacy
unscoped backups belong to heroines. Never include backups, progress files, or archived exports
in frontend dataset imports.

Records remain the existing top-level JSON array, with the raw schema documented in `AGENTS.md`.
Do not add agency IDs to every record or wrap the array in a metadata object. Validate canonical
project URLs for duplicates within an agency; numeric funding/supporter/reward fields, dates,
subject fields, and event year retain their meanings. The same URL in two agencies should be
flagged for ownership review, without silently moving or deleting either record.

### Metadata and freshness

Each metadata sidecar has `schemaVersion: 1`, its matching `agencyId`, and `updatedAt` as a UTC
ISO 8601 timestamp or `null`. For the first heroines sidecar use:

```json
{
	"schemaVersion": 1,
	"agencyId": "heroines",
	"updatedAt": null
}
```

`updatedAt` means the time the current snapshot's record content was last updated. For automated
updates, record the successful staging completion time that produced the applied snapshot.
Publish it only when that snapshot is committed and deployed. It does not mean all source pages
were recently checked or all failed projects were resolved.

Do not invent historical freshness from the build date, filesystem modification time, latest
project date, or metadata creation date. Bootstrap with `null`; a future record-changing update
sets a known timestamp. Missing/malformed sidecars fail release validation; only an explicit
`null` means a valid snapshot whose historical update time is unknown.

| Outcome                                                 | Published timestamp                                         | Repository writes                                             | Rebuild            |
| ------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------- | ------------------ |
| Records changed and application/push succeeded          | Advance for that agency only                                | Records, metadata, progress if changed, backups               | Yes, at pushed SHA |
| Some projects failed, others produced new valid records | Advance for published records; failures remain in progress  | Same as above                                                 | Yes                |
| Only checkpoint or pending state changed                | Preserve                                                    | Selected agency's progress only                               | No                 |
| No changes                                              | Preserve                                                    | None                                                          | No                 |
| Fatal discovery/validation failure                      | Preserve                                                    | No applied files                                              | No                 |
| Dry run                                                 | Preserve deployed value                                     | Temporary candidates/report only                              | No                 |
| Failed apply or rejected push                           | Preserve deployed value                                     | No published update; failed local work is discarded/recovered | No                 |
| Manual record correction                                | Set a known correction time in the same commit              | Selected records and metadata, with backup                    | Yes                |
| Verified correction of metadata alone                   | Correct explicitly, without claiming records were rescraped | Selected metadata                                             | Yes                |

Keep scrape attempt times and errors in the run report/progress, outside the public freshness
label. A date-only rebuild must never refresh every agency's `updatedAt`.

## 5. Frontend behavior and Japanese copy

### Layout

Use the existing CSS variables, panels, and desktop/mobile breakpoints. The header area spans
both columns and contains the site title followed by the agency selector and its information.
Below it, keep filters beside the table on desktop and above the table on narrow screens.
Allow long proper names and source links to wrap without widening the viewport.

The visible arrangement is:

```text
アイドル クラファ記録

事務所  [ heroines/imaginate  ▾ ]
データソース：CAMPFIRE  heroines ／ imaginate
データ最終更新：更新日不明

[ 絞り込む ]    [ 選択した事務所のプロジェクト一覧 ]

サイト更新：2026/09/10
[ ソースコードなどの共通リンク ]
```

This is a layout illustration, not seeded production data. The two source names are links.
Show the dropdown even while it has only one option. Use a native labelled `<select>` with
`事務所`; keep `heroines/imaginate` exactly as written. All surrounding UI, accessible labels,
status messages, and third-party table strings are Japanese. Proper names such as CAMPFIRE,
GitHub, and X retain their names.

Move agency source attribution out of the footer into this header area. Display known dates as
`データ最終更新：YYYY/MM/DD HH:mm（日本時間）`, using `ja-JP` and `Asia/Tokyo` regardless of
the viewer's timezone. Display `データ最終更新：更新日不明` for `null`.

Keep the existing build date in the footer, relabelled `サイト更新：YYYY/MM/DD`, to distinguish
site publication from data freshness; format the full `__BUILD_DATE__` timestamp in Japan time.
Keep shared repository/social/related-site links there. Set `src/app.html` to `lang="ja"`.
Change the site heading and static description/Open Graph/structured-data site name to an
agency-neutral Japanese title. The client document title may be
`heroines/imaginate | クラファ記録` for the selected agency. Do not promise agency-specific
social previews from this client-rendered static shell.

### Selection and state reset

On a fresh page load select `heroines`, the registry default. Changing agencies takes effect
immediately and does not require `条件を適用` or a full browser reload. The selector remains
available throughout loading and errors.

For every actual change of agency, including returning to a previously viewed agency:

1. Update selected agency identity, sources, metadata, and document title together. Remove the
   previous agency's table and filter panel while loading the newly selected snapshot.
2. Load the selected snapshot from this deployment's bundled assets.
3. Mount a new table/filter component instance and derive fresh rows/indexes. Reset draft inputs and applied filters, group
   selections, member options, year options, funding bounds, sorting, page size, pagination,
   row selections, and any row-local UI state.
4. Start with all groups, `全員`, all event years, and no applied funding restriction. Use page 1,
   explicitly 20 rows per page, and snapshot row order with no active column sort. Keep the
   existing page-size options `[5, 10, 20, 50, 100, 200, 300]`.

Compute funding slider bounds from this agency's completed rows so old heroines limits cannot
hide another agency's data. In thousand-yen units use `floor(min(total) / 1000)` and
`ceil(max(total) / 1000)`, with step 1; if equal, extend the upper bound by 1. Initialize and reset
the sliders to those bounds. `リセット` restores these same initial filter values and clears
applied filters. Keep explicit `条件を適用` semantics for ordinary filter edits; reset acts
immediately and returns to page 1, preserving the current sort and page size. Applying any filter
also returns to page 1. If the minimum exceeds the maximum, keep the applied filters unchanged
and show `最小額は最大額以下にしてください。` until the draft range is corrected.

Selecting the already active option is a no-op. Do not retain state per agency between visits.
Use snapshot data only; selection never starts scraping or contacts CAMPFIRE.

### Loading, empty data, and errors

| Condition                              | Behavior/copy                                                                                   |
| -------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Snapshot loading                       | `データを読み込んでいます…`; no previous-agency rows or filter controls                         |
| Valid agency with no completed records | `終了したプロジェクトはありません。`; zero count and disabled data-dependent filters/pagination |
| Filters match no records               | `条件に一致するプロジェクトはありません。`; keep filter controls usable                         |
| Dataset asset cannot load              | `データを読み込めませんでした。`; provide `再試行` and `ページを再読み込み`                     |
| Invalid registry/default               | Japanese page-level data error; do not silently display an arbitrary agency                     |

Retry loads only the currently selected agency. A full reload is a user action useful when an
older open page references chunks removed by a newer deployment. If selection changes A → B → C,
an older request resolving last must never replace C; use a monotonically increasing request
identifier and ignore stale results/errors. Failed loads are not cached as successful results.

Keep keyboard focus on the selector after changes. Announce loading, completion, and errors in
a Japanese live region; mark the results region busy during loading. Use visible focus styles
and associated input labels. Translate existing `Search...`, `Filter`, `No entries found`, and
the `Source Code` image alternative wherever used by the delivered UI.

## 6. Frontend module boundaries

| Module                              | Responsibility/interface                                                                                                                                     |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| New `src/lib/agencies.js`           | Read/validate registry and metadata; expose ordered agency entries and `loadAgencyData(agencyId)` returning `Promise<{ records, metadata }>` for that agency |
| `src/lib/procData.js`               | Export `processAgencyData(records)` returning fresh `{ processedData, gpMap, mbSet, yrSelection }`; keep shared money/date helpers                           |
| New `src/lib/AgencySelector.svelte` | Labelled dropdown plus selected agency's source links and freshness; receives entries, selected ID, and change handler                                       |
| New `src/lib/AgencyProjects.svelte` | Own one fresh processed dataset, `TableHandler`, existing table/cell layout, filter subtree, and table DOM initialization                                    |
| `src/lib/ProjectSelector.svelte`    | Receive `table`, `gpMap`, `mbSet`, and `yrSelection` as props; own this instance's draft/applied filter controls                                             |
| `src/lib/GroupFilter.svelte`        | Receive group counts/index through props; stop importing agency data globally                                                                                |
| `src/routes/+page.svelte`           | Own selected ID and loading/error lifecycle; coordinate header, keyed results component, metadata, and shared footer                                         |
| `src/app.html`                      | Declare Japanese as the page language with `lang="ja"`                                                                                                       |

The processor must not mutate imported records or reuse Maps/Sets between calls. Continue to
include only `per === '終了'`, preserve group/member splitting and monetary meanings, and scope
counts/indexes to completed rows from the selected agency. Render zero-supporter averages as
`—` rather than Infinity/NaN; empty datasets must not produce invalid numeric bounds.

Use an agency-keyed Svelte block around `AgencyProjects` so the `TableHandler`, filters, and
cell state share one lifecycle. Move the existing table `onMount` logic with its DOM rather than
leaving it in the persistent parent. Key blocks recreate their contents when the key changes.
See [Svelte key blocks](https://svelte.dev/docs/svelte/key).

Load metadata eagerly because it is small; load project arrays on demand. Use literal Vite glob
patterns restricted to `./data/heroinesCF.json`, `./data/agencies/*/projects.json`, and, separately,
`./data/agencies/*/metadata.json`, relative to `src/lib/agencies.js`. Strip the registry paths'
`src/lib/` prefix and prepend `./` to obtain those known loader keys; require each registered path to resolve.
Do not use an unrestricted recursive JSON glob or a runtime-composed import path. Vite's default
glob imports produce lazy chunks; see [Vite glob imports](https://vite.dev/guide/features.html#glob-import).

Cache raw loaded arrays if useful, but reconstruct processed state on each mount. Use bundled
imports with the existing production `BASE_PATH`; add no runtime API and no root-relative data
fetch that would break the Pages subpath. Validate registry/file consistency before a release.

## 7. Scraper and publication design

### Configuration and parser boundary

Add `scrape_data/agency_config.py` to resolve and validate the shared registry. Both scraper and
apply entry points accept `--agency <id>`, defaulting to the registry default for compatibility.
The action supplies it explicitly. The scripts resolve their database, metadata, progress,
backup root, listing URL, and adapter from the same entry.

Retain explicit path overrides only for local/test use; defaults come from the selected agency,
and overrides must not target another registered agency's files. The production action passes
no independently editable file paths. Unknown IDs/adapters fail before network access or writes.

Separate shared orchestration from page parsing. Extract current CAMPFIRE parsing to
`scrape_data/adapters/campfire.py` when implementing this boundary. The shared pipeline owns
HTTP spacing/retries, pending retries, canonical deduplication, validation, staging, and reports.
The adapter consumes listing/project HTML and returns listing summaries/next-page URL and the
existing normalized project record. It never writes databases or invokes Git.

Start with only the `campfire` adapter. Onboard another CAMPFIRE agency with it only after fixture
checks confirm markup, title/member/type parsing, and event-year extraction. If a different
parser is needed, add a named script/module behind the same contract. Use an explicit allowlist
mapping adapter IDs to modules, not a command string from the registry. A new parser using the
same CLI/staged schema needs no agency-specific workflow branch. New dependencies, credentials,
platform assumptions, or a changed staged contract require reviewing the workflow too.

### Independent progress and discovery

Keep progress fields `checkpointUrl` and `pending`. Add `schemaVersion: 1` and `agencyId` when
the agency-aware pipeline is implemented. Preserve all current heroines checkpoint and pending
content; do not reset it to the original `956928` checkpoint or a date copied from this spec.

New agencies start from a committed empty array, `updatedAt: null`, and progress with
`checkpointUrl: null` and `pending: {}`. Null means scan to the listing end on first run. Missing
configured database/progress files are setup errors, not an invitation to use heroines defaults.
After successful discovery, retain the existing policy of advancing to the newest discovered
stored project; keep null if none qualifies. An absent old checkpoint causes a complete traversal
and a report warning. `--full-scan` ignores only the selected agency's checkpoint.

Retry unfinished/failed projects from that agency even if older than its listing checkpoint.
Fatal listing failures stop all publication for the selected agency; individual project failures
remain pending and allow valid successes to publish. Keep sequential requests, one-second spacing,
30-second timeout, and three attempts. Detect pagination loops. An empty/unrecognized listing
must not silently pass as a complete successful scan without adapter-supported empty-page evidence.

### Staging and application

Stage `candidate_database.json`, `candidate_metadata.json`, `candidate_progress.json`, and
`run_report.json` under a directory containing agency ID, workflow run ID, and attempt. Extend
the report with `schemaVersion`, `agencyId`, adapter/listing identity, source-file SHA-256
fingerprints, `metadataChanged`, and the existing change/failure fields. Fingerprints cover the
input database, metadata, and progress so stale stages can be rejected before replacement.

`databaseChanged` is based on changed record content, not formatting, timestamps, or merely
having scanned pages. Normal automated `metadataChanged` follows `databaseChanged`; prepare a
new `updatedAt` only for a changed snapshot. Full candidate metadata can still be staged unchanged.

Before any backup/replacement, the apply step validates the selected agency against the report,
all required candidate files and schemas, record integrity, metadata/progress agency IDs, source
fingerprints, and reported change flags. Reject a stage for another agency, missing candidates,
fatal reports, or changed source files. Do not trust booleans alone to authorize a replacement.

For a changed database, save the exact previous records as
`<backupRoot>/backup_at_<UTC>_run<id>_attempt<attempt>.json` and its sidecar as the same stem plus
`.metadata.json`. Preserve both before replacing either. Apply only the selected agency's changed
files; commit records, metadata, changed progress, and backups together. Use temporary replacements
and rollback on a local failure so partial application is not treated as success. Stage only the
explicit owned paths and refuse a dirty/staged production checkout with unrelated changes.

The externally visible transaction is the successful Git commit/push followed by deployment of
that exact SHA. If `main` advances meanwhile, a normal non-fast-forward rejection stops the run:
never force-push or blindly reuse stale candidates after merging. Rerun against current `main`.

Include the agency ID in commit messages and report artifacts. Preserve existing outputs
`database_changed`, `progress_changed`, and `commit_sha`; add `metadata_changed` and
`public_data_changed` (`database_changed OR metadata_changed`). Rebuild only after a successful
push with `public_data_changed=true` and a nonempty commit SHA. A rejected push never supplies a
successful publication result.

## 8. GitHub Actions design, deferred until frontend implementation

Add a required `agency` input to `update-data.yml` with `type: choice`, default `heroines`, and
initial options containing only `heroines`. A suitable Japanese description is
`更新する事務所（heroines = heroines/imaginate）`. Preserve `dry_run` and `full_scan` as booleans.
One invocation selects one agency; there is no `all` option or parallel matrix.

GitHub supports a single-choice manual input whose result is a string. Maintain its declared
options alongside registry IDs; do not depend on a job reading JSON to populate the dispatch
form. Treat this synchronization as an onboarding/release check. See
[GitHub manual workflow inputs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onworkflow_dispatchinputs).

After checkout of current `main` and tests, pass the input through an environment variable and
quoted `--agency` argument to both staging and application. Resolve paths inside Python. Use the
agency/run/attempt in the output directory and artifact name; upload available reports on failure.
Dry runs execute discovery/parsing/staging but skip apply, backups, commits, pushes, and rebuilds.

Keep one repository-wide `scrape-data` concurrency group with `cancel-in-progress: false`, because
all agencies write the same `main` branch. An agency-specific group would permit competing pushes.
Retain the current bounded pending behavior: repeated dispatches may replace a pending run, so
admins must inspect canceled runs rather than assume an unlimited queue. See
[GitHub workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).

Continue explicitly calling `build.yml` at the pushed `commit_sha`, changing its caller condition
to `public_data_changed`. A push made with `GITHUB_TOKEN` does not itself start the push-triggered
build; see [GitHub workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).
The reusable build already accepts a checkout ref and need not accept an agency: each deployment
contains the registry and all committed agency snapshots. Registry/metadata live under `src/**`,
so ordinary manual commits are covered by the existing watched path.

## 9. Future delivery order and agency onboarding

All steps below are future work after implementation confirmation, not work performed by this spec.

1. Add registry/metadata and isolated frontend processing/loading/components. Preserve the heroines
   database and checkpoint paths and all record contents. Prove switching with synthetic test data.
   Complete frontend checks and visual acceptance before editing the update workflow.
2. Implement configuration resolution, adapter boundary, per-agency progress, metadata staging,
   backups, and apply validation. Upgrade existing progress without losing checkpoint/pending data.
   Validate the new CLI in temporary directories; do not run publication against the repository yet.
3. Update `update-data.yml` inputs, arguments, artifact names, and rebuild condition; retain current
   action versions and reusable build. Review frontend and pipeline as one release before enabling
   real agency updates. Avoid a deployed intermediate state where the old action can change records
   while the new frontend displays stale metadata.
4. Run a GitHub dry run for heroines, review its report, then perform an authorized normal update.
   Verify selected files, matching backup/metadata, pushed SHA, and the deployed timestamp/records.
   Update current-architecture sections of `AGENTS.md` and `README.md` after implementation.

To add a real new agency after that release:

1. Choose its ID, official proper-name label, public attribution URLs, and single discovery listing.
2. Test representative finished, unfinished, and unusual/joint-member project pages with the
   selected adapter; add an adapter if necessary and review its workflow requirements.
3. Create its records/metadata/progress files with the initial values above (or reviewed existing
   records and honest metadata), then add its registry entry and workflow choice in one change.
4. Run registry/file/choice consistency checks and an agency-selected dry run. Review duplicates,
   subject parsing, numbers, event years, and pending failures. Confirm heroines files are unchanged.
5. Publish the configuration and reviewed initial data through the normal release, then run its
   agency-selected update. Until populated, an empty registered agency shows the specified empty state.

No Svelte component change should be necessary when adding a compatible CAMPFIRE agency this way.

For rollback, restore a matching agency database/metadata backup pair and rebuild at the restore
commit; keep the restored snapshot's original `updatedAt`. When intentionally rewinding scraping
state, restore progress from the corresponding earlier Git commit too. For a legacy heroines
backup without metadata, use `updatedAt: null`. Review or full-scan if the retained checkpoint
could skip records removed by restoration. Never restore another agency's files.

## 10. Acceptance and validation

### Frontend

- Default shows exactly `heroines/imaginate`, existing records/columns, both attribution links,
  and truthful freshness adjacent to the selector. Generic site branding and all UI copy are Japanese.
- With two synthetic agencies having disjoint groups/members/years/funding ranges, A → B → A
  recreates rows, all filter indexes/counts, draft/applied controls, sort/page state, and row state.
  Each agency's first display starts with all completed rows and 20 rows per page. Filter reset
  restores all completed rows on page 1 while preserving the chosen sort/page size.
- Applying and resetting filters never alters raw arrays or another agency's processor output.
  Zero supporters, empty snapshots, and no-match filters follow the specified numeric/empty behavior.
- A delayed or failed earlier import cannot overwrite the current selection; retry and explicit
  page reload work. Unknown/malformed configuration fails visibly or at release validation.
- At desktop and 375px widths, selector/sources/date fit without page overflow, existing table
  scrolling works, and keyboard focus/announcements remain usable.
- A production-subpath build loads the default and second fixture agency without CAMPFIRE/API
  requests. Backup/progress/archive JSON files are excluded from bundled data loaders.

### Scraper, apply, and workflow

- Tests cover agency resolution, unknown IDs/adapters, duplicate/colliding paths, missing files,
  metadata/progress ID mismatch, and workflow-choice/registry consistency.
- A new null checkpoint discovers the full selected listing without using heroines' checkpoint;
  existing heroines progress survives the upgrade; pending retries remain scoped to their agency.
- New-agency fixture pages prove parser compatibility or exercise a separate adapter. Listing
  failure blocks publication; partial project failure preserves pending entries and valid successes.
- A normal B update changes only B's records/metadata/progress/backups. Hash A's files before/after
  to prove isolation. Semantic no-op, progress-only, failure, and dry-run cases follow the outcome table.
- Tests reject stale source fingerprints, wrong-agency stages, malformed/missing candidates, and
  inconsistent change flags before any replacement. Failure during apply does not commit partial data.
- Backup records and metadata match the previous files exactly. A rejected push causes no rebuild;
  successful public changes rebuild at the returned SHA. Metadata-only correction also rebuilds.
- A fresh site build without record changes preserves all agency timestamps. The deployed site
  associates its timestamp and source links with the same agency as its displayed records.

During future implementation run `bun run check`, `bun run build`,
`python -m unittest discover -s scrape_data -p 'test_*.py' -v`, and formatting for changed files.
Add processor/isolation tests in `src/lib/procData.test.js` using Bun, add configuration tests in
`scrape_data/test_agency_config.py`, and extend `test_scraper.py`/`test_apply_update.py` with Python
fixtures for pipeline behavior. Use browser interaction for the remount/race/layout cases.
Use temporary fixture databases for multi-agency validation, not fabricated production records.

For this documentation-only task, validate Markdown formatting, internal consistency, coverage
of the requested behavior, and the diff boundary. Application tests, live scrapes, and GitHub
workflow runs are not evidence of spec completion and are not required now.

## 11. Document lifecycle

Keep this document in `docs/specs/` with the convention `YYYY-MM-DD-<status>-<feature>.md`.
The creation date and `multiple_agency` feature name stay fixed. Rename `design` to `spec` after
the design write-up is finalized; rename `spec` to `implemented` only after the confirmed feature
and required validation are complete. Update this header and links in `AGENTS.md` on each rename.
Finalizing a design does not authorize implementation or imply that the proposed files exist.
