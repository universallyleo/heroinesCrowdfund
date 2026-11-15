<script>
	// @ts-nocheck
	import { untrack } from 'svelte';
	import { TableHandler, Datatable, RowCount, Pagination } from '@vincjo/datatables';
	import { MoneyString } from './procData.js';
	import { filterAgencyRows } from './agencyState.js';
	import ProjectSelector from './ProjectSelector.svelte';
	import PeriodCell from './PeriodCell.svelte';
	import GroupMemberCell from './GroupMemberCell.svelte';
	import ReturnItemCell from './ReturnItemCell.svelte';
	import EventTypeCell from './EventTypeCell.svelte';
	import ThSortCustom from './ThSortCustom.svelte';
	let { view, settings = $bindable() } = $props();
	const table = untrack(
		() =>
			new TableHandler(filterAgencyRows(view.processedData, settings.applied), {
				rowsPerPage: settings.pageSize,
				i18n: {
					search: '検索…',
					show: '',
					entries: '件表示／ページ',
					filter: '絞り込み',
					rowCount: '全 {total} 件中 {start}〜{end} 件を表示',
					noRows: '該当するプロジェクトはありません',
					previous: '‹ 前',
					next: '次 ›',
					selectedCount: '全 {total} 件中 {count} 件選択'
				}
			})
	);
	const sorts = Object.fromEntries(
		['member', 'total', 'totalpatrons', 'averageFund', 'period'].map((field) => [
			field,
			table.createSort(field)
		])
	);
	untrack(() => {
		if (settings.sort) sorts[settings.sort.field].init(settings.sort.direction);
		table.setPage(Math.min(settings.page, Math.max(1, table.pageCount)));
	});
	$effect(() => {
		const applied = settings.applied;
		untrack(() => {
			table.setRows(filterAgencyRows(view.processedData, applied));
			table.setPage(settings.page);
		});
	});
	$effect(() => {
		const page = table.currentPage,
			pageSize = table.rowsPerPage,
			sort = table.sort;
		untrack(() => {
			settings.page = page;
			settings.pageSize = pageSize;
			settings.sort = sort.direction
				? {
						field: Object.keys(sorts).find((key) => sorts[key].id === sort.id),
						direction: sort.direction
					}
				: null;
		});
	});
	function onSort(sort) {
		const direction = sort.direction === 'asc' ? 'desc' : 'asc';
		table.clearSort();
		sort.init(direction);
	}
	let htmlTbl = $state(null);
	const fundColor = (total) =>
		total < 1_000_000
			? '#fff7ee'
			: total < 4_000_000
				? '#ffcccf'
				: total < 8_000_000
					? '#ffb995'
					: '#ff7200';
</script>

<div class="agency-projects">
	<ProjectSelector {view} bind:settings />
	<section>
		<div class="tbContainer">
			{#if table.allRows.length === 0}<p role="status">
					条件に一致するプロジェクトがありません。
				</p>{/if}
			<Datatable headless {table}>
				{#snippet header()}
					<label class="page-size"
						>表示件数
						<select
							aria-label="表示件数"
							value={table.rowsPerPage}
							onchange={(event) => table.setRowsPerPage(Number(event.currentTarget.value))}
						>
							{#each [5, 10, 20, 50, 100, 200, 300] as size}<option value={size}>{size}</option
								>{/each}
						</select> 件／ページ</label
					>
				{/snippet}
				<table class="dt" bind:this={htmlTbl}>
					<thead>
						<tr>
							<th class="narrow frozenHeader"> # </th>
							<ThSortCustom {onSort} sort={sorts.member} frozen={true}>メンバー</ThSortCustom>
							<ThSortCustom {onSort} sort={sorts.total}>総支援額</ThSortCustom>
							<ThSortCustom {onSort} sort={sorts.totalpatrons}>支援者数</ThSortCustom>
							<ThSortCustom {onSort} sort={sorts.averageFund}>平均支援額</ThSortCustom>
							<ThSortCustom {onSort} sort={sorts.period}>クラファ期間</ThSortCustom>
							<th>イベント</th>
							<th>各リターン品支援額・人数</th>
						</tr>
					</thead>
					<tbody>
						{#each table.rows as row, i}
							<tr>
								<td class="narrow frozen">
									{(table.currentPage - 1) * table.rowsPerPage + i + 1}
								</td>
								<td class="GpMbCell frozen"><GroupMemberCell {row} /></td>
								<td>
									<span class="totalfund" style="--totalFundBGC:{fundColor(row.total)}">
										{MoneyString(row.total)}
									</span>
								</td>
								<td style="text-align: right; ">{row.totalpatrons}</td>
								<td style="text-align: right; ">
									{row.averageFund === null ? '—' : MoneyString(row.averageFund.toFixed(0))}
								</td>
								<td><PeriodCell {row} /></td>
								<td><EventTypeCell {row} /></td>
								<td><ReturnItemCell {row} /></td>
							</tr>
						{/each}
					</tbody>
				</table>
				{#snippet footer()}
					<RowCount {table} />
					<Pagination {table} />
				{/snippet}
			</Datatable>
		</div>
	</section>
</div>

<style>
	.agency-projects {
		display: grid;
		grid-template-columns: max(15%, 10em) minmax(0, 1fr);
		gap: 12px;
		min-width: 0;
	}
	.page-size {
		display: block;
		margin: 8px 16px;
		color: var(--muted);
	}
	@media (max-width: 999px) {
		.agency-projects {
			grid-template-columns: minmax(0, 1fr);
		}
	}
	section {
		background: var(--panel);
		border: 1px solid var(--border);
		border-radius: 10px;
		overflow: hidden;
	}

	section :global(footer) {
		border-top: 1px solid var(--border-strong);
	}

	.tbContainer {
		width: 96%;
		height: 90%;
		margin: 1em auto;
	}

	/* :global(.wx-row:nth-child(even)) {
		--wx-background: hsl(0, 0%, 97%);
	} */

	.dt {
		border-collapse: collapse;
	}
	.dt :global(thead th) {
		/* background-color: var(--bg); */
		background-color: var(--bg-emph2);
		/* border-left: 1px solid var(--border-strong); */
	}

	.dt td {
		padding: 0.4em;
		border: 1px solid var(--tb-border-color);
	}

	.dt .GpMbCell {
		min-width: 12em;
	}

	.dt tbody tr:hover {
		background: var(--weak-hilight);
	}

	.dt .narrow {
		text-align: right;
		padding: 3px;
	}

	.dt .frozen {
		background: var(--bg);
		position: sticky;
		left: 0;
		z-index: 2;
	}

	/* Keep the member and row-number columns visible during horizontal scrolling. */
	.dt .GpMbCell {
		left: 2.4em;
	}
	.dt :global(th.frozen) {
		left: 2.4em;
		z-index: 3;
	}
	.dt .narrow {
		min-width: 2.4em;
		box-sizing: border-box;
	}
	.dt .frozenHeader {
		position: sticky;
		left: 0;
		top: 0;
		z-index: 4;
		background-color: var(--bg-emph2);
	}

	.totalfund {
		background-color: var(--totalFundBGC);
		display: flex;
		align-items: center;
		justify-content: flex-end;
		font-size: large;
		font-weight: bold;
		padding: 0.4em;
		height: 100%;
	}

	@media screen and (max-width: 999px) {
		section {
			border-radius: 0px;
			/* allow the section to take remaining space */
			min-height: 90vh;
			overflow: hidden;
		}

		.tbContainer {
			width: 100%;
			height: 95%;
			margin: 0.5em 0;
			overflow: auto; /* scroll if content exceeds available space */
		}
	}
</style>
