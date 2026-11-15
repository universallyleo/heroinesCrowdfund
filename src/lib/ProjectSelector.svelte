<script>
	// @ts-nocheck
	import { MoneyString } from './procData.js';
	import { createAgencyState, applyDraft, resetFilters } from './agencyState.js';
	import GroupFilter from './GroupFilter.svelte';
	let { view, settings = $bindable() } = $props();
	let error = $state('');
	const collator = new Intl.Collator('ja');
	let gps = $derived([...view.gpMap.keys()].sort(collator.compare));
	let bounds = $derived(createAgencyState(view).draft);
	let members = $derived(
		[...new Set(settings.draft.groups.flatMap((gp) => [...(view.gpMap.get(gp)?.mbs ?? [])]))].sort(
			collator.compare
		)
	);
	$effect(() => {
		if (settings.draft.member && !members.includes(settings.draft.member))
			settings.draft.member = '';
	});
	function apply() {
		try {
			applyDraft(settings);
			error = '';
		} catch (e) {
			error = e.message;
		}
	}
</script>

<aside>
	<h2>絞り込む</h2>
	<div class="filter-group group-filter-container">
		<GroupFilter {gps} gpMap={view.gpMap} bind:selected={settings.draft.groups} />
	</div>
	<div class="filter-group">
		<label
			>メンバー<select bind:value={settings.draft.member}
				><option value="">全員</option>{#each members as mb}<option value={mb}>{mb}</option
					>{/each}</select
			></label
		>
	</div>
	<div class="filter-group">
		<label
			>イベント実施年<select bind:value={settings.draft.year}
				><option value="">全部</option
				>{#each [...view.yrSelection].sort((a, b) => b - a) as year}<option value={year}
						>{year}</option
					>{/each}</select
			></label
		>
	</div>
	<div class="filter-group">
		<span>支援額範囲（千円）</span>
		<label class="range-label"
			><span class="label-text">最小: {MoneyString(settings.draft.minFund)}</span><input
				type="range"
				bind:value={settings.draft.minFund}
				min={bounds.minFund}
				max={bounds.maxFund}
				step="1"
			/></label
		>
		<label class="range-label"
			><span class="label-text">最大: {MoneyString(settings.draft.maxFund)}</span><input
				type="range"
				bind:value={settings.draft.maxFund}
				min={bounds.minFund}
				max={bounds.maxFund}
				step="1"
			/></label
		>
	</div>
	{#if error}<p role="alert">{error}</p>{/if}
	<div class="filter-btns">
		<button onclick={apply}>条件を適用</button><button
			onclick={() => {
				resetFilters(settings, view);
				error = '';
			}}>リセット</button
		>
	</div>
</aside>

<style>
	aside {
		font-family: var(--font-body);
		background: var(--panel);
		border: 1px solid var(--border);
		border-radius: 10px;
		padding: 12px;
	}

	aside > h2 {
		margin: 0 0 0.4em 0;
		font-weight: normal;
		font-size: 1.17em;
		text-align: center;
	}

	.filter-btns {
		margin: 2px auto;
	}

	.filter-group {
		margin-bottom: 1.3em;
		min-width: 0;
	}

	.filter-group label:not(.range-label) {
		display: block;
		margin-bottom: 0.5em;
	}

	.filter-group input,
	.filter-group select {
		width: 100%;
		padding: 6px;
		border: 1px solid var(--border);
		border-radius: 6px;
	}

	.range-label {
		display: grid;
		grid-template-rows: auto 1fr;
		row-gap: 0.25rem;
		/* margin: 0.2em 0.5em; */
		margin-right: 1em;
		min-width: 0;
	}

	.range-label > .label-text {
		white-space: nowrap;
	}

	.range-label > input[type='range'] {
		margin: 0 auto;
		width: 95%;
		min-width: 0;
	}

	@media screen and (max-width: 999px) {
		.filter-group {
			margin-bottom: 0.2em;
		}

		/* Make label + select appear inline on small screens */
		.filter-group > label:not(.range-label) {
			display: flex;
			flex-direction: row;
			align-items: center;
			justify-content: space-between;
			gap: 0.5rem;
			margin-bottom: 0;
		}

		.filter-group > label:not(.range-label) > select {
			width: auto;
			min-width: 60%;
			flex: 0 0 auto;
		}

		/* Make range-label a single row on small screens */
		.range-label {
			display: grid;
			grid-template-columns: 1fr 60%; /* left flexible, right fixed 60% */
			align-items: center; /* vertical center */
			column-gap: 0.5rem;
			width: 100%;
		}

		.range-label .label-text {
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
			min-width: 0; /* important so the label can shrink */
		}

		.range-label input[type='range'] {
			justify-self: end; /* ensures it sits at the right edge of that column */
			box-sizing: border-box;
		}
	}
</style>
