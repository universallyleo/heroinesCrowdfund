# Multiple agency design specification

Date: 2026-09-10 (Asia/Tokyo)  
Feature: `multiple_agency`  
Status: `implemented`

Delivery: implementation authorized on 2026-11-15 for `codex/multiple-agency`, including MAD’S iNK onboarding. Production merge/deployment is outside this delivery.

Last revised: 2026-11-15 (Asia/Tokyo), after implementation, local validation, and confirmed MAD’S iNK membership rules.

## 1. Purpose and scope

Allow the existing Japanese SPA to display idol crowdfunding projects belonging to different
agencies, one agency at a time. Each agency owns an independent JSON database, scraper progress,
update timestamp, and backup history. Keep the static SvelteKit/GitHub Pages architecture.

HEROINES and imaginate identify the same agency: the public-known name and company name,
respectively. Its selector label is exactly `heroines/imaginate`. The implemented registry also
contains `madsink`, labelled `MAD’S iNK`, with a separate database initially populated from
`https://camp-fire.jp/profile/madsink/projects/post`.

This specification covers the selector, data/filter lifecycle, source attribution, database
freshness, scraper configuration, manual GitHub Action input, onboarding, and acceptance criteria.
The user's 2026-11-15 implementation request supersedes the earlier documentation-only scope.
Frontend implementation and browser checks preceded changes to `update-data.yml`.

Excluded: combined cross-agency tables or totals, a backend/admin website, scheduled scraping,
new crowdfunding platforms, automatic agency discovery, and persistent selection in URLs or
browser storage. Existing project columns and financial calculations remain in scope only where
they must consume the selected agency's data safely.

## 2. Pre-implementation behavior and constraints

These historical integration constraints guided implementation. `AGENTS.md` now describes the resulting architecture:

- `src/lib/procData.js` imports `src/lib/data/heroinesCF.json` and creates `processedData`,
  `gpMap`, `mbSet`, and `yrSelection` once at module initialization.
- `ProjectSelector.svelte` and `GroupFilter.svelte` import those global indexes directly.
  `+page.svelte` owns a single `TableHandler`, table markup, header, and footer. Replacing
  the row array alone would leave agency-specific filter options and state behind.
- The footer's `更新` is `__BUILD_DATE__`, not a database update date. It links to both
  CAMPFIRE profiles, but automated discovery uses only
  `https://camp-fire.jp/profile/heroines/projects/post`.
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

`src/lib/data/agencies.json` contains both registered agencies (the file is authoritative):

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
					"label": "CAMPFIRE（heroines）",
					"url": "https://camp-fire.jp/profile/heroines"
				},
				{
					"label": "CAMPFIRE（imaginate）",
					"url": "https://camp-fire.jp/profile/imaginate"
				}
			],
			"databasePath": "src/lib/data/heroinesCF.json",
			"metadataPath": "src/lib/data/agencies/heroines/metadata.json",
			"progressPath": "scrape_data/scrape_progress.json",
			"backupRoot": "src/lib/data/old/heroines",
			"scraper": {
				"id": "campfire",
				"discoverySources": [
					{
						"id": "heroines",
						"listingUrl": "https://camp-fire.jp/profile/heroines/projects/post"
					}
				]
			}
		},
		{
			"id": "madsink",
			"label": "MAD’S iNK",
			"sources": [
				{
					"label": "CAMPFIRE（MAD’S iNK）",
					"url": "https://camp-fire.jp/profile/madsink"
				},
				{
					"label": "Jpop Wiki（所属情報）",
					"url": "https://jpop.fandom.com/wiki/MAD%27S_iNK"
				}
			],
			"databasePath": "src/lib/data/agencies/madsink/projects.json",
			"metadataPath": "src/lib/data/agencies/madsink/metadata.json",
			"progressPath": "scrape_data/progress/madsink.json",
			"backupRoot": "src/lib/data/old/madsink",
			"scraper": {
				"id": "campfire_madsink",
				"discoverySources": [
					{
						"id": "madsink",
						"listingUrl": "https://camp-fire.jp/profile/madsink/projects/post"
					}
				]
			}
		}
	]
}
```

`id` is a permanent machine identifier, unique and matching `[a-z][a-z0-9_]*`; display names
may change independently. Array order determines selector order. `defaultAgencyId` must
resolve to an entry. All registered entries appear in the UI and are eligible for the action;
there is no separate hidden/enabled state in this feature.

`sources` are public attribution links. `scraper.discoverySources` is a nonempty, ordered list
of independently checkpointed discovery profiles. Each entry has an agency-local stable `id`
and `listingUrl`. Support multiple profiles contributing to the same agency database, but
configure the heroines and madsink listings under their respective agencies. Keep both heroines attribution links;
do not infer an imaginate discovery source from its public link.

Paths use forward slashes and are relative to the repository root. Both runtimes must resolve
the same entry. Validate unique agency/source IDs and target paths, known scraper IDs, nonempty labels/source
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
ISO 8601 timestamp or `null`. The shape below illustrates an unknown historical timestamp;
it does not require heroines to discard a date available from verified Git history:

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

Bootstrap an existing snapshot from the latest verified Git commit that changed its record
content, excluding formatting-only commits. Determine that commit at implementation time;
do not hardcode the September timestamp discussed during planning if the database has since
changed. Use `null` only when reliable history is unavailable. Do not infer freshness from the
site build, filesystem modification time, latest project date, or metadata creation date.
Missing/malformed sidecars fail release validation; an explicit `null` is a valid unknown date.

| Outcome                                                                         | Published timestamp                                         | Repository writes                                                                   | Rebuild            |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------ |
| Records changed and application/push succeeded                                  | Advance for that agency only                                | Records, metadata, progress if changed, backups                                     | Yes, at pushed SHA |
| Some projects failed, others produced new valid records                         | Advance for published records; failures remain in progress  | Same as above                                                                       | Yes                |
| Only checkpoint or pending state changed                                        | Preserve                                                    | Selected agency's progress only                                                     | No                 |
| No changes                                                                      | Preserve                                                    | None                                                                                | No                 |
| Some or all listings fail, but pending retries yield valid records              | Advance for published records                               | Records/metadata, applicable progress, backups; failed-source checkpoints unchanged | Yes                |
| All discovery and pending operations fail, or configuration/validation is fatal | Preserve                                                    | No applied files; report only                                                       | No                 |
| Dry run                                                                         | Preserve deployed value                                     | Temporary candidates/report only                                                    | No                 |
| Failed apply or rejected push                                                   | Preserve deployed value                                     | No published update; failed local work is discarded/recovered                       | No                 |
| Manual record correction                                                        | Set a known correction time in the same commit              | Selected records and metadata, with backup                                          | Yes                |
| Verified correction of metadata alone                                           | Correct explicitly, without claiming records were rescraped | Selected metadata                                                                   | Yes                |

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
heroines/imaginate クラファ記録

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
Change the visible heading to `<agency label> クラファ記録` whenever selection changes.
Use `<agency label> | クラファ記録` as the client document title. Keep static descriptions,
Open Graph site metadata, and the structured-data site name agency-neutral; do not promise
agency-specific social previews from this client-rendered static shell.

### Selection and remembered settings

On a fresh page load select `heroines`, the registry default. Changing agencies takes effect
immediately and does not require `条件を適用` or a full browser reload. The selector remains
available throughout loading and errors.

Keep an in-memory settings entry per visited agency outside the component being recreated.
Each entry contains draft filter values, applied filter values, sort column/direction, page size,
and page number. Keep draft and applied filters separate so returning to an agency never applies
previously unapplied edits. This memory lasts only for the current page session; a full reload
resets it and selects heroines again. Scroll position is not persisted.

For every actual change of agency, including returning to a previously viewed agency:

1. Update selected agency identity, sources, metadata, and document title together. Remove the
   previous agency's table and filter panel while loading the newly selected snapshot.
2. Load the selected snapshot from this deployment's bundled assets.
3. Mount a new table/filter component and derive fresh rows/indexes. Restore the selected
   agency's applied filters, sort, page size, and page number, then display its saved draft
   inputs without applying them. Persist later setting changes back to that agency's entry.
4. If this is the agency's first visit, initialize all groups, `全員`, all event years, and no
   applied funding restriction. Use page 1, explicitly 20 rows per page, and snapshot row order
   with no active column sort. Keep page-size options `[5, 10, 20, 50, 100, 200, 300]`.

Restore the saved page only after filters/sorting/page size have been restored, since table
operations can reset pagination. Clamp it to a valid page if necessary. Do not share a live
`TableHandler` or filter builders between agencies, and do not overwrite a saved entry with
initialization defaults while restoring it.

Compute funding slider bounds from this agency's completed rows so old heroines limits cannot
hide another agency's data. In thousand-yen units use `floor(min(total) / 1000)` and
`ceil(max(total) / 1000)`, with step 1; if equal, extend the upper bound by 1. Initialize and reset
the sliders to those bounds. `リセット` restores these same initial filter values and clears
applied filters. Keep explicit `条件を適用` semantics for ordinary filter edits; reset acts
immediately and returns to page 1, preserving the current sort and page size. Applying any filter
also returns to page 1. If the minimum exceeds the maximum, keep the applied filters unchanged
and show `最小額は最大額以下にしてください。` until the draft range is corrected.

Selecting the already active option is a no-op. Reset changes only the active agency's settings.
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
| `src/lib/ProjectSelector.svelte`    | Receive the table, agency-specific indexes, and saved draft/applied values; restore and report filter changes separately                                     |
| `src/lib/GroupFilter.svelte`        | Receive group counts/index through props; stop importing agency data globally                                                                                |
| `src/routes/+page.svelte`           | Own selected ID, the per-agency settings map, and loading/error lifecycle; coordinate header, keyed results, metadata, and footer                            |
| `src/lib/ThSortCustom.svelte`       | Restore the saved active column/direction through the sort builder and report user sort changes to the active agency's settings                              |
| `src/app.html`                      | Declare Japanese as the page language with `lang="ja"`                                                                                                       |

The processor must not mutate imported records or reuse Maps/Sets between calls. Continue to
include only `per === '終了'`, preserve group/member splitting and monetary meanings, and scope
counts/indexes to completed rows from the selected agency. Render zero-supporter averages as
`—` rather than Infinity/NaN; empty datasets must not produce invalid numeric bounds.

Use an agency-keyed Svelte block around `AgencyProjects` so the `TableHandler`, filters, and
cell state share one lifecycle. Move the existing table `onMount` logic with its DOM rather than
leaving it in the persistent parent. Key blocks recreate their contents when the key changes.
Pass saved settings and update callbacks through this boundary; unmounting must not discard
the page-owned settings entry. Restore state through the table's supported public methods.
See [Svelte key blocks](https://svelte.dev/docs/svelte/key).

Load metadata eagerly because it is small; load project arrays on demand. Use literal Vite glob
patterns restricted to `./data/heroinesCF.json`, `./data/agencies/*/projects.json`, and, separately,
`./data/agencies/*/metadata.json`, relative to `src/lib/agencies.js`. Strip the registry paths'
`src/lib/` prefix and prepend `./` to obtain those known loader keys; require each registered path to resolve.
Do not use an unrestricted recursive JSON glob or a runtime-composed import path. Vite's default
glob imports produce lazy chunks; see [Vite glob imports](https://vite.dev/guide/features.html#glob-import).

Cache successfully loaded raw arrays, but reconstruct processed state on each mount. Use bundled
imports with the existing production `BASE_PATH`; add no runtime API and no root-relative data
fetch that would break the Pages subpath. Validate registry/file consistency before a release.

## 7. Scraper and publication design

### Configuration and parser boundary

Add `scrape_data/agency_config.py` to resolve and validate the shared registry. Both scraper and
apply entry points accept `--agency <id>`, defaulting to the registry default for compatibility.
The action supplies it explicitly. The scripts resolve their database, metadata, progress,
backup root, discovery sources, and scraper identifier from the same entry.

Both CLIs resolve paths exclusively through the registry. Local/tests select an isolated `--repo-root`;
individual path overrides were removed to avoid mixing agencies. `apply_update.py` applies locally by
default; `--publish` explicitly enables Git operations and requires a clean main checkout. The production action passes
no independently editable file paths. Unknown agency/scraper IDs fail before network access or writes.

Keep the current CAMPFIRE parsing functions and introduce only a small extension point, identified
by `scraper.id`. Do not extract the working shared parser into a plugin framework. A dedicated MAD’S iNK
details module is necessary because its titles omit the group and encode the event/member/year differently. The shared pipeline owns HTTP spacing/retries, per-source discovery/checkpoints,
pending retries, deduplication, validation, staging, and reports.

The parser contract consumes listing HTML plus its URL and returns project summaries plus the
next-page URL; project HTML plus its canonical URL and listing description produces the existing
normalized record or the existing unfinished/parse-error outcome. Parsers do not write databases
or invoke Git. `campfire` retains the existing heroines rules. MAD’S iNK uses `campfire_madsink`,
which provides title/year details to the shared financial HTML parser.

Before reusing it for another agency, fixture checks must confirm markup, title/member/type
parsing, and event-year extraction. Add a different scraper module behind the same contract only
when needed, selected by a known identifier rather than an executable command from the registry.
Keeping the CLI/staged contract avoids agency-specific workflow branches; new dependencies,
credentials, platform assumptions, or changed output still require reviewing the workflow.

### MAD’S iNK membership and parsing amendment

The initial scrape yielded 27 completed records and one unfinished project (`991831`), with no
parse failures. Subject details are extracted from supported title variants; event years must agree
across the title, explicit story schedule, and available description. The last-live project is
labelled `生誕・卒業公演`, consistent with its CAMPFIRE description. Unknown titles/members and
conflicting years remain pending for review. Financial and reward extraction stays shared.

Per explicit user decisions on 2026-11-15:

- Use [Jpop Wiki](https://jpop.fandom.com/wiki/MAD%27S_iNK) as the group reference. Its link is
  included in public attribution; the reviewed mapping file lists the individual group references.
- Use latest known groups for every project, including historical events; not event-time membership.
- Preserve the existing heroines `subject.group` slash format: main group first, then collaboration
  groups. `ちちゃめど` and `まっずぷりんす` are collaboration groups.
- The user confirmed とら = 猿馬虎, れむ = 朽壊レム, とむら = 悼ミ弔,
  よる = 暗空夜, まなせ = 真鬼マナセ, and MADMED as the latest known group for
  那月邪夢, おなかぺこ, 天噛ミ妖メ, 架空使てんる where no newer group is listed.
- Confirm doubtful membership/alias choices with the user. Never infer a group silently.

Maintain `scrape_data/madsink_members.json` explicitly. A valid MAD’S iNK stage reapplies its reviewed
mapping to stored records, without re-fetching historical pages; changed group content advances
metadata. Stage/apply also fingerprint this mapping to reject a stale mapping revision.

### Independent progress and discovery

Progress has `schemaVersion: 1`, `agencyId`, `sources` keyed by discovery-source ID, and one
agency-wide `pending` map keyed by canonical project ID. Each source stores its `listingUrl`
and `checkpointUrl`; pending entries retain their existing fields and originating `sourceIds`.
Migrate the existing heroines top-level checkpoint into `sources.heroines` and retain every
pending entry, associating it with that source. Do not reset to the original `956928` checkpoint.

New agencies start with an empty record array, `updatedAt: null`,
empty pending state, and null checkpoints for their configured sources. A newly added discovery
source also starts with a null checkpoint. Null means traverse the listing to its end. Missing
configured database/progress files are setup errors, never a fallback to heroines' files.
Do not reuse a checkpoint when a source's configured listing URL changes; explicitly initialize
the changed source with a null checkpoint while retaining known pending projects.

Traverse sources sequentially. Advance each successfully traversed source to its newest
discovered stored project, retaining null if none qualifies. A missing old checkpoint causes a
complete traversal and a report warning. `--full-scan` ignores checkpoints for all configured
sources of the selected agency; stored historical projects are still skipped.

Merge successful discovery results by canonical project ID. A project appearing in several
profiles is processed once. If any listing describes it as completed, inspect the project page;
that page determines whether it is actually complete. Prefer its description for year parsing,
as in the current parser; conflicting fallback descriptions must not silently select a guessed
event year. Keep an unresolved project pending with the parsing error in the report.

A listing failure affects that source: discard its incomplete discovery results and preserve
its checkpoint. Continue other sources and retry already-known pending projects independently,
even when every listing fails. Valid completed projects from those retries may still publish.
Keep unfinished and failed projects pending, removing an entry only when its valid record is
already stored or is included in the applied candidate database. A successful fetch from another
profile must not be overridden by an earlier failure for the same project.

If every discovery and pending-project operation fails, report failure and apply nothing,
including progress. Otherwise stage the valid results and applicable progress, retaining failed
sources' checkpoints. A successful pending check that finds an unfinished project may update
progress without changing records or freshness. Configuration/record-validation failures remain
fatal for the whole stage.

Keep sequential requests, one-second spacing, 30-second timeout, and three attempts. Detect
pagination loops. An empty/unrecognized listing is a source failure unless the parser can
positively recognize a valid empty listing.

### Staging and application

Stage `candidate_database.json`, `candidate_metadata.json`, `candidate_progress.json`, and
`run_report.json` under a directory containing agency ID, workflow run ID, and attempt. Extend
the report with `schemaVersion`, `agencyId`, scraper/discovery-source identities, source-file SHA-256
fingerprints, `metadataChanged`, and the existing change/failure fields. Fingerprints cover the
input database, metadata, and progress so stale stages can be rejected before replacement.
Include source-level discovery outcomes, project-level failures, and an overall `outcome` of
`success`, `partial`, or `failed`. Partial means some operations failed while others succeeded;
it does not necessarily mean records changed. A partial stage remains eligible for application.
Fatal configuration/validation or total operational failure returns failure and is not applied.

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

If push succeeds but the build or Pages deployment fails, retain the committed update and
report deployment failure. Recover by rerunning the build/deployment at the recorded commit,
or at a newer revision containing it if it has been superseded. Do not deploy an old revision
over a newer successful release. Do not rely on rerunning the scraper: it may find no record
changes and correctly skip the rebuild, leaving the previous site deployed.

## 8. GitHub Actions

Add a required `agency` input to `update-data.yml` with `type: choice`, default `heroines`, and
options `heroines` and `madsink`. The Japanese description is `更新する事務所`. Preserve `dry_run` and `full_scan` as booleans.
One invocation selects one agency; there is no `all` option or parallel matrix.

GitHub supports a single-choice manual input whose result is a string. Maintain its declared
options alongside registry IDs; do not depend on a job reading JSON to populate the dispatch
form. Treat this synchronization as an onboarding/release check. See
[GitHub manual workflow inputs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onworkflow_dispatchinputs).

After checkout of current `main` and tests, pass the input through an environment variable and
quoted `--agency` argument to both staging and application. Resolve paths inside Python. Use the
agency/run/attempt in the output directory and artifact name; upload available reports on failure.
Dry runs execute discovery/parsing/staging but skip apply, backups, commits, pushes, and rebuilds.

Report partial runs with prominent workflow warning annotations, a summary identifying failed
sources/projects and what was published, and the full report artifact. Return success from a
valid partial staging step so apply/rebuild can run; do not mark ordinary source failures as a
fatal stage. Total operational failure or invalid configuration/data fails the step and skips
apply. Keep these coverage diagnostics in GitHub; do not publish an incomplete-update notice
or a separate last-scrape timestamp in the SPA.

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

## 9. Delivery order and future agency onboarding

Implementation order was frontend and browser checks, scraper/application validation, then workflow
changes and reviewed initial MAD’S iNK data. Heroines records remain unchanged in Git;
its checkpoint `990003` and all 14 pending entries were migrated losslessly. Heroines metadata
uses the verified content-changing commit `58782adf3287841bccc38f251cd7bc247c2d2fa1`
(`2026-11-12T06:22:24Z`).

This delivery is a GitHub feature branch. Live main-branch update/deployment checks belong to the
subsequent release after merge; they are not performed or claimed by local branch validation.
The manual build now accepts `checkout-ref` and refuses deployment when that revision has been
superseded on main. Recover using current main containing the data update, without another scrape.

For subsequent agency onboarding:

1. Choose its ID, official proper-name label, public attribution URLs, and one or more discovery
   sources with stable IDs and listing URLs.
2. Test representative finished, unfinished, and unusual/joint-member project pages with the
   current scraper; add a different scraper module only if necessary and review its workflow requirements.
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
backup without metadata, recover a verified content-update date from Git history or use `null`
if unavailable. Review or full-scan if retained per-source checkpoints
could skip records removed by restoration. Never restore another agency's files.

## 10. Acceptance and validation

### Frontend

- Default shows exactly `heroines/imaginate`, existing records/columns, both attribution links,
  and truthful freshness adjacent to the selector. The heading follows the selected agency's
  proper-name label; surrounding UI copy is Japanese.
- With two synthetic agencies having disjoint groups/members/years/funding ranges, A → B → A
  recreates rows and filter indexes/counts while restoring A's saved draft/applied filters,
  sorting, page size, and page number. Unapplied drafts remain unapplied, and B's settings stay
  independent. Refresh clears the session memory and returns to heroines.
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

- Tests cover agency resolution, unknown agency/scraper IDs, duplicate/colliding paths, missing files,
  metadata/progress ID mismatch, and workflow-choice/registry consistency.
- New null checkpoints discover each configured listing without using heroines' checkpoint;
  existing heroines progress survives the upgrade; pending retries remain scoped to their agency.
  Overlapping profiles process/store a project only once and maintain independent checkpoints.
- Fixture pages prove compatibility with the current parser and its common input/output contract,
  without requiring adapter extraction. Failed listings keep their checkpoints while valid results
  from other profiles publish. Even all-listing failure allows valid pending-project completions
  to publish; total operational failure applies nothing. Unresolved projects remain pending.
- Partial-run warnings, summaries, and source/project reports are visible in GitHub only. Valid
  partial stages can apply/deploy, while fatal stages cannot.
- A normal B update changes only B's records/metadata/progress/backups. Hash A's files before/after
  to prove isolation. Semantic no-op, progress-only, failure, and dry-run cases follow the outcome table.
- Tests reject stale source fingerprints, wrong-agency stages, malformed/missing candidates, and
  inconsistent change flags before any replacement. Failure during apply does not commit partial data.
- Backup records and metadata match the previous files exactly. A rejected push causes no rebuild;
  successful public changes rebuild at the returned SHA. Metadata-only correction also rebuilds.
- A fresh site build without record changes preserves all agency timestamps. The deployed site
  associates its timestamp and source links with the same agency as its displayed records.
- After successful push and failed deployment, recovery builds the recorded or superseding
  revision without requiring another record change. No recovery rolls back a newer release.

For implementation validation run `bun run check`, `bun run build`,
`python -m unittest discover -s scrape_data -p 'test_*.py' -v`, and formatting for changed files.
Add processor/isolation tests in `src/lib/procData.test.js` using Bun, add configuration tests in
`scrape_data/test_agency_config.py`, and extend `test_scraper.py`/`test_apply_update.py` with Python
fixtures for pipeline behavior. Use browser interaction for the remount/race/layout cases.
Use temporary fixture databases for multi-agency validation, not fabricated production records.

Validation evidence and limitations are recorded in
[2026-11-15-multiple_agency.md](../validation/2026-11-15-multiple_agency.md).
Live Pages publication remains a release operation after this branch is merged.

## 11. Document lifecycle

Keep this document in `docs/specs/` with the convention `YYYY-MM-DD-<status>-<feature>.md`.
The creation date and `multiple_agency` feature name stay fixed. Rename `design` to `spec` after
the design is finalized with user agreement; rename `spec` to `implemented` only after the confirmed feature
and required validation are complete. Update this header and links in `AGENTS.md` on each rename.
Finalizing a design does not authorize implementation or imply that the proposed files exist.
