<script>
	// @ts-nocheck
	import ghlogo from '$lib/assets/github.svg';
	import xicon from '$lib/assets/X_icon.svg';
	import ProjectSelector from '$lib/ProjectSelector.svelte';

	import { MoneyString, processedData } from '$lib/procData';
	import PeriodCell from '$lib/PeriodCell.svelte';
	import GroupMemberCell from '$lib/GroupMemberCell.svelte';
	import ReturnItemCell from '$lib/ReturnItemCell.svelte';
	import EventTypeCell from '$lib/EventTypeCell.svelte';

	import { TableHandler, Datatable, RowsPerPage, RowCount, Pagination } from '@vincjo/datatables';
	import { onMount } from 'svelte';
	import ThSortCustom from '$lib/ThSortCustom.svelte';

	const data = processedData;
	// console.log('called from DT.svelte', data);
	const table = new TableHandler(data, {
		i18n: {
			search: 'Search...',
			show: '',
			entries: '件表示／ページ',
			filter: 'Filter',
			rowCount: '全 {total} 件中 {start}〜{end} 件を表示',
			noRows: 'No entries found',
			previous: '‹ 前',
			next: '次 ›',
			selectedCount: '全 {total} 件中 {count}件.'
		}
	});
	// !! using vinjo's frozen will make the frozen columns resizes (widen) itself when another column trigger a sort
	// onMount(() => {
	// table.createView([
	// 	{ index: 0, isFrozen: true },
	// 	{ index: 1, isFrozen: true }
	// ]);
	// });
	// following is an attempt to fix this issue, but it is not perfect

	let htmlTbl = $state(null);
	onMount(() => {
		const frozen = htmlTbl.querySelectorAll(`.narrow, .frozen`);
		for (const cell of frozen) {
			cell.style.position = 'sticky';
			cell.style.left = '0px'; // TODO: should calculate this correctly, now it will just push all frozen column to 0px
			cell.style.zIndex = '15';
		}
	});

	const fundColor = (total) =>
		total < 1_000_000
			? '#fff7ee'
			: total < 4_000_000
				? '#ffcccf'
				: total < 8_000_000
					? '#ffb995'
					: '#ff7200';

	const buildDate = __BUILD_DATE__.slice(0, 10);
</script>

<svelte:head>
	<title>HEROINES クラファ記録</title>
	<meta name="description" content="ヒロインズ クラウドファンディング記録" />
	<meta property="og:site_name" content="ヒロインズ クラウドファンディング記録" />
	<meta property="og:title" content="ヒロインズ クラウドファンディング記録" />
	<script type="application/ld+json">
        {JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            name: 'ヒロインズ クラウドファンディング記録',
            url: 'https://universallyleo.github.io/heroinesCrowdfund/'
        })}
	</script>
</svelte:head>

<main>
	<header>
		<h1>ヒロインズ &nbsp; クラファ 記録</h1>
	</header>
	<ProjectSelector {table} />
	<section>
		<div class="tbContainer">
			<Datatable headless {table}>
				{#snippet header()}
					<RowsPerPage {table} options={[5, 10, 20, 50, 100, 200, 300]} />
				{/snippet}
				<table class="dt" bind:this={htmlTbl}>
					<thead>
						<tr>
							<th class="narrow frozenHeader"> # </th>
							<ThSortCustom {table} field="member" frozen={true}>メンバー</ThSortCustom>
							<ThSortCustom {table} field="total">総支援額</ThSortCustom>
							<ThSortCustom {table} field="totalpatrons">支援者数</ThSortCustom>
							<ThSortCustom {table} field="averageFund">平均支援額</ThSortCustom>
							<ThSortCustom {table} field="period">クラファ期間</ThSortCustom>
							<th>イベント</th>
							<th>各リターン品支援額・人数</th>
						</tr>
					</thead>
					<tbody>
						{#each table.rows as row, i}
							<tr>
								<td class="narrow frozen"> {i + 1} </td>
								<td class="GpMbCell frozen"><GroupMemberCell {row} /></td>
								<td>
									<span class="totalfund" style="--totalFundBGC:{fundColor(row.total)}">
										{MoneyString(row.total)}
									</span>
								</td>
								<td style="text-align: right; ">{row.totalpatrons}</td>
								<td style="text-align: right; ">
									{MoneyString(row.averageFund.toFixed(0))}
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

	<footer>
		<div>更新：{buildDate}</div>
		<div>
			データソース: camp-fire
			<a href="https://camp-fire.jp/profile/heroines"> heroines </a>
			&nbsp;,&nbsp; <a href="https://camp-fire.jp/profile/imaginate">imaginate </a> ページ
		</div>
		<div>
			<a href="https://github.com/universallyleo/heroinesCrowdfund">
				<img width="32" src={ghlogo} alt="Source Code" />
			</a>
			&nbsp;&nbsp;
			<a href="https://x.com/55gohan06">
				<img width="32" src={xicon} alt="Twitter" />
			</a>
			&nbsp;&nbsp;
			<a href="https://universallyleo.github.io/heroinesLeague/"> ヒロインズリーグ記録 </a>
		</div>
	</footer>
</main>

<style>
	main {
		display: grid;
		height: 90vh;
		grid-template-columns: max(15%, 10em) 1fr;
		grid-template-rows: auto 1fr auto;
		gap: 12px;
		padding: 12px;
		font-family: var(--font-body);
	}

	header {
		grid-column: 1 / -1;
		padding: 1em;
		background: var(--panel);
	}

	header h1 {
		margin: 0;
		font-size: 1.8rem;
		font-weight: bold;
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

	footer {
		display: flex;
		flex-direction: column;
		text-align: center;
		line-height: 3.5ch;
		justify-content: center;
		align-items: center;
		padding: 0.5em;
		border-top: 1px solid var(--muted);
		grid-column: 1 / -1;
		color: var(--muted);
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
	}

	/* does not do anything, just for querySelector to select frozen header */
	.dt .frozenHeader {
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
		main {
			/* switch to single column on small screens */
			grid-template-columns: 1fr;
			/* header (ProjectSelector) + content */
			grid-template-rows: auto 1fr;
			gap: 1em;
			height: 98vh; /* occupy full viewport */
			min-height: 98vh;
		}

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
