# Multiple-agency validation

Date: 2026-11-15 (Asia/Tokyo). Branch: `codex/multiple-agency`.

## Data provenance and review

- MAD’S iNK discovery used its [CAMPFIRE posted-project listing](https://camp-fire.jp/profile/madsink/projects/post).
  One listing page contained 28 projects: 27 completed, one unfinished (`991831`).
  The initial stage had no failed projects or discovery failures. Requests used the shared
  sequential, one-second-spaced fetcher. Cached responses were reused during parser validation.
- Reviewed all 27 normalized subjects, event years, dates, totals, supporter counts and reward
  denominations. Canonical URLs are unique; records pass the shared schema validator.
  Total reported funding is ¥71,467,130; reported supporter counts sum to 2,057.
  Reward-derived totals are deliberately separate from CAMPFIRE's reported funding/supporters.
- Group reference: [Jpop Wiki agency page](https://jpop.fandom.com/wiki/MAD%27S_iNK), with
  individual group references in `scrape_data/madsink_members.json`. The user confirmed latest
  groups for historical events, main/collaboration order and `/` separator, all five MADS PRINCE
  aliases, and MADMED for former members without a newer known group.
- Applied only MAD’S iNK's staged records/metadata/progress locally, with an exact empty-database
  and null-metadata backup pair. No `--publish` invocation was made against this checkout.
- Heroines' 340-record database has the same Git content hash as the base commit (checkout CRLF is normalized by Git).
  Checkpoint `990003` and 14 pending records were migrated without losing fields; each pending
  entry gained `sourceIds: ["heroines"]`. Metadata uses the verified content-changing Git commit
  `58782adf3287841bccc38f251cd7bc247c2d2fa1`, dated `2026-11-12T06:22:24Z`.

## Automated and browser checks

- Final verification: 6 Bun tests and 29 Python tests passed. `bun run check` found zero errors;
  `bun run build` passed both normally and with `BASE_PATH=/heroinesCrowdfund`.
- Bun tests cover processing/index isolation, raw-data immutability, zero supporters/empty data,
  actual calendar-day intervals, separate draft/applied filters, filter reset, load retry/cache,
  stale completion suppression, and invalid registry/default handling.
- Python tests cover registry/path/ownership validation, lossless progress migration, source
  deduplication, failed-source checkpoint retention, all-listing failure with pending success,
  no-op freshness, selected-agency isolation, title/year/group parsing, exact backup pairs,
  stale/wrong/missing stages, semantic flags, metadata-only correction, rollback, and rejection
  of a non-fast-forward publication to a temporary local Git remote.
- Registry IDs and manual workflow choices are checked together. Workflow YAML is parsed locally.
- Svelte checks report zero errors and one pre-existing unused `body` CSS warning. The baseline
  had twelve warnings; the removed singleton filter implementation accounted for the others.
- Browser checks verify selection changes title/attribution/date, empty state, and A → B → A
  restores sorting, page size/page, and an unapplied member draft without applying it. Applying
  and resetting filters return to page 1 while preserving sort/page size. The 375px header has
  no page overflow. A switch-time remount bug found during these checks was fixed by requiring
  the loaded result's agency ID to match the current selection before rendering the subtree.
- With both real snapshots populated, MAD’S iNK → heroines → MAD’S iNK restored the exact
  sorted page-2 rows, five-row page size, and unapplied member draft. Heroines retained its
  independent 20-row page size and member draft. Applying the MAD’S iNK draft selected the one
  matching project; reset restored all 27 records on page 1 and kept sorting/page size.
- At 375px, the populated table has its own horizontal scrolling container and no page overflow.
  The production preview at `/heroinesCrowdfund/` loaded all 340 heroines and 27 MAD’S iNK records
  via the selector, with no browser warnings/errors. The development page also had no new errors
  after the dependency repair. Snapshot loaders include only the two configured record paths;
  archived backups and scraper progress are excluded.
- Final manual review covered selection/session lifetime, staged validation/publication, and the
  workflows. It restored neutral WebSite structured metadata and added `contents: read` to the
  deployment job for its current-main check. The requested independent agent review could not
  run because the reviewer hit its usage limit; no independent review approval is claimed.

## Release boundary

This is feature-branch delivery. Main was not merged, scraped, pushed, or deployed by this task.
The modified production workflows have not been dispatched against main. After merge, run an
agency-selected dry run, inspect its report, and verify normal publication/Pages deployment.
The workflow's manual build recovery accepts a revision and refuses obsolete deployments;
recover at current main containing the update. Production failure/recovery was not simulated.

The local dev server is left running for the user's review.
