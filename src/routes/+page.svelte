<script>
	// @ts-nocheck
	import ghlogo from '$lib/assets/github.svg';
	import xicon from '$lib/assets/X_icon.svg';
	import ProjectSelector from '$lib/ProjectSelector.svelte';

	import { Grid } from '@svar-ui/svelte-grid';
	import { Willow } from '@svar-ui/svelte-core';
	import { processedData } from '$lib/procData';
	import TotalFundCell from '$lib/TotalFundCell.svelte';
	import PeriodCell from '$lib/PeriodCell.svelte';
	import GroupMemberCell from '$lib/GroupMemberCell.svelte';
	import ReturnItemCell from '$lib/ReturnItemCell.svelte';
	import EventTypeCell from '$lib/EventTypeCell.svelte';

	const data = processedData;
	console.log('called from DT.svelte', data);

	const columns = [
		// {
		// 	id: 'id',
		// 	width: 45,
		// 	sort: true
		// },
		{
			id: 'member',
			header: 'メンバー',
			cell: GroupMemberCell,
			width: 185
		},
		{
			id: 'total',
			header: '総支援額',
			cell: TotalFundCell,
			width: 130,
			sort: true
		},
		{
			id: 'totalpatrons',
			header: '支援者数',
			width: 75,
			sort: true
		},
		{
			id: 'averageFund',
			header: '平均支援額',
			width: 95,
			sort: true
		},
		{
			id: 'period',
			header: 'クラファ期間',
			cell: PeriodCell,
			width: 150,
			sort: true
		},
		{
			id: 'type',
			header: 'イベント',
			width: 80,
			cell: EventTypeCell,
			sort: true
		},
		{
			id: 'ppTotal',
			header: { text: '各リターン品支援額・人数' },
			cell: ReturnItemCell,
			width: 540
		}
	];
	/** @type {import("@svar-ui/svelte-grid").ISortMarks} */
	const sortMarks = {
		id: { order: 'asc' },
		// type: { order: 'asc' },
		total: { order: 'desc' },
		totalpatrons: { order: 'desc' },
		averageFund: { order: 'desc' },
		period: { order: 'asc' }
	};
	// const left = 4; // freeze 5 colns
	const left = 0;

	let localGrid = $state();
	// $effect(() => {
	// 	if (localGrid) {
	// 		grid.set(localGrid);
	// 	}
	// });
</script>

<!-- <ProjectOverview /> -->

<main>
	<header>
		<h1>ヒロインズ &nbsp; クラファ データ</h1>
	</header>
	<ProjectSelector grid={localGrid} />

	<section>
		<div class="tbContainer">
			<Willow>
				<Grid
					bind:this={localGrid}
					{data}
					{columns}
					{sortMarks}
					split={{ left }}
					sizes={{ rowHeight: 58 }}
					columnStyle={(col) =>
						col.id === 'totalpatrons' || col.id === 'averageFund' ? 'columnStyle' : ''}
				/>
			</Willow>
		</div>
	</section>
	<footer>
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
		</div>
	</footer>
</main>

<style>
	main {
		display: grid;
		height: 90vh;
		grid-template-columns: max(12%, 8em) 1fr;
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
		--wx-table-select-background: #eaedf5;
		--wx-table-select-focus-background: #ebedf3;
		--wx-table-select-color: var(--wx-color-font);
		--wx-table-border: 1px solid #e6e6e6;
		--wx-table-select-border: inset 3px 0 var(--wx-color-primary);
		--wx-table-header-border: var(--wx-table-border);
		--wx-table-header-cell-border: var(--wx-table-border);
		--wx-table-footer-cell-border: var(--wx-table-border);
		--wx-table-cell-border: var(--wx-table-border);
		--wx-header-font-weight: 600;
		--wx-table-header-background: hsl(228, 24%, 92%);
		--wx-table-fixed-column-right-border: 3px solid #e6e6e6;
	}

	:global(.wx-row:nth-child(even)) {
		--wx-background: hsl(0, 0%, 97%);
	}
	/*  this is recommended officially but didnot work as --wx-background took priority :/
	:global(.rowStyle:nth-child(even)) {
		background-color: cyan;
	} */

	:global(.columnStyle) {
		text-align: end;
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
